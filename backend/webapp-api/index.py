import json
import os
import psycopg2
import requests
import boto3
from typing import Dict, Any, List

SCHEMA = 't_p86463701_eloquent_school_site'

def get_db_connection():
    """Создает подключение к БД"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.autocommit = True
    return conn

def get_proxies():
    """Возвращает прокси из env"""
    proxy_url = os.environ.get('PROXY_URL')
    if proxy_url:
        return {
            'http': f'http://{proxy_url}',
            'https': f'http://{proxy_url}'
        }
    return None

def analyze_goal_for_plan(goal: str) -> Dict[str, Any]:
    """Анализирует цель пользователя и возвращает персонализированный план обучения"""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return {'error': 'GEMINI_API_KEY not found'}
    
    prompt = f"""Студент хочет учить английский. Его цель: "{goal}".

Твоя задача: просто понять и подтвердить цель студента.

Формат ответа (только JSON, без markdown):
{{
  "goal": "Краткое описание цели (1 предложение)",
  "timeline": "Срок ТОЛЬКО если явно указан (например '1 месяц', '2 недели') ИЛИ null если не указан"
}}

⚠️ ВАЖНО:
- goal = понятная формулировка цели студента
- timeline = извлекай ТОЛЬКО если явно указан ("через месяц", "за 2 недели"). Если не указан - ставь null

Отвечай ТОЛЬКО валидным JSON, без объяснений."""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2000
        }
    }
    
    try:
        proxies = get_proxies()
        response = requests.post(url, json=payload, proxies=proxies, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'candidates' in data and len(data['candidates']) > 0:
            text = data['candidates'][0]['content']['parts'][0]['text']
            text = text.replace('```json', '').replace('```', '').strip()
            
            try:
                result = json.loads(text)
                return result
            except json.JSONDecodeError as e:
                # Пытаемся починить JSON
                last_comma = text.rfind(',')
                last_brace = text.rfind('}')
                
                if last_comma > last_brace:
                    text = text[:last_comma]
                
                if text.count('{') > text.count('}'):
                    text += '}' * (text.count('{') - text.count('}'))
                
                if text.count('[') > text.count(']'):
                    text += ']' * (text.count('[') - text.count(']'))
                
                try:
                    result = json.loads(text)
                    return result
                except:
                    return {'error': f'Invalid JSON: {str(e)}'}
        
        return {'error': 'No response from Gemini'}
    
    except Exception as e:
        return {'error': str(e)}

def check_student_level(claimed_level: str, answer: str) -> Dict[str, Any]:
    """Проверяет реальный уровень студента по его ответу"""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return {'error': 'GEMINI_API_KEY not found'}
    
    prompt = f"""Студент утверждает что его уровень английского: {claimed_level}.
Вот его ответ на проверочный вопрос: "{answer}"

Твоя задача: определить РЕАЛЬНЫЙ уровень по ответу.

Критерии оценки:
- A1: Очень простые слова, много ошибок, короткие фразы
- A2: Базовые конструкции, встречаются ошибки, простая лексика
- B1: Связные предложения, разнообразная лексика, грамматика в целом правильная
- B2: Сложные конструкции, богатая лексика, минимум ошибок
- C1: Естественная речь, идиомы, практически без ошибок

Формат ответа (только JSON, без markdown):
{{
  "actual_level": "A1/A2/B1/B2/C1",
  "is_correct": true/false,
  "reasoning": "Краткое объяснение на русском (1-2 предложения)"
}}

⚠️ ВАЖНО:
- actual_level = реальный уровень по ответу
- is_correct = совпадает ли с claimed_level (±1 уровень считается правильным)
- reasoning = почему ты так решил

Отвечай ТОЛЬКО валидным JSON, без объяснений."""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 500
        }
    }
    
    try:
        proxies = get_proxies()
        response = requests.post(url, json=payload, proxies=proxies, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'candidates' in data and len(data['candidates']) > 0:
            text = data['candidates'][0]['content']['parts'][0]['text']
            text = text.replace('```json', '').replace('```', '').strip()
            
            try:
                result = json.loads(text)
                return result
            except json.JSONDecodeError as e:
                print(f"🔴 JSON parse error in check_level: {e}")
                print(f"🔴 Problematic JSON:\n{text}")
                
                try:
                    import re
                    fixed_text = text.strip()
                    
                    # Случай 1: Незакрытая строка после двоеточия
                    last_colon_idx = fixed_text.rfind(':')
                    if last_colon_idx != -1:
                        after_colon = fixed_text[last_colon_idx+1:].strip()
                        if after_colon.startswith('"'):
                            quotes_count = after_colon.count('"')
                            if quotes_count % 2 == 1:
                                fixed_text += '"'
                                print(f"🔧 Fixed unterminated string after colon")
                    
                    # Случай 2: Удаляем незавершенный последний элемент
                    last_comma_idx = fixed_text.rfind(',')
                    last_brace_idx = fixed_text.rfind('}')
                    
                    if last_comma_idx > last_brace_idx and last_comma_idx != -1:
                        fixed_text = fixed_text[:last_comma_idx]
                        print(f"🔧 Removed incomplete trailing item")
                    
                    # Случай 3: Закрываем незакрытые скобки
                    open_braces = fixed_text.count('{')
                    close_braces = fixed_text.count('}')
                    if open_braces > close_braces:
                        fixed_text += '}' * (open_braces - close_braces)
                        print(f"🔧 Added {open_braces - close_braces} closing braces")
                    
                    result = json.loads(fixed_text)
                    print(f"✅ Fixed JSON successfully!")
                    return result
                except Exception as fix_error:
                    print(f"🔴 Failed to fix JSON: {fix_error}")
                    return {'error': f'Invalid JSON: {str(e)}', 'actual_level': claimed_level, 'is_correct': True}
        
        return {'error': 'No response from Gemini', 'actual_level': claimed_level, 'is_correct': True}
    
    except Exception as e:
        return {'error': str(e), 'actual_level': claimed_level, 'is_correct': True}

def analyze_urgent_goal(goal: str) -> Dict[str, Any]:
    """Анализирует срочную цель и предлагает конкретные темы для подготовки через Gemini"""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return {'error': 'GEMINI_API_KEY not found', 'subtopics': []}
    
    prompt = f"""Студент едет/идет куда-то срочно и ему нужен английский. Его задача: "{goal}".

Твоя задача: предложить 3-5 КОНКРЕТНЫХ тем, которые ему понадобятся для этой ситуации.

Примеры:
- Если едет в Лондон → "В аэропорту", "Заселение в отель", "Заказ такси", "В ресторане", "Спросить дорогу"
- Если собеседование → "Рассказ о себе", "Описание опыта", "Обсуждение зарплаты", "Вопросы работодателю"

Формат ответа (только JSON, без markdown):
{{
  "subtopics": [
    {{
      "id": "airport",
      "title": "В аэропорту",
      "description": "Регистрация, паспортный контроль, багаж"
    }},
    {{
      "id": "hotel",
      "title": "Заселение в отель",
      "description": "Бронирование, check-in, вопросы о номере"
    }}
  ]
}}

⚠️ ВАЖНО:
- id = латиница, без пробелов (например: "airport", "job_interview")
- title = русский, короткий (2-4 слова)
- description = русский, что конкретно входит (5-8 слов)
- Темы должны быть ПРАКТИЧНЫЕ и КОНКРЕТНЫЕ для его ситуации

Отвечай ТОЛЬКО валидным JSON, без объяснений."""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 2000
        }
    }
    
    try:
        proxies = get_proxies()
        response = requests.post(url, json=payload, proxies=proxies, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'candidates' in data and len(data['candidates']) > 0:
            text = data['candidates'][0]['content']['parts'][0]['text']
            print(f"🔍 Raw Gemini response: {text}")
            text = text.replace('```json', '').replace('```', '').strip()
            print(f"🔍 Cleaned text: {text}")
            
            try:
                result = json.loads(text)
                print(f"✅ Parsed JSON: {result}")
                return result
            except json.JSONDecodeError as e:
                print(f"🔴 JSON parse error: {e}")
                
                import re
                last_comma = text.rfind(',')
                last_brace = text.rfind('}')
                
                if last_comma > last_brace:
                    text = text[:last_comma]
                    print(f"🔧 Removed incomplete item after last comma")
                
                if text.count('{') > text.count('}'):
                    text += '}' * (text.count('{') - text.count('}'))
                    print(f"🔧 Added missing closing braces")
                
                if text.count('[') > text.count(']'):
                    text += ']' * (text.count('[') - text.count(']'))
                    print(f"🔧 Added missing closing brackets")
                
                try:
                    result = json.loads(text)
                    print(f"✅ Fixed and parsed JSON: {result}")
                    return result
                except:
                    print(f"🔴 Failed to fix JSON")
                    return {'error': f'Invalid JSON: {str(e)}', 'subtopics': []}
        
        return {'error': 'No response from Gemini', 'subtopics': []}
    
    except Exception as e:
        return {'error': str(e), 'subtopics': []}

def generate_learning_goal_suggestions(user_input: str) -> Dict[str, Any]:
    """Генерирует рекомендации по детализации цели обучения через Gemini"""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return {'error': 'GEMINI_API_KEY not found', 'suggestions': []}
    
    prompt = f"""Ты — помощник для изучения английского языка. Студент указал свою цель: "{user_input}".

Твоя задача: дать 2-3 коротких совета (по 1 предложению каждый) как конкретизировать эту цель для более эффективного обучения.

Формат ответа (только JSON, без markdown):
{{
  "suggestions": [
    "Совет 1",
    "Совет 2",
    "Совет 3"
  ]
}}

Отвечай ТОЛЬКО валидным JSON, без объяснений."""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 500
        }
    }
    
    try:
        proxies = get_proxies()
        response = requests.post(url, json=payload, proxies=proxies, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'candidates' in data and len(data['candidates']) > 0:
            text = data['candidates'][0]['content']['parts'][0]['text']
            text = text.replace('```json', '').replace('```', '').strip()
            result = json.loads(text)
            return result
        
        return {'error': 'No response from Gemini', 'suggestions': []}
    
    except Exception as e:
        return {'error': str(e), 'suggestions': []}

def generate_unique_words(student_id: int, learning_goal: str, language_level: str, count: int = 7) -> Dict[str, Any]:
    """Генерирует УНИКАЛЬНЫЕ персональные слова (без дубликатов с существующими)"""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return {'error': 'GEMINI_API_KEY not found', 'words': []}
    
    # Получаем все существующие слова студента
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
    
    existing_words_str = ', '.join(existing_words[:150]) if existing_words else 'none'
    print(f"[DEBUG] Student {student_id} has {len(existing_words)} existing words")
    
    level_descriptions = {
        'A1': 'начальный уровень (простые базовые слова)',
        'A2': 'элементарный уровень (повседневная лексика)',
        'B1': 'средний уровень (распространенная лексика)',
        'B2': 'продвинутый уровень (профессиональная лексика)',
        'C1': 'высокий уровень (сложная лексика)',
        'C2': 'свободное владение (нативная лексика)'
    }
    
    level_desc = level_descriptions.get(language_level, level_descriptions['A1'])
    
    prompt = f"""Ты — эксперт по практическому изучению английского языка. 

Студент изучает английский:
- Цель обучения: {learning_goal}
- Уровень: {language_level} ({level_desc})

Твоя задача: подобрать {count} САМЫХ ПРАКТИЧНЫХ английских слов для РЕАЛЬНЫХ разговоров на эту тему.

⚠️ КРИТИЧЕСКИЕ ПРАВИЛА:

1. НЕ ИСПОЛЬЗУЙ банальные слова: hello, yes, no, cat, dog, book, red, blue, one, two
2. НЕ ИСПОЛЬЗУЙ слишком простые слова, которые все знают
3. ИСПОЛЬЗУЙ глаголы, прилагательные, фразовые глаголы - то что РЕАЛЬНО нужно в разговоре
4. ФОКУС на словах, которые студент будет использовать в диалогах по своей цели
5. ⚠️ CRITICAL: DO NOT use these words (student already knows them): {existing_words_str}
6. Generate ONLY NEW words that are NOT in the existing list

Примеры ХОРОШИХ слов для разных целей:

Цель "Путешествия" → НЕ "airport, ticket", А "delay, boarding, luggage, customs, exchange rate"
Цель "Работа" → НЕ "work, job", А "deadline, collaborate, prioritize, efficiency, feedback"
Цель "Общение" → НЕ "talk, speak", А "suggest, clarify, hesitate, convinced, relevant"
Цель "IT" → НЕ "computer, internet", А "implement, deploy, debugging, optimize, integrate"

Если уровень A1-A2: выбирай САМЫЕ частотные глаголы (want, need, feel, think, understand, explain, prefer)
Если уровень B1-B2: выбирай разговорные конструкции и phrasal verbs (figure out, deal with, come up with, get along)
Если уровень C1-C2: выбирай идиомы и продвинутую лексику

Формат ответа (только JSON, без markdown):
{{
  "words": [
    {{
      "english": "practical_word",
      "russian": "перевод"
    }}
  ]
}}

КРИТИЧНО: 
- Отвечай ТОЛЬКО валидным JSON массивом из {count} слов
- БЕЗ комментариев в JSON
- БЕЗ trailing commas
- БЕЗ markdown форматирования
- Только практичные слова для реальных разговоров!
- НИКАКИХ дубликатов из списка уже известных слов!"""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 2000,
            "responseMimeType": "application/json"
        }
    }
    
    try:
        proxies = get_proxies()
        response = requests.post(url, json=payload, proxies=proxies, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'candidates' in data and len(data['candidates']) > 0:
            text = data['candidates'][0]['content']['parts'][0]['text']
            text = text.replace('```json', '').replace('```', '').strip()
            
            # Удаляем trailing commas
            import re
            text = re.sub(r',\s*}', '}', text)
            text = re.sub(r',\s*]', ']', text)
            
            result = json.loads(text)
            generated_words = result.get('words', [])
            
            # ФИЛЬТРУЕМ дубликаты ПОСЛЕ генерации
            unique_words = []
            duplicates = []
            for word_data in generated_words:
                word_lower = word_data['english'].strip().lower()
                if word_lower not in existing_words:
                    unique_words.append(word_data)
                else:
                    duplicates.append(word_lower)
            
            print(f"[DEBUG] Generated {len(generated_words)}, unique: {len(unique_words)}, duplicates: {len(duplicates)}")
            
            # Если есть дубликаты - запрашиваем замену
            if duplicates and len(unique_words) < count:
                needed = count - len(unique_words)
                print(f"[DEBUG] Requesting {needed} replacement words...")
                
                replacement_prompt = f"""Generate {needed} NEW English words for level {language_level}.
Goal: {learning_goal}

⚠️ CRITICAL: DO NOT use these words (duplicates): {', '.join(duplicates)}
⚠️ ALSO DO NOT use: {existing_words_str}

Return ONLY valid JSON:
{{"words": [{{"english": "word", "russian": "перевод"}}]}}"""
                
                replacement_payload = {
                    "contents": [{"parts": [{"text": replacement_prompt}]}],
                    "generationConfig": {"temperature": 0.95, "maxOutputTokens": 1500, "responseMimeType": "application/json"}
                }
                
                replacement_response = requests.post(url, json=replacement_payload, proxies=proxies, timeout=25)
                replacement_data = replacement_response.json()
                
                if 'candidates' in replacement_data:
                    replacement_text = replacement_data['candidates'][0]['content']['parts'][0]['text']
                    replacement_text = replacement_text.replace('```json', '').replace('```', '').strip()
                    replacement_result = json.loads(replacement_text)
                    
                    for repl_word in replacement_result.get('words', []):
                        if repl_word['english'].strip().lower() not in existing_words:
                            unique_words.append(repl_word)
                    
                    print(f"[DEBUG] Added {len(replacement_result.get('words', []))} replacement words")
            
            # Сохраняем ТОЛЬКО уникальные слова в БД
            conn = get_db_connection()
            cur = conn.cursor()
            
            added_words = []
            for word_data in unique_words[:count]:
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
                
                # Проверяем что слово НЕ добавлено студенту
                cur.execute(
                    f"SELECT id FROM {SCHEMA}.student_words WHERE student_id = {student_id} AND word_id = {word_id}"
                )
                if not cur.fetchone():
                    cur.execute(
                        f"INSERT INTO {SCHEMA}.student_words (student_id, word_id, teacher_id) "
                        f"VALUES ({student_id}, {word_id}, {student_id})"
                    )
                    added_words.append({
                        'id': word_id,
                        'english': english,
                        'russian': russian
                    })
            
            cur.close()
            conn.close()
            
            return {'success': True, 'words': added_words, 'count': len(added_words), 'duplicates_found': len(duplicates)}
        
        return {'error': 'No response from Gemini', 'words': []}
    
    except Exception as e:
        return {'error': str(e), 'words': []}

def generate_personalized_words(student_id: int, learning_goal: str, language_level: str, count: int = 7) -> Dict[str, Any]:
    """Генерирует персональные слова через Gemini на основе цели и уровня студента (DEPRECATED: use generate_unique_words)"""
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return {'error': 'GEMINI_API_KEY not found', 'words': []}
    
    level_descriptions = {
        'A1': 'начальный уровень (простые базовые слова)',
        'A2': 'элементарный уровень (повседневная лексика)',
        'B1': 'средний уровень (распространенная лексика)',
        'B2': 'продвинутый уровень (профессиональная лексика)',
        'C1': 'высокий уровень (сложная лексика)',
        'C2': 'свободное владение (нативная лексика)'
    }
    
    level_desc = level_descriptions.get(language_level, level_descriptions['A1'])
    
    prompt = f"""Ты — эксперт по практическому изучению английского языка. 

Студент изучает английский:
- Цель обучения: {learning_goal}
- Уровень: {language_level} ({level_desc})

Твоя задача: подобрать {count} САМЫХ ПРАКТИЧНЫХ английских слов для РЕАЛЬНЫХ разговоров на эту тему.

⚠️ КРИТИЧЕСКИЕ ПРАВИЛА:

1. НЕ ИСПОЛЬЗУЙ банальные слова: hello, yes, no, cat, dog, book, red, blue, one, two
2. НЕ ИСПОЛЬЗУЙ слишком простые слова, которые все знают
3. ИСПОЛЬЗУЙ глаголы, прилагательные, фразовые глаголы - то что РЕАЛЬНО нужно в разговоре
4. ФОКУС на словах, которые студент будет использовать в диалогах по своей цели

Примеры ХОРОШИХ слов для разных целей:

Цель "Путешествия" → НЕ "airport, ticket", А "delay, boarding, luggage, customs, exchange rate"
Цель "Работа" → НЕ "work, job", А "deadline, collaborate, prioritize, efficiency, feedback"
Цель "Общение" → НЕ "talk, speak", А "suggest, clarify, hesitate, convinced, relevant"
Цель "IT" → НЕ "computer, internet", А "implement, deploy, debugging, optimize, integrate"

Если уровень A1-A2: выбирай САМЫЕ частотные глаголы (want, need, feel, think, understand, explain, prefer)
Если уровень B1-B2: выбирай разговорные конструкции и phrasal verbs (figure out, deal with, come up with, get along)
Если уровень C1-C2: выбирай идиомы и продвинутую лексику

Формат ответа (только JSON, без markdown):
{{
  "words": [
    {{
      "english": "practical_word",
      "russian": "перевод"
    }}
  ]
}}

КРИТИЧНО: 
- Отвечай ТОЛЬКО валидным JSON массивом из {count} слов
- БЕЗ комментариев в JSON
- БЕЗ trailing commas
- БЕЗ markdown форматирования
- Только практичные слова для реальных разговоров!"""
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2000,
            "responseMimeType": "application/json"
        }
    }
    
    try:
        proxies = get_proxies()
        response = requests.post(url, json=payload, proxies=proxies, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'candidates' in data and len(data['candidates']) > 0:
            text = data['candidates'][0]['content']['parts'][0]['text']
            text = text.replace('```json', '').replace('```', '').strip()
            
            # Удаляем trailing commas перед парсингом
            import re
            text = re.sub(r',\s*}', '}', text)
            text = re.sub(r',\s*]', ']', text)
            
            try:
                result = json.loads(text)
            except json.JSONDecodeError as e:
                print(f"🔴 JSON parse error: {e}")
                print(f"🔴 Full problematic JSON:\n{text}")
                
                # Пытаемся починить JSON
                try:
                    import re
                    fixed_text = text.strip()
                    
                    # Случай 1: Обрезанная строка внутри JSON (самая частая проблема)
                    # Ищем последнее вхождение ":" и проверяем незакрытую кавычку
                    last_colon_idx = fixed_text.rfind(':')
                    if last_colon_idx != -1:
                        after_colon = fixed_text[last_colon_idx+1:].strip()
                        # Если после двоеточия начинается строка но не закрывается
                        if after_colon.startswith('"'):
                            # Считаем кавычки после последнего двоеточия
                            quotes_count = after_colon.count('"')
                            if quotes_count % 2 == 1:  # Нечетное число = незакрытая строка
                                fixed_text += '"'
                                print(f"🔧 Fixed unterminated string after colon")
                    
                    # Случай 2: Удаляем незавершенный последний элемент массива
                    # Если есть последняя запятая перед концом - удаляем все после нее
                    last_comma_idx = fixed_text.rfind(',')
                    last_brace_idx = fixed_text.rfind('}')
                    
                    # Если последняя запятая идет ПОСЛЕ последней закрывающей скобки объекта
                    # значит начался новый объект но не завершился - удаляем его
                    if last_comma_idx > last_brace_idx and last_comma_idx != -1:
                        fixed_text = fixed_text[:last_comma_idx]
                        print(f"🔧 Removed incomplete trailing object after comma")
                    
                    # Случай 3: незакрытый объект
                    open_braces = fixed_text.count('{')
                    close_braces = fixed_text.count('}')
                    if open_braces > close_braces:
                        fixed_text += '}' * (open_braces - close_braces)
                        print(f"🔧 Added {open_braces - close_braces} closing braces")
                    
                    # Случай 4: незакрытый массив
                    open_brackets = fixed_text.count('[')
                    close_brackets = fixed_text.count(']')
                    if open_brackets > close_brackets:
                        fixed_text += ']' * (open_brackets - close_brackets)
                        print(f"🔧 Added {open_brackets - close_brackets} closing brackets")
                    
                    result = json.loads(fixed_text)
                    print(f"✅ Fixed JSON successfully! Got {len(result.get('words', []))} words")
                except Exception as fix_error:
                    print(f"🔴 Failed to fix JSON: {fix_error}")
                    print(f"🔴 Attempted fixed text:\n{fixed_text if 'fixed_text' in locals() else 'N/A'}")
                    return {'error': f'Invalid JSON from Gemini: {str(e)}. Повторите попытку через минуту.', 'words': []}
            
            if 'words' in result and len(result['words']) > 0:
                conn = get_db_connection()
                cur = conn.cursor()
                
                added_words = []
                for word_data in result['words']:
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
                    
                    cur.execute(
                        f"INSERT INTO {SCHEMA}.student_words (student_id, word_id, teacher_id) "
                        f"VALUES ({student_id}, {word_id}, {student_id}) "
                        f"ON CONFLICT (student_id, word_id) DO NOTHING"
                    )
                    
                    added_words.append({
                        'id': word_id,
                        'english': english,
                        'russian': russian
                    })
                
                cur.close()
                conn.close()
                
                return {'success': True, 'words': added_words, 'count': len(added_words)}
            
            return {'error': 'No words generated', 'words': []}
        
        return {'error': 'No response from Gemini', 'words': []}
    
    except Exception as e:
        return {'error': str(e), 'words': []}

def get_all_gemini_prompts() -> List[Dict[str, Any]]:
    """Получает все промпты Gemini"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT id, code, name, description, prompt_text, category, is_active, created_at, updated_at "
        f"FROM {SCHEMA}.gemini_prompts ORDER BY category, name"
    )
    
    prompts = []
    for row in cur.fetchall():
        prompts.append({
            'id': row[0],
            'code': row[1],
            'name': row[2],
            'description': row[3],
            'prompt_text': row[4],
            'category': row[5],
            'is_active': row[6],
            'created_at': row[7].isoformat() if row[7] else None,
            'updated_at': row[8].isoformat() if row[8] else None
        })
    
    cur.close()
    conn.close()
    return prompts

def get_gemini_prompt_by_code(code: str) -> Dict[str, Any]:
    """Получает промпт по коду"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    code_escaped = code.replace("'", "''")
    
    cur.execute(
        f"SELECT id, code, name, description, prompt_text, category, is_active "
        f"FROM {SCHEMA}.gemini_prompts WHERE code = '{code_escaped}' AND is_active = TRUE"
    )
    
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if row:
        return {
            'id': row[0],
            'code': row[1],
            'name': row[2],
            'description': row[3],
            'prompt_text': row[4],
            'category': row[5],
            'is_active': row[6]
        }
    return None

def update_gemini_prompt(prompt_id: int, prompt_text: str, description: str = None, is_active: bool = True) -> bool:
    """Обновляет промпт"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    text_escaped = prompt_text.replace("'", "''")
    
    if description:
        desc_escaped = description.replace("'", "''")
        desc_value = f"'{desc_escaped}'"
    else:
        desc_value = 'NULL'
    
    cur.execute(
        f"UPDATE {SCHEMA}.gemini_prompts SET "
        f"prompt_text = '{text_escaped}', "
        f"description = {desc_value}, "
        f"is_active = {is_active}, "
        f"updated_at = CURRENT_TIMESTAMP "
        f"WHERE id = {prompt_id}"
    )
    
    cur.close()
    conn.close()
    return True

def toggle_gemini_prompt(prompt_id: int, is_active: bool) -> bool:
    """Включает/выключает промпт"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"UPDATE {SCHEMA}.gemini_prompts SET is_active = {is_active}, updated_at = CURRENT_TIMESTAMP "
        f"WHERE id = {prompt_id}"
    )
    
    cur.close()
    conn.close()
    return True

def get_financial_analytics() -> Dict[str, Any]:
    """Получает финансовую статистику проекта"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Общее количество пользователей
    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.users WHERE role = 'student'")
    total_students = cur.fetchone()[0]
    
    # Активные подписки (basic)
    cur.execute(
        f"SELECT COUNT(*) FROM {SCHEMA}.subscription_payments "
        f"WHERE period = 'basic' AND status = 'paid' AND expires_at > CURRENT_TIMESTAMP"
    )
    active_basic_subs = cur.fetchone()[0]
    
    # Активные подписки (premium)
    cur.execute(
        f"SELECT COUNT(*) FROM {SCHEMA}.subscription_payments "
        f"WHERE period = 'premium' AND status = 'paid' AND expires_at > CURRENT_TIMESTAMP"
    )
    active_premium_subs = cur.fetchone()[0]
    
    # Активные подписки (bundle)
    cur.execute(
        f"SELECT COUNT(*) FROM {SCHEMA}.subscription_payments "
        f"WHERE period = 'bundle' AND status = 'paid' AND expires_at > CURRENT_TIMESTAMP"
    )
    active_bundle_subs = cur.fetchone()[0]
    
    # Всего активных подписок
    total_active_subs = active_basic_subs + active_premium_subs + active_bundle_subs
    
    # Доход за всё время (сумма всех оплаченных подписок)
    cur.execute(
        f"SELECT COALESCE(SUM(amount_kop), 0) FROM {SCHEMA}.subscription_payments "
        f"WHERE status = 'paid'"
    )
    total_revenue_kop = cur.fetchone()[0] or 0
    total_revenue_rub = total_revenue_kop / 100
    
    # Доход за текущий месяц
    cur.execute(
        f"SELECT COALESCE(SUM(amount_kop), 0) FROM {SCHEMA}.subscription_payments "
        f"WHERE status = 'paid' AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_TIMESTAMP)"
    )
    month_revenue_kop = cur.fetchone()[0] or 0
    month_revenue_rub = month_revenue_kop / 100
    
    # Доход за последние 7 дней
    cur.execute(
        f"SELECT COALESCE(SUM(amount_kop), 0) FROM {SCHEMA}.subscription_payments "
        f"WHERE status = 'paid' AND created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'"
    )
    week_revenue_kop = cur.fetchone()[0] or 0
    week_revenue_rub = week_revenue_kop / 100
    
    # Количество оплат за всё время
    cur.execute(
        f"SELECT COUNT(*) FROM {SCHEMA}.subscription_payments WHERE status = 'paid'"
    )
    total_payments = cur.fetchone()[0]
    
    # Средний чек
    avg_check_rub = total_revenue_rub / total_payments if total_payments > 0 else 0
    
    # Статистика по тарифам (все оплаченные)
    cur.execute(
        f"SELECT period, COUNT(*), COALESCE(SUM(amount_kop), 0) FROM {SCHEMA}.subscription_payments "
        f"WHERE status = 'paid' GROUP BY period"
    )
    plan_stats = {}
    for row in cur.fetchall():
        plan_key = row[0]
        plan_stats[plan_key] = {
            'total_purchases': row[1],
            'total_revenue': row[2] / 100
        }
    
    # История платежей за последние 30 дней (по дням)
    cur.execute(
        f"SELECT DATE(created_at) as payment_date, COUNT(*), COALESCE(SUM(amount_kop), 0) "
        f"FROM {SCHEMA}.subscription_payments "
        f"WHERE status = 'paid' AND created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days' "
        f"GROUP BY DATE(created_at) ORDER BY DATE(created_at)"
    )
    daily_revenue = []
    for row in cur.fetchall():
        daily_revenue.append({
            'date': row[0].isoformat() if row[0] else None,
            'count': row[1],
            'revenue': row[2] / 100
        })
    
    cur.close()
    conn.close()
    
    return {
        'total_students': total_students,
        'total_active_subscriptions': total_active_subs,
        'active_basic': active_basic_subs,
        'active_premium': active_premium_subs,
        'active_bundle': active_bundle_subs,
        'total_revenue': round(total_revenue_rub, 2),
        'month_revenue': round(month_revenue_rub, 2),
        'week_revenue': round(week_revenue_rub, 2),
        'total_payments': total_payments,
        'avg_check': round(avg_check_rub, 2),
        'plan_stats': plan_stats,
        'daily_revenue': daily_revenue
    }

def send_telegram_notification(telegram_id: int, message: str) -> bool:
    """Отправляет уведомление в Telegram"""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        return False
    
    try:
        proxies = get_proxies()
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': telegram_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, proxies=proxies, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")
        return False

def add_learning_goal(student_id: int, goal_text: str) -> Dict[str, Any]:
    """Добавляет новую цель обучения и генерирует слова"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    goal_escaped = goal_text.replace("'", "''")
    
    cur.execute(
        f"INSERT INTO {SCHEMA}.learning_goals (student_id, goal_text) "
        f"VALUES ({student_id}, '{goal_escaped}') "
        f"RETURNING id, goal_text, created_at"
    )
    row = cur.fetchone()
    goal_id = row[0]
    
    cur.execute(f"SELECT language_level FROM {SCHEMA}.users WHERE telegram_id = {student_id}")
    level_row = cur.fetchone()
    language_level = level_row[0] if level_row else 'A1'
    
    cur.close()
    conn.close()
    
    result = generate_personalized_words(student_id, goal_text, language_level, count=7)
    
    if result.get('success') and result.get('words'):
        words_list = [f"• <b>{w['english']}</b> — {w['russian']}" for w in result['words']]
        words_text = '\n'.join(words_list)
        
        notification = f"""🎯 <b>Новая цель добавлена!</b>

<i>{goal_text}</i>

📚 Добавлено {result['count']} новых слов для изучения:

{words_text}

Начни практиковаться прямо сейчас! 💪"""
        
        send_telegram_notification(student_id, notification)
        
        return {
            'success': True,
            'goal_id': goal_id,
            'words_added': result['count']
        }
    
    return {'success': False, 'error': result.get('error', 'Failed to generate words')}

def get_learning_goals(student_id: int) -> List[Dict[str, Any]]:
    """Получает все активные цели студента"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT id, goal_text, created_at, is_active "
        f"FROM {SCHEMA}.learning_goals "
        f"WHERE student_id = {student_id} AND is_active = TRUE "
        f"ORDER BY created_at DESC"
    )
    
    goals = []
    for row in cur.fetchall():
        goals.append({
            'id': row[0],
            'goal_text': row[1],
            'created_at': row[2].isoformat() if row[2] else None,
            'is_active': row[3]
        })
    
    cur.close()
    conn.close()
    return goals

def deactivate_learning_goal(goal_id: int) -> bool:
    """Деактивирует цель обучения"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"UPDATE {SCHEMA}.learning_goals SET is_active = FALSE "
        f"WHERE id = {goal_id}"
    )
    
    cur.close()
    conn.close()
    return True

def get_user_info(telegram_id: int) -> Dict[str, Any]:
    """Получает информацию о пользователе (только студент)"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"SELECT telegram_id, username, first_name, last_name, language_level, preferred_topics, timezone, photo_url, learning_goal, learning_goal_details FROM {SCHEMA}.users WHERE telegram_id = {telegram_id}")
    row = cur.fetchone()
    
    cur.close()
    conn.close()
    
    if row:
        return {
            'telegram_id': row[0],
            'username': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'language_level': row[4] or 'A1',
            'preferred_topics': row[5] if row[5] else [],
            'timezone': row[6] or 'UTC',
            'photo_url': row[7],
            'learning_goal': row[8],
            'learning_goal_details': row[9]
        }
    return None

def create_or_update_user(telegram_id: int, username: str = '', first_name: str = '', last_name: str = '') -> bool:
    """Создает или обновляет пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    username_escaped = username.replace("'", "''") if username else ''
    first_name_escaped = first_name.replace("'", "''") if first_name else ''
    last_name_escaped = last_name.replace("'", "''") if last_name else ''
    
    cur.execute(f"SELECT telegram_id FROM {SCHEMA}.users WHERE telegram_id = {telegram_id}")
    user_exists = cur.fetchone()
    
    if not user_exists:
        cur.execute(
            f"INSERT INTO {SCHEMA}.users (telegram_id, username, first_name, last_name, role, language_level) "
            f"VALUES ({telegram_id}, '{username_escaped}', '{first_name_escaped}', '{last_name_escaped}', 'student', 'A1')"
        )
    else:
        cur.execute(f"UPDATE {SCHEMA}.users SET username = '{username_escaped}', first_name = '{first_name_escaped}', last_name = '{last_name_escaped}', updated_at = CURRENT_TIMESTAMP WHERE telegram_id = {telegram_id}")
    
    cur.close()
    conn.close()
    return True

def get_all_students() -> List[Dict[str, Any]]:
    """Получает список всех студентов с информацией о подписках"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT telegram_id, username, first_name, last_name, created_at, "
        f"language_level, preferred_topics, timezone, photo_url, "
        f"subscription_status, subscription_expires_at "
        f"FROM {SCHEMA}.users "
        f"WHERE role = 'student' "
        f"ORDER BY created_at DESC"
    )
    
    students = []
    for row in cur.fetchall():
        telegram_id = row[0]
        subscription_status = row[9]
        subscription_expires_at = row[10]
        
        # Определяем активна ли базовая подписка
        subscription_active = subscription_status == 'active'
        
        # Проверяем голосовую подписку в subscription_payments
        cur.execute(
            f"SELECT expires_at FROM {SCHEMA}.subscription_payments "
            f"WHERE telegram_id = {telegram_id} AND period = 'premium' "
            f"AND status = 'paid' AND expires_at > CURRENT_TIMESTAMP "
            f"ORDER BY expires_at DESC LIMIT 1"
        )
        voice_sub_row = cur.fetchone()
        voice_subscription_active = voice_sub_row is not None
        voice_subscription_expires_at = voice_sub_row[0] if voice_sub_row else None
        
        students.append({
            'telegram_id': telegram_id,
            'username': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'created_at': row[4].isoformat() if row[4] else None,
            'language_level': row[5] or 'A1',
            'preferred_topics': row[6] if row[6] else [],
            'timezone': row[7] or 'UTC',
            'photo_url': row[8],
            'subscription_active': subscription_active,
            'subscription_expires_at': subscription_expires_at.isoformat() if subscription_expires_at else None,
            'voice_subscription_active': voice_subscription_active,
            'voice_subscription_expires_at': voice_subscription_expires_at.isoformat() if voice_subscription_expires_at else None
        })
    
    cur.close()
    conn.close()
    return students

def get_all_categories() -> List[Dict[str, Any]]:
    """Получает список всех категорий"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT id, name, description, created_at FROM {SCHEMA}.categories ORDER BY name"
    )
    
    categories = []
    for row in cur.fetchall():
        categories.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'created_at': row[3].isoformat() if row[3] else None
        })
    
    cur.close()
    conn.close()
    return categories

def create_category(name: str, description: str = None) -> Dict[str, Any]:
    """Создает новую категорию"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    name_escaped = name.replace("'", "''")
    if description is None:
        desc_value = 'NULL'
    else:
        desc_escaped = description.replace("'", "''")
        desc_value = f"'{desc_escaped}'"
    
    cur.execute(
        f"INSERT INTO {SCHEMA}.categories (name, description) "
        f"VALUES ('{name_escaped}', {desc_value}) "
        f"RETURNING id, name, description, created_at"
    )
    
    row = cur.fetchone()
    result = {
        'id': row[0],
        'name': row[1],
        'description': row[2],
        'created_at': row[3].isoformat() if row[3] else None
    }
    
    cur.close()
    conn.close()
    return result

def delete_category(category_id: int) -> bool:
    """Удаляет категорию"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"DELETE FROM {SCHEMA}.categories WHERE id = {category_id}")
    
    cur.close()
    conn.close()
    return True

def delete_word(word_id: int) -> bool:
    """Удаляет слово из БД"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"DELETE FROM {SCHEMA}.words WHERE id = {word_id}")
    
    cur.close()
    conn.close()
    return True

def get_pricing_plans() -> List[Dict[str, Any]]:
    """Получает тарифные планы из БД"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT plan_key, name, description, price_rub, duration_days "
        f"FROM {SCHEMA}.pricing_plans ORDER BY price_rub"
    )
    
    plans = []
    for row in cur.fetchall():
        plans.append({
            'key': row[0],
            'name': row[1],
            'description': row[2],
            'price_rub': row[3],
            'duration_days': row[4]
        })
    
    cur.close()
    conn.close()
    return plans

def update_pricing_plan(plan: Dict[str, Any]) -> bool:
    """Обновляет тарифный план в БД"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        plan_key = plan['key'].replace("'", "''")
        name = plan['name'].replace("'", "''")
        description = plan['description'].replace("'", "''")
        price_rub = int(plan['price_rub'])
        price_kop = price_rub * 100
        duration_days = int(plan['duration_days'])
        
        cur.execute(
            f"UPDATE {SCHEMA}.pricing_plans SET "
            f"name = '{name}', "
            f"description = '{description}', "
            f"price_rub = {price_rub}, "
            f"price_kop = {price_kop}, "
            f"duration_days = {duration_days}, "
            f"updated_at = CURRENT_TIMESTAMP "
            f"WHERE plan_key = '{plan_key}'"
        )
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating pricing plan: {e}")
        import traceback
        traceback.print_exc()
        cur.close()
        conn.close()
        return False

def get_all_words() -> List[Dict[str, Any]]:
    """Получает список всех слов"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT id, category_id, english_text, russian_translation, created_at "
        f"FROM {SCHEMA}.words "
        f"ORDER BY english_text"
    )
    
    words = []
    for row in cur.fetchall():
        words.append({
            'id': row[0],
            'category_id': row[1],
            'english_text': row[2],
            'russian_translation': row[3],
            'created_at': row[4].isoformat() if row[4] else None
        })
    
    cur.close()
    conn.close()
    return words

def search_words(search_query: str = None, category_id: int = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """Поиск слов с фильтрацией"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    where_clauses = []
    
    if search_query:
        query_escaped = search_query.replace("'", "''")
        where_clauses.append(f"(english_text ILIKE '%{query_escaped}%' OR russian_translation ILIKE '%{query_escaped}%')")
    
    if category_id is not None:
        where_clauses.append(f"category_id = {category_id}")
    
    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    
    cur.execute(
        f"SELECT id, category_id, english_text, russian_translation, created_at "
        f"FROM {SCHEMA}.words "
        f"{where_sql} "
        f"ORDER BY english_text "
        f"LIMIT {limit} OFFSET {offset}"
    )
    
    words = []
    for row in cur.fetchall():
        words.append({
            'id': row[0],
            'category_id': row[1],
            'english_text': row[2],
            'russian_translation': row[3],
            'created_at': row[4].isoformat() if row[4] else None
        })
    
    cur.close()
    conn.close()
    return words

def create_word(english_text: str, russian_translation: str, category_id: int = None) -> Dict[str, Any]:
    """Создает новое слово"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    english_escaped = english_text.replace("'", "''")
    russian_escaped = russian_translation.replace("'", "''")
    category_value = category_id if category_id is not None else 'NULL'
    
    cur.execute(
        f"INSERT INTO {SCHEMA}.words (english_text, russian_translation, category_id) "
        f"VALUES ('{english_escaped}', '{russian_escaped}', {category_value}) "
        f"RETURNING id, category_id, english_text, russian_translation, created_at"
    )
    
    row = cur.fetchone()
    result = {
        'id': row[0],
        'category_id': row[1],
        'english_text': row[2],
        'russian_translation': row[3],
        'created_at': row[4].isoformat() if row[4] else None
    }
    
    cur.close()
    conn.close()
    return result

def delete_word(word_id: int) -> bool:
    """Удаляет слово"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"DELETE FROM {SCHEMA}.words WHERE id = {word_id}")
    
    cur.close()
    conn.close()
    return True

def assign_words_to_student(student_id: int, word_ids: List[int]) -> bool:
    """Назначает слова студенту для изучения"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    for word_id in word_ids:
        cur.execute(
            f"SELECT id FROM {SCHEMA}.student_words WHERE student_id = {student_id} AND word_id = {word_id}"
        )
        if not cur.fetchone():
            cur.execute(
                f"INSERT INTO {SCHEMA}.student_words (student_id, word_id) "
                f"VALUES ({student_id}, {word_id})"
            )
    
    cur.close()
    conn.close()
    return True

def auto_assign_basic_words(student_id: int, count: int = 15) -> Dict[str, Any]:
    """Автоматически назначает базовые слова студенту"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Получаем базовые слова (id < 30 - простые слова)
    cur.execute(
        f"SELECT id FROM {SCHEMA}.words "
        f"WHERE id NOT IN (SELECT word_id FROM {SCHEMA}.student_words WHERE student_id = {student_id}) "
        f"AND id < 30 "
        f"ORDER BY id LIMIT {count}"
    )
    
    word_ids = [row[0] for row in cur.fetchall()]
    
    if word_ids:
        for word_id in word_ids:
            cur.execute(
                f"INSERT INTO {SCHEMA}.student_words (student_id, word_id) "
                f"VALUES ({student_id}, {word_id})"
            )
    
    cur.close()
    conn.close()
    
    return {'success': True, 'count': len(word_ids), 'word_ids': word_ids}

def get_student_words(student_id: int) -> List[Dict[str, Any]]:
    """Получает все слова студента с прогрессом"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT sw.id, sw.word_id, w.english_text, w.russian_translation, w.category_id, "
        f"sw.assigned_at, sw.status, "
        f"COALESCE(wp.mastery_score, 0) as mastery_score, "
        f"COALESCE(wp.attempts, 0) as attempts, "
        f"COALESCE(wp.correct_uses, 0) as correct_uses, "
        f"COALESCE(wp.status, 'new') as progress_status, "
        f"COALESCE(wp.dialog_uses, 0) as dialog_uses, "
        f"COALESCE(wp.needs_check, false) as needs_check "
        f"FROM {SCHEMA}.student_words sw "
        f"JOIN {SCHEMA}.words w ON w.id = sw.word_id "
        f"LEFT JOIN {SCHEMA}.word_progress wp ON wp.student_id = sw.student_id AND wp.word_id = sw.word_id "
        f"WHERE sw.student_id = {student_id} "
        f"ORDER BY sw.assigned_at DESC"
    )
    
    words = []
    for row in cur.fetchall():
        words.append({
            'id': row[0],
            'word_id': row[1],
            'english_text': row[2],
            'russian_translation': row[3],
            'category_id': row[4],
            'assigned_at': row[5].isoformat() if row[5] else None,
            'status': row[6],
            'mastery_score': float(row[7]) if row[7] is not None else 0.0,
            'attempts': row[8],
            'correct_uses': row[9],
            'progress_status': row[10],
            'dialog_uses': row[11],
            'needs_check': row[12]
        })
    
    cur.close()
    conn.close()
    return words

def delete_student_word(student_word_id: int) -> bool:
    """Удаляет слово из списка студента"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Сначала получаем student_id и word_id
        cur.execute(
            f"SELECT student_id, word_id FROM {SCHEMA}.student_words WHERE id = {student_word_id}"
        )
        row = cur.fetchone()
        
        if not row:
            print(f"[WARNING] Student word {student_word_id} not found")
            cur.close()
            conn.close()
            return False
        
        student_id, word_id = row[0], row[1]
        
        # Удаляем прогресс по этому слову
        cur.execute(
            f"DELETE FROM {SCHEMA}.word_progress WHERE student_id = {student_id} AND word_id = {word_id}"
        )
        
        # Удаляем связь студент-слово
        cur.execute(
            f"DELETE FROM {SCHEMA}.student_words WHERE id = {student_word_id}"
        )
        
        print(f"[INFO] Deleted student word: student={student_id}, word={word_id}")
        
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to delete student word: {e}")
        cur.close()
        conn.close()
        return False

def get_student_progress_stats(student_id: int) -> Dict[str, Any]:
    """Получает статистику прогресса студента"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT "
        f"COUNT(*) as total_words, "
        f"COUNT(CASE WHEN COALESCE(wp.status, 'new') = 'new' THEN 1 END) as new, "
        f"COUNT(CASE WHEN wp.status = 'learning' THEN 1 END) as learning, "
        f"COUNT(CASE WHEN wp.status = 'learned' THEN 1 END) as learned, "
        f"COUNT(CASE WHEN wp.status = 'mastered' THEN 1 END) as mastered, "
        f"COALESCE(AVG(wp.mastery_score), 0) as average_mastery "
        f"FROM {SCHEMA}.student_words sw "
        f"LEFT JOIN {SCHEMA}.word_progress wp ON wp.student_id = sw.student_id AND wp.word_id = sw.word_id "
        f"WHERE sw.student_id = {student_id}"
    )
    
    row = cur.fetchone()
    
    cur.execute(
        f"SELECT practice_date, messages_sent, words_practiced, errors_corrected "
        f"FROM {SCHEMA}.daily_stats "
        f"WHERE student_id = {student_id} "
        f"ORDER BY practice_date DESC LIMIT 7"
    )
    
    daily_stats = []
    for stat_row in cur.fetchall():
        daily_stats.append({
            'date': stat_row[0].isoformat() if stat_row[0] else None,
            'messages': stat_row[1] or 0,
            'words': stat_row[2] or 0,
            'errors': stat_row[3] or 0
        })
    
    cur.execute(
        f"SELECT a.code, a.title_en, a.title_ru, a.description_en, a.description_ru, a.emoji, a.points, ua.unlocked_at "
        f"FROM {SCHEMA}.user_achievements ua "
        f"JOIN {SCHEMA}.achievements a ON a.code = ua.achievement_code "
        f"WHERE ua.user_id = {student_id} "
        f"ORDER BY ua.unlocked_at DESC"
    )
    
    achievements = []
    total_points = 0
    for ach_row in cur.fetchall():
        achievements.append({
            'code': ach_row[0],
            'title_en': ach_row[1],
            'title_ru': ach_row[2],
            'emoji': ach_row[5],
            'points': ach_row[6],
            'unlocked_at': ach_row[7].isoformat() if ach_row[7] else None
        })
        total_points += ach_row[6] or 0
    
    cur.close()
    conn.close()
    
    return {
        'total_words': row[0],
        'new': row[1],
        'learning': row[2],
        'learned': row[3],
        'mastered': row[4],
        'average_mastery': float(row[5]) if row[5] else 0.0,
        'daily_stats': daily_stats,
        'achievements': achievements,
        'total_points': total_points
    }

def update_student_settings(telegram_id: int, language_level: str = None, preferred_topics: List[Dict] = None, timezone: str = None, learning_goal: str = None, learning_goal_details: str = None) -> bool:
    """Обновляет настройки студента"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    updates = []
    
    if language_level is not None:
        level_escaped = language_level.replace("'", "''")
        updates.append(f"language_level = '{level_escaped}'")
    
    if preferred_topics is not None:
        topics_json = json.dumps(preferred_topics).replace("'", "''")
        updates.append(f"preferred_topics = '{topics_json}'::jsonb")
    
    if timezone is not None:
        tz_escaped = timezone.replace("'", "''")
        updates.append(f"timezone = '{tz_escaped}'")
    
    if learning_goal is not None:
        if learning_goal:
            goal_escaped = learning_goal.replace("'", "''")
            updates.append(f"learning_goal = '{goal_escaped}'")
        else:
            updates.append("learning_goal = NULL")
    
    if learning_goal_details is not None:
        if learning_goal_details:
            details_escaped = learning_goal_details.replace("'", "''")
            updates.append(f"learning_goal_details = '{details_escaped}'")
        else:
            updates.append("learning_goal_details = NULL")
    
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        update_sql = ", ".join(updates)
        cur.execute(f"UPDATE {SCHEMA}.users SET {update_sql} WHERE telegram_id = {telegram_id}")
    
    cur.close()
    conn.close()
    return True

def update_word_progress(student_id: int, word_id: int, is_correct: bool) -> Dict[str, Any]:
    """Обновляет прогресс изучения слова"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    if is_correct:
        cur.execute(
            f"UPDATE {SCHEMA}.word_progress SET "
            f"dialog_uses = dialog_uses + 1, "
            f"last_practiced = CURRENT_TIMESTAMP, "
            f"status = CASE "
            f"  WHEN dialog_uses + 1 >= 20 THEN 'mastered' "
            f"  WHEN dialog_uses + 1 >= 10 THEN 'learned' "
            f"  WHEN dialog_uses + 1 >= 5 THEN 'learning' "
            f"  ELSE 'new' "
            f"END, "
            f"mastery_score = LEAST(100, mastery_score + 5), "
            f"updated_at = CURRENT_TIMESTAMP "
            f"WHERE student_id = {student_id} AND word_id = {word_id}"
        )
    else:
        cur.execute(
            f"UPDATE {SCHEMA}.word_progress SET "
            f"mastery_score = GREATEST(0, mastery_score - 3), "
            f"updated_at = CURRENT_TIMESTAMP "
            f"WHERE student_id = {student_id} AND word_id = {word_id}"
        )
    
    cur.close()
    conn.close()
    return {'success': True}

def get_all_proxies() -> List[Dict[str, Any]]:
    """Получает все прокси со статистикой"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT id, host, port, username, password, is_active, created_at, "
        f"total_requests, successful_requests, failed_requests, "
        f"last_used_at, last_error, last_error_at "
        f"FROM {SCHEMA}.proxies ORDER BY created_at DESC"
    )
    
    proxies = []
    for row in cur.fetchall():
        proxies.append({
            'id': row[0],
            'host': row[1],
            'port': row[2],
            'username': row[3],
            'password': row[4],
            'is_active': row[5],
            'created_at': row[6].isoformat() if row[6] else None,
            'total_requests': row[7] or 0,
            'successful_requests': row[8] or 0,
            'failed_requests': row[9] or 0,
            'last_used_at': row[10].isoformat() if row[10] else None,
            'last_error': row[11],
            'last_error_at': row[12].isoformat() if row[12] else None
        })
    
    cur.close()
    conn.close()
    return proxies

def get_active_proxy() -> Dict[str, Any]:
    """Получает случайный активный прокси для бота"""
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
        return None
    
    proxy = {
        'id': row[0],
        'host': row[1],
        'port': row[2],
        'username': row[3],
        'password': row[4]
    }
    
    if proxy['username'] and proxy['password']:
        proxy['url'] = f"{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
    else:
        proxy['url'] = f"{proxy['host']}:{proxy['port']}"
    
    return proxy

def add_proxy(host: str, port: int, username: str = None, password: str = None) -> Dict[str, Any]:
    """Добавляет новый прокси"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    host_escaped = host.replace("'", "''")
    
    if username:
        username_escaped = username.replace("'", "''")
        username_value = f"'{username_escaped}'"
    else:
        username_value = 'NULL'
    
    if password:
        password_escaped = password.replace("'", "''")
        password_value = f"'{password_escaped}'"
    else:
        password_value = 'NULL'
    
    cur.execute(
        f"INSERT INTO {SCHEMA}.proxies (host, port, username, password) "
        f"VALUES ('{host_escaped}', {port}, {username_value}, {password_value}) "
        f"ON CONFLICT (host, port) DO UPDATE SET "
        f"username = {username_value}, password = {password_value} "
        f"RETURNING id, host, port, username, is_active, created_at"
    )
    
    row = cur.fetchone()
    result = {
        'id': row[0],
        'host': row[1],
        'port': row[2],
        'username': row[3],
        'is_active': row[4],
        'created_at': row[5].isoformat() if row[5] else None
    }
    
    cur.close()
    conn.close()
    return result

def toggle_proxy(proxy_id: int, is_active: bool) -> bool:
    """Включает/выключает прокси"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"UPDATE {SCHEMA}.proxies SET is_active = {is_active} WHERE id = {proxy_id}"
    )
    
    cur.close()
    conn.close()
    return True

def delete_proxy(proxy_id: int) -> bool:
    """Удаляет прокси"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"DELETE FROM {SCHEMA}.proxies WHERE id = {proxy_id}")
    
    cur.close()
    conn.close()
    return True

def generate_speech(text: str, lang: str = 'en-US') -> Dict[str, Any]:
    """Генерирует озвучку через Yandex SpeechKit с кэшированием в S3"""
    if not text:
        return {'error': 'Text is required'}
    
    # Проверяем кэш в S3
    file_key = f"audio/{lang}/{hash(text)}.ogg"
    
    try:
        s3 = boto3.client('s3',
            endpoint_url='https://bucket.poehali.dev',
            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
        )
        
        # Проверяем существование файла
        try:
            s3.head_object(Bucket='files', Key=file_key)
            cdn_url = f"https://cdn.poehali.dev/projects/{os.environ['AWS_ACCESS_KEY_ID']}/bucket/{file_key}"
            return {'url': cdn_url, 'cached': True}
        except:
            pass
        
        # Генерируем новую озвучку
        api_key = os.environ.get('YANDEX_CLOUD_API_KEY')
        folder_id = os.environ.get('YANDEX_CLOUD_FOLDER_ID')
        
        if not api_key or not folder_id:
            return {'error': 'Yandex Cloud credentials not configured'}
        
        url = 'https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize'
        headers = {'Authorization': f'Api-Key {api_key}'}
        
        data = {
            'text': text,
            'lang': lang,
            'voice': 'alena',
            'format': 'oggopus',
            'speed': '1.0',
            'folderId': folder_id
        }
        
        response = requests.post(url, headers=headers, data=data, timeout=30)
        response.raise_for_status()
        
        # Сохраняем в S3
        s3.put_object(
            Bucket='files',
            Key=file_key,
            Body=response.content,
            ContentType='audio/ogg'
        )
        
        cdn_url = f"https://cdn.poehali.dev/projects/{os.environ['AWS_ACCESS_KEY_ID']}/bucket/{file_key}"
        return {'url': cdn_url, 'cached': False}
        
    except Exception as e:
        return {'error': str(e)}

def toggle_subscription(telegram_id: int, active: bool, days: int = 30, subscription_type: str = 'basic') -> Dict[str, Any]:
    """Включает/выключает подписку студента (basic или premium)"""
    print(f"[INFO] toggle_subscription: telegram_id={telegram_id}, active={active}, days={days}, type={subscription_type}")
    conn = get_db_connection()
    cur = conn.cursor()
    
    if subscription_type == 'premium':
        # Управление голосовой подпиской
        if active:
            # Активируем голосовую подписку в subscription_payments
            print(f"[INFO] Activating premium subscription for {telegram_id}")
            cur.execute(
                f"INSERT INTO {SCHEMA}.subscription_payments "
                f"(telegram_id, period, status, expires_at, payment_method, amount, amount_kop) "
                f"VALUES ({telegram_id}, 'premium', 'paid', CURRENT_TIMESTAMP + INTERVAL '{days} days', 'admin', 0, 0) "
                f"ON CONFLICT (telegram_id, period) DO UPDATE SET "
                f"status = 'paid', "
                f"expires_at = CURRENT_TIMESTAMP + INTERVAL '{days} days', "
                f"updated_at = CURRENT_TIMESTAMP"
            )
            print(f"[SUCCESS] Premium subscription activated for {telegram_id}")
        else:
            # Деактивируем голосовую подписку
            print(f"[INFO] Deactivating premium subscription for {telegram_id}")
            cur.execute(
                f"DELETE FROM {SCHEMA}.subscription_payments "
                f"WHERE telegram_id = {telegram_id} AND period = 'premium'"
            )
            print(f"[SUCCESS] Premium subscription deactivated for {telegram_id}")
    else:
        # Управление базовой подпиской (старая логика + subscription_payments)
        if active:
            # Активируем базовую подписку в users (старая схема)
            print(f"[INFO] Activating basic subscription for {telegram_id}")
            cur.execute(
                f"UPDATE {SCHEMA}.users SET "
                f"subscription_status = 'active', "
                f"subscription_expires_at = CURRENT_TIMESTAMP + INTERVAL '{days} days' "
                f"WHERE telegram_id = {telegram_id}"
            )
            # И в subscription_payments (новая схема)
            cur.execute(
                f"INSERT INTO {SCHEMA}.subscription_payments "
                f"(telegram_id, period, status, expires_at, payment_method, amount, amount_kop) "
                f"VALUES ({telegram_id}, 'basic', 'paid', CURRENT_TIMESTAMP + INTERVAL '{days} days', 'admin', 0, 0) "
                f"ON CONFLICT (telegram_id, period) DO UPDATE SET "
                f"status = 'paid', "
                f"expires_at = CURRENT_TIMESTAMP + INTERVAL '{days} days', "
                f"updated_at = CURRENT_TIMESTAMP"
            )
            print(f"[SUCCESS] Basic subscription activated for {telegram_id}")
        else:
            # Деактивируем базовую подписку
            print(f"[INFO] Deactivating basic subscription for {telegram_id}")
            cur.execute(
                f"UPDATE {SCHEMA}.users SET "
                f"subscription_status = 'inactive', "
                f"subscription_expires_at = NULL "
                f"WHERE telegram_id = {telegram_id}"
            )
            cur.execute(
                f"DELETE FROM {SCHEMA}.subscription_payments "
                f"WHERE telegram_id = {telegram_id} AND period = 'basic'"
            )
            print(f"[SUCCESS] Basic subscription deactivated for {telegram_id}")
    
    cur.close()
    conn.close()
    return {'success': True}

def reset_proxy_stats(proxy_id: int) -> bool:
    """Сбрасывает статистику прокси"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"UPDATE {SCHEMA}.proxies SET "
        f"total_requests = 0, "
        f"successful_requests = 0, "
        f"failed_requests = 0, "
        f"last_used_at = NULL, "
        f"last_error = NULL, "
        f"last_error_at = NULL "
        f"WHERE id = {proxy_id}"
    )
    
    cur.close()
    conn.close()
    return True

def get_all_blog_posts(published_only: bool = False) -> List[Dict[str, Any]]:
    """Получает все статьи блога"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = f"SELECT id, title, slug, excerpt, content, cover_image, author, published, views_count, reading_time, created_at, updated_at FROM {SCHEMA}.blog_posts"
    if published_only:
        query += " WHERE published = true"
    query += " ORDER BY created_at DESC"
    
    cur.execute(query)
    
    posts = []
    for row in cur.fetchall():
        posts.append({
            'id': row[0],
            'title': row[1],
            'slug': row[2],
            'excerpt': row[3],
            'content': row[4],
            'cover_image': row[5],
            'author': row[6],
            'published': row[7],
            'views_count': row[8],
            'reading_time': row[9],
            'created_at': row[10].isoformat() if row[10] else None,
            'updated_at': row[11].isoformat() if row[11] else None
        })
    
    cur.close()
    conn.close()
    return posts

def get_blog_post_by_slug(slug: str) -> Dict[str, Any]:
    """Получает статью по slug"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    slug_escaped = slug.replace("'", "''")
    
    cur.execute(
        f"SELECT id, title, slug, excerpt, content, cover_image, author, published, views_count, reading_time, created_at, updated_at "
        f"FROM {SCHEMA}.blog_posts WHERE slug = '{slug_escaped}'"
    )
    
    row = cur.fetchone()
    
    if row:
        # Увеличиваем счетчик просмотров
        cur.execute(f"UPDATE {SCHEMA}.blog_posts SET views_count = views_count + 1 WHERE slug = '{slug_escaped}'")
        
        post = {
            'id': row[0],
            'title': row[1],
            'slug': row[2],
            'excerpt': row[3],
            'content': row[4],
            'cover_image': row[5],
            'author': row[6],
            'published': row[7],
            'views_count': row[8] + 1,
            'reading_time': row[9],
            'created_at': row[10].isoformat() if row[10] else None,
            'updated_at': row[11].isoformat() if row[11] else None
        }
        
        cur.close()
        conn.close()
        return post
    
    cur.close()
    conn.close()
    return None

def create_blog_post(title: str, slug: str, excerpt: str, content: str, cover_image: str, author: str, published: bool, reading_time: int) -> Dict[str, Any]:
    """Создает новую статью блога"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    title_escaped = title.replace("'", "''")
    slug_escaped = slug.replace("'", "''")
    excerpt_escaped = excerpt.replace("'", "''") if excerpt else ''
    content_escaped = content.replace("'", "''")
    cover_image_escaped = cover_image.replace("'", "''") if cover_image else ''
    author_escaped = author.replace("'", "''")
    
    cur.execute(
        f"INSERT INTO {SCHEMA}.blog_posts (title, slug, excerpt, content, cover_image, author, published, reading_time) "
        f"VALUES ('{title_escaped}', '{slug_escaped}', '{excerpt_escaped}', '{content_escaped}', '{cover_image_escaped}', '{author_escaped}', {published}, {reading_time}) "
        f"RETURNING id, title, slug, excerpt, content, cover_image, author, published, views_count, reading_time, created_at, updated_at"
    )
    
    row = cur.fetchone()
    
    post = {
        'id': row[0],
        'title': row[1],
        'slug': row[2],
        'excerpt': row[3],
        'content': row[4],
        'cover_image': row[5],
        'author': row[6],
        'published': row[7],
        'views_count': row[8],
        'reading_time': row[9],
        'created_at': row[10].isoformat() if row[10] else None,
        'updated_at': row[11].isoformat() if row[11] else None
    }
    
    cur.close()
    conn.close()
    return post

def update_blog_post(post_id: int, title: str, slug: str, excerpt: str, content: str, cover_image: str, author: str, published: bool, reading_time: int) -> Dict[str, Any]:
    """Обновляет статью блога"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    title_escaped = title.replace("'", "''")
    slug_escaped = slug.replace("'", "''")
    excerpt_escaped = excerpt.replace("'", "''") if excerpt else ''
    content_escaped = content.replace("'", "''")
    cover_image_escaped = cover_image.replace("'", "''") if cover_image else ''
    author_escaped = author.replace("'", "''")
    
    cur.execute(
        f"UPDATE {SCHEMA}.blog_posts SET "
        f"title = '{title_escaped}', "
        f"slug = '{slug_escaped}', "
        f"excerpt = '{excerpt_escaped}', "
        f"content = '{content_escaped}', "
        f"cover_image = '{cover_image_escaped}', "
        f"author = '{author_escaped}', "
        f"published = {published}, "
        f"reading_time = {reading_time}, "
        f"updated_at = CURRENT_TIMESTAMP "
        f"WHERE id = {post_id} "
        f"RETURNING id, title, slug, excerpt, content, cover_image, author, published, views_count, reading_time, created_at, updated_at"
    )
    
    row = cur.fetchone()
    
    if row:
        post = {
            'id': row[0],
            'title': row[1],
            'slug': row[2],
            'excerpt': row[3],
            'content': row[4],
            'cover_image': row[5],
            'author': row[6],
            'published': row[7],
            'views_count': row[8],
            'reading_time': row[9],
            'created_at': row[10].isoformat() if row[10] else None,
            'updated_at': row[11].isoformat() if row[11] else None
        }
        
        cur.close()
        conn.close()
        return post
    
    cur.close()
    conn.close()
    return None

def delete_blog_post(post_id: int) -> bool:
    """Удаляет статью блога"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"DELETE FROM {SCHEMA}.blog_posts WHERE id = {post_id}")
    
    cur.close()
    conn.close()
    return True

def delete_user(telegram_id: int) -> bool:
    """Полностью удаляет пользователя и все его данные"""
    print(f"🗑️ Starting deletion for user {telegram_id}")
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Удаляем сообщения из conversations
        try:
            print(f"🗑️ Step 1: Getting conversations...")
            cur.execute(f"SELECT id FROM {SCHEMA}.conversations WHERE user_id = {telegram_id}")
            conversation_ids = [row[0] for row in cur.fetchall()]
            print(f"🗑️ Found {len(conversation_ids)} conversations")
            
            if conversation_ids:
                ids_str = ','.join(str(cid) for cid in conversation_ids)
                cur.execute(f"DELETE FROM {SCHEMA}.messages WHERE conversation_id IN ({ids_str})")
                print(f"🗑️ Deleted messages from {len(conversation_ids)} conversations")
                cur.execute(f"DELETE FROM {SCHEMA}.conversations WHERE user_id = {telegram_id}")
                print(f"🗑️ Deleted conversations")
        except Exception as e:
            print(f"❌ Error in conversations: {e}")
            raise
        
        # Удаляем все связанные данные
        try:
            print(f"🗑️ Step 2: Deleting word_progress...")
            cur.execute(f"DELETE FROM {SCHEMA}.word_progress WHERE student_id = {telegram_id}")
            print(f"🗑️ Deleted word_progress")
        except Exception as e:
            print(f"❌ Error in word_progress: {e}")
            raise
        
        try:
            print(f"🗑️ Step 3: Deleting student_words...")
            cur.execute(f"DELETE FROM {SCHEMA}.student_words WHERE student_id = {telegram_id}")
            print(f"🗑️ Deleted student_words")
        except Exception as e:
            print(f"❌ Error in student_words: {e}")
            raise
        
        try:
            print(f"🗑️ Step 4: Deleting learning_goals...")
            cur.execute(f"DELETE FROM {SCHEMA}.learning_goals WHERE student_id = {telegram_id}")
            print(f"🗑️ Deleted learning_goals")
        except Exception as e:
            print(f"❌ Error in learning_goals: {e}")
            raise
        
        try:
            print(f"🗑️ Step 5: Deleting subscription_payments...")
            cur.execute(f"DELETE FROM {SCHEMA}.subscription_payments WHERE telegram_id = {telegram_id}")
            print(f"🗑️ Deleted subscription_payments")
        except Exception as e:
            print(f"❌ Error in subscription_payments: {e}")
            raise
        
        try:
            print(f"🗑️ Step 6: Deleting user_achievements...")
            cur.execute(f"DELETE FROM {SCHEMA}.user_achievements WHERE student_id = {telegram_id}")
            print(f"🗑️ Deleted user_achievements")
        except Exception as e:
            print(f"❌ Error in user_achievements: {e}")
            raise
        
        try:
            print(f"🗑️ Step 7: Deleting from users...")
            cur.execute(f"DELETE FROM {SCHEMA}.users WHERE telegram_id = {telegram_id}")
            print(f"✅ Deleted user {telegram_id} from users table")
        except Exception as e:
            print(f"❌ Error in users: {e}")
            raise
        
        cur.close()
        conn.close()
        print(f"✅ User {telegram_id} deleted successfully")
        return True
    except Exception as e:
        print(f"❌ Error deleting user {telegram_id}: {e}")
        import traceback
        traceback.print_exc()
        cur.close()
        conn.close()
        raise

def log_user_activity(telegram_id: int, event_type: str, event_data: Dict = None, user_state: Dict = None, error_message: str = None):
    """Логирует активность пользователя для отладки"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        event_data_json = json.dumps(event_data) if event_data else 'null'
        user_state_json = json.dumps(user_state) if user_state else 'null'
        error_escaped = error_message.replace("'", "''") if error_message else 'null'
        error_value = f"'{error_escaped}'" if error_message else 'null'
        
        cur.execute(
            f"INSERT INTO {SCHEMA}.user_activity_logs "
            f"(telegram_id, event_type, event_data, user_state, error_message) "
            f"VALUES ({telegram_id}, '{event_type}', '{event_data_json}'::jsonb, '{user_state_json}'::jsonb, {error_value})"
        )
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] Failed to log user activity: {e}")

def get_user_activity_logs(telegram_id: int, limit: int = 100) -> List[Dict[str, Any]]:
    """Получает логи активности пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT id, telegram_id, event_type, event_data, user_state, error_message, created_at "
        f"FROM {SCHEMA}.user_activity_logs "
        f"WHERE telegram_id = {telegram_id} "
        f"ORDER BY created_at DESC LIMIT {limit}"
    )
    
    logs = []
    for row in cur.fetchall():
        logs.append({
            'id': row[0],
            'telegram_id': row[1],
            'event_type': row[2],
            'event_data': row[3],
            'user_state': row[4],
            'error_message': row[5],
            'created_at': row[6].isoformat() if row[6] else None
        })
    
    cur.close()
    conn.close()
    return logs

def reset_user_onboarding(telegram_id: int) -> bool:
    """Сбрасывает онбординг пользователя - очищает conversation_mode и активирует тестовый период"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Сбрасываем состояние пользователя + активируем тестовый период на 1 день
        cur.execute(
            f"UPDATE {SCHEMA}.users SET "
            f"conversation_mode = NULL, "
            f"learning_mode = 'standard', "
            f"learning_goal = NULL, "
            f"urgent_goals = NULL, "
            f"subscription_status = 'active', "
            f"subscription_expires_at = CURRENT_TIMESTAMP + INTERVAL '1 day' "
            f"WHERE telegram_id = {telegram_id}"
        )
        
        # Логируем событие
        log_user_activity(
            telegram_id,
            'onboarding_reset',
            {'reset_by': 'admin'},
            None,
            None
        )
        
        cur.close()
        conn.close()
        
        print(f"[INFO] Reset onboarding for user {telegram_id} with 1-day trial")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to reset onboarding for {telegram_id}: {e}")
        return False

def call_gemini_demo(user_message: str, history: list) -> str:
    """
    Вызывает Gemini API для демо-чата на лендинге
    Args:
        user_message: текущее сообщение пользователя
        history: список предыдущих сообщений [{'role': 'user'|'model', 'content': str}]
    Returns:
        str: ответ Gemini
    """
    api_key = os.environ['GEMINI_API_KEY']
    proxies = get_proxies()
    
    # System prompt для демо-чата
    system_prompt = """You are Anya, a friendly and helpful English tutor for Russian-speaking students.

Your task in this DEMO chat:
- Have a natural, friendly conversation in English
- Correct grammar and spelling mistakes gently
- Keep responses SHORT (1-3 sentences max)
- Be encouraging and supportive
- Use simple, clear English
- Add 1 emoji per message MAX

When you find a mistake:
- Show correction in this format:
  🔧 Fix:
  ❌ [wrong sentence]
  ✅ [correct sentence]
  🇷🇺 [brief explanation in Russian]

Examples:
User: "I go to shop yesterday"
You: "🔧 Fix:
❌ I go to shop yesterday
✅ I went to the shop yesterday
🇷🇺 С 'yesterday' нужно прошедшее время (went)

Nice! What did you buy? 🛍️"

Be natural, friendly, and helpful! Keep it short and conversational."""

    # Формируем содержимое для Gemini
    contents = []
    
    # Системный промпт
    contents.append({
        'role': 'user',
        'parts': [{'text': system_prompt}]
    })
    
    contents.append({
        'role': 'model',
        'parts': [{'text': 'Understood! I will be Anya, a friendly English tutor.'}]
    })
    
    # Добавляем историю
    for msg in history[-10:]:  # Последние 10 сообщений
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
    
    # Запрос к Gemini
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}'
    
    payload = {
        'contents': contents,
        'generationConfig': {
            'temperature': 0.8,
            'maxOutputTokens': 500,
            'topP': 0.95
        }
    }
    
    response = requests.post(url, json=payload, proxies=proxies, timeout=30)
    response.raise_for_status()
    
    result = response.json()
    return result['candidates'][0]['content']['parts'][0]['text']

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Главный обработчик WebApp API
    Обрабатывает запросы от Telegram WebApp для студентов
    """
    method: str = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    try:
        body_data = json.loads(event.get('body', '{}'))
        action = body_data.get('action')
        print(f"🔥 WEBAPP API: Received action={action}")
        
        if action == 'get_user':
            telegram_id = body_data.get('telegram_id')
            user = get_user_info(telegram_id)
            if not user:
                create_or_update_user(telegram_id)
                user = get_user_info(telegram_id)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'user': user}),
                'isBase64Encoded': False
            }
        
        elif action == 'get_all_students':
            students = get_all_students()
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'students': students}),
                'isBase64Encoded': False
            }
        
        elif action == 'get_financial_analytics':
            try:
                print("[INFO] Loading financial analytics...")
                analytics = get_financial_analytics()
                print(f"[SUCCESS] Analytics loaded: {analytics}")
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'success': True, 'analytics': analytics}),
                    'isBase64Encoded': False
                }
            except Exception as e:
                print(f"[ERROR] Failed to get financial analytics: {e}")
                import traceback
                traceback.print_exc()
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'success': False, 'error': str(e)}),
                    'isBase64Encoded': False
                }
        
        elif action == 'get_categories':
            categories = get_all_categories()
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'categories': categories}),
                'isBase64Encoded': False
            }
        
        elif action == 'create_category':
            name = body_data.get('name')
            description = body_data.get('description')
            category = create_category(name, description)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'category': category}),
                'isBase64Encoded': False
            }
        
        elif action == 'delete_category':
            category_id = body_data.get('category_id')
            delete_category(category_id)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True}),
                'isBase64Encoded': False
            }
        
        elif action == 'get_words':
            words = get_all_words()
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'words': words}),
                'isBase64Encoded': False
            }
        
        elif action == 'search_words':
            search_query = body_data.get('search_query')
            category_id = body_data.get('category_id')
            limit = body_data.get('limit', 100)
            offset = body_data.get('offset', 0)
            words = search_words(search_query, category_id, limit, offset)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'words': words}),
                'isBase64Encoded': False
            }
        
        elif action == 'create_word':
            english_text = body_data.get('english_text')
            russian_translation = body_data.get('russian_translation')
            category_id = body_data.get('category_id')
            word = create_word(english_text, russian_translation, category_id)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'word': word}),
                'isBase64Encoded': False
            }
        
        elif action == 'delete_word':
            word_id = body_data.get('word_id')
            delete_word(word_id)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True}),
                'isBase64Encoded': False
            }
        
        elif action == 'delete_student_word':
            student_word_id = body_data.get('student_word_id')
            success = delete_student_word(student_word_id)
            return {
                'statusCode': 200 if success else 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': success}),
                'isBase64Encoded': False
            }
        
        elif action == 'toggle_subscription':
            telegram_id = body_data.get('telegram_id')
            active = body_data.get('active')
            days = body_data.get('days', 30)
            subscription_type = body_data.get('subscription_type', 'basic')
            result = toggle_subscription(telegram_id, active, days, subscription_type)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result),
                'isBase64Encoded': False
            }
        
        elif action == 'assign_words':
            student_id = body_data.get('student_id')
            word_ids = body_data.get('word_ids', [])
            assign_words_to_student(student_id, word_ids)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True}),
                'isBase64Encoded': False
            }
        
        elif action == 'auto_assign_basic_words':
            student_id = body_data.get('student_id')
            count = body_data.get('count', 15)
            result = auto_assign_basic_words(student_id, count)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result),
                'isBase64Encoded': False
            }
        
        elif action == 'get_student_words':
            student_id = body_data.get('student_id')
            words = get_student_words(student_id)
            print(f"DEBUG get_student_words: student_id={student_id}, words_count={len(words)}")
            if words:
                print(f"DEBUG first word: {words[0]}")
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(words),
                'isBase64Encoded': False
            }
        
        elif action == 'get_progress_stats' or action == 'get_student_progress_stats':
            student_id = body_data.get('student_id')
            stats = get_student_progress_stats(student_id)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(stats),
                'isBase64Encoded': False
            }
        
        elif action == 'update_student_settings':
            telegram_id = body_data.get('telegram_id')
            language_level = body_data.get('language_level')
            preferred_topics = body_data.get('preferred_topics')
            timezone = body_data.get('timezone')
            learning_goal = body_data.get('learning_goal')
            learning_goal_details = body_data.get('learning_goal_details')
            update_student_settings(telegram_id, language_level, preferred_topics, timezone, learning_goal, learning_goal_details)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True}),
                'isBase64Encoded': False
            }
        
        elif action == 'update_word_progress':
            student_id = body_data.get('student_id')
            word_id = body_data.get('word_id')
            is_correct = body_data.get('is_correct', True)
            result = update_word_progress(student_id, word_id, is_correct)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result),
                'isBase64Encoded': False
            }
        
        elif action == 'analyze_urgent_goal':
            goal = body_data.get('goal', '')
            result = analyze_urgent_goal(goal)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result),
                'isBase64Encoded': False
            }
        
        elif action == 'suggest_learning_goal':
            user_input = body_data.get('user_input', '')
            result = generate_learning_goal_suggestions(user_input)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result),
                'isBase64Encoded': False
            }
        
        elif action == 'generate_unique_words':
            student_id = body_data.get('student_id')
            learning_goal = body_data.get('learning_goal', '')
            language_level = body_data.get('language_level', 'A1')
            count = body_data.get('count', 7)
            result = generate_unique_words(student_id, learning_goal, language_level, count)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result),
                'isBase64Encoded': False
            }
        
        elif action == 'generate_personalized_words':
            student_id = body_data.get('student_id')
            learning_goal = body_data.get('learning_goal', '')
            language_level = body_data.get('language_level', 'A1')
            count = body_data.get('count', 7)
            result = generate_personalized_words(student_id, learning_goal, language_level, count)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result),
                'isBase64Encoded': False
            }
        
        elif action == 'generate_speech':
            text = body_data.get('text', '')
            lang = body_data.get('lang', 'en-US')
            result = generate_speech(text, lang)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result),
                'isBase64Encoded': False
            }
        
        elif action == 'get_gemini_prompts':
            prompts = get_all_gemini_prompts()
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'prompts': prompts}),
                'isBase64Encoded': False
            }
        
        elif action == 'update_gemini_prompt':
            prompt_id = body_data.get('prompt_id')
            prompt_text = body_data.get('prompt_text')
            description = body_data.get('description')
            is_active = body_data.get('is_active', True)
            success = update_gemini_prompt(prompt_id, prompt_text, description, is_active)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': success}),
                'isBase64Encoded': False
            }
        
        elif action == 'toggle_gemini_prompt':
            prompt_id = body_data.get('prompt_id')
            is_active = body_data.get('is_active')
            success = toggle_gemini_prompt(prompt_id, is_active)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': success}),
                'isBase64Enabled': False
            }
        
        elif action == 'get_proxies':
            proxies = get_all_proxies()
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'proxies': proxies}),
                'isBase64Encoded': False
            }
        
        elif action == 'get_active_proxy':
            proxy = get_active_proxy()
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'proxy': proxy}),
                'isBase64Encoded': False
            }
        
        elif action == 'add_proxy':
            host = body_data.get('host')
            port = body_data.get('port')
            username = body_data.get('username')
            password = body_data.get('password')
            proxy = add_proxy(host, port, username, password)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'proxy': proxy}),
                'isBase64Encoded': False
            }
        
        elif action == 'toggle_proxy':
            proxy_id = body_data.get('proxy_id')
            is_active = body_data.get('is_active')
            toggle_proxy(proxy_id, is_active)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True}),
                'isBase64Encoded': False
            }
        
        elif action == 'delete_proxy':
            proxy_id = body_data.get('proxy_id')
            delete_proxy(proxy_id)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True}),
                'isBase64Encoded': False
            }
        
        elif action == 'get_user_logs':
            telegram_id = body_data.get('telegram_id')
            limit = body_data.get('limit', 100)
            logs = get_user_activity_logs(telegram_id, limit)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'logs': logs}),
                'isBase64Encoded': False
            }
        
        elif action == 'reset_onboarding':
            telegram_id = body_data.get('telegram_id')
            success = reset_user_onboarding(telegram_id)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': success}),
                'isBase64Encoded': False
            }
        
        elif action == 'get_blog_posts':
            published_only = body_data.get('published_only', False)
            posts = get_all_blog_posts(published_only)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'posts': posts}),
                'isBase64Encoded': False
            }
        
        elif action == 'get_blog_post':
            slug = body_data.get('slug')
            post = get_blog_post_by_slug(slug)
            if post:
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'success': True, 'post': post}),
                    'isBase64Encoded': False
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'success': False, 'error': 'Post not found'}),
                    'isBase64Encoded': False
                }
        
        elif action == 'create_blog_post':
            title = body_data.get('title')
            slug = body_data.get('slug')
            excerpt = body_data.get('excerpt', '')
            content = body_data.get('content')
            cover_image = body_data.get('cover_image', '')
            author = body_data.get('author', 'Команда Anya')
            published = body_data.get('published', False)
            reading_time = body_data.get('reading_time', 5)
            
            post = create_blog_post(title, slug, excerpt, content, cover_image, author, published, reading_time)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'post': post}),
                'isBase64Encoded': False
            }
        
        elif action == 'update_blog_post':
            post_id = body_data.get('post_id')
            title = body_data.get('title')
            slug = body_data.get('slug')
            excerpt = body_data.get('excerpt', '')
            content = body_data.get('content')
            cover_image = body_data.get('cover_image', '')
            author = body_data.get('author', 'Команда Anya')
            published = body_data.get('published', False)
            reading_time = body_data.get('reading_time', 5)
            
            post = update_blog_post(post_id, title, slug, excerpt, content, cover_image, author, published, reading_time)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'post': post}),
                'isBase64Encoded': False
            }
        
        elif action == 'delete_blog_post':
            post_id = body_data.get('post_id')
            delete_blog_post(post_id)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True}),
                'isBase64Encoded': False
            }
        
        elif action == 'delete_user':
            try:
                telegram_id = body_data.get('telegram_id')
                print(f"🗑️ Handler: Starting delete_user for telegram_id={telegram_id}")
                delete_user(telegram_id)
                print(f"✅ Handler: User {telegram_id} deleted successfully")
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'success': True}),
                    'isBase64Encoded': False
                }
            except Exception as e:
                print(f"❌ Handler: Error deleting user: {e}")
                import traceback
                traceback.print_exc()
                return {
                    'statusCode': 500,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'success': False, 'error': str(e)}),
                    'isBase64Encoded': False
                }
        
        elif action == 'reset_proxy_stats':
            proxy_id = body_data.get('proxy_id')
            reset_proxy_stats(proxy_id)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True}),
                'isBase64Encoded': False
            }
        
        elif action == 'analyze_goal':
            goal = body_data.get('goal', '')
            result = analyze_goal_for_plan(goal)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result),
                'isBase64Encoded': False
            }
        
        elif action == 'check_level':
            claimed_level = body_data.get('claimed_level', 'A2')
            answer = body_data.get('answer', '')
            result = check_student_level(claimed_level, answer)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result),
                'isBase64Encoded': False
            }
        
        elif action == 'add_learning_goal':
            student_id = body_data.get('student_id')
            goal_text = body_data.get('goal_text', '')
            result = add_learning_goal(student_id, goal_text)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result),
                'isBase64Encoded': False
            }
        
        elif action == 'get_learning_goals':
            student_id = body_data.get('student_id')
            goals = get_learning_goals(student_id)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'goals': goals}),
                'isBase64Encoded': False
            }
        
        elif action == 'deactivate_learning_goal':
            goal_id = body_data.get('goal_id')
            deactivate_learning_goal(goal_id)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True}),
                'isBase64Encoded': False
            }
        
        elif action == 'demo_chat':
            message = body_data.get('message', '')
            history = body_data.get('history', [])
            
            if not message:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'success': False, 'error': 'message is required'}),
                    'isBase64Encoded': False
                }
            
            response_text = call_gemini_demo(message, history)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'response': response_text}),
                'isBase64Encoded': False
            }
        
        elif action == 'get_pricing_plans':
            plans = get_pricing_plans()
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'plans': plans}),
                'isBase64Encoded': False
            }
        
        elif action == 'update_pricing_plan':
            plan = body_data.get('plan')
            success = update_pricing_plan(plan)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': success}),
                'isBase64Encoded': False
            }
        
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': False, 'error': f'Unknown action: {action}'}),
                'isBase64Encoded': False
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'success': False, 'error': str(e)}),
            'isBase64Encoded': False
        }