import json
import os
import psycopg2
import urllib.request
import random
from datetime import datetime
from typing import Dict, Any, List

SCHEMA = 't_p86463701_eloquent_school_site'

def get_db_connection():
    """Создает подключение к БД"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.autocommit = True
    return conn

def get_local_time_for_timezone(timezone_str: str) -> int:
    """Вычисляет локальный час для указанного timezone"""
    timezone_offsets = {
        'Europe/Kaliningrad': 2,
        'Europe/Moscow': 3,
        'Europe/Samara': 4,
        'Asia/Yekaterinburg': 5,
        'Asia/Omsk': 6,
        'Asia/Krasnoyarsk': 7,
        'Asia/Irkutsk': 8,
        'Asia/Yakutsk': 9,
        'Asia/Vladivostok': 10,
        'Asia/Magadan': 11,
        'Asia/Kamchatka': 12,
        'UTC': 0
    }
    
    utc_hour = datetime.utcnow().hour
    offset = timezone_offsets.get(timezone_str, 0)
    local_hour = (utc_hour + offset) % 24
    
    return local_hour

def count_messages_today(student_id: int) -> int:
    """Подсчитывает сколько проактивных сообщений уже отправлено сегодня"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT COUNT(*) FROM {SCHEMA}.anna_messages "
        f"WHERE student_id = {student_id} "
        f"AND DATE(sent_at) = CURRENT_DATE"
    )
    
    count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    return count

def log_anna_message(student_id: int, message_type: str):
    """Логирует отправленное сообщение от Ани"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"INSERT INTO {SCHEMA}.anna_messages (student_id, message_type, sent_at) "
        f"VALUES ({student_id}, '{message_type}', CURRENT_TIMESTAMP)"
    )
    
    cur.close()
    conn.close()

def get_students_for_practice() -> List[Dict[str, Any]]:
    """
    Получает список студентов для отправки проактивных сообщений
    Критерии: роль = student, последнее сообщение > 3 часов назад или NULL
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT telegram_id, first_name, language_level, preferred_topics, timezone, last_practice_message "
        f"FROM {SCHEMA}.users "
        f"WHERE role = 'student' "
        f"AND (last_practice_message IS NULL OR last_practice_message < NOW() - INTERVAL '3 hours') "
        f"ORDER BY RANDOM() "
        f"LIMIT 100"
    )
    
    students = []
    for row in cur.fetchall():
        students.append({
            'telegram_id': row[0],
            'first_name': row[1] or 'there',
            'language_level': row[2] or 'A1',
            'preferred_topics': row[3] if row[3] else [],
            'timezone': row[4] or 'UTC',
            'last_practice_message': row[5]
        })
    
    cur.close()
    conn.close()
    return students

def is_appropriate_time(student_timezone: str) -> bool:
    """
    Проверяет, подходящее ли время для отправки сообщения
    Не отправляем с 21:00 до 9:00 по местному времени студента
    """
    local_hour = get_local_time_for_timezone(student_timezone)
    
    # Проверяем диапазон 9:00 - 21:00
    if local_hour < 9 or local_hour >= 21:
        return False
    
    return True

def get_session_words(student_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """Получает слова для включения в проактивное сообщение"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT w.id, w.english_text, w.russian_translation FROM {SCHEMA}.word_progress wp "
        f"JOIN {SCHEMA}.words w ON w.id = wp.word_id "
        f"WHERE wp.student_id = {student_id} AND wp.status IN ('new', 'learning') "
        f"ORDER BY wp.created_at ASC LIMIT {limit}"
    )
    
    words = [{'id': row[0], 'english': row[1], 'russian': row[2]} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    return words

def generate_practice_prompt(message_type: str, student_name: str, language_level: str, preferred_topics: List[Dict[str, str]], session_words: List[Dict[str, Any]]) -> str:
    """Генерирует промпт для Gemini для создания проактивного сообщения"""
    
    level_instructions = {
        'A1': 'Use very simple words and short sentences.',
        'A2': 'Use simple everyday vocabulary and clear sentences.',
        'B1': 'Use common vocabulary and clear explanations.',
        'B2': 'Use varied vocabulary and natural expressions.',
        'C1': 'Use sophisticated vocabulary and complex structures.',
        'C2': 'Use native-level vocabulary and expressions.'
    }
    
    level_instruction = level_instructions.get(language_level, level_instructions['A1'])
    
    base_prompt = f"""You are Anya, a friendly English tutor. Generate a {message_type} to engage {student_name} in English practice.

Language level: {language_level} ({level_instruction})

Requirements:
- Write 2-4 sentences maximum
- Be warm, enthusiastic, and natural
- Use emoji naturally (but not too many!)
- Write ONLY in English"""
    
    if message_type == 'story':
        base_prompt += "\n- Share a SHORT interesting story or fun fact"
        base_prompt += "\n- Then ask: 'What do you think?' or similar"
    elif message_type == 'question':
        base_prompt += "\n- Ask an engaging open-ended question"
        base_prompt += "\n- Make it thought-provoking but appropriate for their level"
    elif message_type == 'quiz':
        base_prompt += "\n- Create a fun mini-quiz or word challenge"
        base_prompt += "\n- Make it interactive and educational"
    
    if preferred_topics and len(preferred_topics) > 0:
        topic = random.choice(preferred_topics)
        base_prompt += f"\n- Try to relate to this topic: {topic.get('emoji', '')} {topic.get('topic', '')}"
    
    if session_words and len(session_words) > 0:
        words_sample = random.sample(session_words, min(2, len(session_words)))
        words_list = [f"{w['english']} ({w['russian']})" for w in words_sample]
        base_prompt += f"\n- Try to naturally use 1-2 of these words: {', '.join(words_list)}"
    
    base_prompt += "\n\nWrite only the message text, nothing else."
    
    return base_prompt

def call_gemini(prompt: str) -> str:
    """Вызывает Gemini API через прокси"""
    api_key = os.environ['GEMINI_API_KEY']
    proxy_url = os.environ.get('PROXY_URL', '')
    
    payload = {
        'contents': [{
            'parts': [{'text': prompt}]
        }],
        'generationConfig': {
            'temperature': 0.9,
            'maxOutputTokens': 200
        }
    }
    
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}'
    
    if proxy_url:
        proxy_handler = urllib.request.ProxyHandler({'https': f'http://{proxy_url}'})
        opener = urllib.request.build_opener(proxy_handler)
        urllib.request.install_opener(opener)
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result['candidates'][0]['content']['parts'][0]['text']

def send_telegram_message(chat_id: int, text: str):
    """Отправляет сообщение в Telegram"""
    token = os.environ['TELEGRAM_BOT_TOKEN']
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
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
            return result.get('ok', False)
    except Exception as e:
        print(f"[ERROR] Failed to send message to {chat_id}: {e}")
        return False

def update_last_practice_time(telegram_id: int):
    """Обновляет время последнего проактивного сообщения"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"UPDATE {SCHEMA}.users SET last_practice_message = CURRENT_TIMESTAMP WHERE telegram_id = {telegram_id}"
    )
    
    cur.close()
    conn.close()

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Practice Scheduler - отправляет проактивные сообщения от Ани студентам
    Запускается по cron (каждые 3 часа)
    Отправляет 4-5 сообщений в день каждому студенту (9:00 - 21:00 по их времени)
    """
    method = event.get('httpMethod', 'POST')
    
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
        print("[INFO] Practice scheduler started")
        
        students = get_students_for_practice()
        print(f"[INFO] Found {len(students)} students for practice")
        
        sent_count = 0
        skipped_count = 0
        
        for student in students:
            # Проверяем локальное время
            if not is_appropriate_time(student['timezone']):
                skipped_count += 1
                print(f"[SKIP] Student {student['telegram_id']} - inappropriate time (timezone: {student['timezone']})")
                continue
            
            # Проверяем лимит сообщений за день (макс 5)
            messages_today = count_messages_today(student['telegram_id'])
            if messages_today >= 5:
                skipped_count += 1
                print(f"[SKIP] Student {student['telegram_id']} - daily limit reached ({messages_today}/5)")
                continue
            
            # Выбираем тип сообщения случайным образом
            message_types = ['story', 'question', 'quiz']
            message_type = random.choice(message_types)
            
            # Получаем слова для практики
            session_words = get_session_words(student['telegram_id'], limit=5)
            
            # Генерируем промпт
            prompt = generate_practice_prompt(
                message_type,
                student['first_name'],
                student['language_level'],
                student['preferred_topics'],
                session_words
            )
            
            # Генерируем сообщение через Gemini
            try:
                message = call_gemini(prompt)
                print(f"[DEBUG] Generated {message_type} for {student['telegram_id']}: {message[:50]}...")
                
                # Отправляем через Telegram
                if send_telegram_message(student['telegram_id'], message):
                    update_last_practice_time(student['telegram_id'])
                    log_anna_message(student['telegram_id'], message_type)
                    sent_count += 1
                    print(f"[SUCCESS] Sent {message_type} to {student['telegram_id']}")
                else:
                    print(f"[ERROR] Failed to send to {student['telegram_id']}")
                    
            except Exception as e:
                print(f"[ERROR] Failed to generate/send message for {student['telegram_id']}: {e}")
                continue
        
        result = {
            'success': True,
            'sent': sent_count,
            'skipped': skipped_count,
            'total_students': len(students)
        }
        
        print(f"[INFO] Practice scheduler finished: sent={sent_count}, skipped={skipped_count}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result),
            'isBase64Encoded': False
        }
        
    except Exception as e:
        print(f"[ERROR] Practice scheduler failed: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }
