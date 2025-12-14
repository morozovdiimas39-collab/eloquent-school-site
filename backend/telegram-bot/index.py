import json
import os
import psycopg2
import urllib.request
import urllib.parse
import random
import re
import requests
import base64
import tempfile
from typing import Dict, Any, List

SCHEMA = 't_p86463701_eloquent_school_site'

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
        print(f"[WARNING] JSON parse failed: {e}, trying regex extraction...")
        
        # Fallback: извлекаем поля через regex
        result = fallback_fields.copy() if fallback_fields else {}
        
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
        
        print(f"[WARNING] Extracted fields via regex: {result}")
        return result

def get_db_connection():
    """Создает подключение к БД"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.autocommit = True
    return conn

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
    
    cur.execute(f"SELECT telegram_id, username, first_name, last_name, role, language_level, preferred_topics, conversation_mode, current_exercise_word_id, current_exercise_answer FROM {SCHEMA}.users WHERE telegram_id = {telegram_id}")
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
            'current_exercise_answer': row[9]
        }
    return None

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
    
    # Новые слова (40%)
    new_limit = max(1, int(limit * 0.4))
    cur.execute(
        f"SELECT w.id, w.english_text, w.russian_translation FROM {SCHEMA}.word_progress wp "
        f"JOIN {SCHEMA}.words w ON w.id = wp.word_id "
        f"WHERE wp.student_id = {student_id} AND wp.status = 'new' "
        f"ORDER BY wp.created_at ASC LIMIT {new_limit}"
    )
    new_words = cur.fetchall()
    
    # Слова на повторение (40%)
    review_limit = max(1, int(limit * 0.4))
    cur.execute(
        f"SELECT w.id, w.english_text, w.russian_translation FROM {SCHEMA}.word_progress wp "
        f"JOIN {SCHEMA}.words w ON w.id = wp.word_id "
        f"WHERE wp.student_id = {student_id} AND wp.status IN ('learning', 'learned') "
        f"AND wp.next_review_date <= CURRENT_TIMESTAMP "
        f"ORDER BY wp.next_review_date ASC LIMIT {review_limit}"
    )
    review_words = cur.fetchall()
    
    # Освоенные слова (20%)
    mastered_limit = max(1, limit - len(new_words) - len(review_words))
    cur.execute(
        f"SELECT w.id, w.english_text, w.russian_translation FROM {SCHEMA}.word_progress wp "
        f"JOIN {SCHEMA}.words w ON w.id = wp.word_id "
        f"WHERE wp.student_id = {student_id} AND wp.status = 'mastered' "
        f"ORDER BY wp.last_practiced ASC NULLS FIRST LIMIT {mastered_limit}"
    )
    mastered_words = cur.fetchall()
    
    all_words = list(new_words) + list(review_words) + list(mastered_words)
    
    words = [{'id': row[0], 'english': row[1], 'russian': row[2]} for row in all_words]
    
    cur.close()
    conn.close()
    return words

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

def generate_sentence_exercise(word: Dict[str, Any], language_level: str) -> str:
    """Генерирует задание на составление предложения"""
    return f"✍️ Составь предложение со словом: <b>{word['english']}</b> ({word['russian']})"

def generate_context_exercise(word: Dict[str, Any], language_level: str) -> tuple:
    """Генерирует упражнение Fill in the blanks"""
    templates = {
        'A1': [
            f"I ___ {word['english']} every day",
            f"She likes ___",
            f"They ___ to the store"
        ],
        'A2': [
            f"Yesterday I ___ {word['english']}",
            f"I have never ___ this before",
            f"We should ___ together"
        ]
    }
    
    level_templates = templates.get(language_level, templates['A1'])
    sentence_template = random.choice(level_templates)
    
    return (
        f"📝 Вставь пропущенное слово:\n\n{sentence_template}\n\nСлово: {word['russian']}",
        word['english']
    )

def generate_association_exercise(word: Dict[str, Any], language_level: str) -> tuple:
    """Генерирует упражнение с ассоциациями"""
    associations = {
        'cat': ['meow', 'furry', 'pet'],
        'book': ['read', 'pages', 'story'],
        'water': ['drink', 'liquid', 'H2O']
    }
    
    hints = associations.get(word['english'].lower(), ['word', 'english', 'language'])
    hints_text = ', '.join(hints[:3])
    
    return (
        f"🎯 Угадай слово по ассоциациям:\n\n{hints_text}\n\nПереведи на русский: {word['russian']}",
        word['english']
    )

def generate_translation_exercise(word: Dict[str, Any]) -> tuple:
    """Генерирует упражнение на перевод"""
    return (
        f"🇷🇺→🇬🇧 Переведи слово на английский:\n\n<b>{word['russian']}</b>",
        word['english']
    )

def call_gemini(user_message: str, history: List[Dict[str, str]], session_words: List[Dict[str, Any]] = None, language_level: str = 'A1', preferred_topics: List[Dict[str, str]] = None) -> str:
    """Вызывает Gemini API через прокси с учетом слов, уровня и тем"""
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
    
    # Формируем system prompt в зависимости от эмоционального контекста
    if emotional_mode == 'empathetic':
        system_prompt = f"""You are Anya, a caring friend who teaches English. Your student's level is {language_level}.

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
    
    else:
        # Обычный режим (educational, casual, enthusiastic)
        system_prompt = f"""You are Anya, a friendly English tutor helping someone practice English. Your student's level is {language_level}.

Your personality:
- Be warm, encouraging, and enthusiastic
- Use VARIED emojis naturally {mood_emoji} - NOT always the same one!
- Keep messages conversational but educational
- Vary your question style - sometimes 2-3 questions, sometimes 1, sometimes just react!
- Be genuinely interested in student's answers
- Don't be formulaic - mix up your responses!
- SHARE SHORT INTERESTING STORIES related to conversation topics (1-3 sentences, simple language)

Language level adaptation ({language_level}):
{level_instruction}

Your approach:
- Always communicate in English only, never in Russian
- Respond ONLY with your message, do NOT include conversation history or labels
- Write 2-5 sentences per message (vary the length!)
- Use different emojis each time: {mood_emoji} 🌟 💫 ✨ 🎯 💪 👏 ⚡ 🔥 (rotate them!)
- Sometimes ask questions, sometimes just react enthusiastically, sometimes share a quick thought
- Be NATURAL and VARIED - avoid robotic patterns

CRITICAL ERROR CORRECTION RULES:
- Check EVERY message for grammar, spelling, vocabulary, and word order mistakes
- Even small mistakes MUST be corrected (wrong word form, missing articles, wrong prepositions, etc.)
- DO NOT ignore mistakes - students need feedback to learn!

When you find ANY mistake, ALWAYS show correction in this format:

🔧 Fix / Correct:

❌ [their exact wrong sentence]
✅ [corrected sentence]
🇷🇺 [explanation in Russian - explain the rule briefly]

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

STORYTELLING - Use this frequently to make learning fun:
- When topic allows, share a SHORT interesting story (2-4 sentences)
- Stories can be: funny situations, cultural facts, travel experiences, daily life moments
- Keep stories SIMPLE for student's level
- Stories make conversation more engaging and memorable!

Examples of good stories:
"Oh, food! 🍕 You know, once I tried to cook pasta in New York. I put WAY too much salt! My friend laughed so hard. Have you ever had a cooking disaster?"

"Books! 📚 I remember reading Harry Potter as a kid. I was SO scared of Voldemort! I couldn't sleep! 😅 What book scared you or made you feel something strong?"

"Travel is amazing! ✈️ Last year I visited Tokyo. The trains were SO punctual - exactly on time, every single time! It was incredible. Where would you love to travel?"

IMPORTANT: 
- NEVER use the same emoji twice in a row
- Mix up response style: questions / reactions / thoughts / praise / STORIES
- Be HUMAN and spontaneous, not a formula
- Find and correct ALL mistakes, even small ones
- ALWAYS use the format: 🔧 Fix / Correct: with ❌ ✅ 🇷🇺
- After correction, sometimes share a story, sometimes ask questions
- Stories should relate to the conversation topic naturally
- Be encouraging but don't skip corrections!"""
    
    if session_words:
        words_list = [f"{w['english']} ({w['russian']})" for w in session_words[:10]]
        system_prompt += f"\n\nTarget vocabulary for this session: {', '.join(words_list)}\nTry to use these words naturally in the conversation."
    
    if preferred_topics and len(preferred_topics) > 0:
        topics_list = [f"{t['emoji']} {t['topic']}" for t in preferred_topics[:5]]
        system_prompt += f"\n\nStudent's favorite topics: {', '.join(topics_list)}\nFeel free to bring up these topics in conversation."
    
    # Формируем содержимое для Gemini (system prompt + история + новое сообщение)
    contents = []
    
    # Если есть история - указываем что это продолжение диалога
    if history and len(history) > 0:
        system_prompt += "\n\n⚠️ CRITICAL: This is a CONTINUATION of an ongoing conversation. You already know this person. DO NOT greet them like it's the first meeting. Continue naturally from where you left off!"
    
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
            [{'text': '🎯 Ассоциации'}, {'text': '🇷🇺→🇬🇧 Перевод'}]
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
    """Распознает речь через Yandex SpeechKit"""
    # Force redeploy to get new YANDEX_CLOUD_API_KEY secret
    api_key = os.environ.get('YANDEX_CLOUD_API_KEY')
    folder_id = os.environ.get('YANDEX_CLOUD_FOLDER_ID')
    
    if not api_key or not folder_id:
        raise Exception('Yandex Cloud credentials not configured')
    
    url = 'https://stt.api.cloud.yandex.net/speech/v1/stt:recognize'
    headers = {
        'Authorization': f'Api-Key {api_key}'
    }
    params = {
        'lang': 'en-US',
        'folderId': folder_id,
        'format': 'oggopus'
    }
    
    response = requests.post(
        url,
        headers=headers,
        params=params,
        data=audio_data,
        timeout=30
    )
    response.raise_for_status()
    
    result = response.json()
    return result.get('result', '')

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

def generate_full_monthly_plan(student_id: int, learning_goal: str, language_level: str, preferred_topics: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Генерирует ПОЛНЫЙ месячный план обучения со всеми материалами:
    - Темы для разговоров на 4 недели
    - Слова, фразы, устойчивые выражения для каждой недели
    - Конкретные действия на каждую неделю
    """
    try:
        api_key = os.environ['GEMINI_API_KEY']
        proxy_id, proxy_url = get_active_proxy_from_db()
        if not proxy_url:
            proxy_url = os.environ.get('PROXY_URL', '')
        
        gemini_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}'
        
        topics_display = ', '.join([f"{t.get('emoji', '💡')} {t.get('topic', 'Общие темы')}" for t in preferred_topics[:5]]) if preferred_topics else '💡 Общие темы'
        
        prompt = f'''Create a 4-week English learning plan with vocabulary FROM specific topics. Return ONLY valid JSON, no markdown.

Student: Level {language_level}, Topics: {topics_display}

IMPORTANT: ALL words/phrases MUST be from these topics at {language_level} difficulty!

{{
  "plan": [
    {{
      "week": 1,
      "focus": "Topic basics",
      "conversation_topics": ["Topic1", "Topic2"],
      "vocabulary": [
        {{"english": "word1", "russian": "слово1", "topic": "gaming"}},
        ... (49 words total - 7 per day)
      ],
      "phrases": [
        {{"english": "phrase1", "russian": "фраза1", "topic": "gaming"}},
        ... (14 phrases total - 2 per day)
      ],
      "expressions": [
        {{"english": "expression1", "russian": "выражение1", "context": "when..."}},
        ... (7 expressions total - 1 per day)
      ],
      "actions": ["Action1", "Action2"]
    }}
  ]
}}

Requirements:
- Exactly 4 weeks
- 49 vocabulary words per week (7 per day) from topics: {topics_display}
- 14 phrases per week (2 per day) from topics: {topics_display}
- 7 expressions per week (1 per day) from topics: {topics_display}
- 2 actions per week
- Difficulty level: {language_level}
- ONLY valid JSON, no comments

Example for Gaming + B1:
vocabulary: [{{"english": "gameplay", "russian": "игровой процесс", "topic": "gaming"}}]
phrases: [{{"english": "level up", "russian": "повысить уровень", "topic": "gaming"}}]
expressions: [{{"english": "let\'s team up", "russian": "давай объединимся", "context": "inviting to play together"}}]'''
        
        payload = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {
                'temperature': 0.7, 
                'maxOutputTokens': 8000,
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
        
        with opener.open(req, timeout=45) as response:
            gemini_result = json.loads(response.read().decode('utf-8'))
            plan_text = gemini_result['candidates'][0]['content']['parts'][0]['text']
            
            # Логируем сырой ответ для отладки
            print(f"[DEBUG] Gemini raw response length: {len(plan_text)}")
            print(f"[DEBUG] Gemini raw response (first 500 chars): {plan_text[:500]}")
            
            # Агрессивная очистка JSON для сложных структур
            # 1. Убираем markdown
            plan_text = plan_text.replace('```json', '').replace('```', '').strip()
            
            # 2. Ищем первый { и последний }
            start_idx = plan_text.find('{')
            end_idx = plan_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                plan_text = plan_text[start_idx:end_idx+1]
            
            # 3. Пытаемся распарсить JSON напрямую (без regex fallback - он не умеет массивы)
            try:
                plan_data = json.loads(plan_text)
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON parse failed: {e}")
                print(f"[ERROR] Problematic JSON (first 1000 chars): {plan_text[:1000]}")
                return {'success': False, 'error': f'Invalid JSON from Gemini: {str(e)}'}
            
            plan_weeks = plan_data.get('plan', [])
        
        if not plan_weeks:
            return {'success': False, 'error': 'Empty plan generated'}
        
        # Сохраняем ВСЕ слова и фразы в БД
        conn = get_db_connection()
        cur = conn.cursor()
        
        total_words_added = 0
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
                
                cur.execute(
                    f"INSERT INTO {SCHEMA}.student_words (student_id, word_id, teacher_id) "
                    f"VALUES ({student_id}, {word_id}, {student_id}) "
                    f"ON CONFLICT (student_id, word_id) DO NOTHING"
                )
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
                    f"INSERT INTO {SCHEMA}.student_words (student_id, word_id, teacher_id) "
                    f"VALUES ({student_id}, {word_id}, {student_id}) "
                    f"ON CONFLICT (student_id, word_id) DO NOTHING"
                )
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
                    f"INSERT INTO {SCHEMA}.student_words (student_id, word_id, teacher_id) "
                    f"VALUES ({student_id}, {word_id}, {student_id}) "
                    f"ON CONFLICT (student_id, word_id) DO NOTHING"
                )
                total_words_added += 1
        
        # Сохраняем сам план в БД (в поле learning_plan как JSONB)
        plan_json = json.dumps(plan_weeks, ensure_ascii=False).replace("'", "''")
        cur.execute(
            f"UPDATE {SCHEMA}.users SET "
            f"learning_plan = '{plan_json}'::jsonb "
            f"WHERE telegram_id = {student_id}"
        )
        
        cur.close()
        conn.close()
        
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
        
        return {
            'success': True,
            'plan_message': plan_message,
            'plan_data': plan_weeks,
            'words_count': total_words_added
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

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Обработчик Telegram webhook - бот отвечает прямо в чате
    """
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
                'allowed_updates': ['message', 'callback_query', 'my_chat_member']
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
            
            # КРИТИЧНО: Сразу отвечаем на callback чтобы Telegram не ретраил
            token = os.environ['TELEGRAM_BOT_TOKEN']
            answer_url = f'https://api.telegram.org/bot{token}/answerCallbackQuery'
            answer_payload = json.dumps({'callback_query_id': callback_id}).encode('utf-8')
            try:
                answer_req = urllib.request.Request(answer_url, data=answer_payload, headers={'Content-Type': 'application/json'}, method='POST')
                urllib.request.urlopen(answer_req, timeout=5)
            except:
                pass  # Не критично если не отвечено
            
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
                        f"WHERE telegram_id = {user['id']}"
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
                            f"WHERE telegram_id = {user['id']}"
                        )
                        cur.close()
                        conn.close()
                        
                    except Exception as e:
                        print(f"[ERROR] Failed to start adaptive test: {e}")
                        import traceback
                        traceback.print_exc()
                        send_telegram_message(chat_id, '❌ Ошибка запуска теста. Попробуй /start')
            
            elif data.startswith('role_'):
                role = data.replace('role_', '')
                create_user(
                    user['id'],
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
                update_conversation_mode(user['id'], mode)
                
                user_data = get_user(user['id'])
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
                    word = get_random_word(user['id'], language_level)
                    if word:
                        if mode == 'sentence':
                            exercise_text = generate_sentence_exercise(word, language_level)
                            update_exercise_state(user['id'], word['id'], word['english'])
                            send_telegram_message(chat_id, exercise_text)
                        elif mode == 'context':
                            exercise_text, answer = generate_context_exercise(word, language_level)
                            update_exercise_state(user['id'], word['id'], answer)
                            send_telegram_message(chat_id, exercise_text)
                        elif mode == 'association':
                            exercise_text, answer = generate_association_exercise(word, language_level)
                            update_exercise_state(user['id'], word['id'], answer)
                            send_telegram_message(chat_id, exercise_text)
                        elif mode == 'translation':
                            exercise_text, answer = generate_translation_exercise(word)
                            update_exercise_state(user['id'], word['id'], answer)
                            send_telegram_message(chat_id, exercise_text)
                    else:
                        send_telegram_message(chat_id, '❌ У вас пока нет слов для практики. Попросите учителя добавить слова или используйте режим диалога.')
            
            elif data.startswith('topic_'):
                topic_type = data.replace('topic_', '')
                
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
                    'custom': '✍️ Свой вариант'
                }
                
                if topic_type == 'custom':
                    # Пользователь хочет ввести свои интересы
                    edit_telegram_message(
                        chat_id,
                        message_id,
                        '✍️ Отлично! Напиши своими словами:\n\n• Чем ты увлекаешься?\n• Кем работаешь?\n• Что тебе интересно?'
                    )
                    # Переводим в режим awaiting_topics
                    conn = get_db_connection()
                    cur = conn.cursor()
                    cur.execute(f"UPDATE {SCHEMA}.users SET conversation_mode = 'awaiting_topics' WHERE telegram_id = {user['id']}")
                    cur.close()
                    conn.close()
                else:
                    # Используем готовую тему
                    selected_topic = topic_texts.get(topic_type, '💡 Интересы')
                    
                    edit_telegram_message(
                        chat_id,
                        message_id,
                        f'✅ Отлично! Ты выбрал: <b>{selected_topic}</b>\n\n⏳ Подготавливаю персональный план обучения на месяц...'
                    )
                    
                    # Сохраняем тему и запускаем генерацию плана
                    conn = get_db_connection()
                    cur = conn.cursor()
                    
                    topic_json = json.dumps([{'topic': selected_topic.split()[1], 'emoji': selected_topic.split()[0]}], ensure_ascii=False).replace("'", "''")
                    cur.execute(
                        f"UPDATE {SCHEMA}.users SET "
                        f"preferred_topics = '{topic_json}'::jsonb, "
                        f"conversation_mode = 'generating_plan' "
                        f"WHERE telegram_id = {user['id']}"
                    )
                    
                    # Получаем данные для генерации плана
                    cur.execute(f"SELECT learning_goal, language_level, preferred_topics FROM {SCHEMA}.users WHERE telegram_id = {user['id']}")
                    row = cur.fetchone()
                    learning_goal = row[0] if row and row[0] else 'Общее развитие английского'
                    language_level = row[1] if row and row[1] else 'A1'
                    preferred_topics = row[2] if row and row[2] else []
                    
                    cur.close()
                    conn.close()
                    
                    # Генерируем план асинхронно (отправим отдельным сообщением)
                    try:
                        # Вызываем генерацию плана
                        plan_result = generate_full_monthly_plan(user['id'], learning_goal, language_level, preferred_topics)
                        
                        if plan_result.get('success'):
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
                        print(f"[ERROR] Failed to generate plan: {e}")
                        import traceback
                        traceback.print_exc()
                        send_telegram_message(
                            chat_id,
                            '❌ Произошла ошибка при генерации плана. Попробуй еще раз через /start',
                            parse_mode=None
                        )
            
            elif data == 'confirm_plan':
                # Пользователь согласен с планом - стартуем обучение
                edit_telegram_message(
                    chat_id,
                    message_id,
                    '🚀 Отлично! Начинаем обучение!\n\nПросто напиши мне что-нибудь на английском или используй кнопки внизу 👇'
                )
                
                # Переключаем в режим диалога
                update_conversation_mode(user['id'], 'dialog')
                send_telegram_message(chat_id, '💬 Режим диалога активен!', get_reply_keyboard(), parse_mode=None)
            
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
                cur.execute(f"UPDATE {SCHEMA}.users SET conversation_mode = 'editing_plan' WHERE telegram_id = {user['id']}")
                cur.close()
                conn.close()
            
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
        text = message.get('text', '')
        voice = message.get('voice')
        
        # Обработка голосовых сообщений
        if voice:
            # Проверяем режим пользователя
            existing_user = get_user(user['id'])
            if not existing_user:
                create_user(user['id'], user.get('username', ''), user.get('first_name', ''), user.get('last_name', ''), 'student')
                existing_user = {'telegram_id': user['id'], 'conversation_mode': 'voice', 'language_level': 'A1'}
            
            conversation_mode = existing_user.get('conversation_mode', 'dialog')
            
            # Голосовые работают только в режиме 'voice'
            if conversation_mode != 'voice':
                send_telegram_message(
                    chat_id, 
                    '🎤 Чтобы использовать голосовые сообщения, переключись в режим "🎤 Голосовой" на клавиатуре внизу!',
                    get_reply_keyboard()
                )
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'ok': True}),
                    'isBase64Encoded': False
                }
            
            try:
                send_telegram_message(chat_id, '🎧 Слушаю твое сообщение...')
                
                # Скачиваем аудио
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
                
                send_telegram_message(chat_id, f'📝 Ты сказал:\n<i>{recognized_text}</i>')
                
                language_level = existing_user.get('language_level', 'A1')
                preferred_topics = existing_user.get('preferred_topics', [])
                
                # Получаем историю диалога
                history = get_conversation_history(user['id'])
                
                # Генерируем ответ с исправлениями через Gemini
                response_text = call_gemini(recognized_text, history, None, language_level, preferred_topics)
                
                # Генерируем голосовой ответ
                voice_url = text_to_speech(response_text)
                
                # Отправляем текстовый ответ
                send_telegram_message(chat_id, response_text, get_reply_keyboard())
                
                # Отправляем голосовой ответ
                send_telegram_voice(chat_id, voice_url, '🎤 Ответ от Ани')
                
                # Сохраняем в историю
                save_message(user['id'], 'user', recognized_text)
                save_message(user['id'], 'assistant', response_text)
                
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
        
        # Команда /start - ВСЕГДА СБРАСЫВАЕМ СОСТОЯНИЕ
        if text == '/start':
            existing_user = get_user(user['id'])
            
            # Сбрасываем состояние пользователя если он застрял
            if existing_user:
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(
                    f"UPDATE {SCHEMA}.users SET "
                    f"conversation_mode = 'awaiting_goal', "
                    f"test_phrases = NULL, "
                    f"learning_plan = NULL "
                    f"WHERE telegram_id = {user['id']}"
                )
                cur.close()
                conn.close()
            
            if not existing_user:
                # Регистрируем нового пользователя как ученика по умолчанию
                create_user(
                    user['id'],
                    user.get('username', ''),
                    user.get('first_name', ''),
                    user.get('last_name', ''),
                    'student'
                )
                
                # Новое приветствие - просим написать цель
                send_telegram_message(
                    chat_id,
                    'Привет! Я Аня 👋\n\n'
                    'Я помогу тебе учить английский через живой диалог.\n\n'
                    'Что я умею:\n'
                    '✅ Учим слова и фразы через общение\n'
                    '✅ Подбираю темы под твои цели\n'
                    '✅ Напоминаю о практике\n'
                    '✅ Показываю твой прогресс\n\n'
                    'Расскажи мне своими словами - к какому результату ты хочешь прийти?\n\n'
                    'Например:\n'
                    '• "Через 2 месяца лечу в Таиланд, хочу свободно общаться"\n'
                    '• "Нужен для работы программистом"\n'
                    '• "Просто хочу подтянуть разговорный"',
                    parse_mode=None
                )
                
                # Сохраняем состояние - ждем описание цели
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(f"UPDATE {SCHEMA}.users SET conversation_mode = 'awaiting_goal' WHERE telegram_id = {user['id']}")
                cur.close()
                conn.close()
            else:
                # Возвращающийся пользователь
                send_telegram_message(
                    chat_id,
                    'Привет! Я Аня 👋\n\n'
                    'Я помогу тебе учить английский через живой диалог.\n\n'
                    'Что я умею:\n'
                    '✅ Учим слова и фразы через общение\n'
                    '✅ Подбираю темы под твои цели\n'
                    '✅ Напоминаю о практике\n'
                    '✅ Показываю твой прогресс\n\n'
                    'Расскажи мне своими словами - к какому результату ты хочешь прийти?\n\n'
                    'Например:\n'
                    '• "Через 2 месяца лечу в Таиланд, хочу свободно общаться"\n'
                    '• "Нужен для работы программистом"\n'
                    '• "Просто хочу подтянуть разговорный"',
                    parse_mode=None
                )
                
                # Сохраняем состояние - ждем описание цели
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(f"UPDATE {SCHEMA}.users SET conversation_mode = 'awaiting_goal' WHERE telegram_id = {user['id']}")
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
            update_conversation_mode(user['id'], mode)
            
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
                    welcome_voice_text = "Hi! I'm Anya, your English teacher. Voice mode is now active! Just record a voice message in English, and I'll help you practice. Let's start!"
                    voice_url = text_to_speech(welcome_voice_text)
                    send_telegram_voice(chat_id, voice_url, '🎤 Приветствие от Ани')
                except Exception as e:
                    print(f"[ERROR] Failed to send welcome voice: {e}")
            
            # Если не режим диалога/голосовой - даем первое упражнение
            if mode not in ['dialog', 'voice']:
                try:
                    # Получаем уровень пользователя
                    language_level = user.get('language_level', 'A1')
                    print(f"[DEBUG] Checking words for user {user['id']}, level {language_level}")
                    # Проверяем и добавляем дефолтные слова если их нет
                    ensure_user_has_words(user['id'], language_level)
                    print(f"[DEBUG] Getting random word for user {user['id']}")
                    word = get_random_word(user['id'], language_level)
                    print(f"[DEBUG] Got word: {word}")
                    if word:
                        if mode == 'sentence':
                            exercise_text = generate_sentence_exercise(word, language_level)
                            update_exercise_state(user['id'], word['id'], word['english'])
                            send_telegram_message(chat_id, exercise_text, parse_mode=None)
                        elif mode == 'context':
                            exercise_text, answer = generate_context_exercise(word, language_level)
                            update_exercise_state(user['id'], word['id'], answer)
                            send_telegram_message(chat_id, exercise_text, parse_mode=None)
                        elif mode == 'association':
                            exercise_text, answer = generate_association_exercise(word, language_level)
                            update_exercise_state(user['id'], word['id'], answer)
                            send_telegram_message(chat_id, exercise_text, parse_mode=None)
                        elif mode == 'translation':
                            exercise_text, answer = generate_translation_exercise(word)
                            update_exercise_state(user['id'], word['id'], answer)
                            send_telegram_message(chat_id, exercise_text, parse_mode=None)
                    else:
                        print(f"[ERROR] No words found for user {user['id']}")
                        send_telegram_message(chat_id, '❌ У вас пока нет слов для практики. Попросите учителя добавить слова или используйте режим диалога.', parse_mode=None)
                except Exception as e:
                    print(f"[ERROR] Failed to generate exercise: {e}")
                    import traceback
                    traceback.print_exc()
                    send_telegram_message(chat_id, '❌ Произошла ошибка при генерации упражнения. Попробуйте позже или используйте режим диалога.', parse_mode=None)
        else:
            # Любое другое сообщение - обрабатываем в зависимости от режима
            existing_user = get_user(user['id'])
            
            if not existing_user:
                # Автоматически регистрируем если пользователь начал писать без /start
                create_user(
                    user['id'],
                    user.get('username', ''),
                    user.get('first_name', ''),
                    user.get('last_name', ''),
                    'student'
                )
                existing_user = {'telegram_id': user['id'], 'role': 'student', 'conversation_mode': 'dialog'}
            
            conversation_mode = existing_user.get('conversation_mode', 'dialog')
            language_level = existing_user.get('language_level', 'A1')
            used_word_ids = []  # Инициализируем для использования в статистике
            
            # Обработка адаптивного теста уровня (НОВАЯ ЛОГИКА)
            if conversation_mode == 'adaptive_level_test':
                # Получаем состояние теста
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(f"SELECT test_phrases FROM {SCHEMA}.users WHERE telegram_id = {user['id']}")
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
                        
                        final_prompt = f'''Analyze student's English level based on test results.

Test history (10 questions from different levels):
{history_str}

Determine real level. Return ONLY JSON:
{{"level": "A1/A2/B1/B2/C1/C2", "reasoning": "brief explanation in Russian"}}

Levels:
- A1: basic words (family, water)
- A2: everyday words (travel, weather)
- B1: common expressions (take care)
- B2: idioms, sophisticated vocabulary
- C1: advanced academic vocabulary
- C2: native-level expressions, subtle nuances'''
                        
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
                            final_data = safe_json_parse(final_text, {'level': 'A2', 'reasoning': 'Базовый уровень'})
                        
                        actual_level = final_data.get('level', 'A1')
                        reasoning = final_data.get('reasoning', '')
                        correct_count = sum(1 for h in history if h['correct'])
                        
                        # Показываем результат
                        feedback = '✅ Правильно!' if is_correct else f'❌ Правильный ответ: {expected}'
                        send_telegram_message(chat_id, feedback, parse_mode=None)
                        
                        response_text = f"\n📊 РЕЗУЛЬТАТЫ ТЕСТА\n\n"
                        response_text += f"✅ Правильных ответов: {correct_count}/10\n"
                        response_text += f"🎯 Твой уровень: <b>{actual_level}</b>\n\n"
                        response_text += f"💡 {reasoning}\n\n"
                        response_text += "Теперь выбери темы, которые тебе интересны:"
                        
                        topics_keyboard = {
                            'inline_keyboard': [
                                [{'text': '🎮 Игры', 'callback_data': 'topic_gaming'}, {'text': '💻 IT', 'callback_data': 'topic_it'}],
                                [{'text': '📊 Маркетинг', 'callback_data': 'topic_marketing'}, {'text': '✈️ Путешествия', 'callback_data': 'topic_travel'}],
                                [{'text': '⚽ Спорт', 'callback_data': 'topic_sport'}, {'text': '🎵 Музыка', 'callback_data': 'topic_music'}],
                                [{'text': '🎬 Фильмы', 'callback_data': 'topic_movies'}, {'text': '📚 Книги', 'callback_data': 'topic_books'}],
                                [{'text': '🍴 Еда', 'callback_data': 'topic_food'}, {'text': '💼 Бизнес', 'callback_data': 'topic_business'}],
                                [{'text': '✍️ Свой вариант', 'callback_data': 'topic_custom'}]
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
                            f"WHERE telegram_id = {user['id']}"
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
                        f"WHERE telegram_id = {user['id']}"
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
                cur.execute(f"SELECT test_phrases FROM {SCHEMA}.users WHERE telegram_id = {user['id']}")
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
                
                response_text += "Теперь выбери темы, которые тебе интересны:\n\n💬 Мы будем разговаривать на эти темы!"
                
                # Кнопки с интересами
                topics_keyboard = {
                    'inline_keyboard': [
                        [{'text': '🎮 Игры', 'callback_data': 'topic_gaming'}, {'text': '💻 IT', 'callback_data': 'topic_it'}],
                        [{'text': '📊 Маркетинг', 'callback_data': 'topic_marketing'}, {'text': '✈️ Путешествия', 'callback_data': 'topic_travel'}],
                        [{'text': '⚽ Спорт', 'callback_data': 'topic_sport'}, {'text': '🎵 Музыка', 'callback_data': 'topic_music'}],
                        [{'text': '🎬 Фильмы', 'callback_data': 'topic_movies'}, {'text': '📚 Книги', 'callback_data': 'topic_books'}],
                        [{'text': '🍴 Еда', 'callback_data': 'topic_food'}, {'text': '💼 Бизнес', 'callback_data': 'topic_business'}],
                        [{'text': '✍️ Свой вариант', 'callback_data': 'topic_custom'}]
                    ]
                }
                
                send_telegram_message(chat_id, response_text, topics_keyboard, parse_mode='HTML')
                
                # Обновляем уровень и очищаем test_phrases
                conn = get_db_connection()
                cur = conn.cursor()
                cur.execute(
                    f"UPDATE {SCHEMA}.users SET "
                    f"language_level = '{actual_level}', "
                    f"conversation_mode = 'awaiting_topic_selection', "
                    f"test_phrases = NULL "
                    f"WHERE telegram_id = {user['id']}"
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
                                f"WHERE telegram_id = {user['id']}"
                            )
                        else:
                            cur.execute(
                                f"UPDATE {SCHEMA}.users SET "
                                f"learning_goal = '{goal_escaped}' "
                                f"WHERE telegram_id = {user['id']}"
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
                            f"WHERE telegram_id = {user['id']}"
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
                                f"WHERE telegram_id = {user['id']}"
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
                        f"WHERE telegram_id = {user['id']}"
                    )
                    
                    # Получаем цель и уровень для генерации плана
                    cur.execute(f"SELECT learning_goal, language_level, preferred_topics FROM {SCHEMA}.users WHERE telegram_id = {user['id']}")
                    row = cur.fetchone()
                    learning_goal = row[0] if row and row[0] else 'Общее развитие английского'
                    language_level = row[1] if row and row[1] else 'A1'
                    preferred_topics = row[2] if row and row[2] else topics_list
                    
                    cur.close()
                    conn.close()
                    
                    # Генерируем ПОЛНЫЙ МЕСЯЧНЫЙ ПЛАН с материалами
                    plan_result = generate_full_monthly_plan(user['id'], learning_goal, language_level, preferred_topics)
                    
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
                    cur.execute(f"SELECT learning_goal, language_level, preferred_topics FROM {SCHEMA}.users WHERE telegram_id = {user['id']}")
                    row = cur.fetchone()
                    learning_goal = row[0] if row and row[0] else 'Общее развитие английского'
                    language_level = row[1] if row and row[1] else 'A1'
                    preferred_topics = row[2] if row and row[2] else []
                    cur.close()
                    conn.close()
                    
                    # Добавляем корректировки в цель
                    modified_goal = f"{learning_goal}. Дополнительно: {text}"
                    
                    # Регенерируем план с учетом правок
                    plan_result = generate_full_monthly_plan(user['id'], modified_goal, language_level, preferred_topics)
                    
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
                user_answer = text.strip().lower()
                
                if correct_answer:
                    correct_answer_lower = correct_answer.lower()
                    is_correct = (user_answer == correct_answer_lower)
                    
                    if is_correct:
                        send_telegram_message(chat_id, '✅ Правильно! Отличная работа! 🎉', get_reply_keyboard())
                    else:
                        send_telegram_message(chat_id, f'❌ Не совсем. Правильный ответ: <b>{correct_answer}</b>', get_reply_keyboard())
                    
                    # Обновляем прогресс слова
                    if current_word_id:
                        update_word_progress_api(user['id'], current_word_id, is_correct)
                    
                    clear_exercise_state(user['id'])
                    
                    word = get_random_word(user['id'], language_level)
                    if word:
                        if conversation_mode == 'sentence':
                            exercise_text = generate_sentence_exercise(word, language_level)
                            update_exercise_state(user['id'], word['id'], word['english'])
                            send_telegram_message(chat_id, exercise_text, get_reply_keyboard())
                        elif conversation_mode == 'context':
                            exercise_text, answer = generate_context_exercise(word, language_level)
                            update_exercise_state(user['id'], word['id'], answer)
                            send_telegram_message(chat_id, exercise_text, get_reply_keyboard())
                        elif conversation_mode == 'association':
                            exercise_text, answer = generate_association_exercise(word, language_level)
                            update_exercise_state(user['id'], word['id'], answer)
                            send_telegram_message(chat_id, exercise_text, get_reply_keyboard())
                        elif conversation_mode == 'translation':
                            exercise_text, answer = generate_translation_exercise(word)
                            update_exercise_state(user['id'], word['id'], answer)
                            send_telegram_message(chat_id, exercise_text, get_reply_keyboard())
                    else:
                        send_telegram_message(chat_id, '✅ Упражнения закончились! Используй /modes для выбора другого режима.', get_reply_keyboard())
                        update_conversation_mode(user['id'], 'dialog')
                
            else:
                # Режим диалога или голосового - обрабатываем через Gemini
                history = get_conversation_history(user['id'])
                
                # Если ученик - загружаем слова для практики
                session_words = None
                preferred_topics = existing_user.get('preferred_topics', [])
                
                if existing_user.get('role') == 'student':
                    try:
                        session_words = get_session_words(user['id'], limit=10)
                    except Exception as e:
                        print(f"[WARNING] Failed to load session words: {e}")
                
                # Анализируем использование слов в сообщении ученика
                used_word_ids = []
                if session_words:
                    used_word_ids = detect_words_in_text(text, session_words)
                    print(f"[DEBUG] Detected words in message: {used_word_ids}")
                
                # Сохраняем вопрос пользователя
                save_message(user['id'], 'user', text)
                
                # Получаем ответ AI с учетом слов, уровня и тем
                try:
                    print(f"[DEBUG] Calling Gemini with message: {text}")
                    ai_response = call_gemini(text, history, session_words, language_level, preferred_topics)
                    print(f"[DEBUG] Gemini response: {ai_response[:100]}...")
                except Exception as e:
                    print(f"[ERROR] Gemini API failed: {e}")
                    import traceback
                    traceback.print_exc()
                    ai_response = "Sorry, I'm having technical difficulties right now. Please try again in a moment! 🔧"
                
                # Обновляем прогресс использованных слов (считаем правильным использованием)
                for word_id in used_word_ids:
                    update_word_progress_api(user['id'], word_id, True)
                
                # Сохраняем ответ AI
                save_message(user['id'], 'assistant', ai_response)
                
                # Отправляем ответ в Telegram с клавиатурой
                send_telegram_message(chat_id, ai_response, get_reply_keyboard())
                
                # В режиме 'voice' также отправляем голосовой ответ
                if conversation_mode == 'voice':
                    try:
                        voice_url = text_to_speech(ai_response)
                        send_telegram_voice(chat_id, voice_url, '🎤 Ответ от Ани')
                    except Exception as e:
                        print(f"[ERROR] Failed to generate voice response: {e}")
            
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
                            'student_id': user['id'],
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
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }