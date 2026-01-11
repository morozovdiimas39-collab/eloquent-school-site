import json
import os
import psycopg2
# Force redeploy v7 - fixed context exercise generation via Gemini
import urllib.request
import urllib.parse
import random
import re
import requests
import base64
import tempfile
from typing import Dict, Any, List

SCHEMA = 't_p86463701_eloquent_school_site'

def get_subscription_plans() -> dict:
    """Загружает актуальные тарифные планы из БД (ТОЛЬКО ИЗ АДМИНКИ!)"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT plan_key, name, description, price_rub, price_kop, duration_days "
        f"FROM {SCHEMA}.pricing_plans ORDER BY price_rub"
    )
    
    plans = {}
    for row in cur.fetchall():
        plans[row[0]] = {
            'name': row[1],
            'description': row[2],
            'price_rub': row[3],
            'price_kop': row[4],
            'duration_days': row[5]
        }
    
    cur.close()
    conn.close()
    
    print(f"[DEBUG] Loaded {len(plans)} pricing plans from DB: {plans}")
    return plans

# Глобальный кэш для оптимизации ensure_user_has_words (живет только в рамках одного запроса)
_words_ensured_cache = {}

def clean_gemini_json(text: str) -> str:
    """Очищает ответ Gemini от markdown и фиксит невалидный JSON"""
    # Удаляем markdown блоки
    text = text.replace('```json', '').replace('```', '').strip()
    
    # Пытаемся найти JSON объект в тексте
    # Ищем первую { и последнюю }
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    # Если не нашли закрывающую скобку - добавляем её
    if start_idx != -1:
        if end_idx == -1 or end_idx < start_idx:
            # JSON не закрыт - добавляем закрывающую скобку
            text = text[start_idx:] + '}'
        else:
            text = text[start_idx:end_idx+1]
    
    # Убираем все переносы строк и лишние пробелы внутри JSON
    # Это агрессивный подход, но работает для простых структур
    text = ' '.join(text.split())
    
    return text.strip()

def safe_json_parse(text: str, fallback_fields: dict = None) -> dict:
    """Безопасный парсинг JSON с fallback на regex извлечение"""
    try:
        cleaned = clean_gemini_json(text)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"[WARNING] JSON parse failed: {e}, trying aggressive fix...")
        
        # Агрессивная починка JSON
        try:
            fixed = clean_gemini_json(text)
            
            # ⚠️ CRITICAL: Удаляем незавершенные строки внутри массивов
            # Ищем последнюю открывающую кавычку без закрывающей
            # Паттерн: "текст без закрывающей кавычки до конца строки/файла
            fixed = re.sub(r'"[^"]*$', '"', fixed)  # Закрываем последнюю незавершенную строку
            
            # Удаляем trailing commas
            fixed = re.sub(r',\s*}', '}', fixed)
            fixed = re.sub(r',\s*]', ']', fixed)
            
            # Удаляем незавершенные элементы после последней запятой
            last_comma_idx = fixed.rfind(',')
            last_closing_brace = max(fixed.rfind('}'), fixed.rfind(']'))
            
            if last_comma_idx > last_closing_brace and last_comma_idx != -1:
                # Есть запятая после последней закрывающей скобки - обрезаем до последней завершенной строки
                # Ищем последнюю завершенную строку перед этой запятой
                last_complete_string = fixed.rfind('"', 0, last_comma_idx)
                if last_complete_string != -1:
                    fixed = fixed[:last_complete_string + 1]
            
            # Закрываем незакрытые скобки
            open_braces = fixed.count('{')
            close_braces = fixed.count('}')
            if open_braces > close_braces:
                fixed += '}' * (open_braces - close_braces)
            
            open_brackets = fixed.count('[')
            close_brackets = fixed.count(']')
            if open_brackets > close_brackets:
                fixed += ']' * (open_brackets - close_brackets)
            
            print(f"[DEBUG] Attempting to parse fixed JSON...")
            result = json.loads(fixed)
            print(f"[SUCCESS] Fixed JSON successfully!")
            return result
            
        except Exception as fix_error:
            print(f"[ERROR] Failed to fix JSON: {fix_error}")
            
            # Последний fallback: извлекаем массивы через regex
            if fallback_fields is None:
                fallback_fields = {}
            
            result = fallback_fields.copy()
            
            # Извлекаем строковые поля: "key": "value"
            string_pattern = r'"(\w+)"\s*:\s*"([^"]*)"'
            for match in re.finditer(string_pattern, text):
                key, value = match.groups()
                result[key] = value
            
            # Извлекаем boolean поля: "key": true/false
            bool_pattern = r'"(\w+)"\s*:\s*(true|false)'
            for match in re.finditer(bool_pattern, text):
                key, value = match.groups()
                result[key] = value == 'true'
            
            # ⚠️ CRITICAL: Извлекаем массивы строк для "goals"
            # Паттерн: "goals": ["Цель 1", "Цель 2", ...]
            goals_pattern = r'"goals"\s*:\s*\[(.*?)\]'
            goals_match = re.search(goals_pattern, text, re.DOTALL)
            if goals_match:
                goals_array_content = goals_match.group(1)
                # Извлекаем все строки из массива
                string_items = re.findall(r'"([^"]+)"', goals_array_content)
                result['goals'] = string_items
                print(f"[DEBUG] Extracted {len(string_items)} goals via regex")
            
            print(f"[WARNING] Extracted fields via regex: {result}")
            return result

def get_db_connection():
    """Создает подключение к БД"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.autocommit = True
    return conn

def get_prompt_from_db(code: str, fallback: str = '') -> str:
    """Получает промпт из БД по коду, если не найден - возвращает fallback"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        code_escaped = code.replace("'", "''")
        cur.execute(
            f"SELECT prompt_text FROM {SCHEMA}.gemini_prompts "
            f"WHERE code = '{code_escaped}' AND is_active = TRUE"
        )
        row = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if row:
            return row[0]
        return fallback
    except Exception as e:
        print(f"[WARNING] Failed to load prompt '{code}' from DB: {e}")
        return fallback

def get_active_proxy_from_db() -> tuple:
    """Получает случайный активный прокси из БД - возвращает (id, url)"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT id, host, port, username, password "
        f"FROM {SCHEMA}.proxies WHERE is_active = TRUE "
        f"ORDER BY RANDOM() LIMIT 1"
    )
    
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        return None, None
    
    proxy_id, host, port, username, password = row
    
    if username and password:
        proxy_url = f"{username}:{password}@{host}:{port}"
    else:
        proxy_url = f"{host}:{port}"
    
    return proxy_id, proxy_url

def log_proxy_success(proxy_id: int):
    """Логирует успешный запрос через прокси"""
    if not proxy_id:
        return
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"UPDATE {SCHEMA}.proxies SET "
        f"total_requests = total_requests + 1, "
        f"successful_requests = successful_requests + 1, "
        f"last_used_at = CURRENT_TIMESTAMP "
        f"WHERE id = {proxy_id}"
    )
    
    cur.close()
    conn.close()

def log_proxy_failure(proxy_id: int, error_message: str):
    """Логирует ошибку прокси и автоматически отключает при >5 ошибках подряд"""
    if not proxy_id:
        return
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    error_escaped = error_message[:500].replace("'", "''")
    
    cur.execute(
        f"UPDATE {SCHEMA}.proxies SET "
        f"total_requests = total_requests + 1, "
        f"failed_requests = failed_requests + 1, "
        f"last_error = '{error_escaped}', "
        f"last_error_at = CURRENT_TIMESTAMP "
        f"WHERE id = {proxy_id}"
    )
    
    # Проверяем процент ошибок - если >80% и >3 запросов - отключаем
    cur.execute(
        f"SELECT total_requests, failed_requests FROM {SCHEMA}.proxies WHERE id = {proxy_id}"
    )
    row = cur.fetchone()
    
    if row:
        total, failed = row
        if total >= 3 and (failed / total) > 0.8:
            cur.execute(
                f"UPDATE {SCHEMA}.proxies SET is_active = FALSE WHERE id = {proxy_id}"
            )
            print(f"[WARNING] Proxy {proxy_id} auto-disabled: {failed}/{total} failures ({failed/total*100:.1f}%)")
    
    cur.close()
    conn.close()

def get_user(telegram_id: int):
    """Получает пользователя из БД"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"SELECT telegram_id, username, first_name, last_name, role, language_level, preferred_topics, conversation_mode, current_exercise_word_id, current_exercise_answer, learning_goal, urgent_goals, learning_mode FROM {SCHEMA}.users WHERE telegram_id = {telegram_id}")
    row = cur.fetchone()
    
    cur.close()
    conn.close()
    
    if row:
        return {
            'telegram_id': row[0],
            'username': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'role': row[4],
            'language_level': row[5] or 'A1',
            'preferred_topics': row[6] if row[6] else [],
            'conversation_mode': row[7] or 'dialog',
            'current_exercise_word_id': row[8],
            'current_exercise_answer': row[9],
            'learning_goal': row[10],
            'urgent_goals': row[11] if row[11] else [],
            'learning_mode': row[12] or 'standard'
        }
    return None

def auto_generate_new_words(student_id: int, how_many: int = 10) -> Dict[str, Any]:
    """Автоматически генерирует новые слова, фразы и выражения когда старые освоены"""
    try:
        print(f"[DEBUG auto_generate_new_words] Generating {how_many} new items for student {student_id}")
        
        # Получаем данные пользователя
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            f"SELECT language_level, preferred_topics FROM {SCHEMA}.users WHERE telegram_id = {student_id}"
        )
        user_data = cur.fetchone()
        
        if not user_data:
            print(f"[ERROR] User {student_id} not found")
            return {'added_count': 0, 'new_items': []}
        
        language_level = user_data[0] or 'A1'
        preferred_topics = user_data[1] or []
        
        # Получаем ВСЕ существующие слова/фразы/выражения
        cur.execute(
            f"SELECT DISTINCT w.english_text FROM {SCHEMA}.student_words sw "
            f"JOIN {SCHEMA}.words w ON w.id = sw.word_id "
            f"WHERE sw.student_id = {student_id}"
        )
        existing_words = [row[0].lower().strip() for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        print(f"[DEBUG] Student level: {language_level}")
        print(f"[DEBUG] Student has {len(existing_words)} existing items")
        
        # Генерируем новый контент через Gemini
        api_key = os.environ['GEMINI_API_KEY']
        proxy_id, proxy_url = get_active_proxy_from_db()
        if not proxy_url:
            proxy_url = os.environ.get('PROXY_URL', '')
        
        if not proxy_url:
            print(f"[ERROR] No proxy available")
            return {'added_count': 0, 'new_items': []}
        
        topics_text = ', '.join([t.get('topic', '') for t in preferred_topics[:3]]) if preferred_topics else 'general topics'
        
        # Показываем ВСЕ существующие слова для избежания дубликатов
        existing_sample = ', '.join(existing_words[:200]) if existing_words else 'none'
        
        # Определяем сколько чего генерировать в зависимости от уровня
        if language_level in ['A1', 'A2']:
            words_count = 7
            phrases_count = 2
            expressions_count = 1
        elif language_level == 'B1':
            words_count = 5
            phrases_count = 3
            expressions_count = 2
        else:  # B2, C1, C2
            words_count = 4
            phrases_count = 3
            expressions_count = 3
        
        prompt = f'''Generate NEW English learning materials for level {language_level}.
Topics: {topics_text}

⚠️ CRITICAL: DO NOT use ANY of these existing words/phrases/expressions: {existing_sample}
⚠️ EVERY item must be 100% UNIQUE and NOT in the list above!

Generate:
- {words_count} vocabulary words (single words like "achieve", "comfortable")
- {phrases_count} common phrases (2-3 word phrases like "take care", "by the way")
- {expressions_count} idioms/expressions (like "break the ice", "piece of cake")

Level guidelines:
- A1/A2: simple everyday vocabulary
- B1: common abstract concepts
- B2+: sophisticated vocabulary and idioms
- C1/C2: advanced expressions and nuanced language

Return ONLY valid JSON:
{{
  "vocabulary": [{{"english": "word1", "russian": "перевод1"}}, {{"english": "word2", "russian": "перевод2"}}],
  "phrases": [{{"english": "phrase1", "russian": "перевод1"}}, {{"english": "phrase2", "russian": "перевод2"}}],
  "expressions": [{{"english": "expression1", "russian": "перевод1"}}, {{"english": "expression2", "russian": "перевод2"}}]
}}'''

        gemini_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}'
        
        payload = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.9, 'maxOutputTokens': 3000, 'topP': 0.95}
        }
        
        proxy_handler = urllib.request.ProxyHandler({
            'http': f'http://{proxy_url}',
            'https': f'http://{proxy_url}'
        })
        opener = urllib.request.build_opener(proxy_handler)
        
        req = urllib.request.Request(
            gemini_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with opener.open(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            text = result['candidates'][0]['content']['parts'][0]['text']
            
            data = safe_json_parse(text, {'vocabulary': [], 'phrases': [], 'expressions': []})
            
            print(f"[DEBUG] Gemini generated: {len(data.get('vocabulary', []))} words, {len(data.get('phrases', []))} phrases, {len(data.get('expressions', []))} expressions")
            
            # Сохраняем в БД
            conn = get_db_connection()
            cur = conn.cursor()
            
            added_count = 0
            new_items = []
            
            # Добавляем vocabulary
            for item in data.get('vocabulary', []):
                english = item['english'].strip().lower()
                russian = item['russian'].strip()
                
                # СТРОГАЯ проверка дубликатов
                if english in existing_words:
                    print(f"[WARNING] Skipping DUPLICATE vocabulary: {english}")
                    continue
                
                english_escaped = english.replace("'", "''")
                russian_escaped = russian.replace("'", "''")
                
                cur.execute(
                    f"INSERT INTO {SCHEMA}.words (english_text, russian_translation) "
                    f"VALUES ('{english_escaped}', '{russian_escaped}') "
                    f"ON CONFLICT (english_text) DO UPDATE SET russian_translation = EXCLUDED.russian_translation "
                    f"RETURNING id"
                )
                word_id = cur.fetchone()[0]
                
                cur.execute(
                    f"INSERT INTO {SCHEMA}.student_words (student_id, word_id, teacher_id) "
                    f"VALUES ({student_id}, {word_id}, {student_id}) "
                    f"ON CONFLICT DO NOTHING"
                )
                
                existing_words.append(english)
                added_count += 1
                new_items.append(f"📖 {english} — {russian}")
                print(f"[DEBUG] Added vocabulary: {english}")
            
            # Добавляем phrases
            for item in data.get('phrases', []):
                english = item['english'].strip().lower()
                russian = item['russian'].strip()
                
                if english in existing_words:
                    print(f"[WARNING] Skipping DUPLICATE phrase: {english}")
                    continue
                
                english_escaped = english.replace("'", "''")
                russian_escaped = russian.replace("'", "''")
                
                cur.execute(
                    f"INSERT INTO {SCHEMA}.words (english_text, russian_translation) "
                    f"VALUES ('{english_escaped}', '{russian_escaped}') "
                    f"ON CONFLICT (english_text) DO UPDATE SET russian_translation = EXCLUDED.russian_translation "
                    f"RETURNING id"
                )
                word_id = cur.fetchone()[0]
                
                cur.execute(
                    f"INSERT INTO {SCHEMA}.student_words (student_id, word_id, teacher_id) "
                    f"VALUES ({student_id}, {word_id}, {student_id}) "
                    f"ON CONFLICT DO NOTHING"
                )
                
                existing_words.append(english)
                added_count += 1
                new_items.append(f"💭 {english} — {russian}")
                print(f"[DEBUG] Added phrase: {english}")
            
            # Добавляем expressions
            for item in data.get('expressions', []):
                english = item['english'].strip().lower()
                russian = item['russian'].strip()
                
                if english in existing_words:
                    print(f"[WARNING] Skipping DUPLICATE expression: {english}")
                    continue
                
                english_escaped = english.replace("'", "''")
                russian_escaped = russian.replace("'", "''")
                
                cur.execute(
                    f"INSERT INTO {SCHEMA}.words (english_text, russian_translation) "
                    f"VALUES ('{english_escaped}', '{russian_escaped}') "
                    f"ON CONFLICT (english_text) DO UPDATE SET russian_translation = EXCLUDED.russian_translation "
                    f"RETURNING id"
                )
                word_id = cur.fetchone()[0]
                
                cur.execute(
                    f"INSERT INTO {SCHEMA}.student_words (student_id, word_id, teacher_id) "
                    f"VALUES ({student_id}, {word_id}, {student_id}) "
                    f"ON CONFLICT DO NOTHING"
                )
                
                existing_words.append(english)
                added_count += 1
                new_items.append(f"✨ {english} — {russian}")
                print(f"[DEBUG] Added expression: {english}")
            
            cur.close()
            conn.close()
            
            log_proxy_success(proxy_id)
            
            print(f"[DEBUG auto_generate_new_words] Successfully added {added_count} new items")
            return {
                'added_count': added_count,
                'new_items': new_items,
                'language_level': language_level
            }
            
    except Exception as e:
        print(f"[ERROR auto_generate_new_words] Failed: {e}")
        import traceback
        traceback.print_exc()
        return {'added_count': 0, 'new_items': []}

def get_session_words(student_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Получает слова для практики в сессии"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Инициализируем прогресс для новых слов
    cur.execute(
        f"INSERT INTO {SCHEMA}.word_progress (student_id, word_id) "
        f"SELECT sw.student_id, sw.word_id FROM {SCHEMA}.student_words sw "
        f"WHERE sw.student_id = {student_id} "
        f"AND NOT EXISTS (SELECT 1 FROM {SCHEMA}.word_progress wp WHERE wp.student_id = sw.student_id AND wp.word_id = sw.word_id)"
    )
    
    print(f"[DEBUG get_session_words] student_id={student_id}, limit={limit}")
    
    # ПРИОРИТЕТ 1: Слова которые нужно проверить (dialog_uses = 5)
    cur.execute(
        f"SELECT w.id, w.english_text, w.russian_translation, wp.dialog_uses FROM {SCHEMA}.word_progress wp "
        f"JOIN {SCHEMA}.words w ON w.id = wp.word_id "
        f"WHERE wp.student_id = {student_id} AND wp.dialog_uses = 5 AND wp.needs_check = TRUE "
        f"ORDER BY wp.updated_at ASC LIMIT 1"
    )
    check_word = cur.fetchone()
    print(f"[DEBUG get_session_words] check_word (dialog_uses=5): {check_word}")
    
    if check_word:
        # Возвращаем ТОЛЬКО слово на проверку с флагом
        words = [{'id': check_word[0], 'english': check_word[1], 'russian': check_word[2], 'needs_check': True}]
        cur.close()
        conn.close()
        print(f"[DEBUG get_session_words] Returning check word: {words}")
        return words
    
    # Новые слова (40%) - БЕЗ фильтра по dialog_uses
    new_limit = max(1, int(limit * 0.4))
    cur.execute(
        f"SELECT w.id, w.english_text, w.russian_translation FROM {SCHEMA}.word_progress wp "
        f"JOIN {SCHEMA}.words w ON w.id = wp.word_id "
        f"WHERE wp.student_id = {student_id} AND wp.status = 'new' "
        f"ORDER BY wp.created_at ASC LIMIT {new_limit}"
    )
    new_words = cur.fetchall()
    print(f"[DEBUG get_session_words] new_words (status=new): {len(new_words)} words")
    
    # Слова на повторение (40%) - БЕЗ фильтра по dialog_uses
    review_limit = max(1, int(limit * 0.4))
    cur.execute(
        f"SELECT w.id, w.english_text, w.russian_translation FROM {SCHEMA}.word_progress wp "
        f"JOIN {SCHEMA}.words w ON w.id = wp.word_id "
        f"WHERE wp.student_id = {student_id} AND wp.status IN ('learning', 'learned') "
        f"AND wp.next_review_date <= CURRENT_TIMESTAMP "
        f"ORDER BY wp.next_review_date ASC LIMIT {review_limit}"
    )
    review_words = cur.fetchall()
    print(f"[DEBUG get_session_words] review_words (status=learning/learned, next_review_date<=NOW): {len(review_words)} words")
    
    # ⚠️ CRITICAL: НЕ ВКЛЮЧАЕМ освоенные слова в активную практику!
    # Освоенные слова (status=mastered) НЕ должны постоянно повторяться
    # Они уже изучены на 100% - фокусируемся только на новых и learning/learned
    
    print(f"[DEBUG get_session_words] Skipping mastered words - they are already 100% learned")
    
    # ⚠️ CRITICAL: Автоматически генерируем новые слова если недостаточно активных
    active_words_count = len(new_words) + len(review_words)
    if active_words_count < 5:  # Если меньше 5 активных слов - генерируем новые
        print(f"[WARNING] Only {active_words_count} active words - generating more!")
        
        # Проверяем режим пользователя - НЕ генерируем если идет генерация плана
        cur.execute(f"SELECT conversation_mode FROM {SCHEMA}.users WHERE telegram_id = {student_id}")
        mode_row = cur.fetchone()
        conversation_mode = mode_row[0] if mode_row else 'dialog'
        
        if conversation_mode == 'generating_plan':
            print(f"[DEBUG] User is in generating_plan mode - skipping auto-generation")
            cur.close()
            conn.close()
            return []  # Возвращаем пустой список, план сгенерируется асинхронно
        
        # Считаем сколько слов освоено
        cur.execute(
            f"SELECT COUNT(*) FROM {SCHEMA}.word_progress "
            f"WHERE student_id = {student_id} AND status = 'mastered'"
        )
        mastered_count = cur.fetchone()[0]
        
        cur.close()
        conn.close()
        
        result = auto_generate_new_words(student_id, how_many=10)
        
        if result['added_count'] > 0:
            # Отправляем уведомление о новых материалах
            notification = f"🎉 ПОЗДРАВЛЯЮ!\n\n"
            notification += f"✅ Ты освоил {mastered_count} слов!\n\n"
            notification += f"🆕 Я добавила {result['added_count']} новых материалов для уровня {result['language_level']}:\n\n"
            
            for item in result['new_items'][:10]:  # Показываем первые 10
                notification += f"{item}\n"
            
            if len(result['new_items']) > 10:
                notification += f"\n...и еще {len(result['new_items']) - 10}!\n"
            
            notification += f"\nПродолжаем практиковать! 🚀"
            
            try:
                send_telegram_message(student_id, notification, parse_mode=None)
                print(f"[DEBUG] Notification sent to student {student_id}")
            except Exception as e:
                print(f"[ERROR] Failed to send notification: {e}")
            
            # ⚠️ FIX: Открываем НОВОЕ подключение и инициализируем прогресс для новых слов
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Инициализируем прогресс для только что добавленных слов
            cur.execute(
                f"INSERT INTO {SCHEMA}.word_progress (student_id, word_id) "
                f"SELECT sw.student_id, sw.word_id FROM {SCHEMA}.student_words sw "
                f"WHERE sw.student_id = {student_id} "
                f"AND NOT EXISTS (SELECT 1 FROM {SCHEMA}.word_progress wp WHERE wp.student_id = sw.student_id AND wp.word_id = sw.word_id)"
            )
            
            print(f"[DEBUG] Re-initialized word_progress after auto-generation")
            
            # Повторно запрашиваем новые слова (теперь они должны быть в word_progress)
            cur.execute(
                f"SELECT w.id, w.english_text, w.russian_translation FROM {SCHEMA}.word_progress wp "
                f"JOIN {SCHEMA}.words w ON w.id = wp.word_id "
                f"WHERE wp.student_id = {student_id} AND wp.status = 'new' "
                f"ORDER BY wp.created_at ASC LIMIT {new_limit}"
            )
            new_words = cur.fetchall()
            print(f"[DEBUG] After generation: new_words count = {len(new_words)}")
            
            # Повторно запрашиваем review слова
            cur.execute(
                f"SELECT w.id, w.english_text, w.russian_translation FROM {SCHEMA}.word_progress wp "
                f"JOIN {SCHEMA}.words w ON w.id = wp.word_id "
                f"WHERE wp.student_id = {student_id} AND wp.status IN ('learning', 'learned') "
                f"AND wp.next_review_date <= CURRENT_TIMESTAMP "
                f"ORDER BY wp.next_review_date ASC LIMIT {review_limit}"
            )
            review_words = cur.fetchall()
            print(f"[DEBUG] After generation: review_words count = {len(review_words)}")
    
    # ⚠️ CRITICAL: Возвращаем ТОЛЬКО новые и review слова (БЕЗ mastered!)
    all_words = list(new_words) + list(review_words)
    
    words = [{'id': row[0], 'english': row[1], 'russian': row[2], 'needs_check': False} for row in all_words]
    
    print(f"[DEBUG get_session_words] FINAL RESULT: returning {len(words)} words total (NEW + REVIEW only, NO mastered)")
    if words:
        print(f"[DEBUG get_session_words] First word: {words[0]}")
    
    cur.close()
    conn.close()
    return words

def increment_dialog_uses(student_id: int, word_ids: List[int]):
    """Увеличивает счётчик использования слов Аней в диалоге"""
    if not word_ids:
        return
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    for word_id in word_ids:
        cur.execute(
            f"UPDATE {SCHEMA}.word_progress "
            f"SET dialog_uses = COALESCE(dialog_uses, 0) + 1, "
            f"needs_check = CASE WHEN COALESCE(dialog_uses, 0) + 1 = 5 THEN TRUE ELSE needs_check END, "
            f"updated_at = CURRENT_TIMESTAMP "
            f"WHERE student_id = {student_id} AND word_id = {word_id}"
        )
        print(f"[DEBUG] Incremented dialog_uses for word_id={word_id}")
    
    cur.close()
    conn.close()

def mark_word_as_mastered(student_id: int, word_id: int):
    """Помечает слово как освоенное после успешной проверки"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"UPDATE {SCHEMA}.word_progress "
        f"SET status = 'mastered', "
        f"needs_check = FALSE, "
        f"mastery_score = 100, "
        f"updated_at = CURRENT_TIMESTAMP "
        f"WHERE student_id = {student_id} AND word_id = {word_id}"
    )
    
    cur.close()
    conn.close()
    print(f"[DEBUG] Word {word_id} marked as mastered for student {student_id}")

def create_user(telegram_id: int, username: str, first_name: str, last_name: str, role: str):
    """Создает пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    username = username.replace("'", "''") if username else ''
    first_name = first_name.replace("'", "''") if first_name else ''
    last_name = last_name.replace("'", "''") if last_name else ''
    
    cur.execute(
        f"INSERT INTO {SCHEMA}.users (telegram_id, username, first_name, last_name, role) "
        f"VALUES ({telegram_id}, '{username}', '{first_name}', '{last_name}', '{role}')"
    )
    
    cur.close()
    conn.close()

def get_conversation_history(user_id: int) -> List[Dict[str, str]]:
    """Получает историю диалога"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"SELECT id FROM {SCHEMA}.conversations WHERE user_id = {user_id} ORDER BY updated_at DESC LIMIT 1")
    row = cur.fetchone()
    
    if not row:
        cur.close()
        conn.close()
        return []
    
    conversation_id = row[0]
    
    cur.execute(f"SELECT role, content FROM {SCHEMA}.messages WHERE conversation_id = {conversation_id} ORDER BY created_at ASC LIMIT 50")
    
    history = [{'role': row[0], 'content': row[1]} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    return history

def save_message(user_id: int, role: str, content: str):
    """Сохраняет сообщение"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"SELECT id FROM {SCHEMA}.conversations WHERE user_id = {user_id} ORDER BY updated_at DESC LIMIT 1")
    row = cur.fetchone()
    
    if row:
        conversation_id = row[0]
        cur.execute(f"UPDATE {SCHEMA}.conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = {conversation_id}")
    else:
        cur.execute(f"INSERT INTO {SCHEMA}.conversations (user_id, title) VALUES ({user_id}, 'Новый диалог') RETURNING id")
        conversation_id = cur.fetchone()[0]
    
    content = content.replace("'", "''")
    cur.execute(f"INSERT INTO {SCHEMA}.messages (conversation_id, role, content) VALUES ({conversation_id}, '{role}', '{content}')")
    
    cur.close()
    conn.close()

def detect_emotional_context(message: str) -> str:
    """Определяет эмоциональный контекст сообщения"""
    message_lower = message.lower()
    
    # Тяжелые эмоции (грусть, страх, боль)
    heavy_keywords = ['death', 'dead', 'died', 'dying', 'kill', 'suicide', 
                      'fear', 'scared', 'afraid', 'terrified', 'panic',
                      'lonely', 'alone', 'depression', 'depressed', 'sad', 'cry', 'crying',
                      'difficult', 'hard time', 'struggle', 'pain', 'hurt', 'suffering',
                      'lost', 'miss', 'gone', 'never', 'hate', 'angry', 'upset']
    
    # Позитивные эмоции
    positive_keywords = ['happy', 'joy', 'excited', 'love', 'amazing', 'wonderful',
                        'great', 'awesome', 'perfect', 'fantastic', 'excellent']
    
    # Нейтральные/обучающие
    learning_keywords = ['how', 'what', 'why', 'when', 'where', 'explain', 'mean',
                        'help', 'learn', 'study', 'practice']
    
    if any(word in message_lower for word in heavy_keywords):
        return 'empathetic'
    elif any(word in message_lower for word in positive_keywords):
        return 'enthusiastic'
    elif any(word in message_lower for word in learning_keywords):
        return 'educational'
    else:
        return 'casual'

def get_emoji_for_mood(mood: str) -> str:
    """Возвращает подходящий emoji для настроения"""
    emoji_sets = {
        'empathetic': ['💙', '❤️', '🫂', '💛', '🤗', '💜'],
        'enthusiastic': ['🌟', '✨', '🎉', '💫', '🔥', '⚡'],
        'educational': ['😊', '🙂', '👍', '✅', '💡', '📚'],
        'casual': ['😊', '🙂', '😄', '👋', '💬', '✨']
    }
    
    emojis = emoji_sets.get(mood, emoji_sets['casual'])
    return random.choice(emojis)

def update_conversation_mode(telegram_id: int, mode: str):
    """Обновляет режим разговора для пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE {SCHEMA}.users SET conversation_mode = '{mode}' WHERE telegram_id = {telegram_id}")
    cur.close()
    conn.close()

def update_exercise_state(telegram_id: int, word_id: int, answer: str):
    """Сохраняет состояние текущего упражнения"""
    conn = get_db_connection()
    cur = conn.cursor()
    answer_escaped = answer.replace("'", "''")
    cur.execute(f"UPDATE {SCHEMA}.users SET current_exercise_word_id = {word_id}, current_exercise_answer = '{answer_escaped}' WHERE telegram_id = {telegram_id}")
    cur.close()
    conn.close()

def clear_exercise_state(telegram_id: int):
    """Очищает состояние упражнения"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE {SCHEMA}.users SET current_exercise_word_id = NULL, current_exercise_answer = NULL WHERE telegram_id = {telegram_id}")
    cur.close()
    conn.close()

def update_word_progress_api(student_id: int, word_id: int, is_correct: bool):
    """Обновляет прогресс слова через webapp-api"""
    try:
        webapp_api_url = os.environ.get('WEBAPP_API_URL', '')
        if not webapp_api_url:
            print("[WARNING] WEBAPP_API_URL not set, skipping progress update")
            return
        
        payload = json.dumps({
            'action': 'update_word_progress',
            'student_id': student_id,
            'word_id': word_id,
            'is_correct': is_correct
        }).encode('utf-8')
        
        req = urllib.request.Request(
            webapp_api_url,
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            print(f"[DEBUG] Word progress updated: word_id={word_id}, is_correct={is_correct}, result={result}")
            return result
    except Exception as e:
        print(f"[ERROR] Failed to update word progress: {e}")
        return None

def detect_words_in_text(text: str, session_words: List[Dict[str, Any]]) -> List[int]:
    """Определяет, какие слова из сессии использованы в тексте"""
    text_lower = text.lower()
    # Убираем пунктуацию для точного поиска
    text_clean = re.sub(r'[^\w\s]', ' ', text_lower)
    words_in_text = set(text_clean.split())
    
    used_word_ids = []
    for word in session_words:
        # Проверяем точное совпадение слова
        if word['english'].lower() in words_in_text:
            used_word_ids.append(word['id'])
    
    return used_word_ids

def get_learning_mode_keyboard():
    """Возвращает Inline Keyboard с режимами обучения"""
    return {
        'inline_keyboard': [
            [
                {'text': '💬 Диалог', 'callback_data': 'mode_dialog'},
                {'text': '✍️ Предложения', 'callback_data': 'mode_sentence'}
            ],
            [
                {'text': '📝 Контекст', 'callback_data': 'mode_context'},
                {'text': '🎯 Ассоциации', 'callback_data': 'mode_association'}
            ],
            [
                {'text': '🇷🇺→🇬🇧 Перевод', 'callback_data': 'mode_translation'}
            ]
        ]
    }

def get_default_words_for_level(language_level: str) -> List[Dict[str, str]]:
    """Возвращает базовый набор слов для самостоятельного обучения"""
    words_by_level = {
        'A1': [
            {'english': 'hello', 'russian': 'привет'},
            {'english': 'family', 'russian': 'семья'},
            {'english': 'food', 'russian': 'еда'},
            {'english': 'water', 'russian': 'вода'},
            {'english': 'house', 'russian': 'дом'},
            {'english': 'friend', 'russian': 'друг'},
            {'english': 'book', 'russian': 'книга'},
            {'english': 'cat', 'russian': 'кот'},
            {'english': 'dog', 'russian': 'собака'},
            {'english': 'work', 'russian': 'работа'}
        ],
        'A2': [
            {'english': 'travel', 'russian': 'путешествие'},
            {'english': 'weather', 'russian': 'погода'},
            {'english': 'meeting', 'russian': 'встреча'},
            {'english': 'money', 'russian': 'деньги'},
            {'english': 'health', 'russian': 'здоровье'},
            {'english': 'hobby', 'russian': 'хобби'},
            {'english': 'sport', 'russian': 'спорт'},
            {'english': 'movie', 'russian': 'фильм'},
            {'english': 'music', 'russian': 'музыка'},
            {'english': 'language', 'russian': 'язык'}
        ],
        'B1': [
            {'english': 'experience', 'russian': 'опыт'},
            {'english': 'relationship', 'russian': 'отношения'},
            {'english': 'opportunity', 'russian': 'возможность'},
            {'english': 'challenge', 'russian': 'вызов'},
            {'english': 'decision', 'russian': 'решение'},
            {'english': 'environment', 'russian': 'окружающая среда'},
            {'english': 'technology', 'russian': 'технология'},
            {'english': 'knowledge', 'russian': 'знание'},
            {'english': 'development', 'russian': 'развитие'},
            {'english': 'achievement', 'russian': 'достижение'}
        ],
        'B2': [
            {'english': 'perspective', 'russian': 'перспектива'},
            {'english': 'ambition', 'russian': 'амбиция'},
            {'english': 'consequence', 'russian': 'последствие'},
            {'english': 'phenomenon', 'russian': 'феномен'},
            {'english': 'hypothesis', 'russian': 'гипотеза'},
            {'english': 'innovation', 'russian': 'инновация'},
            {'english': 'controversy', 'russian': 'спор'},
            {'english': 'sustainability', 'russian': 'устойчивость'},
            {'english': 'diversity', 'russian': 'разнообразие'},
            {'english': 'resilience', 'russian': 'жизнестойкость'}
        ]
    }
    
    return words_by_level.get(language_level, words_by_level['A1'])

def ensure_user_has_words(telegram_id: int, language_level: str):
    """Проверяет есть ли у пользователя слова, если нет - добавляет базовые"""
    # ⚡ ОПТИМИЗАЦИЯ: Кэшируем проверку в рамках одного запроса
    # Это убирает дублирование вызовов (например, get_random_word тоже вызывает эту функцию)
    cache_key = f"{telegram_id}_{language_level}"
    if cache_key in _words_ensured_cache:
        return  # Уже проверяли в этом запросе
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT COUNT(*) FROM {SCHEMA}.student_words WHERE student_id = {telegram_id}"
    )
    count = cur.fetchone()[0]
    
    if count == 0:
        default_words = get_default_words_for_level(language_level)
        
        for word_data in default_words:
            english = word_data['english'].replace("'", "''")
            russian = word_data['russian'].replace("'", "''")
            
            cur.execute(
                f"INSERT INTO {SCHEMA}.words (english_text, russian_translation) "
                f"VALUES ('{english}', '{russian}') "
                f"ON CONFLICT (english_text) DO UPDATE SET english_text = EXCLUDED.english_text "
                f"RETURNING id"
            )
            word_id = cur.fetchone()[0]
            
            cur.execute(
                f"INSERT INTO {SCHEMA}.student_words (student_id, word_id) "
                f"VALUES ({telegram_id}, {word_id}) "
                f"ON CONFLICT DO NOTHING"
            )
    
    cur.close()
    conn.close()
    
    # Помечаем что проверили для этого пользователя
    _words_ensured_cache[cache_key] = True

def get_random_word(telegram_id: int, language_level: str = 'A1') -> Dict[str, Any]:
    """Получает случайное слово для упражнения"""
    ensure_user_has_words(telegram_id, language_level)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT w.id, w.english_text, w.russian_translation FROM {SCHEMA}.student_words sw "
        f"JOIN {SCHEMA}.words w ON w.id = sw.word_id "
        f"WHERE sw.student_id = {telegram_id} "
        f"ORDER BY RANDOM() LIMIT 1"
    )
    
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if row:
        return {'id': row[0], 'english': row[1], 'russian': row[2]}
    return None

def get_word_transcription(word: str) -> str:
    """Получает транскрипцию слова через Gemini"""
    try:
        api_key = os.environ['GEMINI_API_KEY']
        proxy_id, proxy_url = get_active_proxy_from_db()
        if not proxy_url:
            proxy_url = os.environ.get('PROXY_URL', '')
        
        gemini_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}'
        
        prompt = f"Return ONLY the phonetic transcription (IPA) for the English word '{word}'. No explanations, just the transcription in format: /transcription/"
        
        payload = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.1, 'maxOutputTokens': 100}
        }
        
        proxy_handler = urllib.request.ProxyHandler({
            'http': f'http://{proxy_url}',
            'https': f'http://{proxy_url}'
        })
        opener = urllib.request.build_opener(proxy_handler)
        
        req = urllib.request.Request(
            gemini_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with opener.open(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            transcription = result['candidates'][0]['content']['parts'][0]['text'].strip()
            log_proxy_success(proxy_id)
            return transcription
    except Exception as e:
        print(f"[ERROR] Failed to get transcription: {e}")
        if proxy_id:
            log_proxy_failure(proxy_id, str(e))
        return ''

def generate_sentence_exercise(word: Dict[str, Any], language_level: str) -> tuple:
    """Генерирует задание на составление предложения с транскрипцией"""
    transcription = get_word_transcription(word['english'])
    
    message = f"✍️ Составь предложение со словом:\n\n"
    message += f"<b>{word['english']}</b>"
    if transcription:
        message += f" {transcription}"
    message += f"\n🇷🇺 {word['russian']}"
    
    # Inline клавиатура с кнопкой "Послушать"
    keyboard = {
        'inline_keyboard': [[
            {'text': '🔊 Послушать произношение', 'callback_data': f'pronounce:{word["english"]}'}
        ]]
    }
    
    return message, keyboard

def generate_context_exercise(word: Dict[str, Any], language_level: str, all_words: List[Dict[str, Any]] = None) -> tuple:
    """Генерирует упражнение Fill in the blanks с вариантами ответа через Gemini"""
    try:
        api_key = os.environ['GEMINI_API_KEY']
        proxy_id, proxy_url = get_active_proxy_from_db()
        if not proxy_url:
            proxy_url = os.environ.get('PROXY_URL', '')
        
        if not proxy_url:
            print(f"[WARNING] No proxy available - using fallback sentence")
            sentence_template = f"I use ___ every day"
        else:
            # Генерируем контекстное предложение через Gemini
            prompt = f'''Create a simple English sentence with a blank (___) where the word "{word['english']}" should go.

Rules:
- Make it natural and grammatically correct for level {language_level}
- The sentence should make sense with "{word['english']}" in the blank
- Keep it simple and clear
- Use ___ to mark the blank

Examples:
- For "book": "I read a ___ before bed"
- For "cat": "My ___ loves to play"
- For "travel": "I want to ___ around the world"
- For "happy": "She feels very ___ today"

Return ONLY the sentence with ___, nothing else.'''

            gemini_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}'
            
            payload = {
                'contents': [{'parts': [{'text': prompt}]}],
                'generationConfig': {'temperature': 0.7, 'maxOutputTokens': 100}
            }
            
            proxy_handler = urllib.request.ProxyHandler({
                'http': f'http://{proxy_url}',
                'https': f'http://{proxy_url}'
            })
            opener = urllib.request.build_opener(proxy_handler)
            
            req = urllib.request.Request(
                gemini_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            
            with opener.open(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))
                sentence_template = result['candidates'][0]['content']['parts'][0]['text'].strip()
                log_proxy_success(proxy_id)
                print(f"[DEBUG] Generated sentence: {sentence_template}")
    
    except Exception as e:
        print(f"[ERROR] Failed to generate context sentence: {e}")
        if proxy_id:
            log_proxy_failure(proxy_id, str(e))
        # Fallback на простое предложение
        sentence_template = f"I like ___"
    
    # Генерируем варианты ответов (правильный + 3 неправильных) - НА АНГЛИЙСКОМ
    options = [word['english']]  # Правильный ответ
    
    # Добавляем 3 случайных слова как отвлекатели
    if all_words and len(all_words) > 1:
        other_words = [w for w in all_words if w['id'] != word['id']]
        random.shuffle(other_words)
        for other in other_words[:3]:
            options.append(other['english'])
    else:
        # Fallback если нет других слов
        options.extend(['wrong', 'incorrect', 'mistake'])
    
    # Перемешиваем варианты
    random.shuffle(options)
    
    # Убираем транскрипцию и кнопку произношения из режима Контекст
    message = f"📝 Fill in the blank:\n\n{sentence_template}\n\n"
    message += f"🔑 Слово: <b>{word['english']}</b>"
    message += f"\n🇷🇺 {word['russian']}"
    
    return (
        message,
        word['english'],
        options
    )

def get_mastered_words(student_id: int) -> List[str]:
    """Получает список освоенных слов студента (status=mastered)"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT w.english_text FROM {SCHEMA}.word_progress wp "
        f"JOIN {SCHEMA}.words w ON w.id = wp.word_id "
        f"WHERE wp.student_id = {student_id} AND wp.status = 'mastered' "
        f"ORDER BY wp.updated_at DESC"
    )
    
    mastered_words = [row[0] for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    print(f"[DEBUG get_mastered_words] Found {len(mastered_words)} mastered words for student {student_id}")
    return mastered_words

def generate_association_exercise(word: Dict[str, Any], language_level: str, student_id: int = None) -> tuple:
    """Генерирует упражнение с ассоциациями через Gemini, используя освоенные слова"""
    try:
        print(f"[DEBUG generate_association_exercise] Starting for word: {word['english']}, level: {language_level}")
        
        api_key = os.environ['GEMINI_API_KEY']
        proxy_id, proxy_url = get_active_proxy_from_db()
        if not proxy_url:
            proxy_url = os.environ.get('PROXY_URL', '')
            print(f"[DEBUG] Using PROXY_URL from env for associations")
        
        if not proxy_url:
            print(f"[WARNING] No proxy available - using fallback associations")
            hints = ['word', 'thing', 'item']
            hints_text = ', '.join(hints)
            return (
                f"🎯 Guess the word by associations:\n\n{hints_text}\n\nRussian translation: {word['russian']}",
                word['english']
            )
        
        # Получаем освоенные слова студента
        mastered_words = []
        if student_id:
            mastered_words = get_mastered_words(student_id)
        
        mastered_words_hint = ''
        if mastered_words:
            mastered_sample = ', '.join(mastered_words[:15])  # Показываем первые 15
            mastered_words_hint = f"\n\n⚠️ CRITICAL: You MUST use ONLY these MASTERED words as associations: {mastered_sample}\n- ONLY use words from this list - student already knows them\n- DO NOT use any other words that are not in this list\n- This helps reinforce learned vocabulary"
        
        # Генерируем 3 ассоциации через Gemini
        prompt = f'''Generate 3 short English associations (1-2 words each) for the word "{word['english']}".

Rules:
- Make hints clear but not too obvious
- Don't use the word itself or direct translations
- Focus on: what it does, how it looks, where you find it, related concepts{mastered_words_hint}

Examples:
- "cat" → meow, furry, pet
- "travel" → journey, explore, adventure
- "book" → read, pages, story
- "music" → sound, melody, listen

Return ONLY valid JSON:
{{"associations": ["hint1", "hint2", "hint3"]}}'''

        print(f"[DEBUG] Calling Gemini for associations...")
        
        gemini_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}'
        
        payload = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {'temperature': 0.7, 'maxOutputTokens': 500}
        }
        
        proxy_handler = urllib.request.ProxyHandler({
            'http': f'http://{proxy_url}',
            'https': f'http://{proxy_url}'
        })
        opener = urllib.request.build_opener(proxy_handler)
        
        req = urllib.request.Request(
            gemini_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with opener.open(req, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))
            text = result['candidates'][0]['content']['parts'][0]['text']
            
            print(f"[DEBUG] Gemini response for associations: {text}")
            
            data = safe_json_parse(text, {'associations': ['word', 'thing', 'item']})
            hints = data.get('associations', ['word', 'thing', 'item'])[:3]
            
            print(f"[DEBUG] Parsed associations: {hints}")
            
            log_proxy_success(proxy_id)
            
            hints_text = ', '.join(hints)
            
            # Убираем транскрипцию и кнопку произношения
            message = f"🎯 Guess the word by associations:\n\n{hints_text}\n\n"
            message += f"🔑 Слово: <b>{word['english']}</b>"
            message += f"\n🇷🇺 {word['russian']}"
            
            return (message, word['english'])
            
    except Exception as e:
        print(f"[ERROR] Failed to generate associations for '{word['english']}': {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback на простые ассоциации
        hints = ['word', 'thing', 'item']
        hints_text = ', '.join(hints)
        
        message = f"🎯 Guess the word by associations:\n\n{hints_text}\n\n"
        message += f"🔑 Слово: <b>{word['english']}</b>"
        message += f"\n🇷🇺 {word['russian']}"
        
        return (message, word['english'])

def generate_translation_exercise(word: Dict[str, Any]) -> tuple:
    """Генерирует упражнение на перевод"""
    # Убираем транскрипцию и кнопку произношения
    message = f"🇷🇺→🇬🇧 Переведи слово на английский:\n\n🇷🇺 {word['russian']}\n\n"
    message += f"🔑 Правильный ответ: <b>{word['english']}</b>"
    
    return (message, word['english'])

def call_gemini(user_message: str, history: List[Dict[str, str]], session_words: List[Dict[str, Any]] = None, language_level: str = 'A1', preferred_topics: List[Dict[str, str]] = None, urgent_goals: List[str] = None, learning_goal: str = None, learning_mode: str = 'standard') -> str:
    """Вызывает Gemini API через прокси с учетом слов, уровня, тем и срочных целей"""
    print(f"[DEBUG call_gemini] Received session_words: {session_words}")
    print(f"[DEBUG call_gemini] Received language_level: {language_level}")
    print(f"[DEBUG call_gemini] Received learning_mode: {learning_mode}, learning_goal: {learning_goal}")
    
    api_key = os.environ['GEMINI_API_KEY']
    
    # Получаем прокси из БД (приоритет) или из env как fallback
    proxy_id, proxy_url = get_active_proxy_from_db()
    if not proxy_url:
        proxy_id = None
        proxy_url = os.environ.get('PROXY_URL', '')
        print("[DEBUG] Using PROXY_URL from env (no active proxies in DB)")
    
    # Определяем эмоциональный контекст
    emotional_mode = detect_emotional_context(user_message)
    mood_emoji = get_emoji_for_mood(emotional_mode)
    
    # Определяем сложность диалога по уровню
    level_instructions = {
        'A1': 'Use very simple words and short sentences. Speak slowly and clearly. Use present simple tense mostly.',
        'A2': 'Use simple everyday vocabulary. Keep sentences clear and not too long. Use basic grammar structures.',
        'B1': 'Use common vocabulary. You can use more complex sentences. Mix different tenses naturally.',
        'B2': 'Use varied vocabulary including some idioms. Use complex grammar naturally. Discuss abstract topics.',
        'C1': 'Use sophisticated vocabulary and expressions. Use advanced grammar structures. Discuss nuanced topics.',
        'C2': 'Use native-level vocabulary and expressions. Feel free to use idioms, slang, and complex structures.'
    }
    
    level_instruction = level_instructions.get(language_level, level_instructions['A1'])
    
    # Получаем промпты из БД
    empathetic_prompt_template = get_prompt_from_db('empathetic_mode', '')
    error_correction_rules = get_prompt_from_db('error_correction_rules', '')
    
    # Если промпты не найдены в БД - используем fallback (но это не должно случаться)
    if not empathetic_prompt_template:
        empathetic_prompt_template = """You are Anya, a caring friend who teaches English. Your student's level is {language_level}.

RIGHT NOW your student is sharing something difficult or emotional. Be a HUMAN first, tutor second.

Your personality in this moment:
- Show GENUINE empathy and care {mood_emoji}
- Acknowledge their feelings BEFORE anything else
- DON'T use happy emojis (😊🎉) on serious topics - use caring ones ({mood_emoji})
- Be supportive and understanding
- Let them know it's okay to feel what they feel
- Ask if they want to continue or need a break

Language level adaptation ({language_level}):
{level_instruction}

Your approach RIGHT NOW:
- Respond in English, but prioritize emotional support over grammar correction
- If there are mistakes, correct them GENTLY at the end (or skip if topic is too sensitive)
- Use {mood_emoji} or similar caring emojis
- 2-3 sentences of support first
- Then ask: "Would you like to talk about it? Or shall we practice something else today?"
- Be a friend who happens to teach English

Example:
Student: "My grandfather is dead. I feel fear"
You: "I'm so sorry to hear about your grandfather {mood_emoji} Losing someone we love is really hard, and feeling scared is completely normal. You're being very brave by sharing this.

Would you like to talk about your feelings, or would you prefer to practice something lighter today? I'm here for you either way {mood_emoji}"

CRITICAL: NO corrections on deeply emotional messages. Just support."""
    
    if not error_correction_rules:
        error_correction_rules = """⚠️⚠️⚠️ CRITICAL ERROR CORRECTION - MANDATORY FOR EVERY MESSAGE ⚠️⚠️⚠️

BEFORE responding, you MUST check the student's message for:
1. **Spelling mistakes** (helo → hello, nothih → nothing, etc.)
2. **Grammar errors** (I go yesterday → I went yesterday)
3. **Word order** (I not like → I don't like)
4. **Missing articles** (I have cat → I have a cat)
5. **Wrong verb forms** (He go → He goes)
6. **Wrong prepositions** (depend from → depend on)

⚠️ DO NOT CORRECT:
- Extra spaces before punctuation (I am okay . → this is just a typo, NOT an English mistake)
- Typos in punctuation (? ! , . spacing is NOT grammar)
- Only correct REAL English language errors (spelling, grammar, vocabulary)

IF you find ANY REAL ENGLISH MISTAKE, you MUST show correction in this format FIRST:

🔧 Fix / Correct:
❌ [their exact wrong sentence]
✅ [corrected sentence]
🇷🇺 [explanation in Russian - explain the rule briefly]

Then continue with your regular response.

⚠️ DO NOT skip corrections even if the message is short or simple!
⚠️ Even one misspelled word MUST be corrected!"""
    
    # Формируем system prompt в зависимости от эмоционального контекста
    if emotional_mode == 'empathetic':
        # Подставляем переменные в шаблон промпта
        system_prompt = empathetic_prompt_template.format(
            language_level=language_level,
            mood_emoji=mood_emoji,
            level_instruction=level_instruction
        )
    
    else:
        # Обычный режим (educational, casual, enthusiastic)
        # ⚠️ КРИТИЧЕСКИ ВАЖНО: ВСЕ РЕЖИМЫ ДОЛЖНЫ ПРОВЕРЯТЬ ОРФОГРАФИЮ И ГРАММАТИКУ!
        # error_correction_rules уже загружены из БД выше
        
        # КРИТИЧНО: Используем learning_mode для выбора промпта, НЕ наличие learning_goal!
        if learning_mode == 'urgent_task':
            # РЕЖИМ СРОЧНОЙ ЗАДАЧИ - Аня играет роли из целей
            goals_list = '\n'.join([f'  {i+1}. {goal}' for i, goal in enumerate(urgent_goals)])
            system_prompt = f"""You are Anya, a friendly English tutor helping someone with an URGENT TASK. Your student's level is {language_level}.

{error_correction_rules}

🚨 URGENT TASK MODE - Role-playing scenarios!

Student's urgent task: {learning_goal}

Specific goals to practice:
{goals_list}

Your mission:
- Play characters from these scenarios (airport staff, hotel receptionist, restaurant waiter, conference attendee, taxi driver, etc.)
- Create realistic situations that help practice these specific goals
- Stay in character and make the conversation feel REAL
- Use vocabulary and phrases relevant to each goal

Language level adaptation ({language_level}):
{level_instruction}

Your approach:
- Introduce yourself as a character related to one of the goals (e.g., "Hi! I'm at the airport information desk. How can I help you?")
- Create realistic dialogues that force the student to practice the specific goal
- Keep messages short and conversational (2-3 sentences)
- React naturally to their responses
- Correct mistakes FIRST, then continue in character
- When one goal is practiced enough, switch to another scenario/character

Examples:
Goal: "Забронировать отель на английском"
You: "Good afternoon! Welcome to Grand Hotel. Are you checking in today?"

Goal: "Заказать еду в ресторане" 
You: "Hi there! I'm your server today. Can I start you off with something to drink?"

Goal: "Спросить дорогу у прохожих"
You: "*walking by with headphones* Oh, did you need directions? I live nearby!"

Remember: You're helping them prepare for REAL situations. Make it practical and realistic!"""
        elif learning_mode == 'specific_topic':
            # РЕЖИМ ОПРЕДЕЛЕННЫХ ЦЕЛЕЙ - Аня общается ТОЛЬКО в рамках цели (БЕЗ интересов!)
            system_prompt = f"""You are Anya, a friendly English tutor helping someone with a SPECIFIC LEARNING GOAL. Your student's level is {language_level}.

{error_correction_rules}

🎯 CRITICAL: Student's specific goal: {learning_goal}

Your mission:
- Talk ONLY about topics related to their goal
- Help them practice vocabulary and phrases they'll actually need for this goal
- Make conversations realistic and practical for their specific purpose

Examples:
Goal: "Хочу смотреть Рик и Морти в оригинале"
You: "So you want to watch Rick and Morty! 🎬 Have you tried watching with English subtitles first? Which character do you like most?"

Goal: "Хочу читать Оруэлла"
You: "Orwell is amazing! 📚 Are you starting with 1984 or Animal Farm? The language can be tricky - I can help you with difficult words!"

Goal: "Подготовка к собеседованию"
You: "Let's practice interview questions! Tell me about yourself and your experience. What position are you applying for?"

Language level adaptation ({language_level}):
{level_instruction}

Your approach:
- Always communicate in English only, never in Russian
- Keep messages short and conversational (1-3 sentences)
- Use 1-2 emojis MAX per message
- ⚠️ CRITICAL: ALL topics MUST relate to their goal - don't discuss random things!
- ⚠️ If goal is about movies/series - discuss episodes, characters, quotes
- ⚠️ If goal is about books - discuss plot, characters, themes, vocabulary
- ⚠️ If goal is about work/interviews - practice professional language
- ⚠️ If you see previous messages → JUMP STRAIGHT into conversation, NO greetings!
- Be NATURAL and focused on helping them achieve their specific goal"""
        else:
            # СТАНДАРТНОЕ ОБУЧЕНИЕ - обычная Аня без специфики
            system_prompt = f"""You are Anya, a friendly English tutor helping someone practice English. Your student's level is {language_level}.

{error_correction_rules}

Your personality:
- Be chill, friendly, and natural (NOT overly enthusiastic or pushy)
- Use emojis sparingly - 1-2 per message MAX
- Keep messages short and conversational (1-3 sentences)
- DON'T greet in EVERY message - only at the start of NEW conversation
- Ask MAX 1 question per message (not 2-3!)
- Be genuinely interested but NOT interrogating
- React naturally like a friend texting, not a teacher testing

Language level adaptation ({language_level}):
{level_instruction}

Your approach:
- Always communicate in English only, never in Russian
- Respond ONLY with your message, do NOT include conversation history or labels
- Write 1-3 sentences per message (keep it SHORT!)
- Use 1-2 emojis MAX per message
- ⚠️ CRITICAL: ABSOLUTELY FORBIDDEN to use these greetings if conversation already started:
  - "Hey there" / "Hi there" / "Hello" / "Hey" / "Hi"
  - "So glad we're back" / "Good to see you" / "Welcome back"
  - "Glad we got things working" / ANY greeting phrase
- ⚠️ If you see ANY previous messages in history → JUMP STRAIGHT into conversation, NO greetings!
- Sometimes just react (Cool / Nice / I see / Got it), sometimes ask ONE question
- Be NATURAL like texting a friend - avoid teacher-like patterns
- Don't be repetitive with greetings or phrases

Then continue conversation in VARIED ways - not always the same pattern!

Examples of VARIED responses after corrections:

Example 1 (multiple questions):
"🔧 Fix / Correct:
❌ I like play football
✅ I like playing football
🇷🇺 После 'like' нужен глагол с -ing

Great! ⚽ How often do you play? What position?"

Example 2 (reaction + one question):
"🔧 Fix / Correct:
❌ Yesterday I go to shop
✅ Yesterday I went to the shop
🇷🇺 С 'yesterday' нужно прошедшее время (went)

Shopping trips are fun! 🛍️ Did you find something cool?"

Example 3 (just supportive, no questions):
"🔧 Fix / Correct:
❌ I doesbt bo
✅ I don't know
🇷🇺 Правильная форма: don't know

That's totally okay! 💙 Everyone says 'I don't know' sometimes."

Example 4 (enthusiastic praise):
"Perfect sentence! 🌟 You're really improving!"

Example 5 (casual reaction):
"Nice! 👍 That's exactly right."

🎬 STORYTELLING - Adjust frequency based on student level:

⚠️ IMPORTANT: Story frequency depends on student level:
- A1-A2: Use stories in 30% of responses (simple words, basic grammar)
- B1-B2: Use stories in 35% of responses (medium complexity)
- C1-C2: Use stories in 40% of responses (advanced language, idioms)

⚠️ Adjust story language complexity to match student's level!
⚠️ Most responses should still include corrections, reactions, and questions

Types of stories to share:

1. **Word Origin Stories** (etymology, history):
   - "The word 'salary' comes from Latin 'salarium' - it was SALT money! Roman soldiers got paid in salt because it was so valuable! 🧂"
   - "'Quarantine' comes from Italian 'quaranta giorni' - 40 days! Ships had to wait 40 days before entering Venice during the plague."
   - "'Nightmare' literally means a female evil spirit (mare) that sits on your chest at night! Creepy, right? 😱"

2. **Funny Language Mistakes** (embarrassing situations):
   - "Once my friend wanted to say 'I'm embarrassed' but said 'I'm pregnant' instead! Everyone was shocked! 😂"
   - "A tourist in Spain tried to order 'pollo' (chicken) but said 'polla' instead - everyone laughed! That's a VERY rude word!"
   - "I once told my English teacher 'I have a headache' but said 'I have a heartache' - she thought I was in love! 💔"

3. **Cultural & Travel Stories** (real experiences):
   - "In Japan, slurping noodles is POLITE! I was so confused at first - back home it's rude! 🍜"
   - "Last year in London, I asked for 'chips' and got fries! I wanted potato chips (they call them 'crisps')! 🥔"
   - "Once I visited Iceland in winter - the sun came up at 11 AM and set at 3 PM! Only 4 hours of daylight! ☀️"

4. **Celebrity & Pop Culture Facts** (interesting trivia):
   - "Did you know Arnold Schwarzenegger couldn't say his own name when he started acting? That's why early movies used 'Arnold Strong'! 💪"
   - "The Beatles had to learn German to perform in Hamburg! John Lennon hated it but it made them famous! 🎸"
   - "Elon Musk taught himself English by reading comics and playing video games! Now he's a billionaire! 🚀"

5. **Historical Fun Facts** (crazy true stories):
   - "During WW2, Coca-Cola invented Fanta in Germany because they couldn't get Coke syrup! 🥤"
   - "Shakespeare invented over 1,700 words we still use today - like 'eyeball', 'bedroom', and 'lonely'!"
   - "The longest English word has 189,819 letters! It's a chemical name - it takes 3.5 hours to say! 😅"

6. **Daily Life Stories** (relatable moments):
   - "Yesterday I was texting in English and autocorrect changed 'meeting' to 'eating' - my boss was confused! 😂"
   - "My neighbor from Texas speaks SO fast! Even I can't understand him sometimes - and I'm a tutor! 🤠"
   - "I once fell asleep during a Zoom call and my cat walked across the keyboard! Everyone saw it! 🐱"

🎯 HOW TO USE STORIES:
- Pick a story that relates to the VOCABULARY WORD you're teaching
- Tell it naturally, like chatting with a friend
- Keep it 2-4 sentences (SHORT!)
- End with a question that uses the vocabulary word
- Make the student WANT to respond!

EXAMPLES:

"Speaking of **travel** ✈️ - you won't believe this! I once booked a flight to Budapest but went to Bucharest by mistake! They sound SO similar! I only realized when I landed! 😱 Have you ever mixed up two places?"

"Oh, **restaurant**! 🍽️ Funny story - last month I went to a fancy restaurant in Paris. I tried to order in French but said 'Je suis chaud' (I'm horny) instead of 'J'ai chaud' (I'm hot/warm)! The waiter laughed SO hard! Have you ever made a funny mistake when ordering food?"

"**Weekend** plans? 🎉 You know what's weird? In Saudi Arabia, the weekend is Friday-Saturday, not Saturday-Sunday! I worked there for a year - it took me MONTHS to get used to it! What do you usually do on weekends?"

⚠️ CRITICAL RULES FOR STORIES:
- Frequency depends on level: A1-A2 (30%), B1-B2 (35%), C1-C2 (40%)
- Adjust vocabulary and grammar complexity to match student level
- For A1-A2: use simple words, short sentences, present tense mostly
- For B1-B2: use varied vocabulary, mix tenses naturally
- For C1-C2: use idioms, advanced expressions, sophisticated language
- Stories are engaging teaching moments - use them to show word usage in context

IMPORTANT: 
- NEVER use the same emoji twice in a row
- Mix up response style: reactions (40%) / questions (30%) / corrections (20%) / stories (10%)
- Be HUMAN and spontaneous, not a formula
- Find and correct ALL mistakes, even small ones
- ALWAYS use the format: 🔧 Fix / Correct: with ❌ ✅ 🇷🇺
- MOST OF THE TIME: just react naturally without long stories
- Be encouraging but don't skip corrections!"""
    
    if session_words:
        print(f"[DEBUG call_gemini] Adding {len(session_words)} words to prompt")
        check_word = next((w for w in session_words if w.get('needs_check')), None)
        
        if check_word:
            print(f"[DEBUG call_gemini] Found check word: {check_word}")
            system_prompt += f"\n\n🎯 CRITICAL TASK - WORD MASTERY CHECK:\n"
            system_prompt += f"The word '{check_word['english']}' ({check_word['russian']}) has been used 5 times in conversations.\n"
            system_prompt += f"NOW you must CHECK if the student truly knows this word.\n\n"
            system_prompt += f"Your task:\n"
            system_prompt += f"1. Ask a question that REQUIRES using '{check_word['english']}' in the answer\n"
            system_prompt += f"2. Make it natural and conversational (not like a test)\n"
            system_prompt += f"3. The question should be related to the word's meaning\n\n"
            system_prompt += f"Examples:\n"
            system_prompt += f"- For 'cat': 'Do you have any pets? Tell me about them!' or 'What animals do you like?'\n"
            system_prompt += f"- For 'travel': 'Where would you like to go? Tell me about your dream destination!'\n"
            system_prompt += f"- For 'book': 'What are you reading these days? Any favorite books?'\n\n"
            system_prompt += f"After the student answers, analyze if they used '{check_word['english']}' correctly.\n"
            system_prompt += f"If YES → reply with: '✅ WORD_MASTERED: {check_word['english']}' at the END of your message (after regular response)\n"
            system_prompt += f"If NO or incorrectly → continue teaching naturally"
        else:
            words_list = [f"{w['english']} ({w['russian']})" for w in session_words[:10]]
            print(f"[DEBUG call_gemini] Adding word list to prompt: {words_list}")
            
            # ЖОРСТКИЙ НАКАЗ використовувати слова + примеры + короткие истории
            system_prompt += f"\n\n🎯 CRITICAL VOCABULARY TASK:\n"
            system_prompt += f"You MUST use these words in your responses: {', '.join(words_list)}\n\n"
            system_prompt += f"RULES:\n"
            system_prompt += f"- Use AT LEAST 1 word from this list in EVERY response\n"
            system_prompt += f"- ⚠️ CRITICAL: When you use a word, wrap it in **bold**: **travel**, **plausible**, **weekend**\n"
            system_prompt += f"- Make examples or mini-stories with the word to make it memorable!\n"
            system_prompt += f"- Show the word in CONTEXT so student understands usage\n\n"
            
            system_prompt += f"🎨 HOW TO TEACH WORDS EFFECTIVELY:\n\n"
            system_prompt += f"1. **Simple usage** (30% of time):\n"
            system_prompt += f"   'That sounds **plausible**! Makes sense.'\n\n"
            
            system_prompt += f"2. **Quick example** (40% of time):\n"
            system_prompt += f"   'Nice! So you want to **emmerse** yourself in the game world? Like when you play and forget about everything else?'\n"
            system_prompt += f"   'That's **plausible**! Like saying a story could really happen in real life.'\n\n"
            
            system_prompt += f"3. **Mini-story** (20% of time - 2-3 sentences):\n"
            system_prompt += f"   'Speaking of **travel** ✈️ - I once met a guy who traveled to 30 countries in one year! He said the best part was trying local food. Have you traveled anywhere cool?'\n"
            system_prompt += f"   'You know, **plausible** is interesting! 🤔 My friend told me he saw a UFO - I said 'hmm, not very plausible!' But then he showed me a photo! Was it **plausible** after all? What do you think?'\n\n"
            
            system_prompt += f"4. **Comparison** (10% of time):\n"
            system_prompt += f"   'So **plausible** means believable - like 'that excuse sounds plausible' vs 'that excuse sounds ridiculous'. Make sense?'\n\n"
            
            system_prompt += f"⚠️ IMPORTANT RULES:\n"
            system_prompt += f"- VARY your approach - don't always use same pattern!\n"
            system_prompt += f"- Each word should appear in DIFFERENT context every time\n"
            system_prompt += f"- After giving example/story, ask a follow-up question\n"
            system_prompt += f"- Keep it conversational and fun, not like a textbook\n"
            system_prompt += f"- Use emojis sparingly (1-2 max per message)\n\n"
            
            system_prompt += f"⚠️ CRITICAL: DO NOT just repeat the same word without showing HOW to use it!\n"
            system_prompt += f"⚠️ CRITICAL: ROTATE through words - don't use same word every message!"
    else:
        print(f"[DEBUG call_gemini] NO session_words provided!")
    
    if preferred_topics and len(preferred_topics) > 0:
        topics_list = [f"{t['emoji']} {t['topic']}" for t in preferred_topics[:5]]
        system_prompt += f"\n\nStudent's favorite topics: {', '.join(topics_list)}\nFeel free to bring up these topics in conversation."
    
    # Формируем содержимое для Gemini (system prompt + история + новое сообщение)
    contents = []
    
    # Если есть история - указываем что это продолжение диалога
    if history and len(history) > 0:
        system_prompt += "\n\n⚠️⚠️⚠️ ABSOLUTELY CRITICAL - CONVERSATION IN PROGRESS ⚠️⚠️⚠️\n"
        system_prompt += "This is a CONTINUATION of an existing conversation. You are ALREADY talking to this person.\n\n"
        system_prompt += "FORBIDDEN GREETINGS (DO NOT USE):\n"
        system_prompt += "- 'Hey there' / 'Hi there' / 'Hello' / 'Hey' / 'Hi'\n"
        system_prompt += "- 'So glad' / 'Glad we're back' / 'Good to see you' / 'Welcome back'\n"
        system_prompt += "- 'Glad we got things working' / 'Nice to chat again'\n"
        system_prompt += "- ANY form of greeting or welcoming phrase\n\n"
        system_prompt += "CORRECT APPROACH:\n"
        system_prompt += "- Jump DIRECTLY into responding to their last message\n"
        system_prompt += "- Continue the conversation naturally as if you never stopped\n"
        system_prompt += "- If they ask a question, answer it directly (no greeting first)\n"
        system_prompt += "- If they make a statement, react to it naturally (no greeting first)\n\n"
        system_prompt += "EXAMPLE - WRONG vs RIGHT:\n"
        system_prompt += "Student: 'No'\n"
        system_prompt += "❌ WRONG: 'Hey there! So glad we got things working...'\n"
        system_prompt += "✅ RIGHT: 'Got it! That's totally fine.'\n\n"
        system_prompt += "⚠️ DO NOT say 'Hey there' / 'Hi' / 'Hello' / 'Glad we're back' - you're already talking\n"
        system_prompt += "- Continue like you're in the middle of a text conversation\n"
        system_prompt += "- NEVER greet someone you're already talking to - that's weird!\n"
        system_prompt += "- Imagine you just sent your last message 10 seconds ago - you wouldn't say 'Hey' again!"
    
    # Добавляем системный промпт как первое сообщение пользователя
    contents.append({
        'role': 'user',
        'parts': [{'text': system_prompt}]
    })
    
    # Добавляем ответ модели что она поняла
    contents.append({
        'role': 'model',
        'parts': [{'text': 'Understood! I will follow these instructions.'}]
    })
    
    # Добавляем историю диалога
    for msg in history[-15:]:
        role = 'user' if msg['role'] == 'user' else 'model'
        contents.append({
            'role': role,
            'parts': [{'text': msg['content']}]
        })
    
    # Добавляем новое сообщение
    contents.append({
        'role': 'user',
        'parts': [{'text': user_message}]
    })
    
    # Проверяем доступность API через прокси - сначала получим список моделей
    if proxy_url:
        print(f"[DEBUG] Testing proxy connection with ListModels...")
        list_url = f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}'
        
        proxy_handler = urllib.request.ProxyHandler({
            'http': f'http://{proxy_url}',
            'https': f'http://{proxy_url}'
        })
        opener = urllib.request.build_opener(proxy_handler)
        
        try:
            req = urllib.request.Request(list_url)
            with opener.open(req, timeout=30) as response:
                models_result = json.loads(response.read().decode('utf-8'))
                print(f"[DEBUG] Available models: {[m['name'] for m in models_result.get('models', [])][:5]}")
        except Exception as e:
            print(f"[DEBUG] Failed to list models: {e}")
    
    # Подготавливаем запрос к Gemini REST API
    gemini_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}'
    
    payload = {
        'contents': contents,
        'generationConfig': {
            'temperature': 0.8,
            'maxOutputTokens': 2000,
            'topP': 0.95
        }
    }
    
    # ВСЕГДА используем прокси (прямое подключение из РФ заблокировано Google)
    if not proxy_url:
        raise Exception("PROXY_URL is required for Gemini API access from Russia")
    
    print(f"[DEBUG] Calling Gemini with proxy...")
    print(f"[DEBUG] URL: {gemini_url[:80]}...")
    
    proxy_handler = urllib.request.ProxyHandler({
        'http': f'http://{proxy_url}',
        'https': f'http://{proxy_url}'
    })
    opener = urllib.request.build_opener(proxy_handler)
    
    req = urllib.request.Request(
        gemini_url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with opener.open(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"[DEBUG] Gemini success with proxy!")
            
            # Логируем успешный запрос через прокси
            log_proxy_success(proxy_id)
            
            return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        error_message = str(e)
        if isinstance(e, urllib.error.HTTPError):
            error_body = e.read().decode('utf-8') if e.fp else 'no body'
            error_message = f"HTTP {e.code}: {error_body[:200]}"
        
        print(f"[ERROR] Gemini API failed: {error_message}")
        
        # Логируем ошибку прокси
        log_proxy_failure(proxy_id, error_message)
        
        raise

def get_reply_keyboard():
    """Возвращает актуальную клавиатуру для всех пользователей"""
    return {
        'keyboard': [
            [{'text': '💬 Диалог'}, {'text': '🎤 Голосовой'}],
            [{'text': '✍️ Предложения'}, {'text': '📝 Контекст'}],
            [{'text': '🎯 Ассоциации'}, {'text': '🇷🇺→🇬🇧 Перевод'}],
            [{'text': '🔄 Задать цель заново'}]
        ],
        'resize_keyboard': True,
        'persistent': True
    }

def send_chat_action(chat_id: int, action: str = 'typing'):
    """Отправляет индикатор активности бота (печатает, отправляет фото и тд)"""
    token = os.environ['TELEGRAM_BOT_TOKEN']
    url = f'https://api.telegram.org/bot{token}/sendChatAction'
    
    payload = {
        'chat_id': chat_id,
        'action': action
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=3) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"[WARNING] Failed to send chat action: {e}")
        pass

def send_telegram_voice(chat_id: int, voice_url: str, caption: str = None):
    """Отправляет голосовое сообщение в Telegram"""
    send_chat_action(chat_id, 'record_voice')
    
    token = os.environ['TELEGRAM_BOT_TOKEN']
    url = f'https://api.telegram.org/bot{token}/sendVoice'
    
    payload = {
        'chat_id': chat_id,
        'voice': voice_url
    }
    
    if caption:
        payload['caption'] = caption
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"[ERROR] Failed to send voice: {e}")
        raise

def send_telegram_sticker(chat_id: int, sticker_id: str):
    """Отправляет стикер в Telegram"""
    token = os.environ['TELEGRAM_BOT_TOKEN']
    url = f'https://api.telegram.org/bot{token}/sendSticker'
    
    payload = {
        'chat_id': chat_id,
        'sticker': sticker_id
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"[DEBUG] Sticker sent: {result}")
            return result
    except Exception as e:
        print(f"[ERROR] Failed to send sticker: {e}")
        # Не падаем если стикер не отправился
        return None

def send_telegram_message(chat_id: int, text: str, reply_markup=None, parse_mode='HTML'):
    """Отправляет сообщение в Telegram"""
    send_chat_action(chat_id, 'typing')
    
    token = os.environ['TELEGRAM_BOT_TOKEN']
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    
    if parse_mode:
        payload['parse_mode'] = parse_mode
    
    if reply_markup:
        payload['reply_markup'] = reply_markup
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"[DEBUG] Telegram API response: {result}")
            return result
    except Exception as e:
        print(f"[ERROR] Failed to send message: {e}")
        raise

def edit_telegram_message(chat_id: int, message_id: int, text: str):
    """Редактирует сообщение в Telegram"""
    token = os.environ['TELEGRAM_BOT_TOKEN']
    url = f'https://api.telegram.org/bot{token}/editMessageText'
    
    data = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def set_bot_commands():
    """Устанавливает команды бота в меню Telegram"""
    token = os.environ['TELEGRAM_BOT_TOKEN']
    url = f'https://api.telegram.org/bot{token}/setMyCommands'
    
    commands = [
        {
            'command': 'start',
            'description': '🔄 Начать заново / Изменить цель обучения'
        }
    ]
    
    payload = {
        'commands': commands
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"[DEBUG] Bot commands set: {result}")
            return result
    except Exception as e:
        print(f"[ERROR] Failed to set bot commands: {e}")
        return None

def download_telegram_file(file_id: str) -> bytes:
    """Скачивает файл из Telegram"""
    token = os.environ['TELEGRAM_BOT_TOKEN']
    
    # Получаем путь к файлу
    url = f'https://api.telegram.org/bot{token}/getFile?file_id={file_id}'
    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode('utf-8'))
        file_path = data['result']['file_path']
    
    # Скачиваем файл
    file_url = f'https://api.telegram.org/file/bot{token}/{file_path}'
    with urllib.request.urlopen(file_url) as response:
        return response.read()

def speech_to_text(audio_data: bytes) -> str:
    """Распознает речь через OpenAI Whisper с прокси"""
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    
    if not openai_api_key:
        raise Exception('OpenAI API key not configured')
    
    # Получаем прокси из БД
    proxy_id, proxy_url = get_active_proxy_from_db()
    if not proxy_url:
        proxy_id = None
        proxy_url = os.environ.get('PROXY_URL', '')
        print("[DEBUG] Using PROXY_URL from env for Whisper")
    
    if not proxy_url:
        raise Exception("PROXY_URL is required for OpenAI API access")
    
    # Сохраняем audio_data во временный файл (Whisper требует файл)
    with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_audio:
        temp_audio.write(audio_data)
        temp_audio_path = temp_audio.name
    
    try:
        url = 'https://api.openai.com/v1/audio/transcriptions'
        
        # Настройка прокси для requests
        proxies = {
            'http': f'http://{proxy_url}',
            'https': f'http://{proxy_url}'
        }
        
        with open(temp_audio_path, 'rb') as audio_file:
            files = {
                'file': ('voice.ogg', audio_file, 'audio/ogg')
            }
            data = {
                'model': 'whisper-1',
                'language': 'en'
            }
            headers = {
                'Authorization': f'Bearer {openai_api_key}'
            }
            
            response = requests.post(
                url,
                headers=headers,
                files=files,
                data=data,
                proxies=proxies,
                timeout=30
            )
        
        response.raise_for_status()
        result = response.json()
        
        # Логируем успешный запрос через прокси
        log_proxy_success(proxy_id)
        
        return result.get('text', '')
    
    finally:
        # Удаляем временный файл
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

def text_to_speech_openai(text: str) -> str:
    """Генерирует озвучку через OpenAI TTS с прокси и возвращает CDN URL"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise Exception('OPENAI_API_KEY not configured')
    
    # Получаем прокси из БД
    proxy_id, proxy_url = get_active_proxy_from_db()
    if not proxy_url:
        proxy_id = None
        proxy_url = os.environ.get('PROXY_URL', '')
        print("[DEBUG] Using PROXY_URL from env for OpenAI TTS")
    
    if not proxy_url:
        raise Exception("PROXY_URL is required for OpenAI API access")
    
    # OpenAI TTS API endpoint
    url = 'https://api.openai.com/v1/audio/speech'
    
    payload = {
        'model': 'tts-1',
        'input': text,
        'voice': 'nova',
        'response_format': 'opus'
    }
    
    # Используем прокси для OpenAI
    proxy_handler = urllib.request.ProxyHandler({
        'http': f'http://{proxy_url}',
        'https': f'http://{proxy_url}'
    })
    opener = urllib.request.build_opener(proxy_handler)
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    )
    
    try:
        with opener.open(req, timeout=30) as response:
            audio_data = response.read()
            print(f"[DEBUG] OpenAI TTS success! Audio size: {len(audio_data)} bytes")
            
            # Логируем успешный запрос через прокси
            log_proxy_success(proxy_id)
            
            # Сохраняем в S3
            import boto3
            s3 = boto3.client('s3',
                endpoint_url='https://bucket.poehali.dev',
                aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
            )
            
            file_key = f"voice/{hash(text)}.opus"
            s3.put_object(
                Bucket='files',
                Key=file_key,
                Body=audio_data,
                ContentType='audio/ogg'
            )
            
            cdn_url = f"https://cdn.poehali.dev/projects/{os.environ['AWS_ACCESS_KEY_ID']}/bucket/{file_key}"
            return cdn_url
            
    except Exception as e:
        error_message = str(e)
        if isinstance(e, urllib.error.HTTPError):
            error_body = e.read().decode('utf-8') if e.fp else 'no body'
            error_message = f"HTTP {e.code}: {error_body[:200]}"
        
        print(f"[ERROR] OpenAI TTS failed: {error_message}")
        
        # Логируем ошибку прокси
        log_proxy_failure(proxy_id, error_message)
        
        raise

def text_to_speech(text: str) -> str:
    """Генерирует озвучку через OpenAI TTS (было Yandex)"""
    return text_to_speech_openai(text)

def generate_plan_batch(student_id: int, learning_goal: str, language_level: str, preferred_topics: List[Dict[str, str]], batch_num: int) -> Dict[str, Any]:
    """
    Генерирует план обучения через Gemini API
    """
    try:
        print(f"[DEBUG] generate_plan_batch STARTED: batch={batch_num}")
        
        api_key = os.environ['GEMINI_API_KEY']
        proxy_id, proxy_url = get_active_proxy_from_db()
        if not proxy_url:
            proxy_id = None
            proxy_url = os.environ.get('PROXY_URL', '')
        
        if not proxy_url:
            return {'success': False, 'error': 'PROXY_URL is required'}
        
        gemini_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}'
        
        topics_display = ', '.join([f"{t.get('emoji', '💡')} {t.get('topic', 'Общие темы')}" for t in preferred_topics[:5]]) if preferred_topics else '💡 Общие темы'
        
        week_start = (batch_num - 1) * 2 + 1
        week_end = batch_num * 2
        
        # Получаем список уже добавленных слов студента
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            f"SELECT DISTINCT w.english_text FROM {SCHEMA}.student_words sw "
            f"JOIN {SCHEMA}.words w ON w.id = sw.word_id "
            f"WHERE sw.student_id = {student_id}"
        )
        existing_words = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        existing_words_str = ', '.join(existing_words[:100]) if existing_words else 'none'
        print(f"[DEBUG] Student has {len(existing_words)} existing words")
        print(f"[DEBUG] Generating weeks {week_start}-{week_end}...")
        
        prompt = f'''Generate 1 English word for level {language_level}. Goal: {learning_goal}

Return JSON: {{"plan": [{{"week": 1, "vocabulary": [{{"english": "word", "russian": "перевод"}}], "phrases": [], "expressions": []}}]}}'''
        
        payload = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {
                'temperature': 0.7, 
                'maxOutputTokens': 2000,
                'topP': 0.95,
                'topK': 40
            }
        }
        
        proxy_handler = urllib.request.ProxyHandler({
            'http': f'http://{proxy_url}',
            'https': f'http://{proxy_url}'
        })
        opener = urllib.request.build_opener(proxy_handler)
        
        req = urllib.request.Request(
            gemini_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
            
        # Пытаемся сгенерировать план с retry
        max_retries = 2
        for attempt in range(max_retries):
            print(f"[DEBUG] Calling Gemini API for weeks {week_start}-{week_end}... (timeout=25s, attempt {attempt+1}/{max_retries})")
            try:
                with opener.open(req, timeout=25) as response:
                    print(f"[DEBUG] Gemini API responded for weeks {week_start}-{week_end}!")
                    gemini_result = json.loads(response.read().decode('utf-8'))
                    plan_text = gemini_result['candidates'][0]['content']['parts'][0]['text']
                    
                    print(f"[DEBUG] Parsing JSON for weeks {week_start}-{week_end}...")
                    print(f"[DEBUG] Raw Gemini response length: {len(plan_text)} chars")
                    
                    # Используем safe_json_parse для обработки кривого JSON
                    batch_data = safe_json_parse(plan_text, None)
                    
                    if not batch_data or 'plan' not in batch_data:
                        print(f"[WARNING] Failed to parse JSON on attempt {attempt+1}")
                        print(f"[DEBUG] Raw response (first 1000 chars): {plan_text[:1000]}")
                        if attempt < max_retries - 1:
                            print(f"[DEBUG] Retrying...")
                            continue
                        else:
                            return {'success': False, 'error': f'Failed to parse Gemini response after {max_retries} attempts'}
                    
                    batch_weeks = batch_data.get('plan', [])
                    
                    if not batch_weeks or len(batch_weeks) == 0:
                        print(f"[WARNING] Empty plan array on attempt {attempt+1}")
                        if attempt < max_retries - 1:
                            print(f"[DEBUG] Retrying...")
                            continue
                        else:
                            return {'success': False, 'error': f'Gemini returned empty plan after {max_retries} attempts'}
                    
                    log_proxy_success(proxy_id)
                    print(f"[DEBUG] Generated {len(batch_weeks)} weeks successfully on attempt {attempt+1}")
                    break
                    
            except Exception as api_error:
                print(f"[ERROR] Gemini API call failed on attempt {attempt+1}: {api_error}")
                log_proxy_failure(proxy_id, str(api_error))
                if attempt < max_retries - 1:
                    print(f"[DEBUG] Retrying with new proxy...")
                    # Получаем новый прокси для retry
                    proxy_id, proxy_url = get_active_proxy_from_db()
                    if not proxy_url:
                        proxy_url = os.environ.get('PROXY_URL', '')
                    proxy_handler = urllib.request.ProxyHandler({
                        'http': f'http://{proxy_url}',
                        'https': f'http://{proxy_url}'
                    })
                    opener = urllib.request.build_opener(proxy_handler)
                    continue
                else:
                    return {'success': False, 'error': f'Gemini API error after {max_retries} attempts: {str(api_error)}'}
        
        plan_weeks = batch_weeks
        
        # Фильтруем дубликаты ПОСЛЕ генерации Gemini
        print(f"[DEBUG] Filtering duplicates from generated words...")
        all_generated_words = []
        for week_data in plan_weeks:
            all_generated_words.extend([w['english'].strip().lower() for w in week_data.get('vocabulary', [])])
            all_generated_words.extend([p['english'].strip().lower() for p in week_data.get('phrases', [])])
            all_generated_words.extend([e['english'].strip().lower() for e in week_data.get('expressions', [])])
        
        # Проверяем какие слова РЕАЛЬНО есть дубликаты
        duplicates = [w for w in all_generated_words if w in existing_words]
        
        if duplicates:
            print(f"[WARNING] Found {len(duplicates)} duplicates: {duplicates[:10]}")
            
            # Запрашиваем замену у Gemini для дубликатов
            replacement_prompt = f'''Generate {len(duplicates)} NEW English words/phrases for level {language_level}.
Goal: {learning_goal}

⚠️ CRITICAL: DO NOT use these words (they are duplicates): {', '.join(duplicates)}
⚠️ ALSO DO NOT use existing words: {existing_words_str}

Return ONLY valid JSON:
{{"words": [{{"english": "word1", "russian": "перевод1"}}, {{"english": "word2", "russian": "перевод2"}}]}}'''
            
            try:
                replacement_payload = {
                    'contents': [{'parts': [{'text': replacement_prompt}]}],
                    'generationConfig': {'temperature': 0.9, 'maxOutputTokens': 2000}
                }
                
                replacement_req = urllib.request.Request(
                    gemini_url,
                    data=json.dumps(replacement_payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json'}
                )
                
                with opener.open(replacement_req, timeout=25) as resp:
                    replacement_result = json.loads(resp.read().decode('utf-8'))
                    replacement_text = replacement_result['candidates'][0]['content']['parts'][0]['text']
                    replacement_data = safe_json_parse(replacement_text, {'words': []})
                    
                    print(f"[DEBUG] Got {len(replacement_data.get('words', []))} replacement words")
                    
                    # Заменяем дубликаты в plan_weeks
                    replacement_idx = 0
                    for week_data in plan_weeks:
                        for category in ['vocabulary', 'phrases', 'expressions']:
                            for i, item in enumerate(week_data.get(category, [])):
                                if item['english'].strip().lower() in duplicates and replacement_idx < len(replacement_data['words']):
                                    week_data[category][i] = replacement_data['words'][replacement_idx]
                                    replacement_idx += 1
                                    print(f"[DEBUG] Replaced duplicate '{item['english']}' with '{replacement_data['words'][replacement_idx-1]['english']}'")
            except Exception as e:
                print(f"[ERROR] Failed to get replacements: {e}")
        
        # Сохраняем ВСЕ слова и фразы в БД
        print(f"[DEBUG] Saving {len(plan_weeks)} weeks to DB...")
        conn = get_db_connection()
        cur = conn.cursor()
        
        total_words_added = 0
        actually_added = 0
        for week_data in plan_weeks:
            # Добавляем vocabulary
            for word_data in week_data.get('vocabulary', []):
                english = word_data['english'].strip().lower()
                russian = word_data['russian'].strip()
                
                english_escaped = english.replace("'", "''")
                russian_escaped = russian.replace("'", "''")
                
                cur.execute(
                    f"INSERT INTO {SCHEMA}.words (english_text, russian_translation) "
                    f"VALUES ('{english_escaped}', '{russian_escaped}') "
                    f"ON CONFLICT (english_text) DO UPDATE SET russian_translation = EXCLUDED.russian_translation "
                    f"RETURNING id"
                )
                word_id = cur.fetchone()[0]
                
                # Проверяем добавилось ли слово студенту
                cur.execute(
                    f"SELECT id FROM {SCHEMA}.student_words WHERE student_id = {student_id} AND word_id = {word_id}"
                )
                already_exists = cur.fetchone()
                
                if not already_exists:
                    cur.execute(
                        f"INSERT INTO {SCHEMA}.student_words (student_id, word_id, teacher_id) "
                        f"VALUES ({student_id}, {word_id}, {student_id})"
                    )
                    actually_added += 1
                
                total_words_added += 1
            
            # Добавляем phrases
            for phrase_data in week_data.get('phrases', []):
                english = phrase_data['english'].strip().lower()
                russian = phrase_data['russian'].strip()
                
                english_escaped = english.replace("'", "''")
                russian_escaped = russian.replace("'", "''")
                
                cur.execute(
                    f"INSERT INTO {SCHEMA}.words (english_text, russian_translation) "
                    f"VALUES ('{english_escaped}', '{russian_escaped}') "
                    f"ON CONFLICT (english_text) DO UPDATE SET russian_translation = EXCLUDED.russian_translation "
                    f"RETURNING id"
                )
                word_id = cur.fetchone()[0]
                
                cur.execute(
                    f"SELECT id FROM {SCHEMA}.student_words WHERE student_id = {student_id} AND word_id = {word_id}"
                )
                already_exists = cur.fetchone()
                
                if not already_exists:
                    cur.execute(
                        f"INSERT INTO {SCHEMA}.student_words (student_id, word_id, teacher_id) "
                        f"VALUES ({student_id}, {word_id}, {student_id})"
                    )
                    actually_added += 1
                
                total_words_added += 1
            
            # Добавляем expressions
            for expr_data in week_data.get('expressions', []):
                english = expr_data['english'].strip().lower()
                russian = expr_data['russian'].strip()
                
                english_escaped = english.replace("'", "''")
                russian_escaped = russian.replace("'", "''")
                
                cur.execute(
                    f"INSERT INTO {SCHEMA}.words (english_text, russian_translation) "
                    f"VALUES ('{english_escaped}', '{russian_escaped}') "
                    f"ON CONFLICT (english_text) DO UPDATE SET russian_translation = EXCLUDED.russian_translation "
                    f"RETURNING id"
                )
                word_id = cur.fetchone()[0]
                
                cur.execute(
                    f"SELECT id FROM {SCHEMA}.student_words WHERE student_id = {student_id} AND word_id = {word_id}"
                )
                already_exists = cur.fetchone()
                
                if not already_exists:
                    cur.execute(
                        f"INSERT INTO {SCHEMA}.student_words (student_id, word_id, teacher_id) "
                        f"VALUES ({student_id}, {word_id}, {student_id})"
                    )
                    actually_added += 1
                
                total_words_added += 1
        
        print(f"[DEBUG] Total: {total_words_added}, Actually added (new): {actually_added}")
        
        # Сохраняем сам план в БД (в поле learning_plan как JSONB)
        plan_json = json.dumps(plan_weeks, ensure_ascii=False).replace("'", "''")
        cur.execute(
            f"UPDATE {SCHEMA}.users SET "
            f"learning_plan = '{plan_json}'::jsonb "
            f"WHERE telegram_id = {student_id}"
        )
        
        cur.close()
        conn.close()
        
        print(f"[DEBUG] Saved {total_words_added} words/phrases to DB. Formatting message...")
        
        # Форматируем сообщение с планом для пользователя
        plan_message = f"📋 ТВОЙ ПЕРСОНАЛЬНЫЙ ПЛАН НА МЕСЯЦ\n\n"
        plan_message += f"🎯 Цель: {learning_goal}\n"
        plan_message += f"📊 Уровень: {language_level}\n"
        plan_message += f"💡 Темы: {topics_display}\n"
        plan_message += f"📚 Всего материалов: {total_words_added} слов и фраз\n\n"
        plan_message += "━━━━━━━━━━━━━━━━━━━\n\n"
        
        for week_data in plan_weeks:
            week_num = week_data.get('week', 1)
            focus = week_data.get('focus', 'Обучение')
            topics = week_data.get('conversation_topics', [])
            vocab = week_data.get('vocabulary', [])
            phrases = week_data.get('phrases', [])
            expressions = week_data.get('expressions', [])
            actions = week_data.get('actions', [])
            
            plan_message += f"📅 НЕДЕЛЯ {week_num}: {focus}\n\n"
            
            if topics:
                plan_message += "💬 Темы для разговоров:\n"
                for topic in topics:
                    plan_message += f"  • {topic}\n"
                plan_message += "\n"
            
            if vocab:
                plan_message += f"📖 Слова (7 в день, всего {len(vocab)}):\n"
                for word in vocab[:7]:  # Показываем первые 7 (1 день)
                    plan_message += f"  • {word['english']} — {word['russian']}\n"
                if len(vocab) > 7:
                    plan_message += f"  ... и еще {len(vocab) - 7} слов\n"
                plan_message += "\n"
            
            if phrases:
                plan_message += f"💭 Фразы (2 в день, всего {len(phrases)}):\n"
                for phrase in phrases[:4]:  # Показываем первые 4 (2 дня)
                    plan_message += f"  • {phrase['english']} — {phrase['russian']}\n"
                if len(phrases) > 4:
                    plan_message += f"  ... и еще {len(phrases) - 4} фраз\n"
                plan_message += "\n"
            
            if expressions:
                plan_message += f"✨ Устойчивые выражения (1 в день, всего {len(expressions)}):\n"
                for expr in expressions[:3]:  # Показываем первые 3
                    plan_message += f"  • {expr['english']} — {expr['russian']}\n"
                if len(expressions) > 3:
                    plan_message += f"  ... и еще {len(expressions) - 3} выражений\n"
                plan_message += "\n"
            
            if actions:
                plan_message += "✅ Действия:\n"
                for action in actions:
                    plan_message += f"  • {action}\n"
            
            plan_message += "\n━━━━━━━━━━━━━━━━━━━\n\n"
        
        plan_message += "❓ Тебе подходит этот план?"
        
        print(f"[DEBUG] Batch {batch_num} complete: {len(plan_weeks)} weeks, {total_words_added} words added")
        
        return {
            'success': True,
            'weeks': plan_weeks,
            'words_added': total_words_added
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to generate monthly plan: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def generate_adaptive_question(level: str, used_words: list) -> dict:
    """Генерирует вопрос для адаптивного теста через Gemini"""
    api_key = os.environ['GEMINI_API_KEY']
    proxy_id, proxy_url = get_active_proxy_from_db()
    if not proxy_url:
        proxy_url = os.environ.get('PROXY_URL', '')
    
    gemini_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}'
    
    # Для высоких уровней (B2+) используем фразы и выражения
    import random
    item_types = ['word', 'phrase', 'expression'] if level in ['B2', 'C1', 'C2'] else ['word', 'phrase']
    chosen_type = random.choice(item_types)
    
    used_words_str = ', '.join(used_words) if used_words else 'none'
    
    # Пытаемся сгенерировать уникальное слово (максимум 3 попытки)
    for attempt in range(3):
        prompt = f'''You are testing English level. Generate ONE {chosen_type} for level {level}.

CRITICAL: You MUST NOT use these words: {used_words_str}

Type: {chosen_type}
- word: single vocabulary word (e.g. "achieve")
- phrase: common phrase (e.g. "take care")  
- expression: idiom (e.g. "break the ice")

Level guidelines:
- A1: basic words (cat, book, home)
- A2: everyday words (hobby, weather)
- B1: abstract words (decision, opportunity)
- B2+: sophisticated vocabulary
- C1+: advanced vocabulary
- C2: native-level expressions

Return ONLY short JSON:
{{"english": "word_here", "type": "{chosen_type}", "level": "{level}"}}'''
        
        payload = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {
                'temperature': 0.9 + (attempt * 0.05),
                'maxOutputTokens': 2000,
                'topP': 0.95,
                'topK': 50
            }
        }
        
        proxy_handler = urllib.request.ProxyHandler({
            'http': f'http://{proxy_url}',
            'https': f'http://{proxy_url}'
        })
        opener = urllib.request.build_opener(proxy_handler)
        
        req = urllib.request.Request(
            gemini_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            with opener.open(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                text = result['candidates'][0]['content']['parts'][0]['text']
                
                print(f"[DEBUG] Gemini generated (level={level}, type={chosen_type}, attempt={attempt+1}): {text[:200]}")
                
                # Парсим БЕЗ fallback
                item = safe_json_parse(text, None)
                
                if not item or 'english' not in item:
                    print(f"[ERROR] Invalid JSON on attempt {attempt+1}: {text[:200]}")
                    if attempt == 2:
                        raise Exception(f"Gemini failed after 3 attempts")
                    continue
                
                # Проверяем уникальность
                if item['english'] not in used_words:
                    print(f"[DEBUG] Accepted: {item['english']}")
                    log_proxy_success(proxy_id)
                    return item
                else:
                    print(f"[WARNING] Word '{item['english']}' already used")
                    
        except Exception as e:
            error_msg = str(e)
            print(f"[ERROR] Attempt {attempt+1} failed: {error_msg}")
            
            # Логируем ошибку прокси
            log_proxy_failure(proxy_id, error_msg)
            
            # Если прокси упал - берем новый на следующей попытке
            if attempt < 2:
                print(f"[WARNING] Proxy failed, getting new one for attempt {attempt+2}")
                proxy_id, proxy_url = get_active_proxy_from_db()
                if not proxy_url:
                    proxy_url = os.environ.get('PROXY_URL', '')
                proxy_handler = urllib.request.ProxyHandler({
                    'http': f'http://{proxy_url}',
                    'https': f'http://{proxy_url}'
                })
                opener = urllib.request.build_opener(proxy_handler)
                continue
            else:
                raise
    
    raise Exception(f"Failed to generate unique {chosen_type} for level {level}")

def generate_plan_async(chat_id: int, user_id: int):
    """
    Асинхронная генерация плана через HTTP POST к самому себе
    Используется для запуска генерации в отдельном потоке
    """
    try:
        # Получаем данные пользователя
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            f"SELECT learning_goal, language_level, preferred_topics FROM {SCHEMA}.users WHERE telegram_id = {user_id}"
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            print(f"[ERROR] User {user_id} not found for async plan generation")
            return
        
        learning_goal, language_level, preferred_topics = row
        
        # URL самого себя из func2url.json
        bot_url = 'https://functions.poehali.dev/92013b11-9080-40b5-8b24-10317e48a4f7'
        
        payload = {
            'action': 'generate_plan_async',
            'user_id': user_id,
            'chat_id': chat_id,
            'learning_goal': learning_goal,
            'language_level': language_level,
            'preferred_topics': preferred_topics or [],
            'selected_topic': '💡 Общие темы'
        }
        
        req = urllib.request.Request(
            bot_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        print(f"[DEBUG] Triggering async plan generation via HTTP POST for user {user_id}")
        
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"[DEBUG] Async plan generation triggered: {result}")
            
    except Exception as e:
        print(f"[ERROR] Failed to trigger async plan generation: {e}")
        import traceback
        traceback.print_exc()

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Обработчик Telegram webhook - бот отвечает прямо в чате
    """
    # ⚡ ОПТИМИЗАЦИЯ: Очищаем кэш в начале каждого запроса
    global _words_ensured_cache
    _words_ensured_cache = {}
    
    # Устанавливаем команды бота при первом запуске (идемпотентно)
    try:
        set_bot_commands()
    except Exception as e:
        print(f"[WARNING] Failed to set bot commands: {e}")
    
    method = event.get('httpMethod', 'POST')
    path = event.get('path', '/')
    query_params = event.get('queryStringParameters', {}) or {}
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    # СПЕЦИАЛЬНЫЙ ЭНДПОИНТ: Асинхронная генерация плана
    # Вызывается из самого бота для фоновой генерации
    if method == 'POST':
        body_str = event.get('body', '{}')
        body_data = json.loads(body_str) if body_str else {}
        
        if body_data.get('action') == 'generate_plan_async':
            try:
                user_id = body_data['user_id']
                chat_id = body_data['chat_id']
                learning_goal = body_data['learning_goal']
                language_level = body_data['language_level']
                preferred_topics = body_data['preferred_topics']
                selected_topic = body_data['selected_topic']
                
                print(f"[DEBUG] ASYNC: Starting plan generation for user {user_id}")
                
                result = generate_plan_batch(user_id, learning_goal, language_level, preferred_topics, batch_num=1)
                print(f"[DEBUG] ASYNC: Plan generation finished: success={result.get('success')}")
                
                if not result.get('success'):
                    send_telegram_message(
                        chat_id,
                        f'❌ Ошибка генерации плана: {result.get("error", "Unknown error")}\n\nПопробуй /start',
                        parse_mode=None
                    )
                else:
                    # Сохраняем план
                    conn = get_db_connection()
                    cur = conn.cursor()
                    plan_json = json.dumps(result['weeks'], ensure_ascii=False).replace("'", "''")
                    cur.execute(
                        f"UPDATE {SCHEMA}.users SET learning_plan = '{plan_json}'::jsonb WHERE telegram_id = {user_id}"
                    )
                    cur.close()
                    conn.close()
                    
                    # Форматируем и отправляем сообщение
                    if not result.get('weeks') or len(result['weeks']) == 0:
                        send_telegram_message(chat_id, '❌ План пустой. Попробуй /start', parse_mode=None)
                    else:
                        week_data = result['weeks'][0]
                        vocab = week_data.get('vocabulary', [])
                        phrases = week_data.get('phrases', [])
                        expressions = week_data.get('expressions', [])
                        
                        topics_text = ', '.join([f"{t.get('emoji', '💡')} {t.get('topic', 'Общие темы')}" for t in preferred_topics[:5]]) if preferred_topics else selected_topic
                        
                        plan_message = f"✅ ГОТОВО! Твой стартовый набор:\n\n"
                        plan_message += f"🎯 Цель: {learning_goal}\n"
                        plan_message += f"📊 Уровень: {language_level}\n"
                        plan_message += f"💡 Темы: {topics_text}\n\n"
                        
                        if vocab:
                            plan_message += f"📖 Слова ({len(vocab)} шт):\n"
                            for word in vocab:
                                plan_message += f"  • {word['english']} — {word['russian']}\n"
                            plan_message += "\n"
                        
                        if phrases:
                            plan_message += f"💭 Фразы ({len(phrases)} шт):\n"
                            for phrase in phrases:
                                plan_message += f"  • {phrase['english']} — {phrase['russian']}\n"
                            plan_message += "\n"
                        
                        if expressions:
                            plan_message += f"✨ Выражения ({len(expressions)} шт):\n"
                            for expr in expressions:
                                plan_message += f"  • {expr['english']} — {expr['russian']}\n"
                            plan_message += "\n"
                        
                        plan_message += "Начинаем практику! 🚀"
                        
                        send_telegram_message(
                            chat_id,
                            plan_message,
                            parse_mode=None
                        )
                        print(f"[DEBUG] ASYNC: Plan message sent successfully")
                        
                        # Переключаем в режим диалога
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute(f"UPDATE {SCHEMA}.users SET conversation_mode = 'dialog' WHERE telegram_id = {user_id}")
                        cur.close()
                        conn.close()
                        
                        # Получаем данные пользователя для call_gemini
                        user_data = get_user(user_id)
                        session_words = get_session_words(user_id, limit=10)
                        
                        # Просто отправляем приветствие и ждём что пользователь напишет первым
                        send_telegram_message(
                            chat_id,
                            '💬 Готова начать! Напиши мне что-нибудь на английском 😊',
                            get_reply_keyboard(),
                            parse_mode=None
                        )
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'success': True}),
                    'isBase64Encoded': False
                }
                
            except Exception as e:
                print(f"[ERROR] ASYNC generation failed: {e}")
                import traceback
                traceback.print_exc()
                
                # Отправляем сообщение об ошибке
                try:
                    send_telegram_message(
                        body_data.get('chat_id'),
                        '❌ Произошла ошибка при генерации плана. Попробуй еще раз через /start',
                        parse_mode=None
                    )
                except:
                    pass
                
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': str(e)}),
                    'isBase64Encoded': False
                }
    
    # СПЕЦИАЛЬНЫЙ ЭНДПОИНТ: Асинхронная генерация плана
    # Вызывается из самого бота для фоновой генерации
    if method == 'POST':
        body_str = event.get('body', '{}')
        try:
            body_data = json.loads(body_str) if body_str else {}
        except:
            body_data = {}
        
        if body_data.get('action') == 'generate_plan_async':
            try:
                user_id = body_data['user_id']
                chat_id = body_data['chat_id']
                learning_goal = body_data['learning_goal']
                language_level = body_data['language_level']
                preferred_topics = body_data['preferred_topics']
                selected_topic = body_data['selected_topic']
                
                print(f"[DEBUG] ASYNC: Starting plan generation for user {user_id}")
                
                result = generate_plan_batch(user_id, learning_goal, language_level, preferred_topics, batch_num=1)
                print(f"[DEBUG] ASYNC: Plan generation finished: success={result.get('success')}")
                
                if not result.get('success'):
                    send_telegram_message(
                        chat_id,
                        f'❌ Ошибка генерации плана: {result.get("error", "Unknown error")}\n\nПопробуй /start',
                        parse_mode=None
                    )
                else:
                    # Сохраняем план
                    conn = get_db_connection()
                    cur = conn.cursor()
                    plan_json = json.dumps(result['weeks'], ensure_ascii=False).replace("'", "''")
                    cur.execute(
                        f"UPDATE {SCHEMA}.users SET learning_plan = '{plan_json}'::jsonb WHERE telegram_id = {user_id}"
                    )
                    cur.close()
                    conn.close()
                    
                    # Форматируем и отправляем сообщение
                    if not result.get('weeks') or len(result['weeks']) == 0:
                        send_telegram_message(chat_id, '❌ План пустой. Попробуй /start', parse_mode=None)
                    else:
                        week_data = result['weeks'][0]
                        vocab = week_data.get('vocabulary', [])
                        phrases = week_data.get('phrases', [])
                        expressions = week_data.get('expressions', [])
                        
                        topics_text = ', '.join([f"{t.get('emoji', '💡')} {t.get('topic', 'Общие темы')}" for t in preferred_topics[:5]]) if preferred_topics else selected_topic
                        
                        plan_message = f"✅ ГОТОВО! Твой стартовый набор:\n\n"
                        plan_message += f"🎯 Цель: {learning_goal}\n"
                        plan_message += f"📊 Уровень: {language_level}\n"
                        plan_message += f"💡 Темы: {topics_text}\n\n"
                        
                        if vocab:
                            plan_message += f"📖 Слова ({len(vocab)} шт):\n"
                            for word in vocab:
                                plan_message += f"  • {word['english']} — {word['russian']}\n"
                            plan_message += "\n"
                        
                        if phrases:
                            plan_message += f"💭 Фразы ({len(phrases)} шт):\n"
                            for phrase in phrases:
                                plan_message += f"  • {phrase['english']} — {phrase['russian']}\n"
                            plan_message += "\n"
                        
                        if expressions:
                            plan_message += f"✨ Выражения ({len(expressions)} шт):\n"
                            for expr in expressions:
                                plan_message += f"  • {expr['english']} — {expr['russian']}\n"
                            plan_message += "\n"
                        
                        plan_message += "Начинаем практику! 🚀"
                        
                        send_telegram_message(
                            chat_id,
                            plan_message,
                            parse_mode=None
                        )
                        print(f"[DEBUG] ASYNC: Plan message sent successfully")
                        
                        # Переключаем в режим диалога
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute(f"UPDATE {SCHEMA}.users SET conversation_mode = 'dialog' WHERE telegram_id = {user_id}")
                        cur.close()
                        conn.close()
                        
                        # Получаем данные пользователя для call_gemini
                        user_data = get_user(user_id)
                        session_words = get_session_words(user_id, limit=10)
                        
                        # Просто отправляем приветствие и ждём что пользователь напишет первым
                        send_telegram_message(
                            chat_id,
                            '💬 Готова начать! Напиши мне что-нибудь на английском 😊',
                            get_reply_keyboard(),
                            parse_mode=None
                        )
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'success': True}),
                    'isBase64Encoded': False
                }
                
            except Exception as e:
                print(f"[ERROR] ASYNC generation failed: {e}")
                import traceback
                traceback.print_exc()
                
                # Отправляем сообщение об ошибке
                try:
                    send_telegram_message(
                        body_data.get('chat_id'),
                        '❌ Произошла ошибка при генерации плана. Попробуй еще раз через /start',
                        parse_mode=None
                    )
                except:
                    pass
                
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': str(e)}),
                    'isBase64Encoded': False
                }
    
    # СПЕЦИАЛЬНЫЙ ЭНДПОИНТ: Очистка webhook и pending updates
    # Вызов: GET https://your-function-url/?action=clear_webhook
    if method == 'GET' and query_params.get('action') == 'clear_webhook':
        try:
            bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
            if not bot_token:
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'TELEGRAM_BOT_TOKEN not configured'}),
                    'isBase64Encoded': False
                }
            
            webhook_url = 'https://functions.poehali.dev/92013b11-9080-40b5-8b24-10317e48a4f7'
            
            # 1. Получаем текущий статус
            get_info_url = f'https://api.telegram.org/bot{bot_token}/getWebhookInfo'
            with urllib.request.urlopen(get_info_url) as response:
                webhook_info = json.loads(response.read().decode('utf-8'))
            
            pending_before = webhook_info.get('result', {}).get('pending_update_count', 0)
            
            # 2. Удаляем webhook с drop_pending_updates=true
            delete_url = f'https://api.telegram.org/bot{bot_token}/deleteWebhook'
            delete_payload = json.dumps({'drop_pending_updates': True}).encode('utf-8')
            
            req = urllib.request.Request(
                delete_url,
                data=delete_payload,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                delete_result = json.loads(response.read().decode('utf-8'))
            
            # 3. Устанавливаем webhook заново
            set_url = f'https://api.telegram.org/bot{bot_token}/setWebhook'
            set_payload = json.dumps({
                'url': webhook_url,
                'drop_pending_updates': True,
                'max_connections': 40,
                'allowed_updates': ['message', 'callback_query', 'my_chat_member', 'pre_checkout_query', 'successful_payment']
            }).encode('utf-8')
            
            req = urllib.request.Request(
                set_url,
                data=set_payload,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                set_result = json.loads(response.read().decode('utf-8'))
            
            # 4. Проверяем финальный статус
            with urllib.request.urlopen(get_info_url) as response:
                final_info = json.loads(response.read().decode('utf-8'))
            
            pending_after = final_info.get('result', {}).get('pending_update_count', 0)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': True,
                    'webhook_url': webhook_url,
                    'pending_updates_before': pending_before,
                    'pending_updates_after': pending_after,
                    'deleted_updates': pending_before - pending_after,
                    'message': f'✅ Webhook очищен! Удалено {pending_before - pending_after} старых сообщений.'
                }),
                'isBase64Encoded': False
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to clear webhook: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': str(e)}),
                'isBase64Encoded': False
            }
    
    try:
        body = json.loads(event.get('body', '{}'))
        print(f"[DEBUG] Received update: {json.dumps(body)}")
        
        # Обработка callback_query (выбор роли или режима)
        if 'callback_query' in body:
            callback = body['callback_query']
            data = callback.get('data', '')
            chat_id = callback['message']['chat']['id']
            message_id = callback['message']['message_id']
            user = callback['from']
            callback_id = callback['id']
            
            # Отвечаем на callback (если упадёт - продолжаем работу)
            try:
                token = os.environ['TELEGRAM_BOT_TOKEN']
                answer_url = f'https://api.telegram.org/bot{token}/answerCallbackQuery'
                answer_payload = json.dumps({'callback_query_id': callback_id}).encode('utf-8')
                
                answer_req = urllib.request.Request(answer_url, data=answer_payload, headers={'Content-Type': 'application/json'}, method='POST')
                with urllib.request.urlopen(answer_req, timeout=5) as resp:
                    answer_result = json.loads(resp.read().decode('utf-8'))
                    print(f"[DEBUG] answerCallbackQuery success: {answer_result.get('ok')}")
            except Exception as e:
                print(f"[ERROR] answerCallbackQuery failed: {e} - continuing anyway")
            
            if data.startswith('goal_'):
                goal_type = data.replace('goal_', '')
                
                goal_texts = {
                    'travel': 'Хочу свободно общаться в путешествиях',
                    'career': 'Нужен английский для работы и карьеры',
                    'communication': 'Хочу общаться с людьми по всему миру',
                    'study': 'Готовлюсь к экзамену или учебе за границей',
                    'custom': ''
                }
                
                if goal_type == 'custom':
                    # Пользователь хочет ввести свою цель
                    edit_telegram_message(
                        chat_id,
                        message_id,
                        '✍️ Отлично! Напиши своими словами - к какому результату ты хочешь прийти?\n\n'
                        'Например:\n'
                        '• "Через 2 месяца лечу в Таиланд, хочу свободно общаться"\n'
                        '• "Нужен для работы программистом"\n'
                        '• "Просто хочу подтянуть разговорный"'
                    )
                    # Оставляем в режиме awaiting_goal
                else:
                    # Используем готовую цель
                    goal_text = goal_texts.get(goal_type, 'Хочу улучшить английский')
                    
                    edit_telegram_message(
                        chat_id,
                        message_id,
                        f'✅ Понял! Твоя цель: <b>{goal_text}</b>.\n\n'
                        '⏳ Сейчас запущу адаптивный тест - он САМ определит твой уровень через вопросы...'
                    )
                    
                    # СРАЗУ НАЧИНАЕМ АДАПТИВНЫЙ ТЕСТ (БЕЗ ВЫБОРА УРОВНЯ!)
                    # Сохраняем состояние - начинаем адаптивный тест
                    conn = get_db_connection()
                    cur = conn.cursor()
                    
                    # Инициализируем тест: начинаем с A1
                    test_state = json.dumps({
                        'question_num': 0,
                        'history': []  # [{"level": "A2", "item": "travel", "answer": "путешествие", "correct": true}]
                    }, ensure_ascii=False).replace("'", "''")
                    
                    cur.execute(
                        f"UPDATE {SCHEMA}.users SET "
                        f"conversation_mode = 'adaptive_level_test', "
                        f"test_phrases = '{test_state}'::jsonb "
                        f"WHERE telegram_id = {telegram_id}"
                    )
                    cur.close()
                    conn.close()
                    
                    # Генерируем ПЕРВЫЙ вопрос через Gemini (начинаем с A1)
                    try:
                        first_item = generate_adaptive_question('A1', [])
                        
                        # Отправляем первый вопрос
                        type_emojis = {'word': '📖', 'phrase': '💬', 'expression': '✨'}
                        emoji = type_emojis.get(first_item.get('type', 'word'), '📖')
                        
                        question_message = f'{emoji} <b>Вопрос 1/10</b>\n\n'
                        question_message += f'Переведи на русский:\n<b>{first_item["english"]}</b>'
                        
                        send_telegram_message(chat_id, question_message)
                        
                        # Обновляем состояние с текущим вопросом
                        test_state = {
                            'current_item': first_item,
                            'question_num': 1,
                            'history': []
                        }
                        
                        conn = get_db_connection()
                        cur = conn.cursor()
                        test_state_json = json.dumps(test_state, ensure_ascii=False).replace("'", "''")
                        cur.execute(
                            f"UPDATE {SCHEMA}.users SET test_phrases = '{test_state_json}'::jsonb "
                            f"WHERE telegram_id = {telegram_id}"
                        )
                        cur.close()
                        conn.close()
                        
                    except Exception as e:
                        print(f"[ERROR] Failed to start adaptive test: {e}")
                        import traceback
                        traceback.print_exc()
                        send_telegram_message(chat_id, '❌ Ошибка запуска теста. Попробуй /start')
            
            elif data.startswith('subscribe_'):
                # Обработка выбора тарифа подписки через ЮKassa
                plan_key = data.replace('subscribe_', '')
                
                print(f"[DEBUG PAYMENT] User {chat_id} clicked subscribe_{plan_key}")
                
                # Загружаем актуальные цены из БД
                SUBSCRIPTION_PLANS = get_subscription_plans()
                print(f"[DEBUG PAYMENT] Loaded plans: {SUBSCRIPTION_PLANS}")
                
                if plan_key not in SUBSCRIPTION_PLANS:
                    send_telegram_message(chat_id, '❌ Неизвестный тариф')
                else:
                    plan = SUBSCRIPTION_PLANS[plan_key]
                    
                    # Отправляем инвойс через Telegram Payments API
                    try:
                        token = os.environ['TELEGRAM_BOT_TOKEN']
                        payment_token = os.environ.get('YOOKASSA_PAYMENT_TOKEN')
                        
                        if not payment_token:
                            send_telegram_message(
                                chat_id,
                                '❌ Оплата временно недоступна. Обратитесь к администратору @admin_anya_gpt'
                            )
                        else:
                            url = f'https://api.telegram.org/bot{token}/sendInvoice'
                            
                            # Убираем \n из описания (они уже есть как реальные переносы)
                            clean_description = plan['description'].replace('\\n', '\n')
                            
                            # Данные для фискализации через ЮKassa
                            # ⚠️ CRITICAL: YooKassa НЕ принимает эмодзи в description чека!
                            # Удаляем эмодзи из названия тарифа для фискализации
                            import re
                            clean_plan_name = re.sub(r'[^\w\s\-]', '', plan["name"]).strip()
                            
                            provider_data = {
                                'receipt': {
                                    'items': [{
                                        'description': f'{clean_plan_name} ({plan["duration_days"]} дней)',
                                        'quantity': 1,
                                        'amount': {
                                            'value': f'{plan["price_kop"] / 100:.2f}',
                                            'currency': 'RUB'
                                        },
                                        'vat_code': 1,
                                        'payment_mode': 'full_payment',
                                        'payment_subject': 'service'
                                    }],
                                    'tax_system_code': 1
                                }
                            }
                            
                            invoice_payload = {
                                'chat_id': chat_id,
                                'title': plan['name'],
                                'description': clean_description,
                                'payload': json.dumps({
                                    'telegram_id': telegram_id,
                                    'plan': plan_key,
                                    'duration_days': plan['duration_days']
                                }),
                                'provider_token': payment_token,
                                'currency': 'RUB',
                                'prices': [{
                                    'label': plan['name'],
                                    'amount': plan['price_kop']
                                }],
                                'need_email': True,
                                'send_email_to_provider': True,
                                'provider_data': json.dumps(provider_data)
                            }
                            
                            print(f"[DEBUG PAYMENT] Sending invoice: price_kop={plan['price_kop']}, price_rub={plan['price_rub']}")
                            print(f"[DEBUG PAYMENT] provider_token length: {len(payment_token)}")
                            print(f"[DEBUG PAYMENT] Invoice payload: {json.dumps(invoice_payload, ensure_ascii=False)[:500]}")
                            
                            req = urllib.request.Request(
                                url,
                                data=json.dumps(invoice_payload).encode('utf-8'),
                                headers={'Content-Type': 'application/json'}
                            )
                            
                            with urllib.request.urlopen(req) as response:
                                result = json.loads(response.read().decode('utf-8'))
                                print(f"[DEBUG PAYMENT] sendInvoice response: {result}")
                                if not result.get('ok'):
                                    print(f"[ERROR PAYMENT] sendInvoice failed: {result}")
                                    send_telegram_message(
                                        chat_id,
                                        '❌ Не удалось создать платёж. Попробуй позже или обратись @admin_anya_gpt'
                                    )
                                else:
                                    print(f"[SUCCESS PAYMENT] Invoice sent successfully!")
                    except urllib.error.HTTPError as e:
                        error_body = e.read().decode('utf-8') if e.fp else 'no body'
                        print(f"[ERROR PAYMENT] Failed to send invoice - HTTP {e.code}: {error_body}")
                        import traceback
                        traceback.print_exc()
                        send_telegram_message(
                            chat_id,
                            f'❌ Ошибка при создании платежа (HTTP {e.code}): {error_body[:200]}. Попробуй позже или обратись @admin_anya_gpt'
                        )
                    except Exception as e:
                        print(f"[ERROR PAYMENT] Failed to send invoice: {e}")
                        import traceback
                        traceback.print_exc()
                        send_telegram_message(
                            chat_id,
                            f'❌ Ошибка при создании платежа: {str(e)[:200]}. Попробуй позже или обратись @admin_anya_gpt'
                        )
            
            elif data.startswith('learning_mode_'):
                # Обработка выбора режима обучения (НОВЫЙ ШАГ)
                mode = data.replace('learning_mode_', '')
                
                if mode == 'standard':
                    # СТАНДАРТНОЕ ОБУЧЕНИЕ: сразу к тесту, без ввода цели
                    edit_telegram_message(
                        chat_id,
                        message_id,
                        '📚 Стандартное обучение\n\n'
                        '✅ Отлично! Будем изучать общие темы.\n\n'
                        '⏳ Сейчас запущу адаптивный тест - он САМ определит твой уровень через вопросы...'
                    )
                    
                    # Сохраняем цель по умолчанию и сразу начинаем тест
                    conn = get_db_connection()
                    cur = conn.cursor()
                    
                    default_goal = 'Хочу улучшить английский через общение'
                    goal_escaped = default_goal.replace("'", "''")
                    
                    # Инициализируем тест
                    test_state = json.dumps({
                        'question_num': 0,
                        'history': []
                    }, ensure_ascii=False).replace("'", "''")
                    
                    cur.execute(
                        f"UPDATE {SCHEMA}.users SET "
                        f"learning_goal = '{goal_escaped}', "
                        f"learning_mode = 'standard', "
                        f"conversation_mode = 'adaptive_level_test', "
                        f"test_phrases = '{test_state}'::jsonb "
                        f"WHERE telegram_id = {telegram_id}"
                    )
                    cur.close()
                    conn.close()
                    
                    # Генерируем первый вопрос
                    try:
                        first_item = generate_adaptive_question('A1', [])
                        
                        type_emojis = {'word': '📖', 'phrase': '💬', 'expression': '✨'}
                        emoji = type_emojis.get(first_item.get('type', 'word'), '📖')
                        
                        question_message = f'{emoji} <b>Вопрос 1/10</b>\n\n'
                        question_message += f'Переведи на русский:\n<b>{first_item["english"]}</b>'
                        
                        send_telegram_message(chat_id, question_message)
                        
                        # Обновляем состояние с текущим вопросом
                        test_state = {
                            'current_item': first_item,
                            'question_num': 1,
                            'history': []
                        }
                        
                        conn = get_db_connection()
                        cur = conn.cursor()
                        test_state_json = json.dumps(test_state, ensure_ascii=False).replace("'", "''")
                        cur.execute(
                            f"UPDATE {SCHEMA}.users SET test_phrases = '{test_state_json}'::jsonb WHERE telegram_id = {telegram_id}"
                        )
                        cur.close()
                        conn.close()
                    except Exception as e:
                        print(f"[ERROR] Failed to start adaptive test: {e}")
                        send_telegram_message(chat_id, f'❌ Ошибка запуска теста: {e}\n\nПопробуй /start')
                
                elif mode == 'specific':
                    # КОНКРЕТНАЯ ТЕМА: просим ввести тему (без изменений)
                    edit_telegram_message(
                        chat_id,
                        message_id,
                        '🎯 Конкретная тема\n\nНапиши что именно хочешь освоить:\n\n'
                        'Например:\n'
                        '• "Хочу посмотреть сериал Friends в оригинале"\n'
                        '• "Читаю книгу Harry Potter, нужна помощь"\n'
                        '• "Изучаю IT-термины для работы"'
                    )
                    
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute(
                        f"UPDATE {SCHEMA}.users SET "
                        f"conversation_mode = 'awaiting_goal', "
                        f"learning_mode = 'specific_topic' "
                        f"WHERE telegram_id = {telegram_id}"
                    )
                    cur.close()
                    conn.close()
                
                elif mode == 'urgent':
                    # СРОЧНАЯ ЗАДАЧА: просим ввести задачу + Gemini сгенерирует цели
                    edit_telegram_message(
                        chat_id,
                        message_id,
                        '🚨 Срочная задача\n\nОпиши свою задачу и когда она нужна:\n\n'
                        'Например:\n'
                        '• "Через неделю лечу в Лондон"\n'
                        '• "Завтра собеседование на английском"\n'
                        '• "В четверг встреча с иностранными партнерами"'
                    )
                    
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute(
                        f"UPDATE {SCHEMA}.users SET "
                        f"conversation_mode = 'awaiting_urgent_task', "
                        f"learning_mode = 'urgent_task' "
                        f"WHERE telegram_id = {telegram_id}"
                    )
                    cur.close()
                    conn.close()
            
            elif data.startswith('role_'):
                role = data.replace('role_', '')
                create_user(
                    telegram_id,
                    user.get('username', ''),
                    user.get('first_name', ''),
                    user.get('last_name', ''),
                    role
                )
                
                role_text = '👨‍🎓 Ученик' if role == 'student' else '👨‍🏫 Преподаватель'
                edit_telegram_message(
                    chat_id,
                    message_id,
                    f'✅ Отлично! Вы зарегистрированы как <b>{role_text}</b>\n\n'
                    f'Теперь просто пишите мне вопросы, и я буду отвечать прямо здесь в чате!'
                )
            

            elif data.startswith('mode_'):
                mode = data.replace('mode_', '')
                update_conversation_mode(telegram_id, mode)
                
                user_data = get_user(telegram_id)
                language_level = user_data.get('language_level', 'A1') if user_data else 'A1'
                
                mode_names = {
                    'dialog': '💬 Диалог с Аней',
                    'sentence': '✍️ Составление предложений',
                    'context': '📝 Контекст (Fill in the blanks)',
                    'association': '🎯 Ассоциации',
                    'translation': '🇷🇺→🇬🇧 Перевод'
                }
                
                mode_name = mode_names.get(mode, mode)
                edit_telegram_message(
                    chat_id,
                    message_id,
                    f'✅ Режим изменен на: <b>{mode_name}</b>'
                )
                
                if mode != 'dialog':
                    word = get_random_word(telegram_id, language_level)
                    if word:
                        if mode == 'sentence':
                            exercise_text = generate_sentence_exercise(word, language_level)
                            update_exercise_state(telegram_id, word['id'], word['english'])
                            send_telegram_message(chat_id, exercise_text)
                        elif mode == 'context':
                            exercise_text, answer = generate_context_exercise(word, language_level)
                            update_exercise_state(telegram_id, word['id'], answer)
                            send_telegram_message(chat_id, exercise_text)
                        elif mode == 'association':
                            exercise_text, answer = generate_association_exercise(word, language_level)
                            update_exercise_state(telegram_id, word['id'], answer)
                            send_telegram_message(chat_id, exercise_text)
                        elif mode == 'translation':
                            exercise_text, answer = generate_translation_exercise(word)
                            update_exercise_state(telegram_id, word['id'], answer)
                            send_telegram_message(chat_id, exercise_text)
                    else:
                        send_telegram_message(chat_id, '❌ У вас пока нет слов для практики. Попросите учителя добавить слова или используйте режим диалога.')
            
            elif data.startswith('topic_'):
                print(f"[DEBUG] TOPIC CALLBACK RECEIVED: {data}")
                topic_type = data.replace('topic_', '')
                print(f"[DEBUG] topic_type extracted: {topic_type}")
                
                topic_texts = {
                    'gaming': '🎮 Игры',
                    'it': '💻 IT и технологии',
                    'marketing': '📊 Маркетинг',
                    'travel': '✈️ Путешествия',
                    'sport': '⚽ Спорт',
                    'music': '🎵 Музыка',
                    'movies': '🎬 Фильмы',
                    'books': '📚 Книги',
                    'food': '🍴 Еда и кулинария',
                    'business': '💼 Бизнес',
                    'art': '🎨 Искусство',
                    'science': '🔬 Наука',
                    'fashion': '🎯 Мода',
                    'home': '🏠 Дом и уют',
                    'custom': '✍️ Свой вариант'
                }
                
                print(f"[DEBUG] topic_texts defined, checking if custom...")
                if topic_type == 'custom':
                    # Пользователь хочет ввести свои интересы
                    print(f"[DEBUG] Custom topic selected, editing message...")
                    edit_telegram_message(
                        chat_id,
                        message_id,
                        '✍️ Отлично! Напиши своими словами:\n\n• Чем ты увлекаешься?\n• Кем работаешь?\n• Что тебе интересно?'
                    )
                    # Переводим в режим awaiting_topics
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute(f"UPDATE {SCHEMA}.users SET conversation_mode = 'awaiting_topics' WHERE telegram_id = {telegram_id}")
                    cur.close()
                    conn.close()
                else:
                    # Множественный выбор интересов - добавляем к существующим
                    print(f"[DEBUG] Topic selected: {topic_type}")
                    selected_topic = topic_texts.get(topic_type, '💡 Интересы')
                    
                    conn = get_db_connection()
                    cur = conn.cursor()
                    
                    # Получаем текущие интересы
                    cur.execute(f"SELECT preferred_topics FROM {SCHEMA}.users WHERE telegram_id = {telegram_id}")
                    row = cur.fetchone()
                    current_topics = row[0] if row and row[0] else []
                    
                    # Проверяем есть ли уже этот интерес
                    topic_emoji = selected_topic.split()[0]
                    topic_name = ' '.join(selected_topic.split()[1:])
                    topic_exists = any(t.get('topic') == topic_name for t in current_topics)
                    
                    if topic_exists:
                        # Удаляем интерес (toggle)
                        current_topics = [t for t in current_topics if t.get('topic') != topic_name]
                        action_text = '➖ Убрано'
                    else:
                        # Добавляем новый интерес
                        current_topics.append({'topic': topic_name, 'emoji': topic_emoji})
                        action_text = '✅ Добавлено'
                    
                    # Сохраняем обновленный список
                    topics_json = json.dumps(current_topics, ensure_ascii=False).replace("'", "''")
                    cur.execute(
                        f"UPDATE {SCHEMA}.users SET "
                        f"preferred_topics = '{topics_json}'::jsonb "
                        f"WHERE telegram_id = {telegram_id}"
                    )
                    
                    cur.close()
                    conn.close()
                    
                    # Обновляем клавиатуру с галочками
                    selected_topics_names = [t.get('topic') for t in current_topics]
                    
                    topics_keyboard = {
                        'inline_keyboard': [
                            [{
                                'text': f"{'✅ ' if 'Игры' in selected_topics_names else ''}🎮 Игры", 
                                'callback_data': 'topic_gaming'
                            }, {
                                'text': f"{'✅ ' if 'IT и технологии' in selected_topics_names else ''}💻 IT", 
                                'callback_data': 'topic_it'
                            }],
                            [{
                                'text': f"{'✅ ' if 'Маркетинг' in selected_topics_names else ''}📊 Маркетинг", 
                                'callback_data': 'topic_marketing'
                            }, {
                                'text': f"{'✅ ' if 'Путешествия' in selected_topics_names else ''}✈️ Путешествия", 
                                'callback_data': 'topic_travel'
                            }],
                            [{
                                'text': f"{'✅ ' if 'Спорт' in selected_topics_names else ''}⚽ Спорт", 
                                'callback_data': 'topic_sport'
                            }, {
                                'text': f"{'✅ ' if 'Музыка' in selected_topics_names else ''}🎵 Музыка", 
                                'callback_data': 'topic_music'
                            }],
                            [{
                                'text': f"{'✅ ' if 'Фильмы' in selected_topics_names else ''}🎬 Фильмы", 
                                'callback_data': 'topic_movies'
                            }, {
                                'text': f"{'✅ ' if 'Книги' in selected_topics_names else ''}📚 Книги", 
                                'callback_data': 'topic_books'
                            }],
                            [{
                                'text': f"{'✅ ' if 'Еда и кулинария' in selected_topics_names else ''}🍴 Еда", 
                                'callback_data': 'topic_food'
                            }, {
                                'text': f"{'✅ ' if 'Бизнес' in selected_topics_names else ''}💼 Бизнес", 
                                'callback_data': 'topic_business'
                            }],
                            [{
                                'text': f"{'✅ ' if 'Искусство' in selected_topics_names else ''}🎨 Искусство", 
                                'callback_data': 'topic_art'
                            }, {
                                'text': f"{'✅ ' if 'Наука' in selected_topics_names else ''}🔬 Наука", 
                                'callback_data': 'topic_science'
                            }],
                            [{
                                'text': f"{'✅ ' if 'Мода' in selected_topics_names else ''}🎯 Мода", 
                                'callback_data': 'topic_fashion'
                            }, {
                                'text': f"{'✅ ' if 'Дом и уют' in selected_topics_names else ''}🏠 Дом и уют", 
                                'callback_data': 'topic_home'
                            }],
                            [{'text': '✍️ Свой вариант', 'callback_data': 'topic_custom'}],
                            [{'text': '✅ Готово!', 'callback_data': 'topics_done'}]
                        ]
                    }
                    
                    # Обновляем сообщение с галочками
                    selected_display = ', '.join([t.get('emoji', '') + ' ' + t.get('topic', '') for t in current_topics]) if current_topics else 'Ничего не выбрано'
                    
                    try:
                        edit_telegram_message(
                            chat_id,
                            message_id,
                            f'{action_text}: <b>{selected_topic}</b>\n\nТвои интересы: {selected_display}\n\n💡 Выбери еще или нажми "Готово"'
                        )
                    except Exception as e:
                        print(f"[WARNING] Failed to edit message text: {e}")
                    
                    # Обновляем клавиатуру
                    try:
                        token = os.environ['TELEGRAM_BOT_TOKEN']
                        url = f'https://api.telegram.org/bot{token}/editMessageReplyMarkup'
                        payload = {
                            'chat_id': chat_id,
                            'message_id': message_id,
                            'reply_markup': topics_keyboard
                        }
                        req = urllib.request.Request(
                            url,
                            data=json.dumps(payload).encode('utf-8'),
                            headers={'Content-Type': 'application/json'}
                        )
                        with urllib.request.urlopen(req) as response:
                            print(f"[DEBUG] Keyboard updated successfully")
                    except Exception as e:
                        print(f"[WARNING] Failed to update keyboard: {e}")
            
            elif data == 'topics_done':
                # Пользователь закончил выбирать интересы - запускаем генерацию плана
                conn = get_db_connection()
                cur = conn.cursor()
                
                # Получаем выбранные интересы
                cur.execute(f"SELECT preferred_topics FROM {SCHEMA}.users WHERE telegram_id = {telegram_id}")
                row = cur.fetchone()
                selected_topics = row[0] if row and row[0] else []
                
                if not selected_topics or len(selected_topics) == 0:
                    # Если ничего не выбрано - просим выбрать хотя бы одну тему
                    edit_telegram_message(
                        chat_id,
                        message_id,
                        '❗ Пожалуйста, выбери хотя бы одну тему для обучения!\n\nИли нажми "✍️ Свой вариант" чтобы ввести вручную.'
                    )
                else:
                    # Формируем сообщение с выбранными интересами
                    topics_display = ', '.join([t.get('emoji', '') + ' ' + t.get('topic', '') for t in selected_topics])
                    
                    edit_telegram_message(
                        chat_id,
                        message_id,
                        f'✅ Отлично! Ты выбрал: <b>{topics_display}</b>\n\n⏳ Генерирую персональный план... (это займёт ~30 сек)'
                    )
                    
                    # Получаем данные для генерации плана
                    cur.execute(f"SELECT learning_goal, language_level, preferred_topics FROM {SCHEMA}.users WHERE telegram_id = {telegram_id}")
                    row = cur.fetchone()
                    learning_goal = row[0] if row and row[0] else 'Общее развитие английского'
                    language_level = row[1] if row and row[1] else 'A1'
                    preferred_topics = row[2] if row and row[2] else []
                    
                    # Обновляем режим на generating_plan
                    cur.execute(f"UPDATE {SCHEMA}.users SET conversation_mode = 'generating_plan' WHERE telegram_id = {telegram_id}")
                    
                    cur.close()
                    conn.close()
                    
                    # АСИНХРОННАЯ ГЕНЕРАЦИЯ - запускаем в фоне
                    try:
                        function_url = 'https://functions.poehali.dev/92013b11-9080-40b5-8b24-10317e48a4f7'
                        async_payload = json.dumps({
                            'action': 'generate_plan_async',
                            'user_id': telegram_id,
                            'chat_id': chat_id,
                            'learning_goal': learning_goal,
                            'language_level': language_level,
                            'preferred_topics': preferred_topics,
                            'selected_topic': topics_display
                        }).encode('utf-8')
                        
                        async_req = urllib.request.Request(
                            function_url,
                            data=async_payload,
                            headers={'Content-Type': 'application/json'},
                            method='POST'
                        )
                        
                        # Запускаем без ожидания результата (fire-and-forget)
                        import threading
                        def fire_async():
                            try:
                                with urllib.request.urlopen(async_req, timeout=120) as resp:
                                    print(f"[DEBUG] Async generation completed")
                            except Exception as e:
                                print(f"[ERROR] Async generation failed: {e}")
                        
                        thread = threading.Thread(target=fire_async)
                        thread.daemon = True
                        thread.start()
                        
                    except Exception as e:
                        print(f"[ERROR] Failed to start async generation: {e}")
                        import traceback
                        traceback.print_exc()
                        send_telegram_message(
                            chat_id,
                            '❌ Произошла ошибка при запуске генерации плана. Попробуй еще раз через /start',
                            parse_mode=None
                        )
            
            elif data == 'confirm_plan':
                # Пользователь согласен с планом - стартуем обучение
                edit_telegram_message(
                    chat_id,
                    message_id,
                    '🚀 Отлично! Начинаем обучение!'
                )
                
                # Переключаем в режим диалога
                update_conversation_mode(telegram_id, 'dialog')
                
                # Получаем данные пользователя для call_gemini
                existing_user = get_user(telegram_id)
                session_words = get_session_words(telegram_id, limit=10)
                
                # Аня инициирует диалог ПЕРВОЙ
                try:
                    anya_greeting = call_gemini(
                        user_message='[SYSTEM: Start conversation naturally based on student\'s goal and level]',
                        history=[],
                        session_words=session_words,
                        language_level=existing_user.get('language_level', 'A1'),
                        preferred_topics=existing_user.get('preferred_topics', []),
                        urgent_goals=existing_user.get('urgent_goals', []),
                        learning_goal=existing_user.get('learning_goal', 'Общее развитие английского'),
                        learning_mode=existing_user.get('learning_mode', 'standard')
                    )
                    
                    # Отправляем приветствие от Ани
                    send_telegram_message(chat_id, anya_greeting, get_reply_keyboard(), parse_mode=None)
                    
                    # Сохраняем в историю
                    save_message(telegram_id, 'assistant', anya_greeting)
                    
                except Exception as e:
                    print(f"[ERROR] Failed to send Anya's greeting: {e}")
                    # Fallback - просто отправляем стандартное сообщение
                    send_telegram_message(
                        chat_id,
                        '💬 Режим диалога активен! Напиши мне что-нибудь на английском 😊',
                        get_reply_keyboard(),
                        parse_mode=None
                    )
            
            elif data == 'edit_plan':
                # Пользователь хочет изменить план
                edit_telegram_message(
                    chat_id,
                    message_id,
                    '✏️ Напиши что бы ты хотел изменить в плане:\n\n• Другие темы?\n• Больше/меньше слов?\n• Другой подход к обучению?'
                )
                
                # Переводим в режим корректировки плана
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(f"UPDATE {SCHEMA}.users SET conversation_mode = 'editing_plan' WHERE telegram_id = {telegram_id}")
                cur.close()
                conn.close()
            
            elif data.startswith('pronounce:'):
                # Обработка кнопки "Послушать произношение"
                word = data.replace('pronounce:', '')
                
                try:
                    # Генерируем аудио через OpenAI TTS (функция возвращает CDN URL)
                    voice_url = text_to_speech(word)
                    
                    # Отправляем голосовое сообщение
                    send_telegram_voice(chat_id, voice_url)
                    print(f"[SUCCESS] Voice sent for word: {word}")
                    
                except Exception as e:
                    print(f"[ERROR] TTS failed for word '{word}': {e}")
                    import traceback
                    traceback.print_exc()
                    send_telegram_message(chat_id, f'❌ Ошибка при генерации произношения', parse_mode=None)
            
            elif data.startswith('context_answer:'):
                # Обработка ответа в режиме контекста (multiple choice)
                selected_answer = data.replace('context_answer:', '')
                
                # Получаем данные пользователя
                existing_user = get_user(telegram_id)
                if not existing_user:
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({'ok': True}),
                        'isBase64Encoded': False
                    }
                
                current_word_id = existing_user.get('current_exercise_word_id')
                correct_answer = existing_user.get('current_exercise_answer')
                language_level = existing_user.get('language_level', 'A1')
                
                if not correct_answer:
                    edit_telegram_message(chat_id, message_id, '❌ Ошибка: не найдено текущее упражнение')
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({'ok': True}),
                        'isBase64Encoded': False
                    }
                
                # Сравниваем английские слова (теперь варианты на английском)
                is_correct = (selected_answer.lower() == correct_answer.lower())
                
                if is_correct:
                    # Получаем русский перевод для показа
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute(
                        f"SELECT w.russian_translation FROM {SCHEMA}.words w "
                        f"WHERE w.english_text = '{correct_answer.replace(chr(39), chr(39)+chr(39))}'"
                    )
                    row = cur.fetchone()
                    russian_translation = row[0] if row else ''
                    cur.close()
                    conn.close()
                    
                    edit_telegram_message(chat_id, message_id, f'✅ Correct! Great job! 🎉\n\n{correct_answer} = {russian_translation}')
                    
                    # Обновляем прогресс
                    if current_word_id:
                        update_word_progress_api(telegram_id, current_word_id, True)
                    
                    clear_exercise_state(telegram_id)
                    
                    # Генерируем следующее упражнение
                    word = get_random_word(telegram_id, language_level)
                    if word:
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute(
                            f"SELECT w.id, w.english_text, w.russian_translation FROM {SCHEMA}.student_words sw "
                            f"JOIN {SCHEMA}.words w ON w.id = sw.word_id "
                            f"WHERE sw.student_id = {telegram_id} LIMIT 20"
                        )
                        all_words = [{'id': row[0], 'english': row[1], 'russian': row[2]} for row in cur.fetchall()]
                        cur.close()
                        conn.close()
                        
                        exercise_text, answer, options = generate_context_exercise(word, language_level, all_words)
                        update_exercise_state(telegram_id, word['id'], answer)
                        
                        inline_keyboard = {
                            'inline_keyboard': [
                                [{'text': opt, 'callback_data': f'context_answer:{opt}'}] for opt in options
                            ]
                        }
                        send_telegram_message(chat_id, exercise_text, reply_markup=inline_keyboard, parse_mode=None)
                    else:
                        send_telegram_message(chat_id, '✅ Упражнения закончились!', get_reply_keyboard())
                        update_conversation_mode(telegram_id, 'dialog')
                else:
                    # НЕПРАВИЛЬНЫЙ ОТВЕТ - показываем ошибку и ДУБЛИРУЕМ вопрос
                    conn = get_db_connection()
                    cur = conn.cursor()
                    
                    # Получаем русский перевод и исходный вопрос
                    cur.execute(
                        f"SELECT w.russian_translation FROM {SCHEMA}.words w "
                        f"WHERE w.english_text = '{correct_answer.replace(chr(39), chr(39)+chr(39))}'"
                    )
                    row = cur.fetchone()
                    russian_translation = row[0] if row else ''
                    
                    # Получаем данные текущего слова для повторной генерации вопроса
                    cur.execute(
                        f"SELECT w.id, w.english_text, w.russian_translation FROM {SCHEMA}.words w "
                        f"WHERE w.id = {current_word_id}"
                    )
                    word_row = cur.fetchone()
                    
                    # Получаем все слова для генерации вариантов
                    cur.execute(
                        f"SELECT w.id, w.english_text, w.russian_translation FROM {SCHEMA}.student_words sw "
                        f"JOIN {SCHEMA}.words w ON w.id = sw.word_id "
                        f"WHERE sw.student_id = {telegram_id} LIMIT 20"
                    )
                    all_words = [{'id': row[0], 'english': row[1], 'russian': row[2]} for row in cur.fetchall()]
                    
                    cur.close()
                    conn.close()
                    
                    # Редактируем сообщение, показывая ошибку
                    edit_telegram_message(
                        chat_id,
                        message_id,
                        f'❌ Wrong!\n\n✅ Correct answer: {correct_answer} = {russian_translation}'
                    )
                    
                    # ДУБЛИРУЕМ вопрос - отправляем тот же самый вопрос заново
                    if word_row:
                        word = {'id': word_row[0], 'english': word_row[1], 'russian': word_row[2]}
                        exercise_text, answer, options = generate_context_exercise(word, language_level, all_words)
                        
                        # НЕ обновляем exercise_state - оставляем то же слово!
                        
                        inline_keyboard = {
                            'inline_keyboard': [
                                [{'text': opt, 'callback_data': f'context_answer:{opt}'}] for opt in options
                            ]
                        }
                        send_telegram_message(chat_id, exercise_text, reply_markup=inline_keyboard, parse_mode=None)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'ok': True}),
                'isBase64Encoded': False
            }
        
        # Обработка pre_checkout_query
        if 'pre_checkout_query' in body:
            pre_checkout = body['pre_checkout_query']
            query_id = pre_checkout['id']
            
            print(f"[DEBUG PAYMENT] Received pre_checkout_query: {pre_checkout}")
            
            # Всегда подтверждаем (валидация уже была при создании инвойса)
            try:
                token = os.environ['TELEGRAM_BOT_TOKEN']
                url = f'https://api.telegram.org/bot{token}/answerPreCheckoutQuery'
                
                answer_payload = {
                    'pre_checkout_query_id': query_id,
                    'ok': True
                }
                
                req = urllib.request.Request(
                    url,
                    data=json.dumps(answer_payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json'}
                )
                
                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    print(f"[DEBUG PAYMENT] answerPreCheckoutQuery response: {result}")
            except Exception as e:
                print(f"[ERROR PAYMENT] Failed to answer pre_checkout_query: {e}")
                import traceback
                traceback.print_exc()
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'ok': True}),
                'isBase64Encoded': False
            }
        
        # Обработка successful_payment
        if 'message' in body and 'successful_payment' in body['message']:
            message = body['message']
            payment = message['successful_payment']
            user = message.get('from', {})
            chat_id = message['chat']['id']
            
            print(f"[DEBUG PAYMENT] Received successful_payment: {payment}")
            
            # Парсим payload
            try:
                payload_data = json.loads(payment['invoice_payload'])
                telegram_id = payload_data['telegram_id']
                plan_key = payload_data['plan']
                duration_days = payload_data['duration_days']
                
                # Сохраняем платёж в БД
                from datetime import datetime, timedelta
                
                conn = get_db_connection()
                cur = conn.cursor()
                
                # ⚠️ CRITICAL: Новая подписка ВСЕГДА начинается с текущего момента
                # НЕ продлеваем старую подписку, а ЗАМЕНЯЕМ её на новую
                now = datetime.now()
                new_expires = now + timedelta(days=duration_days)
                
                # Обновляем подписку пользователя
                cur.execute(
                    f"UPDATE {SCHEMA}.users SET "
                    f"subscription_status = 'active', "
                    f"subscription_expires_at = '{new_expires.isoformat()}', "
                    f"trial_used = TRUE "
                    f"WHERE telegram_id = {telegram_id}"
                )
                
                # Сохраняем запись о платеже
                SUBSCRIPTION_PLANS = get_subscription_plans()
                plan = SUBSCRIPTION_PLANS.get(plan_key, {'name': plan_key})
                amount = payment['total_amount'] / 100  # Копейки в рубли
                
                cur.execute(
                    f"INSERT INTO {SCHEMA}.subscription_payments "
                    f"(telegram_id, amount, currency, period, status, "
                    f"provider_payment_id, telegram_payment_charge_id, paid_at, expires_at) "
                    f"VALUES ({telegram_id}, {amount}, 'RUB', '{plan_key}', 'paid', "
                    f"'{payment.get('provider_payment_charge_id', '')}', "
                    f"'{payment.get('telegram_payment_charge_id', '')}', "
                    f"CURRENT_TIMESTAMP, '{new_expires.isoformat()}')"
                )
                
                cur.close()
                conn.close()
                
                # Отправляем подтверждение
                success_message = (
                    f"✅ <b>Оплата прошла успешно!</b>\n\n"
                    f"Подписка активирована до: {new_expires.strftime('%d.%m.%Y')}\n\n"
                    f"Теперь у тебя полный доступ ко всем функциям бота! 🚀\n\n"
                    f"Начни практиковаться прямо сейчас!"
                )
                
                send_telegram_message(chat_id, success_message, get_reply_keyboard())
                
                print(f"[SUCCESS] Subscription activated for user {telegram_id} until {new_expires}")
                
            except Exception as e:
                print(f"[ERROR] Failed to process successful_payment: {e}")
                import traceback
                traceback.print_exc()
                
                send_telegram_message(
                    chat_id,
                    '✅ Платёж получен, но возникла ошибка активации. Обратитесь к @admin_anya_gpt'
                )
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'ok': True}),
                'isBase64Encoded': False
            }
        
        # Обработка обычных сообщений
        if 'message' not in body:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'ok': True}),
                'isBase64Encoded': False
            }
        
        message = body['message']
        chat_id = message['chat']['id']
        user = message['from']
        telegram_id = user['id']  # ⚠️ CRITICAL FIX: Extract telegram_id from user (v4)
        text = message.get('text', '')
        voice = message.get('voice')
        sticker = message.get('sticker')
        
        # ⚠️ НОВАЯ ЛОГИКА: Проверяем подписку для базовых функций
        # basic → базовые функции (диалог, упражнения)
        # premium → ТОЛЬКО голосовой режим
        # bundle → всё (базовые + голосовой)
        # ⚠️ CRITICAL: НЕ проверяем подписку для кнопок переключения режима и /start
        mode_buttons = ['💬 Диалог', '🎤 Голосовой', '✍️ Предложения', '📝 Контекст', '🎯 Ассоциации', '🇷🇺→🇬🇧 Перевод', '🔄 Задать цель заново']
        
        # Пропускаем проверку подписки ТОЛЬКО для /start и mode_buttons - они проверяют подписку сами!
        if text != '/start' and text not in mode_buttons:
            from datetime import datetime
            conn = get_db_connection()
            cur = conn.cursor()
            
            # Проверяем активную подписку (basic или bundle)
            cur.execute(
                f"SELECT period FROM {SCHEMA}.subscription_payments "
                f"WHERE telegram_id = {telegram_id} "
                f"AND status = 'paid' "
                f"AND expires_at > CURRENT_TIMESTAMP "
                f"ORDER BY expires_at DESC LIMIT 1"
            )
            subscription_row = cur.fetchone()
            cur.close()
            conn.close()
            
            subscription_type = subscription_row[0] if subscription_row else None
            
            print(f"[DEBUG SUBSCRIPTION CHECK] User {telegram_id}, subscription_type: {subscription_type}")
            
            # ⚠️ CRITICAL: Проверяем есть ли доступ к функциям
            # basic, premium, bundle - все дают доступ к диалогу
            # premium работает как обычная подписка (не только голосовой!)
            has_basic_access = subscription_type in ['basic', 'premium', 'bundle']
            
            print(f"[DEBUG SUBSCRIPTION CHECK] has_basic_access: {has_basic_access}")
            
            # Если нет доступа к базовым функциям - блокируем
            if not has_basic_access:
                print(f"[DEBUG SUBSCRIPTION CHECK] Sending subscription required message...")
                
                # КРИТИЧНО: Понятное сообщение почему бот не отвечает
                # Если у юзера premium (только голосовой) — предлагаем basic или bundle
                if subscription_type == 'premium':
                    text_sub = (
                        "🔒 <b>Нужна подписка для базовых функций</b>\n\n"
                        "У тебя активен только голосовой режим. Для доступа к диалогу и упражнениям нужен тариф Basic или Всё сразу:\n\n"
                    )
                else:
                    text_sub = (
                        "🔒 <b>Подписка истекла</b>\n\n"
                        "Твой доступ к AnyaGPT закончился, но ты можешь продолжить обучение прямо сейчас!\n\n"
                        "Выбери свой тариф:\n\n"
                    )
                
                # Добавляем платные тарифы (только basic и bundle для базовых функций)
                SUBSCRIPTION_PLANS = get_subscription_plans()
                inline_buttons = []
                for key in ['basic', 'bundle']:
                    plan = SUBSCRIPTION_PLANS[key]
                    text_sub += f"{plan['name']} — {plan['price_rub']}₽/мес\n"
                    text_sub += f"{plan['description']}\n\n"
                    inline_buttons.append([{'text': f"{plan['name']} — {plan['price_rub']}₽/мес", 'callback_data': f'subscribe_{key}'}])
                
                keyboard_sub = {
                    'inline_keyboard': inline_buttons
                }
                
                try:
                    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
                    print(f"[DEBUG SUB MSG] bot_token exists: {bool(bot_token)}")
                    
                    if bot_token:
                        proxy_id, proxy_url = get_active_proxy_from_db()
                        proxies = None
                        if proxy_url:
                            proxies = {
                                'http': f'http://{proxy_url}',
                                'https': f'http://{proxy_url}'
                            }
                        
                        print(f"[DEBUG SUB MSG] Using proxy: {bool(proxy_url)}")
                        
                        url_photo = f'https://api.telegram.org/bot{bot_token}/sendMessage'
                        payload_photo = {
                            'chat_id': chat_id,
                            'text': text_sub,
                            'parse_mode': 'HTML',
                            'reply_markup': keyboard_sub
                        }
                        
                        print(f"[DEBUG SUB MSG] Sending to chat_id={chat_id}, text_length={len(text_sub)}, buttons={len(inline_buttons)}")
                        
                        response = requests.post(url_photo, json=payload_photo, proxies=proxies, timeout=30)
                        
                        print(f"[DEBUG SUB MSG] Response status: {response.status_code}")
                        print(f"[DEBUG SUB MSG] Response body: {response.text[:500]}")
                        
                        if response.status_code == 200:
                            print(f"[DEBUG SUB MSG] Message sent successfully!")
                            if proxy_id:
                                log_proxy_success(proxy_id)
                        else:
                            print(f"[ERROR SUB MSG] Failed with status {response.status_code}")
                            if proxy_id:
                                log_proxy_failure(proxy_id, f"HTTP {response.status_code}")
                except Exception as e:
                    print(f"[ERROR] Failed to send subscription message: {e}")
                    import traceback
                    traceback.print_exc()
                    if 'proxy_id' in locals() and proxy_id:
                        log_proxy_failure(proxy_id, str(e))
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'ok': True, 'subscription_required': True}),
                    'isBase64Encoded': False
                }
        
        # Логируем file_id стикеров для добавления в коллекцию
        if sticker:
            file_id = sticker.get('file_id')
            set_name = sticker.get('set_name', '')
            print(f"[DEBUG] Sticker received: file_id={file_id}, set_name={set_name}")
            # Не обрабатываем дальше, просто логируем
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'ok': True, 'sticker_logged': file_id}),
                'isBase64Encoded': False
            }
        
        # Обработка голосовых сообщений
        if voice:
            # Проверяем режим пользователя
            existing_user = get_user(telegram_id)
            if not existing_user:
                create_user(telegram_id, user.get('username', ''), user.get('first_name', ''), user.get('last_name', ''), 'student')
                existing_user = {'telegram_id': telegram_id, 'conversation_mode': 'voice', 'language_level': 'A1'}
            
            conversation_mode = existing_user.get('conversation_mode', 'dialog')
            
            # В режиме voice обрабатываем голосовые, в других режимах - предлагаем переключиться
            if conversation_mode != 'voice':
                send_telegram_message(
                    chat_id, 
                    '🎤 Чтобы я отвечала голосом, переключись в режим "🎤 Голосовой" на клавиатуре внизу!',
                    get_reply_keyboard()
                )
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'ok': True}),
                    'isBase64Encoded': False
                }
            
            try:
                # Скачиваем аудио (БЕЗ текстовых уведомлений - только голос!)
                audio_data = download_telegram_file(voice['file_id'])
                
                # Распознаем речь
                recognized_text = speech_to_text(audio_data)
                
                if not recognized_text:
                    send_telegram_message(chat_id, '❌ Не удалось распознать речь. Попробуй еще раз!')
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({'ok': True}),
                        'isBase64Encoded': False
                    }
                
                language_level = existing_user.get('language_level', 'A1')
                preferred_topics = existing_user.get('preferred_topics', [])
                
                # Получаем историю диалога
                history = get_conversation_history(telegram_id)
                
                # Получаем слова для практики
                session_words = None
                if existing_user.get('role') == 'student':
                    try:
                        session_words = get_session_words(telegram_id, limit=10)
                    except Exception as e:
                        print(f"[WARNING] Failed to load session words: {e}")
                
                # Генерируем ответ с исправлениями через Gemini
                urgent_goals = existing_user.get('urgent_goals', [])
                learning_mode = existing_user.get('learning_mode', 'standard')
                learning_goal = existing_user.get('learning_goal') if learning_mode in ['specific_topic', 'urgent_task'] else None
                
                response_text = call_gemini(recognized_text, history, session_words, language_level, preferred_topics, urgent_goals, learning_goal, learning_mode)
                
                # ⚠️ CRITICAL: В голосовом режиме отправляем исправления ТЕКСТОМ (отдельно)
                # Ищем блок исправлений в ответе: 🔧 Fix / Correct:
                correction_block = ''
                clean_response = response_text
                
                if '🔧 Fix / Correct:' in response_text or '🔧' in response_text:
                    # Извлекаем блок исправлений (от 🔧 до первого пустого \n\n)
                    parts = response_text.split('\n\n', 1)
                    if len(parts) > 1 and '🔧' in parts[0]:
                        correction_block = parts[0]
                        clean_response = parts[1].strip() if len(parts) > 1 else response_text
                    else:
                        # Ищем конец блока по первой строке без ❌✅🇷🇺
                        lines = response_text.split('\n')
                        correction_lines = []
                        remaining_lines = []
                        in_correction = False
                        
                        for line in lines:
                            if '🔧' in line:
                                in_correction = True
                            
                            if in_correction:
                                correction_lines.append(line)
                                # Конец блока: строка без специальных символов И не пустая
                                if line.strip() and not any(marker in line for marker in ['🔧', '❌', '✅', '🇷🇺']):
                                    in_correction = False
                                    remaining_lines = lines[len(correction_lines):]
                                    break
                            else:
                                remaining_lines.append(line)
                        
                        if correction_lines:
                            correction_block = '\n'.join(correction_lines)
                            clean_response = '\n'.join(remaining_lines).strip()
                
                # Если нашли исправления - отправляем их ТЕКСТОМ
                if correction_block:
                    send_telegram_message(chat_id, correction_block, parse_mode='HTML')
                
                # Генерируем голосовой ответ (БЕЗ исправлений - только чистый ответ)
                voice_url = text_to_speech(clean_response)
                
                # Отправляем голосовой ответ
                send_telegram_voice(chat_id, voice_url)
                
                # Сохраняем в историю (полный ответ с исправлениями для контекста)
                save_message(telegram_id, 'user', recognized_text)
                save_message(telegram_id, 'assistant', response_text)
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'ok': True}),
                    'isBase64Encoded': False
                }
                
            except Exception as e:
                print(f"[ERROR] Voice processing failed: {e}")
                import traceback
                traceback.print_exc()
                send_telegram_message(chat_id, '❌ Ошибка обработки голосового. Проверь что говоришь на английском!')
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'ok': True}),
                    'isBase64Encoded': False
                }
        
        # Команда /start или кнопка "🔄 Задать цель заново" - ВСЕГДА СБРАСЫВАЕМ СОСТОЯНИЕ
        if text == '/start' or text == '🔄 Задать цель заново':
            existing_user = get_user(telegram_id)
            
            # Сбрасываем состояние пользователя если он застрял
            if existing_user:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(
                    f"UPDATE {SCHEMA}.users SET "
                    f"conversation_mode = 'awaiting_goal', "
                    f"test_phrases = NULL, "
                    f"learning_plan = NULL "
                    f"WHERE telegram_id = {telegram_id}"
                )
                cur.close()
                conn.close()
            
            if not existing_user:
                # Регистрируем нового пользователя как ученика по умолчанию
                create_user(
                    telegram_id,
                    user.get('username', ''),
                    user.get('first_name', ''),
                    user.get('last_name', ''),
                    'student'
                )
                
                # Отправляем приветственный стикер (из стикер-пака Hey_Anya)
                try:
                    # File ID нужно получить отправив стикер боту и залогировав его
                    # Временно используем заглушку - обновим после получения реального ID
                    sticker_file_id = os.environ.get('WELCOME_STICKER_ID', '')
                    if sticker_file_id:
                        send_telegram_sticker(chat_id, sticker_file_id)
                except Exception as e:
                    print(f"[ERROR] Failed to send welcome sticker: {e}")
                
                # НОВЫЙ онбординг - сначала спрашиваем режим обучения
                send_telegram_message(
                    chat_id,
                    'Привет! Я Аня 👋\n\n'
                    'Я помогу тебе учить английский через живой диалог.\n\n'
                    'Что я умею:\n'
                    '✅ Учим слова и фразы через общение\n'
                    '✅ Подбираю темы под твои цели\n'
                    '✅ Напоминаю о практике\n'
                    '✅ Показываю твой прогресс\n\n'
                    '❓ <b>Выбери режим обучения:</b>',
                    {
                        'inline_keyboard': [
                            [{'text': '📚 Стандартное обучение (общие темы)', 'callback_data': 'learning_mode_standard'}],
                            [{'text': '🎯 Конкретная тема (фильм/книга)', 'callback_data': 'learning_mode_specific'}],
                            [{'text': '🚨 Срочная задача (отпуск, собеседование)', 'callback_data': 'learning_mode_urgent'}]
                        ]
                    },
                    parse_mode='HTML'
                )
                
                # Сохраняем состояние - ждем выбор режима обучения
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(f"UPDATE {SCHEMA}.users SET conversation_mode = 'awaiting_learning_mode' WHERE telegram_id = {telegram_id}")
                cur.close()
                conn.close()
            else:
                # Возвращающийся пользователь
                # Отправляем приветственный стикер
                try:
                    sticker_file_id = os.environ.get('WELCOME_STICKER_ID', '')
                    if sticker_file_id:
                        send_telegram_sticker(chat_id, sticker_file_id)
                except Exception as e:
                    print(f"[ERROR] Failed to send welcome sticker: {e}")
                
                send_telegram_message(
                    chat_id,
                    'Привет! Я Аня 👋\n\n'
                    'Я помогу тебе учить английский через живой диалог.\n\n'
                    'Что я умею:\n'
                    '✅ Учим слова и фразы через общение\n'
                    '✅ Подбираю темы под твои цели\n'
                    '✅ Напоминаю о практике\n'
                    '✅ Показываю твой прогресс\n\n'
                    '❓ <b>Выбери режим обучения:</b>',
                    {
                        'inline_keyboard': [
                            [{'text': '📚 Стандартное обучение (общие темы)', 'callback_data': 'learning_mode_standard'}],
                            [{'text': '🎯 Конкретная тема (фильм/книга)', 'callback_data': 'learning_mode_specific'}],
                            [{'text': '🚨 Срочная задача (отпуск, собеседование)', 'callback_data': 'learning_mode_urgent'}]
                        ]
                    },
                    parse_mode='HTML'
                )
                
                # Сохраняем состояние - ждем выбор режима обучения
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(f"UPDATE {SCHEMA}.users SET conversation_mode = 'awaiting_learning_mode' WHERE telegram_id = {telegram_id}")
                cur.close()
                conn.close()
            
            # ВАЖНО: Возвращаем ответ после /start, чтобы не продолжить обработку
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'ok': True}),
                'isBase64Encoded': False
            }
        
        # Обработка выбора режима через Reply Keyboard
        elif text in ['💬 Диалог', '🎤 Голосовой', '✍️ Предложения', '📝 Контекст', '🎯 Ассоциации', '🇷🇺→🇬🇧 Перевод']:
            mode_map = {
                '💬 Диалог': 'dialog',
                '🎤 Голосовой': 'voice',
                '✍️ Предложения': 'sentence',
                '📝 Контекст': 'context',
                '🎯 Ассоциации': 'association',
                '🇷🇺→🇬🇧 Перевод': 'translation'
            }
            mode = mode_map[text]
            
            # ⚠️ CRITICAL: Проверяем подписку ДЛЯ ВСЕХ платных режимов
            # Получаем активную подписку
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                f"SELECT period FROM {SCHEMA}.subscription_payments "
                f"WHERE telegram_id = {telegram_id} "
                f"AND status = 'paid' "
                f"AND expires_at > CURRENT_TIMESTAMP "
                f"ORDER BY expires_at DESC LIMIT 1"
            )
            subscription_row = cur.fetchone()
            cur.close()
            conn.close()
            
            subscription_type = subscription_row[0] if subscription_row else None
            print(f"[DEBUG] Subscription check: telegram_id={telegram_id}, subscription_type={subscription_type}")
            plans = get_subscription_plans()
            
            # Проверяем доступ к голосовому режиму (premium или bundle)
            if mode == 'voice':
                # Если подписка НЕ premium и НЕ bundle - запрещаем голосовой режим
                if subscription_type not in ['premium', 'bundle']:
                    message = "🔒 Голосовой режим доступен только в тарифах:\n\n"
                    
                    if 'premium' in plans:
                        premium = plans['premium']
                        message += f"🎤 {premium['name']} — {premium['price_rub']}₽/мес\n{premium['description']}\n\n"
                    
                    if 'bundle' in plans:
                        bundle = plans['bundle']
                        message += f"🔥 {bundle['name']} — {bundle['price_rub']}₽/мес\n{bundle['description']}\n\n"
                    
                    message += "Выбери тариф чтобы активировать голосовой режим! 🎙️"
                    
                    keyboard = {
                        'inline_keyboard': []
                    }
                    
                    if 'premium' in plans:
                        keyboard['inline_keyboard'].append([
                            {'text': f"🎤 {plans['premium']['name']} — {plans['premium']['price_rub']}₽/мес", 'callback_data': 'subscribe_premium'}
                        ])
                    
                    if 'bundle' in plans:
                        keyboard['inline_keyboard'].append([
                            {'text': f"🔥 {plans['bundle']['name']} — {plans['bundle']['price_rub']}₽/мес", 'callback_data': 'subscribe_bundle'}
                        ])
                    
                    send_telegram_message(chat_id, message, reply_markup=keyboard, parse_mode=None)
                    return {
                        'statusCode': 200,
                        'body': json.dumps({'status': 'voice_mode_requires_subscription'})
                    }
            
            # Проверяем доступ ко ВСЕМ режимам - все платные!
            # Проверяем есть ли вообще подписка (любая)
            if not subscription_type:
                mode_names = {
                    'dialog': 'Диалог',
                    'voice': 'Голосовой',
                    'sentence': 'Предложения',
                    'context': 'Контекст',
                    'association': 'Ассоциации',
                    'translation': 'Перевод'
                }
                
                message = f"🔒 Режим {mode_names.get(mode, mode)} доступен в тарифах:\n\n"
                
                if 'basic' in plans:
                    basic = plans['basic']
                    message += f"💬 {basic['name']} — {basic['price_rub']}₽/мес\n{basic['description']}\n\n"
                
                if 'bundle' in plans:
                    bundle = plans['bundle']
                    message += f"🔥 {bundle['name']} — {bundle['price_rub']}₽/мес\n{bundle['description']}\n\n"
                
                message += "Выбери тариф чтобы начать обучение!"
                
                keyboard = {
                    'inline_keyboard': []
                }
                
                if 'basic' in plans:
                    keyboard['inline_keyboard'].append([
                        {'text': f"💬 {plans['basic']['name']} — {plans['basic']['price_rub']}₽/мес", 'callback_data': 'subscribe_basic'}
                    ])
                
                if 'bundle' in plans:
                    keyboard['inline_keyboard'].append([
                        {'text': f"🔥 {plans['bundle']['name']} — {plans['bundle']['price_rub']}₽/мес", 'callback_data': 'subscribe_bundle'}
                    ])
                
                send_telegram_message(chat_id, message, reply_markup=keyboard, parse_mode=None)
                return {
                    'statusCode': 200,
                    'body': json.dumps({'status': 'mode_requires_subscription'})
                }
            
            # Если проверка прошла - активируем режим
            update_conversation_mode(telegram_id, mode)
            
            mode_messages = {
                'dialog': '💬 Режим "Диалог" активирован!\n\nТеперь просто пиши мне на английском, и я буду помогать тебе практиковать разговорную речь в естественных диалогах.',
                'voice': '🎤 Режим "Голосовой" активирован!\n\n🎙️ Записывай голосовые сообщения на английском, и я:\n\n✅ Распознаю твою речь\n✅ Исправлю ошибки с объяснениями\n✅ Отвечу голосом от Ани\n\nГовори что угодно - начни прямо сейчас! 🚀',
                'sentence': '✍️ Режим "Предложения" активирован!\n\nСейчас я дам тебе слово, а ты составь с ним предложение на английском.',
                'context': '📝 Режим "Контекст" активирован!\n\nЯ буду давать предложения с пропущенными словами, а ты вставляй нужное слово.',
                'association': '🎯 Режим "Ассоциации" активирован!\n\nЯ дам тебе три подсказки, а ты угадай слово на английском.',
                'translation': '🇷🇺→🇬🇧 Режим "Перевод" активирован!\n\nЯ буду давать слова на русском, а ты переводи их на английском.'
            }
            
            send_telegram_message(chat_id, mode_messages[mode], parse_mode=None)
            
            # В режиме голосового отправляем голосовое приветствие от Ани
            if mode == 'voice':
                try:
                    welcome_voice_text = "Hey! I'm Anya 😊 I'll help you practice English."
                    voice_url = text_to_speech(welcome_voice_text)
                    send_telegram_voice(chat_id, voice_url)
                except Exception as e:
                    print(f"[ERROR] Failed to send welcome voice: {e}")
            
            # Если не режим диалога/голосовой - даем первое упражнение
            if mode not in ['dialog', 'voice']:
                try:
                    # Получаем уровень пользователя
                    language_level = user.get('language_level', 'A1')
                    print(f"[DEBUG] Checking words for user {telegram_id}, level {language_level}")
                    # Проверяем и добавляем дефолтные слова если их нет
                    ensure_user_has_words(telegram_id, language_level)
                    print(f"[DEBUG] Getting random word for user {telegram_id}")
                    word = get_random_word(telegram_id, language_level)
                    print(f"[DEBUG] Got word: {word}")
                    if word:
                        if mode == 'sentence':
                            exercise_text, keyboard = generate_sentence_exercise(word, language_level)
                            update_exercise_state(telegram_id, word['id'], word['english'])
                            send_telegram_message(chat_id, exercise_text, reply_markup=keyboard, parse_mode='HTML')
                        elif mode == 'context':
                            # Получаем все слова студента для генерации вариантов
                            conn = get_db_connection()
                            cur = conn.cursor()
                            cur.execute(
                                f"SELECT w.id, w.english_text, w.russian_translation FROM {SCHEMA}.student_words sw "
                                f"JOIN {SCHEMA}.words w ON w.id = sw.word_id "
                                f"WHERE sw.student_id = {telegram_id} LIMIT 20"
                            )
                            all_words = [{'id': row[0], 'english': row[1], 'russian': row[2]} for row in cur.fetchall()]
                            cur.close()
                            conn.close()
                            
                            exercise_text, answer, options = generate_context_exercise(word, language_level, all_words)
                            update_exercise_state(telegram_id, word['id'], answer)
                            
                            # Создаем inline keyboard с вариантами ответов + кнопка произношения
                            inline_keyboard = {
                                'inline_keyboard': [
                                    [{'text': opt, 'callback_data': f'context_answer:{opt}'}] for opt in options
                                ] + [[
                                    {'text': '🔊 Послушать произношение', 'callback_data': f'pronounce:{word["english"]}'}
                                ]]
                            }
                            send_telegram_message(chat_id, exercise_text, reply_markup=inline_keyboard, parse_mode='HTML')
                        elif mode == 'association':
                            exercise_text, answer, keyboard = generate_association_exercise(word, language_level, student_id=telegram_id)
                            update_exercise_state(telegram_id, word['id'], answer)
                            send_telegram_message(chat_id, exercise_text, reply_markup=keyboard, parse_mode='HTML')
                        elif mode == 'translation':
                            exercise_text, answer, keyboard = generate_translation_exercise(word)
                            update_exercise_state(telegram_id, word['id'], answer)
                            send_telegram_message(chat_id, exercise_text, reply_markup=keyboard, parse_mode='HTML')
                    else:
                        print(f"[ERROR] No words found for user {telegram_id}")
                        send_telegram_message(chat_id, '❌ У вас пока нет слов для практики. Попросите учителя добавить слова или используйте режим диалога.', parse_mode=None)
                except Exception as e:
                    print(f"[ERROR] Failed to generate exercise: {e}")
                    import traceback
                    traceback.print_exc()
                    send_telegram_message(chat_id, '❌ Произошла ошибка при генерации упражнения. Попробуйте позже или используйте режим диалога.', parse_mode=None)
                    # ⚠️ CRITICAL: Возвращаем ответ даже если ошибка генерации!
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({'ok': True, 'error': 'exercise_generation_failed'}),
                        'isBase64Encoded': False
                    }
            
            # ⚠️ CRITICAL: Возвращаем ответ после обработки режима!
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'ok': True, 'mode': mode}),
                'isBase64Encoded': False
            }
        else:
            # Любое другое сообщение - обрабатываем в зависимости от режима
            existing_user = get_user(telegram_id)
            
            if not existing_user:
                # Автоматически регистрируем если пользователь начал писать без /start
                create_user(
                    telegram_id,
                    user.get('username', ''),
                    user.get('first_name', ''),
                    user.get('last_name', ''),
                    'student'
                )
                existing_user = {'telegram_id': telegram_id, 'role': 'student', 'conversation_mode': 'dialog'}
            
            conversation_mode = existing_user.get('conversation_mode', 'dialog')
            language_level = existing_user.get('language_level', 'A1')
            used_word_ids = []  # Инициализируем для использования в статистике
            
            # Обработка адаптивного теста уровня (НОВАЯ ЛОГИКА)
            if conversation_mode == 'adaptive_level_test':
                # Получаем состояние теста
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(f"SELECT test_phrases FROM {SCHEMA}.users WHERE telegram_id = {telegram_id}")
                row = cur.fetchone()
                cur.close()
                conn.close()
                
                if not row or not row[0]:
                    send_telegram_message(chat_id, '❌ Ошибка теста. Попробуй /start', parse_mode=None)
                    return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'ok': True}), 'isBase64Encoded': False}
                
                test_state = row[0]
                current_item = test_state.get('current_item')
                question_num = test_state.get('question_num', 0)
                history = test_state.get('history', [])
                
                if not current_item:
                    send_telegram_message(chat_id, '❌ Ошибка теста. Попробуй /start', parse_mode=None)
                    return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'ok': True}), 'isBase64Encoded': False}
                
                # Анализируем ответ через Gemini
                send_telegram_message(chat_id, '⏳ Проверяю...', parse_mode=None)
                
                # Инициализируем переменные для использования во всем блоке
                api_key = os.environ.get('GEMINI_API_KEY', '')
                proxy_id = None
                proxy_url = None
                gemini_url = ''
                
                try:
                    proxy_id, proxy_url = get_active_proxy_from_db()
                    if not proxy_url:
                        proxy_url = os.environ.get('PROXY_URL', '')
                    
                    gemini_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}'
                    
                    # Проверяем текущий ответ (КОРОТКИЙ промпт)
                    check_prompt = f'''Check translation:
English: {current_item["english"]}
Student answer: {text}

Return short JSON:
{{"correct": true, "expected": "правильный_русский_перевод"}}

IMPORTANT: "expected" must be RUSSIAN!'''
                    
                    payload = {
                        'contents': [{'parts': [{'text': check_prompt}]}],
                        'generationConfig': {'temperature': 0.3, 'maxOutputTokens': 2000}
                    }
                    
                    proxy_handler = urllib.request.ProxyHandler({
                        'http': f'http://{proxy_url}',
                        'https': f'http://{proxy_url}'
                    })
                    opener = urllib.request.build_opener(proxy_handler)
                    
                    req = urllib.request.Request(
                        gemini_url,
                        data=json.dumps(payload).encode('utf-8'),
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    with opener.open(req, timeout=30) as response:
                        check_result = json.loads(response.read().decode('utf-8'))
                        check_text = check_result['candidates'][0]['content']['parts'][0]['text']
                        
                        print(f"[DEBUG] Gemini check response: {check_text[:300]}")
                        
                        check_data = safe_json_parse(check_text, {'correct': False, 'expected': '???'})
                    
                    is_correct = check_data.get('correct', False)
                    expected = check_data.get('expected', '???')
                    
                    # КРИТИЧНО: Проверяем что expected на русском (не латиница)
                    # Игнорируем "???" - это fallback от safe_json_parse
                    if expected and expected != '???' and all(ord(c) < 128 for c in expected.replace(' ', '').replace('-', '')):
                        # expected содержит только латиницу - это английское слово!
                        print(f"[ERROR] Gemini returned English as 'expected': {expected}. Asking for Russian translation...")
                        
                        # Делаем второй запрос - явно просим перевод
                        translate_prompt = f'''Translate English word/phrase to Russian.

English: {current_item["english"]}

Return ONLY valid JSON:
{{"russian": "перевод на русском языке"}}

Example: {{"russian": "путешествие"}}'''
                        
                        translate_payload = {
                            'contents': [{'parts': [{'text': translate_prompt}]}],
                            'generationConfig': {'temperature': 0.2, 'maxOutputTokens': 100}
                        }
                        
                        translate_req = urllib.request.Request(
                            gemini_url,
                            data=json.dumps(translate_payload).encode('utf-8'),
                            headers={'Content-Type': 'application/json'}
                        )
                        
                        try:
                            with opener.open(translate_req, timeout=15) as translate_resp:
                                translate_result = json.loads(translate_resp.read().decode('utf-8'))
                                translate_text = translate_result['candidates'][0]['content']['parts'][0]['text']
                                translate_data = safe_json_parse(translate_text, {'russian': expected})
                                expected = translate_data.get('russian', expected)
                                print(f"[DEBUG] Got Russian translation: {expected}")
                        except Exception as e:
                            print(f"[WARNING] Failed to get Russian translation: {e}")
                            expected = '(перевод не определен)'
                    
                    # ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: Сравниваем строки напрямую (fallback если Gemini ошибся)
                    # Убираем пробелы, приводим к нижнему регистру
                    user_answer_clean = text.strip().lower()
                    expected_clean = expected.strip().lower()
                    
                    # Если ответы практически идентичны - считаем правильным
                    if user_answer_clean == expected_clean:
                        print(f"[DEBUG] Strings match exactly: '{user_answer_clean}' == '{expected_clean}' - overriding is_correct to True")
                        is_correct = True
                    
                    # Сохраняем результат в историю
                    history.append({
                        'level': current_item.get('level', 'A1'),
                        'item': current_item['english'],
                        'answer': text,
                        'correct': is_correct
                    })
                    
                    # Если 10 вопросов - завершаем тест и определяем уровень
                    if question_num >= 10:
                        # Финальный анализ уровня
                        history_str = '\n'.join([f"{i+1}. [{h['level']}] {h['item']} → {h['answer']} ({'✅' if h['correct'] else '❌'})" for i, h in enumerate(history)])
                        
                        final_prompt = f'''Analyze student's English level based on their 10 test answers.

Test history (level of question → student answer → correct/wrong):
{history_str}

Rules for level determination:
- A1: knows only basic words (cat, home, family, water)
- A2: knows everyday words (travel, weather, hobby)
- B1: knows common phrases and expressions (take care, by the way)
- B2: knows idioms and sophisticated vocabulary
- C1: knows advanced academic vocabulary
- C2: knows native-level expressions and subtle nuances

IMPORTANT:
- Count how many questions from each level (A1/A2/B1/B2/C1/C2) were answered correctly
- If student answered correctly most B2/C1/C2 questions → level is B2 or higher
- If student answered correctly most B1 questions → level is B1
- If student answered correctly most A2 questions → level is A2
- If student failed most questions → level is A1

Return ONLY valid JSON with actual level (choose ONE from: A1, A2, B1, B2, C1, C2):
{{"level": "B1", "reasoning": "Краткое объяснение на русском"}}

No markdown, no explanations, just JSON.'''
                        
                        payload = {
                            'contents': [{'parts': [{'text': final_prompt}]}],
                            'generationConfig': {'temperature': 0.3, 'maxOutputTokens': 300}
                        }
                        
                        req = urllib.request.Request(
                            gemini_url,
                            data=json.dumps(payload).encode('utf-8'),
                            headers={'Content-Type': 'application/json'}
                        )
                        
                        with opener.open(req, timeout=30) as response:
                            final_result = json.loads(response.read().decode('utf-8'))
                            final_text = final_result['candidates'][0]['content']['parts'][0]['text']
                            print(f"[DEBUG] Gemini level analysis response: {final_text}")
                            final_data = safe_json_parse(final_text, {'level': 'A2', 'reasoning': 'Базовый уровень'})
                            print(f"[DEBUG] Parsed level data: {final_data}")
                        
                        actual_level = final_data.get('level', 'A1')
                        reasoning = final_data.get('reasoning', '')
                        correct_count = sum(1 for h in history if h['correct'])
                        
                        # Показываем результат
                        feedback = '✅ Правильно!' if is_correct else f'❌ Правильный ответ: {expected}'
                        send_telegram_message(chat_id, feedback, parse_mode=None)
                        
                        # ⚠️ КРИТИЧНО: Проверяем режим обучения - для срочных задач И конкретных целей НЕ спрашиваем интересы!
                        learning_mode = existing_user.get('learning_mode', 'standard')
                        
                        if learning_mode in ['urgent_task', 'specific_topic']:
                            # СРОЧНАЯ ЗАДАЧА или КОНКРЕТНАЯ ЦЕЛЬ - пропускаем интересы, сразу генерируем план
                            response_text = f"\n📊 РЕЗУЛЬТАТЫ ТЕСТА\n\n"
                            response_text += f"✅ Правильных ответов: {correct_count}/10\n"
                            response_text += f"🎯 Твой уровень: <b>{actual_level}</b>\n\n"
                            response_text += f"💡 {reasoning}\n\n"
                            
                            if learning_mode == 'urgent_task':
                                response_text += "⏳ Сейчас сгенерирую план обучения для твоей срочной задачи..."
                            else:
                                response_text += "⏳ Сейчас сгенерирую персональный план обучения..."
                            
                            send_telegram_message(chat_id, response_text, parse_mode='HTML')
                            
                            # Обновляем уровень и сразу переходим к генерации плана
                            conn = get_db_connection()
                            cur = conn.cursor()
                            cur.execute(
                                f"UPDATE {SCHEMA}.users SET "
                                f"language_level = '{actual_level}', "
                                f"conversation_mode = 'generating_plan', "
                                f"test_phrases = NULL "
                                f"WHERE telegram_id = {telegram_id}"
                            )
                            cur.close()
                            conn.close()
                            
                            # Запускаем асинхронную генерацию плана (как в topics_done)
                            import threading
                            thread = threading.Thread(
                                target=generate_plan_async,
                                args=(chat_id, telegram_id)
                            )
                            thread.daemon = True
                            thread.start()
                            
                            return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'ok': True}), 'isBase64Encoded': False}
                        
                        # СТАНДАРТНЫЙ РЕЖИМ - показываем выбор интересов
                        response_text = f"\n📊 РЕЗУЛЬТАТЫ ТЕСТА\n\n"
                        response_text += f"✅ Правильных ответов: {correct_count}/10\n"
                        response_text += f"🎯 Твой уровень: <b>{actual_level}</b>\n\n"
                        response_text += f"💡 {reasoning}\n\n"
                        response_text += "Теперь выбери темы, которые тебе интересны:\n\n💡 Можно выбрать несколько!"
                        
                        topics_keyboard = {
                            'inline_keyboard': [
                                [{'text': '🎮 Игры', 'callback_data': 'topic_gaming'}, {'text': '💻 IT', 'callback_data': 'topic_it'}],
                                [{'text': '📊 Маркетинг', 'callback_data': 'topic_marketing'}, {'text': '✈️ Путешествия', 'callback_data': 'topic_travel'}],
                                [{'text': '⚽ Спорт', 'callback_data': 'topic_sport'}, {'text': '🎵 Музыка', 'callback_data': 'topic_music'}],
                                [{'text': '🎬 Фильмы', 'callback_data': 'topic_movies'}, {'text': '📚 Книги', 'callback_data': 'topic_books'}],
                                [{'text': '🍴 Еда', 'callback_data': 'topic_food'}, {'text': '💼 Бизнес', 'callback_data': 'topic_business'}],
                                [{'text': '🎨 Искусство', 'callback_data': 'topic_art'}, {'text': '🔬 Наука', 'callback_data': 'topic_science'}],
                                [{'text': '🎯 Мода', 'callback_data': 'topic_fashion'}, {'text': '🏠 Дом и уют', 'callback_data': 'topic_home'}],
                                [{'text': '✍️ Свой вариант', 'callback_data': 'topic_custom'}],
                                [{'text': '✅ Готово!', 'callback_data': 'topics_done'}]
                            ]
                        }
                        
                        send_telegram_message(chat_id, response_text, topics_keyboard, parse_mode='HTML')
                        
                        # Обновляем уровень пользователя
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute(
                            f"UPDATE {SCHEMA}.users SET "
                            f"language_level = '{actual_level}', "
                            f"conversation_mode = 'awaiting_topics', "
                            f"test_phrases = NULL "
                            f"WHERE telegram_id = {telegram_id}"
                        )
                        cur.close()
                        conn.close()
                        
                        return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'ok': True}), 'isBase64Encoded': False}
                    
                    # Продолжаем тест - генерируем следующий вопрос
                    feedback = '✅ Правильно!' if is_correct else f'❌ Правильный ответ: {expected}'
                    send_telegram_message(chat_id, feedback, parse_mode=None)
                    
                    # Определяем следующий уровень сложности (адаптивно)
                    levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
                    current_level_idx = levels.index(current_item.get('level', 'A1'))
                    
                    if is_correct and current_level_idx < len(levels) - 1:
                        next_level = levels[current_level_idx + 1]  # Сложнее
                    elif not is_correct and current_level_idx > 0:
                        next_level = levels[current_level_idx - 1]  # Проще
                    else:
                        next_level = current_item.get('level', 'A1')  # Тот же уровень
                    
                    # Собираем уже использованные слова
                    used_words = [h['item'] for h in history]
                    
                    # Генерируем следующий вопрос через функцию
                    next_item = generate_adaptive_question(next_level, used_words)
                    
                    # Отправляем следующий вопрос
                    type_emojis = {'word': '📖', 'phrase': '💬', 'expression': '✨'}
                    emoji = type_emojis.get(next_item.get('type', 'word'), '📖')
                    
                    question_message = f'{emoji} <b>Вопрос {question_num + 1}/10</b>\n\n'
                    question_message += f'Переведи на русский:\n<b>{next_item["english"]}</b>'
                    
                    send_telegram_message(chat_id, question_message)
                    
                    # Обновляем состояние
                    test_state['current_item'] = next_item
                    test_state['question_num'] = question_num + 1
                    test_state['history'] = history
                    
                    conn = get_db_connection()
                    cur = conn.cursor()
                    test_state_json = json.dumps(test_state, ensure_ascii=False).replace("'", "''")
                    cur.execute(
                        f"UPDATE {SCHEMA}.users SET test_phrases = '{test_state_json}'::jsonb "
                        f"WHERE telegram_id = {telegram_id}"
                    )
                    cur.close()
                    conn.close()
                    
                except Exception as e:
                    print(f"[ERROR] Adaptive test failed: {e}")
                    import traceback
                    traceback.print_exc()
                    send_telegram_message(chat_id, '❌ Ошибка теста. Попробуй /start', parse_mode=None)
                
                return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'ok': True}), 'isBase64Encoded': False}
            
            # Проверяем - проверяем ли уровень пользователя (СТАРАЯ ЛОГИКА - fallback)
            elif conversation_mode.startswith('checking_level_'):
                claimed_level = conversation_mode.replace('checking_level_', '')
                
                # Получаем сохраненные фразы для проверки
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(f"SELECT test_phrases FROM {SCHEMA}.users WHERE telegram_id = {telegram_id}")
                row = cur.fetchone()
                cur.close()
                conn.close()
                
                test_phrases = row[0] if row and row[0] else None
                
                if not test_phrases:
                    # Если нет фраз - используем старый метод (fallback)
                    send_telegram_message(chat_id, '⏳ Анализирую твой ответ...', parse_mode=None)
                    
                    try:
                        webapp_api_url = 'https://functions.poehali.dev/42c13bf2-f4d5-4710-9170-596c38d438a4'
                        response = requests.post(
                            webapp_api_url,
                            json={
                                'action': 'check_level',
                                'claimed_level': claimed_level,
                                'answer': text
                            },
                            timeout=30
                        )
                        result = response.json()
                        
                        if 'error' in result:
                            send_telegram_message(chat_id, f'❌ Ошибка: {result["error"]}', parse_mode=None)
                            return {
                                'statusCode': 200,
                                'headers': {'Content-Type': 'application/json'},
                                'body': json.dumps({'ok': True}),
                                'isBase64Encoded': False
                            }
                        
                        actual_level = result.get('actual_level', claimed_level)
                        
                    except Exception as e:
                        print(f"[ERROR] Failed to check level: {e}")
                        actual_level = claimed_level
                else:
                    # Проверяем переводы через Gemini
                    send_telegram_message(chat_id, '⏳ Проверяю переводы...', parse_mode=None)
                    
                    try:
                        api_key = os.environ['GEMINI_API_KEY']
                        proxy_id, proxy_url = get_active_proxy_from_db()
                        if not proxy_url:
                            proxy_url = os.environ.get('PROXY_URL', '')
                        
                        gemini_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}'
                        
                        # Формируем список слов и фраз для проверки
                        items_str = ''
                        for i, item in enumerate(test_phrases, 1):
                            emoji = '📖' if item.get('type') == 'word' else '💬'
                            items_str += f"{i}. {emoji} {item['english']}\n"
                        
                        prompt = f'''Ты — эксперт по оценке знания английских слов и фраз.

Студент заявил уровень: {claimed_level}

Я дал ему 10 слов и фраз на английском для перевода на русский:
{items_str}

Его переводы:
{text}

Твоя задача: определить РЕАЛЬНЫЙ уровень студента по качеству переводов КОНКРЕТНЫХ слов и фраз.

Критерии оценки:
- A1: Не знает базовых слов (family, water, friend) и простых фраз (How are you?)
- A2: Знает базовую лексику, но путается в фразах и значениях
- B1: Хорошо переводит бытовую лексику и фразовые глаголы
- B2: Знает профессиональную лексику и устойчивые выражения
- C1: Отлично переводит сложную лексику и идиомы

⚠️ КРИТИЧНО:
- Оценивай ТОЛЬКО знание КОНКРЕТНЫХ слов и фраз из списка
- НЕ оценивай грамматику или стиль - только точность перевода
- Если студент перевел 7-10 правильно → уровень подтвержден
- Если 4-6 правильно → на уровень ниже
- Если 0-3 правильно → на 2 уровня ниже

Формат ответа (только JSON, без markdown):
{{
  "actual_level": "A1/A2/B1/B2/C1",
  "is_correct": true/false,
  "correct_count": 7,
  "reasoning": "Перевел X из 10. Краткое объяснение."
}}

ВАЖНО:
- actual_level = реальный уровень по переводам
- is_correct = совпадает ли с {claimed_level} (±1 уровень = true)
- correct_count = сколько слов/фраз перевел правильно (0-10)
- Отвечай ТОЛЬКО валидным JSON.'''
                        
                        payload = {
                            'contents': [{'parts': [{'text': prompt}]}],
                            'generationConfig': {'temperature': 0.3, 'maxOutputTokens': 500}
                        }
                        
                        proxy_handler = urllib.request.ProxyHandler({
                            'http': f'http://{proxy_url}',
                            'https': f'http://{proxy_url}'
                        })
                        opener = urllib.request.build_opener(proxy_handler)
                        
                        req = urllib.request.Request(
                            gemini_url,
                            data=json.dumps(payload).encode('utf-8'),
                            headers={'Content-Type': 'application/json'}
                        )
                        
                        with opener.open(req, timeout=30) as response:
                            gemini_result = json.loads(response.read().decode('utf-8'))
                            result_text = gemini_result['candidates'][0]['content']['parts'][0]['text']
                            result_text = result_text.replace('```json', '').replace('```', '').strip()
                            result = json.loads(result_text)
                        
                        actual_level = result.get('actual_level', claimed_level)
                        is_correct = result.get('is_correct', True)
                        correct_count = result.get('correct_count', 0)
                        reasoning = result.get('reasoning', '')
                        
                    except Exception as e:
                        print(f"[ERROR] Failed to check translations: {e}")
                        import traceback
                        traceback.print_exc()
                        actual_level = claimed_level
                        is_correct = True
                        correct_count = 7
                        reasoning = ''
                
                # Показываем результат и просим выбрать интересы
                if is_correct:
                    response_text = f"✅ Отлично! Твой уровень: <b>{actual_level}</b>\n\n"
                    response_text += f"📊 Правильных переводов: {correct_count}/10\n"
                    if reasoning:
                        response_text += f"💡 {reasoning}\n"
                    response_text += "\n"
                else:
                    response_text = f"📊 Твой реальный уровень: <b>{actual_level}</b>\n\n"
                    response_text += f"📈 Правильных переводов: {correct_count}/10\n"
                    if reasoning:
                        response_text += f"💡 {reasoning}\n"
                    response_text += f"\n🎯 Не переживай! Мы подберем материалы под твой уровень.\n\n"
                
                # Проверяем режим обучения - для specific_topic НЕ НУЖНЫ интересы
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(f"SELECT learning_mode FROM {SCHEMA}.users WHERE telegram_id = {telegram_id}")
                row = cur.fetchone()
                learning_mode = row[0] if row and row[0] else 'standard'
                
                if learning_mode == 'specific_topic':
                    # РЕЖИМ КОНКРЕТНОЙ ЦЕЛИ - НЕ СПРАШИВАЕМ ИНТЕРЕСЫ, СРАЗУ НАЧИНАЕМ ДИАЛОГ
                    response_text += "\n\n🚀 Отлично! Начинаем практику! Просто напиши мне что-нибудь на английском 👇"
                    
                    send_telegram_message(chat_id, response_text, parse_mode='HTML')
                    
                    # Обновляем уровень и переводим в режим диалога
                    cur.execute(
                        f"UPDATE {SCHEMA}.users SET "
                        f"language_level = '{actual_level}', "
                        f"conversation_mode = 'dialog', "
                        f"test_phrases = NULL "
                        f"WHERE telegram_id = {telegram_id}"
                    )
                    cur.close()
                    conn.close()
                    
                    # Отправляем клавиатуру для диалога
                    send_telegram_message(chat_id, '💬 Режим диалога активен!', get_reply_keyboard(), parse_mode=None)
                else:
                    # СТАНДАРТНЫЙ РЕЖИМ - СПРАШИВАЕМ ИНТЕРЕСЫ
                    response_text += "Теперь выбери темы, которые тебе интересны:\n\n💬 Мы будем разговаривать на эти темы!\n💡 Можно выбрать несколько!"
                    
                    # Кнопки с интересами
                    topics_keyboard = {
                        'inline_keyboard': [
                            [{'text': '🎮 Игры', 'callback_data': 'topic_gaming'}, {'text': '💻 IT', 'callback_data': 'topic_it'}],
                            [{'text': '📊 Маркетинг', 'callback_data': 'topic_marketing'}, {'text': '✈️ Путешествия', 'callback_data': 'topic_travel'}],
                            [{'text': '⚽ Спорт', 'callback_data': 'topic_sport'}, {'text': '🎵 Музыка', 'callback_data': 'topic_music'}],
                            [{'text': '🎬 Фильмы', 'callback_data': 'topic_movies'}, {'text': '📚 Книги', 'callback_data': 'topic_books'}],
                            [{'text': '🍴 Еда', 'callback_data': 'topic_food'}, {'text': '💼 Бизнес', 'callback_data': 'topic_business'}],
                            [{'text': '🎨 Искусство', 'callback_data': 'topic_art'}, {'text': '🔬 Наука', 'callback_data': 'topic_science'}],
                            [{'text': '🎯 Мода', 'callback_data': 'topic_fashion'}, {'text': '🏠 Дом и уют', 'callback_data': 'topic_home'}],
                            [{'text': '✍️ Свой вариант', 'callback_data': 'topic_custom'}],
                            [{'text': '✅ Готово!', 'callback_data': 'topics_done'}]
                        ]
                    }
                    
                    send_telegram_message(chat_id, response_text, topics_keyboard, parse_mode='HTML')
                    
                    # Обновляем уровень и очищаем test_phrases
                    cur.execute(
                        f"UPDATE {SCHEMA}.users SET "
                        f"language_level = '{actual_level}', "
                        f"conversation_mode = 'awaiting_topic_selection', "
                        f"test_phrases = NULL "
                        f"WHERE telegram_id = {telegram_id}"
                    )
                    cur.close()
                    conn.close()
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'ok': True}),
                    'isBase64Encoded': False
                }
            
            # Проверяем - ждем ли мы описание цели от пользователя
            elif conversation_mode == 'awaiting_goal':
                # Пользователь ввел свою цель - отправляем в Gemini для анализа
                send_telegram_message(chat_id, '⏳ Анализирую твою цель и составляю план обучения...', parse_mode=None)
                
                try:
                    # Вызываем webapp-api для анализа цели через Gemini
                    webapp_api_url = 'https://functions.poehali.dev/42c13bf2-f4d5-4710-9170-596c38d438a4'
                    response = requests.post(
                        webapp_api_url,
                        json={'action': 'analyze_goal', 'goal': text},
                        timeout=30
                    )
                    result = response.json()
                    
                    if 'error' in result:
                        send_telegram_message(chat_id, f'❌ Ошибка при анализе цели: {result["error"]}', parse_mode=None)
                    else:
                        # Сохраняем цель в БД
                        conn = get_db_connection()
                        cur = conn.cursor()
                        
                        goal_escaped = result.get('goal', text).replace("'", "''")
                        timeline = result.get('timeline', '')
                        timeline_escaped = timeline.replace("'", "''") if timeline else ''
                        
                        if timeline:
                            details = f"Срок: {timeline}"
                            details_escaped = details.replace("'", "''")
                            cur.execute(
                                f"UPDATE {SCHEMA}.users SET "
                                f"learning_goal = '{goal_escaped}', "
                                f"learning_goal_details = '{details_escaped}' "
                                f"WHERE telegram_id = {telegram_id}"
                            )
                        else:
                            cur.execute(
                                f"UPDATE {SCHEMA}.users SET "
                                f"learning_goal = '{goal_escaped}' "
                                f"WHERE telegram_id = {telegram_id}"
                            )
                        
                        cur.close()
                        conn.close()
                        
                        # Подтверждаем цель
                        goal_text = f"✅ Понял! Твоя цель: <b>{result.get('goal')}</b>"
                        
                        if timeline:
                            goal_text += f"\n⏰ Срок: {timeline}"
                        
                        goal_text += "\n\n⏳ Сейчас запущу адаптивный тест - он САМ определит твой уровень через вопросы..."
                        
                        send_telegram_message(chat_id, goal_text, parse_mode='HTML')
                        
                        # СРАЗУ НАЧИНАЕМ АДАПТИВНЫЙ ТЕСТ (БЕЗ ВЫБОРА УРОВНЯ!)
                        # Сохраняем состояние - начинаем адаптивный тест
                        conn = get_db_connection()
                        cur = conn.cursor()
                        
                        # Инициализируем тест: начинаем с A1
                        test_state = json.dumps({
                            'question_num': 0,
                            'history': []
                        }, ensure_ascii=False).replace("'", "''")
                        
                        cur.execute(
                            f"UPDATE {SCHEMA}.users SET "
                            f"conversation_mode = 'adaptive_level_test', "
                            f"test_phrases = '{test_state}'::jsonb "
                            f"WHERE telegram_id = {telegram_id}"
                        )
                        cur.close()
                        conn.close()
                        
                        # Генерируем ПЕРВЫЙ вопрос через Gemini (начинаем с A1)
                        try:
                            first_item = generate_adaptive_question('A1', [])
                            
                            # Отправляем первый вопрос
                            type_emojis = {'word': '📖', 'phrase': '💬', 'expression': '✨'}
                            emoji = type_emojis.get(first_item.get('type', 'word'), '📖')
                            
                            question_message = f'{emoji} <b>Вопрос 1/10</b>\n\n'
                            question_message += f'Переведи на русский:\n<b>{first_item["english"]}</b>'
                            
                            send_telegram_message(chat_id, question_message)
                            
                            # Обновляем состояние с текущим вопросом
                            test_state = {
                                'current_item': first_item,
                                'question_num': 1,
                                'history': []
                            }
                            
                            conn = get_db_connection()
                            cur = conn.cursor()
                            test_state_json = json.dumps(test_state, ensure_ascii=False).replace("'", "''")
                            cur.execute(
                                f"UPDATE {SCHEMA}.users SET test_phrases = '{test_state_json}'::jsonb "
                                f"WHERE telegram_id = {telegram_id}"
                            )
                            cur.close()
                            conn.close()
                            
                        except Exception as e:
                            print(f"[ERROR] Failed to start adaptive test: {e}")
                            import traceback
                            traceback.print_exc()
                            send_telegram_message(chat_id, '❌ Ошибка запуска теста. Попробуй /start')
                except Exception as e:
                    print(f"[ERROR] Failed to analyze goal: {e}")
                    send_telegram_message(chat_id, '❌ Не удалось проанализировать цель. Попробуй еще раз или напиши /start', parse_mode=None)
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'ok': True}),
                    'isBase64Encoded': False
                }
            
            # Проверяем - ждем ли мы описание СРОЧНОЙ ЗАДАЧИ (новое состояние)
            elif conversation_mode == 'awaiting_urgent_task':
                # Пользователь описал срочную задачу - Gemini генерирует конкретные цели
                send_telegram_message(chat_id, '⏳ Анализирую твою задачу и подбираю конкретные цели...', parse_mode=None)
                
                try:
                    # Генерируем цели через Gemini
                    api_key = os.environ['GEMINI_API_KEY']
                    proxy_id, proxy_url = get_active_proxy_from_db()
                    if not proxy_url:
                        proxy_url = os.environ.get('PROXY_URL', '')
                    
                    gemini_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}'
                    
                    prompt = f'''Задача: Сгенерируй 5-7 конкретных целей для срочной задачи студента.

Студент написал: "{text}"

Примеры:
- Задача: "Лечу в Лондон через неделю"
  Цели: ["Забронировать отель на английском", "Заказать еду в ресторане", "Спросить дорогу у прохожих", "Пройти паспортный контроль в аэропорту", "Купить билеты на транспорт"]

- Задача: "Завтра собеседование на английском"
  Цели: ["Рассказать о себе и опыте работы", "Описать свои сильные стороны", "Ответить на вопрос Почему эта компания", "Задать вопросы интервьюеру", "Обсудить зарплату и условия работы"]

Выведи ТОЛЬКО этот JSON (без markdown, без лишнего текста):
{{"goals": ["Цель 1", "Цель 2", "Цель 3", "Цель 4", "Цель 5"]}}

Правила:
- Цели должны быть КОНКРЕТНЫМИ действиями (не общие "улучшить английский")
- Используй глаголы действия: "Забронировать...", "Спросить...", "Рассказать..."
- Учитывай срочность (если завтра - базовые фразы, если через месяц - больше деталей)
- Все цели пиши НА РУССКОМ ЯЗЫКЕ

⚠️ ВАЖНО: Выводи ТОЛЬКО валидный JSON, ничего больше.'''
                    
                    payload = {
                        'contents': [{'parts': [{'text': prompt}]}],
                        'generationConfig': {
                            'temperature': 0.7,
                            'maxOutputTokens': 3000,
                            'topP': 0.9,
                            'topK': 40
                        }
                    }
                    
                    proxy_handler = urllib.request.ProxyHandler({
                        'http': f'http://{proxy_url}',
                        'https': f'http://{proxy_url}'
                    })
                    opener = urllib.request.build_opener(proxy_handler)
                    
                    req = urllib.request.Request(
                        gemini_url,
                        data=json.dumps(payload).encode('utf-8'),
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    with opener.open(req, timeout=30) as response:
                        gemini_result = json.loads(response.read().decode('utf-8'))
                        goals_text = gemini_result['candidates'][0]['content']['parts'][0]['text']
                        
                        print(f"[DEBUG] Raw Gemini response: {goals_text}")
                        
                        goals_data = safe_json_parse(goals_text, {'goals': []})
                        
                        print(f"[DEBUG] Parsed goals_data: {goals_data}")
                    
                    goals_list = goals_data.get('goals', [])
                    
                    if not goals_list or len(goals_list) == 0:
                        print(f"[ERROR] Empty goals_list after parsing! goals_data: {goals_data}")
                        raise Exception(f"Gemini returned empty goals. Raw response: {goals_text[:200]}")
                    
                    log_proxy_success(proxy_id)
                    
                    # Формируем красивое сообщение с целями
                    goals_message = f"✅ <b>Понял! Готовлюсь к твоей задаче</b>\n\n"
                    goals_message += f"📋 <i>{text}</i>\n\n"
                    goals_message += "━━━━━━━━━━━━━━━━━━━\n\n"
                    goals_message += "🎯 <b>Вот что нам нужно освоить:</b>\n\n"
                    
                    for i, goal in enumerate(goals_list, 1):
                        goals_message += f"   {i}. {goal}\n"
                    
                    goals_message += "\n━━━━━━━━━━━━━━━━━━━\n\n"
                    goals_message += "⏳ Сейчас запущу адаптивный тест — он определит твой уровень, и мы подберём нужные материалы!\n\n"
                    goals_message += "💡 <i>По мере изучения я буду автоматически добавлять новые слова и фразы</i>"
                    
                    send_telegram_message(chat_id, goals_message, parse_mode='HTML')
                    
                    # Сохраняем цель и цели в БД
                    conn = get_db_connection()
                    cur = conn.cursor()
                    
                    goal_escaped = text.replace("'", "''")
                    goals_json = json.dumps(goals_list, ensure_ascii=False).replace("'", "''")
                    
                    # Сохраняем основную цель + список подцелей
                    cur.execute(
                        f"UPDATE {SCHEMA}.users SET "
                        f"learning_goal = '{goal_escaped}', "
                        f"urgent_goals = '{goals_json}'::jsonb "
                        f"WHERE telegram_id = {telegram_id}"
                    )
                    
                    cur.close()
                    conn.close()
                    
                    # Начинаем адаптивный тест (как в awaiting_goal)
                    conn = get_db_connection()
                    cur = conn.cursor()
                    
                    test_state = json.dumps({
                        'question_num': 0,
                        'history': []
                    }, ensure_ascii=False).replace("'", "''")
                    
                    cur.execute(
                        f"UPDATE {SCHEMA}.users SET "
                        f"conversation_mode = 'adaptive_level_test', "
                        f"test_phrases = '{test_state}'::jsonb "
                        f"WHERE telegram_id = {telegram_id}"
                    )
                    cur.close()
                    conn.close()
                    
                    # Генерируем первый вопрос теста
                    try:
                        first_item = generate_adaptive_question('A1', [])
                        
                        type_emojis = {'word': '📖', 'phrase': '💬', 'expression': '✨'}
                        emoji = type_emojis.get(first_item.get('type', 'word'), '📖')
                        
                        question_message = f'{emoji} <b>Вопрос 1/10</b>\n\n'
                        question_message += f'Переведи на русский:\n<b>{first_item["english"]}</b>'
                        
                        send_telegram_message(chat_id, question_message)
                        
                        test_state = {
                            'current_item': first_item,
                            'question_num': 1,
                            'history': []
                        }
                        
                        conn = get_db_connection()
                        cur = conn.cursor()
                        test_state_json = json.dumps(test_state, ensure_ascii=False).replace("'", "''")
                        cur.execute(
                            f"UPDATE {SCHEMA}.users SET test_phrases = '{test_state_json}'::jsonb "
                            f"WHERE telegram_id = {telegram_id}"
                        )
                        cur.close()
                        conn.close()
                        
                    except Exception as e:
                        print(f"[ERROR] Failed to start adaptive test: {e}")
                        import traceback
                        traceback.print_exc()
                        send_telegram_message(chat_id, '❌ Ошибка запуска теста. Попробуй /start')
                
                except Exception as e:
                    print(f"[ERROR] Failed to generate urgent goals: {e}")
                    import traceback
                    traceback.print_exc()
                    log_proxy_failure(proxy_id, str(e))
                    send_telegram_message(chat_id, '❌ Не удалось проанализировать задачу. Попробуй еще раз или напиши /start', parse_mode=None)
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'ok': True}),
                    'isBase64Encoded': False
                }
            
            # Проверяем - ждем ли мы описание интересов/тем от пользователя (свой вариант)
            elif conversation_mode == 'awaiting_topics':
                # Пользователь описал свои интересы - парсим через Gemini, генерируем ПОЛНЫЙ ПЛАН
                send_telegram_message(chat_id, '⏳ Анализирую твои интересы и готовлю полный план обучения на месяц...', parse_mode=None)
                
                try:
                    # Парсим интересы через Gemini
                    api_key = os.environ['GEMINI_API_KEY']
                    proxy_id, proxy_url = get_active_proxy_from_db()
                    if not proxy_url:
                        proxy_url = os.environ.get('PROXY_URL', '')
                    
                    gemini_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}'
                    
                    prompt = f'''Студент описал свои интересы: "{text}"

Извлеки из текста темы в формате JSON массива объектов.

Формат ответа (только JSON, без markdown):
{{
  "topics": [
    {{"topic": "Игры", "emoji": "🎮"}},
    {{"topic": "Маркетинг", "emoji": "📊"}}
  ]
}}

Важно:
- topic = краткое название темы (1-2 слова)
- emoji = подходящий эмодзи
- Извлекай ВСЕ упомянутые темы (работа, хобби, интересы)

Отвечай ТОЛЬКО валидным JSON.'''
                    
                    payload = {
                        'contents': [{'parts': [{'text': prompt}]}],
                        'generationConfig': {'temperature': 0.3, 'maxOutputTokens': 500}
                    }
                    
                    proxy_handler = urllib.request.ProxyHandler({
                        'http': f'http://{proxy_url}',
                        'https': f'http://{proxy_url}'
                    })
                    opener = urllib.request.build_opener(proxy_handler)
                    
                    req = urllib.request.Request(
                        gemini_url,
                        data=json.dumps(payload).encode('utf-8'),
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    with opener.open(req, timeout=30) as response:
                        gemini_result = json.loads(response.read().decode('utf-8'))
                        topics_text = gemini_result['candidates'][0]['content']['parts'][0]['text']
                        topics_text = topics_text.replace('```json', '').replace('```', '').strip()
                        topics_data = json.loads(topics_text)
                        topics_list = topics_data.get('topics', [])
                    
                    # Сохраняем темы в БД
                    conn = get_db_connection()
                    cur = conn.cursor()
                    
                    topics_json = json.dumps(topics_list, ensure_ascii=False).replace("'", "''")
                    cur.execute(
                        f"UPDATE {SCHEMA}.users SET "
                        f"preferred_topics = '{topics_json}'::jsonb "
                        f"WHERE telegram_id = {telegram_id}"
                    )
                    
                    # Получаем цель и уровень для генерации плана
                    cur.execute(f"SELECT learning_goal, language_level, preferred_topics FROM {SCHEMA}.users WHERE telegram_id = {telegram_id}")
                    row = cur.fetchone()
                    learning_goal = row[0] if row and row[0] else 'Общее развитие английского'
                    language_level = row[1] if row and row[1] else 'A1'
                    preferred_topics = row[2] if row and row[2] else topics_list
                    
                    cur.close()
                    conn.close()
                    
                    # Генерируем ПОЛНЫЙ МЕСЯЧНЫЙ ПЛАН с материалами
                    plan_result = generate_full_monthly_plan(telegram_id, learning_goal, language_level, preferred_topics)
                    
                    if plan_result.get('success'):
                        # Отправляем план с кнопками подтверждения
                        send_telegram_message(
                            chat_id,
                            plan_result['plan_message'],
                            {
                                'inline_keyboard': [
                                    [{'text': '✅ Да, начинаем!', 'callback_data': 'confirm_plan'}],
                                    [{'text': '✏️ Хочу изменить', 'callback_data': 'edit_plan'}]
                                ]
                            },
                            parse_mode=None
                        )
                    else:
                        send_telegram_message(
                            chat_id,
                            f'❌ Не удалось сгенерировать план: {plan_result.get("error", "Unknown error")}\n\nПопробуй еще раз через /start',
                            parse_mode=None
                        )
                    
                except Exception as e:
                    print(f"[ERROR] Failed to process topics: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    # Fallback
                    send_telegram_message(
                        chat_id,
                        '❌ Произошла ошибка при генерации плана. Попробуй еще раз через /start',
                        parse_mode=None
                    )
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'ok': True}),
                    'isBase64Encoded': False
                }
            
            # Проверяем - хочет ли пользователь изменить план
            elif conversation_mode == 'editing_plan':
                # Пользователь написал что хочет изменить - регенерируем план
                send_telegram_message(chat_id, '⏳ Корректирую план обучения с учетом твоих пожеланий...', parse_mode=None)
                
                try:
                    # Получаем данные пользователя
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute(f"SELECT learning_goal, language_level, preferred_topics FROM {SCHEMA}.users WHERE telegram_id = {telegram_id}")
                    row = cur.fetchone()
                    learning_goal = row[0] if row and row[0] else 'Общее развитие английского'
                    language_level = row[1] if row and row[1] else 'A1'
                    preferred_topics = row[2] if row and row[2] else []
                    cur.close()
                    conn.close()
                    
                    # Добавляем корректировки в цель
                    modified_goal = f"{learning_goal}. Дополнительно: {text}"
                    
                    # Регенерируем план с учетом правок
                    plan_result = generate_full_monthly_plan(telegram_id, modified_goal, language_level, preferred_topics)
                    
                    if plan_result.get('success'):
                        send_telegram_message(
                            chat_id,
                            plan_result['plan_message'],
                            {
                                'inline_keyboard': [
                                    [{'text': '✅ Да, начинаем!', 'callback_data': 'confirm_plan'}],
                                    [{'text': '✏️ Еще изменить', 'callback_data': 'edit_plan'}]
                                ]
                            },
                            parse_mode=None
                        )
                    else:
                        send_telegram_message(
                            chat_id,
                            f'❌ Не удалось сгенерировать план: {plan_result.get("error", "Unknown error")}',
                            parse_mode=None
                        )
                except Exception as e:
                    print(f"[ERROR] Failed to edit plan: {e}")
                    send_telegram_message(chat_id, '❌ Ошибка при корректировке плана. Попробуй еще раз.', parse_mode=None)
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'ok': True}),
                    'isBase64Encoded': False
                }
            
            # Если режим не диалог - проверяем ответ на упражнение
            elif conversation_mode != 'dialog':
                correct_answer = existing_user.get('current_exercise_answer', '')
                current_word_id = existing_user.get('current_exercise_word_id')
                user_answer = text.strip()
                
                if correct_answer:
                    # ⚠️ CRITICAL: В режиме sentence проверяем через Gemini (не точное совпадение!)
                    if conversation_mode == 'sentence':
                        # Проверяем предложение через AI
                        try:
                            api_key = os.environ['GEMINI_API_KEY']
                            proxy_id, proxy_url = get_active_proxy_from_db()
                            if not proxy_url:
                                proxy_id = None
                                proxy_url = os.environ.get('PROXY_URL', '')
                            
                            check_prompt = f'''Check if this English sentence is grammatically correct and uses the word "{correct_answer}" properly.

Student's sentence: "{user_answer}"
Required word: {correct_answer}
Student level: {language_level}

⚠️ CRITICAL - Check for these errors:
1. Subject-verb agreement (I am/he is, I have/he has)
2. Verb tenses (present/past/future)
3. Articles (a/an/the)
4. Word order
5. Does sentence contain the required word?

Respond ONLY with this JSON:
{{
  "is_correct": true/false,
  "has_word": true/false,
  "grammar_ok": true/false,
  "feedback": "short explanation in Russian about the mistake",
  "corrected": "corrected sentence if needed (or empty string if correct)"
}}

Rules:
- is_correct = true ONLY if: has_word=true AND grammar_ok=true AND no major errors
- has_word = true if sentence contains the required word "{correct_answer}"
- grammar_ok = true if there are NO grammar mistakes (even small ones!)
- feedback should explain the error clearly in Russian
- corrected should show the fixed sentence

Example:
Input: "I has a voice"
Output: {{"is_correct": false, "has_word": true, "grammar_ok": false, "feedback": "Ошибка: 'I has' неправильно. С местоимением 'I' используется 'have', а не 'has'", "corrected": "I have a voice"}}'''
                            
                            gemini_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}'
                            payload = {
                                'contents': [{'parts': [{'text': check_prompt}]}],
                                'generationConfig': {'temperature': 0.3, 'maxOutputTokens': 2000}
                            }
                            
                            proxy_handler = urllib.request.ProxyHandler({
                                'http': f'http://{proxy_url}',
                                'https': f'http://{proxy_url}'
                            })
                            opener = urllib.request.build_opener(proxy_handler)
                            
                            req = urllib.request.Request(
                                gemini_url,
                                data=json.dumps(payload).encode('utf-8'),
                                headers={'Content-Type': 'application/json'}
                            )
                            
                            with opener.open(req, timeout=15) as response:
                                result = json.loads(response.read().decode('utf-8'))
                                check_text = result['candidates'][0]['content']['parts'][0]['text']
                                print(f'[DEBUG] Gemini raw response for sentence check: {check_text}')
                                
                                check_data = safe_json_parse(check_text, {'is_correct': False, 'feedback': 'Ошибка проверки', 'corrected': '', 'has_word': False, 'grammar_ok': False})
                                print(f'[DEBUG] Parsed check_data: {check_data}')
                                
                                log_proxy_success(proxy_id)
                                
                                is_correct = check_data.get('is_correct', False)
                                feedback = check_data.get('feedback', '')
                                corrected = check_data.get('corrected', '')
                                
                                if is_correct:
                                    send_telegram_message(chat_id, f'✅ Отлично! {feedback} 🎉', get_reply_keyboard())
                                    
                                    # Переходим к следующему слову
                                    if current_word_id:
                                        update_word_progress_api(telegram_id, current_word_id, True)
                                    
                                    clear_exercise_state(telegram_id)
                                    
                                    word = get_random_word(telegram_id, language_level)
                                    if word:
                                        exercise_text = generate_sentence_exercise(word, language_level)
                                        update_exercise_state(telegram_id, word['id'], word['english'])
                                        send_telegram_message(chat_id, exercise_text, get_reply_keyboard())
                                    else:
                                        send_telegram_message(chat_id, '✅ Упражнения закончились! Используй /modes для выбора другого режима.', get_reply_keyboard())
                                        update_conversation_mode(telegram_id, 'dialog')
                                else:
                                    # ⚠️ КРИТИЧНО: При ошибке показываем исправление и просим ПОВТОРИТЬ ТО ЖЕ СЛОВО
                                    response_text = '🔧 Fix / Correct:\n'
                                    response_text += f'❌ {user_answer}\n'
                                    response_text += f'✅ {corrected}\n'
                                    response_text += f'🇷🇺 {feedback}\n\n'
                                    response_text += f'Попробуй еще раз со словом: {correct_answer}'
                                    
                                    send_telegram_message(chat_id, response_text, get_reply_keyboard(), parse_mode=None)
                                    
                                    # НЕ обновляем прогресс и НЕ меняем слово - пусть повторит!
                                    # current_exercise_word_id и current_exercise_answer остаются те же
                                    return {
                                        'statusCode': 200,
                                        'headers': {'Content-Type': 'application/json'},
                                        'body': json.dumps({'status': 'retry_same_word'})
                                    }
                        
                        except Exception as e:
                            print(f'[ERROR] Failed to check sentence: {e}')
                            # Fallback: простая проверка наличия слова
                            is_correct = correct_answer.lower() in user_answer.lower()
                            if is_correct:
                                send_telegram_message(chat_id, '✅ Хорошо! Предложение использует слово правильно! 🎉', get_reply_keyboard())
                                
                                # Переходим к следующему слову
                                if current_word_id:
                                    update_word_progress_api(telegram_id, current_word_id, True)
                                
                                clear_exercise_state(telegram_id)
                                
                                word = get_random_word(telegram_id, language_level)
                                if word:
                                    exercise_text = generate_sentence_exercise(word, language_level)
                                    update_exercise_state(telegram_id, word['id'], word['english'])
                                    send_telegram_message(chat_id, exercise_text, get_reply_keyboard())
                                else:
                                    send_telegram_message(chat_id, '✅ Упражнения закончились! Используй /modes для выбора другого режима.', get_reply_keyboard())
                                    update_conversation_mode(telegram_id, 'dialog')
                            else:
                                # При ошибке - просим повторить то же слово
                                response_text = f'❌ Предложение не содержит слово "{correct_answer}".\n\nПопробуй еще раз!'
                                send_telegram_message(chat_id, response_text, get_reply_keyboard())
                                
                                # НЕ меняем слово - пусть повторит
                                return {
                                    'statusCode': 200,
                                    'headers': {'Content-Type': 'application/json'},
                                    'body': json.dumps({'status': 'retry_same_word'})
                                }
                    else:
                        # Для других режимов (context, association, translation) - точное совпадение
                        correct_answer_lower = correct_answer.lower()
                        is_correct = (user_answer.lower() == correct_answer_lower)
                        
                        if is_correct:
                            send_telegram_message(chat_id, '✅ Правильно! Отличная работа! 🎉', get_reply_keyboard())
                            
                            # Обновляем прогресс слова
                            if current_word_id:
                                update_word_progress_api(telegram_id, current_word_id, True)
                            
                            clear_exercise_state(telegram_id)
                            
                            word = get_random_word(telegram_id, language_level)
                            if word:
                                if conversation_mode == 'context':
                                    # Получаем все слова для генерации вариантов
                                    conn = get_db_connection()
                                    cur = conn.cursor()
                                    cur.execute(
                                        f"SELECT w.id, w.english_text, w.russian_translation FROM {SCHEMA}.student_words sw "
                                        f"JOIN {SCHEMA}.words w ON w.id = sw.word_id "
                                        f"WHERE sw.student_id = {telegram_id} LIMIT 20"
                                    )
                                    all_words = [{'id': row[0], 'english': row[1], 'russian': row[2]} for row in cur.fetchall()]
                                    cur.close()
                                    conn.close()
                                    
                                    exercise_text, answer, options = generate_context_exercise(word, language_level, all_words)
                                    update_exercise_state(telegram_id, word['id'], answer)
                                    
                                    inline_keyboard = {
                                        'inline_keyboard': [
                                            [{'text': opt, 'callback_data': f'context_answer:{opt}'}] for opt in options
                                        ]
                                    }
                                    send_telegram_message(chat_id, exercise_text, reply_markup=inline_keyboard, parse_mode=None)
                                elif conversation_mode == 'association':
                                    exercise_text, answer = generate_association_exercise(word, language_level)
                                    update_exercise_state(telegram_id, word['id'], answer)
                                    send_telegram_message(chat_id, exercise_text, get_reply_keyboard())
                                elif conversation_mode == 'translation':
                                    exercise_text, answer = generate_translation_exercise(word)
                                    update_exercise_state(telegram_id, word['id'], answer)
                                    send_telegram_message(chat_id, exercise_text, get_reply_keyboard())
                            else:
                                send_telegram_message(chat_id, '✅ Упражнения закончились! Используй /modes для выбора другого режима.', get_reply_keyboard())
                                update_conversation_mode(telegram_id, 'dialog')
                        else:
                            # При ошибке - показываем правильный ответ и ДУБЛИРУЕМ вопрос
                            response_text = '🔧 Fix / Correct:\n'
                            response_text += f'❌ {user_answer}\n'
                            response_text += f'✅ {correct_answer}\n'
                            response_text += f'🇷🇺 Правильный ответ: {correct_answer}\n\n'
                            response_text += 'Попробуй еще раз!'
                            
                            send_telegram_message(chat_id, response_text, get_reply_keyboard(), parse_mode=None)
                            
                            # ДУБЛИРУЕМ вопрос - отправляем тот же самый вопрос заново
                            if current_word_id:
                                conn = get_db_connection()
                                cur = conn.cursor()
                                cur.execute(
                                    f"SELECT w.id, w.english_text, w.russian_translation FROM {SCHEMA}.words w "
                                    f"WHERE w.id = {current_word_id}"
                                )
                                word_row = cur.fetchone()
                                cur.close()
                                conn.close()
                                
                                if word_row:
                                    word = {'id': word_row[0], 'english': word_row[1], 'russian': word_row[2]}
                                    
                                    # Генерируем тот же тип упражнения заново
                                    if conversation_mode == 'association':
                                        exercise_text, answer = generate_association_exercise(word, language_level)
                                        send_telegram_message(chat_id, exercise_text, get_reply_keyboard(), parse_mode=None)
                                    elif conversation_mode == 'translation':
                                        exercise_text, answer = generate_translation_exercise(word)
                                        send_telegram_message(chat_id, exercise_text, get_reply_keyboard(), parse_mode=None)
                                    
                                    # НЕ обновляем exercise_state - оставляем то же слово!
                            
                            # НЕ обновляем прогресс и НЕ меняем слово
                            return {
                                'statusCode': 200,
                                'headers': {'Content-Type': 'application/json'},
                                'body': json.dumps({'status': 'retry_same_word'}),
                                'isBase64Encoded': False
                            }
                
            else:
                # Режим диалога или голосового - обрабатываем через Gemini
                history = get_conversation_history(telegram_id)
                
                # Если ученик - загружаем слова для практики
                session_words = None
                preferred_topics = existing_user.get('preferred_topics', [])
                
                if existing_user.get('role') == 'student':
                    # КРИТИЧНО: Если идет генерация плана - НЕ трогаем слова вообще!
                    if existing_user.get('conversation_mode') == 'generating_plan':
                        print(f"[DEBUG] User is generating plan - skipping word loading")
                        send_telegram_message(
                            chat_id,
                            '⏳ Подожди, я все еще генерирую твой персональный план обучения...\n\nЭто займет еще ~20 секунд! 🚀'
                        )
                        return {
                            'statusCode': 200,
                            'body': json.dumps({'ok': True})
                        }
                    
                    try:
                        session_words = get_session_words(telegram_id, limit=10)
                    except Exception as e:
                        print(f"[WARNING] Failed to load session words: {e}")
                    
                    # Проверяем, есть ли у студента слова
                    if not session_words or len(session_words) == 0:
                        # Проверяем: может быть слова есть, но все освоены?
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute(
                            f"SELECT COUNT(*) FROM {SCHEMA}.student_words WHERE student_id = {telegram_id}"
                        )
                        total_words = cur.fetchone()[0]
                        
                        # Проверяем количество освоенных слов
                        cur.execute(
                            f"SELECT COUNT(*) FROM {SCHEMA}.word_progress "
                            f"WHERE student_id = {telegram_id} AND status = 'mastered'"
                        )
                        mastered_count = cur.fetchone()[0]
                        cur.close()
                        conn.close()
                        
                        # Если есть слова и много освоенных - поздравляем и генерируем новые
                        if total_words > 0 and mastered_count >= 5:
                            send_telegram_message(
                                chat_id,
                                f'🎉 Поздравляю! Ты освоил {mastered_count} слов!\n\n'
                                f'⏳ Генерирую новую порцию слов для тебя...'
                            )
                            
                            # Получаем данные пользователя для генерации
                            conn = get_db_connection()
                            cur = conn.cursor()
                            cur.execute(
                                f"SELECT learning_goal, language_level FROM {SCHEMA}.users "
                                f"WHERE telegram_id = {telegram_id}"
                            )
                            user_data = cur.fetchone()
                            cur.close()
                            conn.close()
                            
                            learning_goal = user_data[0] if user_data and user_data[0] else 'общение на английском'
                            user_language_level = user_data[1] if user_data and user_data[1] else 'A1'
                            
                            # Генерируем новые слова через webapp-api
                            try:
                                webapp_api_url = os.environ.get('WEBAPP_API_URL', '')
                                if webapp_api_url:
                                    generate_payload = json.dumps({
                                        'action': 'generate_unique_words',
                                        'student_id': telegram_id,
                                        'learning_goal': learning_goal,
                                        'language_level': user_language_level,
                                        'count': 10
                                    }).encode('utf-8')
                                    
                                    req = urllib.request.Request(
                                        webapp_api_url,
                                        data=generate_payload,
                                        headers={'Content-Type': 'application/json'},
                                        method='POST'
                                    )
                                    
                                    with urllib.request.urlopen(req, timeout=30) as resp:
                                        result = json.loads(resp.read().decode('utf-8'))
                                        if result.get('success'):
                                            new_words_count = result.get('count', 0)
                                            send_telegram_message(
                                                chat_id,
                                                f'✅ Добавлено {new_words_count} новых слов!\n\n'
                                                f'Продолжай практиковаться! 💪'
                                            )
                                            # Перезагружаем слова и продолжаем диалог
                                            session_words = get_session_words(telegram_id, limit=10)
                                        else:
                                            send_telegram_message(
                                                chat_id,
                                                '❌ Не удалось сгенерировать новые слова. Попробуй /start'
                                            )
                                            return {
                                                'statusCode': 200,
                                                'body': json.dumps({'ok': True})
                                            }
                            except Exception as gen_error:
                                print(f"[ERROR] Failed to generate new words: {gen_error}")
                                send_telegram_message(
                                    chat_id,
                                    '❌ Ошибка генерации новых слов. Попробуй /start'
                                )
                                return {
                                    'statusCode': 200,
                                    'body': json.dumps({'ok': True})
                                }
                        else:
                            # Если вообще нет слов - предлагаем пройти /start
                            send_telegram_message(
                                chat_id,
                                'У тебя пока нет слов для практики! 📚\n\n'
                                'Чтобы начать обучение:\n'
                                '1. Нажми /start\n'
                                '2. Выбери режим обучения\n'
                                '3. Я подберу слова специально для тебя!'
                            )
                            return {
                                'statusCode': 200,
                                'body': json.dumps({'ok': True})
                            }
                
                # Анализируем использование слов в сообщении ученика
                used_word_ids = []
                if session_words:
                    used_word_ids = detect_words_in_text(text, session_words)
                    print(f"[DEBUG] Detected words in message: {used_word_ids}")
                
                # Сохраняем вопрос пользователя
                save_message(telegram_id, 'user', text)
                
                # Получаем ответ AI с учетом слов, уровня, тем и срочных целей
                try:
                    print(f"[DEBUG] Calling Gemini with message: {text}")
                    print(f"[DEBUG] session_words={session_words}, language_level={language_level}")
                    urgent_goals = existing_user.get('urgent_goals', [])
                    learning_mode = existing_user.get('learning_mode', 'standard')
                    
                    # КРИТИЧНО: learning_goal используется ТОЛЬКО для specific_topic и urgent_task
                    # В стандартном режиме learning_goal игнорируется (там используются preferred_topics)
                    if learning_mode in ['specific_topic', 'urgent_task']:
                        learning_goal = existing_user.get('learning_goal')
                    else:
                        learning_goal = None
                    
                    print(f"[DEBUG] learning_mode={learning_mode}, learning_goal={learning_goal}")
                    ai_response = call_gemini(text, history, session_words, language_level, preferred_topics, urgent_goals, learning_goal, learning_mode)
                    print(f"[DEBUG] Gemini response: {ai_response[:100]}...")
                except Exception as e:
                    print(f"[ERROR] Gemini API failed: {e}")
                    import traceback
                    traceback.print_exc()
                    ai_response = "Sorry, I'm having technical difficulties right now. Please try again in a moment! 🔧"
                
                # Проверяем маркер освоения слова
                mastered_word_marker = '✅ WORD_MASTERED:'
                if mastered_word_marker in ai_response:
                    # Извлекаем слово
                    marker_pos = ai_response.find(mastered_word_marker)
                    word_text = ai_response[marker_pos + len(mastered_word_marker):].strip().split()[0]
                    
                    # Находим word_id
                    if session_words:
                        mastered_word = next((w for w in session_words if w['english'].lower() == word_text.lower()), None)
                        if mastered_word:
                            update_word_progress_api(telegram_id, mastered_word['id'], is_correct=True)
                            print(f"[SUCCESS] Word '{word_text}' marked as mastered!")
                    
                    # Убираем маркер из ответа пользователю
                    ai_response = ai_response[:marker_pos].strip()
                
                # Обновляем прогресс использованных слов учеником
                for word_id in used_word_ids:
                    update_word_progress_api(telegram_id, word_id, True)
                
                # Отслеживаем какие слова Аня использовала в своём ответе
                if session_words:
                    ai_used_words = detect_words_in_text(ai_response, session_words)
                    if ai_used_words:
                        # Обновляем прогресс для каждого слова которое Аня использовала
                        for word_id in ai_used_words:
                            update_word_progress_api(telegram_id, word_id, True)
                        print(f"[DEBUG] Anya used words in response: {ai_used_words}")
                
                # Сохраняем ответ AI
                save_message(telegram_id, 'assistant', ai_response)
                
                # В режиме 'voice' отправляем ТОЛЬКО голосовое сообщение (БЕЗ текста)
                if conversation_mode == 'voice':
                    try:
                        voice_url = text_to_speech(ai_response)
                        send_telegram_voice(chat_id, voice_url)
                    except Exception as e:
                        print(f"[ERROR] Failed to generate voice response: {e}")
                        # Fallback - отправляем текст если голос не сгенерировался
                        send_telegram_message(chat_id, ai_response, get_reply_keyboard())
                else:
                    # В обычном режиме диалога отправляем текст
                    send_telegram_message(chat_id, ai_response, get_reply_keyboard())
            
            # Обновляем статистику практики (для всех режимов)
            if existing_user.get('role') == 'student':
                try:
                    # Отправляем статистику в webapp-api
                    webapp_api_url = os.environ.get('WEBAPP_API_URL', '')
                    if webapp_api_url:
                        # В режиме диалога считаем использованные слова, в упражнениях - 1 слово
                        words_count = len(used_word_ids) if conversation_mode == 'dialog' else 1
                        
                        record_payload = json.dumps({
                            'action': 'record_practice',
                            'student_id': telegram_id,
                            'messages': 1,
                            'words': words_count,
                            'errors': 0
                        }).encode('utf-8')
                        
                        record_req = urllib.request.Request(
                            webapp_api_url,
                            data=record_payload,
                            headers={'Content-Type': 'application/json'},
                            method='POST'
                        )
                        
                        with urllib.request.urlopen(record_req) as resp:
                            result = json.loads(resp.read().decode('utf-8'))
                            # Если разблокировали достижение - отправляем уведомление
                            if result.get('unlocked_achievements'):
                                for ach in result['unlocked_achievements']:
                                    achievement_msg = f"\n\n🎉 Achievement Unlocked!\n{ach['emoji']} {ach['title_en']} (+{ach['points']} points)"
                                    ai_response += achievement_msg
                except Exception as e:
                    print(f"[WARNING] Failed to record practice: {e}")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'ok': True}),
            'isBase64Encoded': False
        }
        
    except Exception as e:
        print(f"[ERROR] Exception in handler: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }