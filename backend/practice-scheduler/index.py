import json
import os
import psycopg2
import urllib.request
import random
from datetime import datetime, timezone
from typing import Dict, Any, List

SCHEMA = 't_p86463701_eloquent_school_site'

def get_db_connection():
    """Создает подключение к БД"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.autocommit = True
    return conn

def get_students_for_practice() -> List[Dict[str, Any]]:
    """
    Получает список студентов, которым пора отправить практику
    Критерии: роль = student, последнее сообщение > 2 часов назад или NULL
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Получаем студентов, которым давно не писали (или вообще не писали)
    cur.execute(
        f"SELECT telegram_id, first_name, language_level, preferred_topics, timezone, last_practice_message "
        f"FROM {SCHEMA}.users "
        f"WHERE role = 'student' "
        f"AND (last_practice_message IS NULL OR last_practice_message < NOW() - INTERVAL '2 hours') "
        f"ORDER BY RANDOM() "
        f"LIMIT 50"
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
    Не отправляем с 23:00 до 7:00 по местному времени студента
    """
    # Упрощенная проверка - используем UTC время
    # В реальности нужно учитывать timezone студента
    current_hour = datetime.now(timezone.utc).hour
    
    # Не отправляем ночью (UTC 21:00 - 5:00)
    if current_hour >= 21 or current_hour < 5:
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

def generate_practice_prompt(student_name: str, language_level: str, preferred_topics: List[Dict[str, str]], session_words: List[Dict[str, Any]]) -> str:
    """Генерирует промпт для YandexGPT для создания проактивного сообщения"""
    
    level_instructions = {
        'A1': 'Use very simple words and short sentences.',
        'A2': 'Use simple everyday vocabulary and clear sentences.',
        'B1': 'Use common vocabulary and clear explanations.',
        'B2': 'Use varied vocabulary and natural expressions.',
        'C1': 'Use sophisticated vocabulary and complex structures.',
        'C2': 'Use native-level vocabulary and expressions.'
    }
    
    level_instruction = level_instructions.get(language_level, level_instructions['A1'])
    
    prompt = f"""You are Anya, a friendly English tutor. Generate a short, engaging message to start a conversation with {student_name}.

Language level: {language_level} ({level_instruction})

Requirements:
- Write 2-3 sentences maximum
- Be warm and enthusiastic
- Ask an interesting question to start conversation
- Sound natural and friendly, not like a robot"""
    
    if preferred_topics and len(preferred_topics) > 0:
        topic = random.choice(preferred_topics)
        prompt += f"\n- Try to relate your message to this topic: {topic['emoji']} {topic['topic']}"
    
    if session_words and len(session_words) > 0:
        words_sample = random.sample(session_words, min(2, len(session_words)))
        words_list = [f"{w['english']} ({w['russian']})" for w in words_sample]
        prompt += f"\n- Try to naturally use one of these words: {', '.join(words_list)}"
    
    prompt += "\n\nWrite only the message text, nothing else."
    
    return prompt

def call_yandex_gpt(prompt: str) -> str:
    """Вызывает YandexGPT для генерации сообщения"""
    api_key = os.environ['YANDEX_CLOUD_API_KEY']
    folder_id = os.environ['YANDEX_CLOUD_FOLDER_ID']
    
    payload = {
        'modelUri': f'gpt://{folder_id}/yandexgpt-lite',
        'completionOptions': {
            'stream': False,
            'temperature': 0.8,
            'maxTokens': 200
        },
        'messages': [
            {'role': 'user', 'text': prompt}
        ]
    }
    
    req = urllib.request.Request(
        'https://llm.api.cloud.yandex.net/foundationModels/v1/completion',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Api-Key {api_key}',
            'x-folder-id': folder_id
        }
    )
    
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result['result']['alternatives'][0]['message']['text']

def send_telegram_message(chat_id: int, text: str):
    """Отправляет сообщение в Telegram"""
    token = os.environ['TELEGRAM_BOT_TOKEN']
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    
    payload = {
        'chat_id': chat_id,
        'text': text
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
    Practice Scheduler - отправляет проактивные сообщения студентам
    Запускается по расписанию (каждый час)
    Отправляет 4-5 сообщений в день каждому студенту (не ночью)
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
        
        # Получаем студентов для практики
        students = get_students_for_practice()
        print(f"[INFO] Found {len(students)} students for practice")
        
        sent_count = 0
        skipped_count = 0
        
        for student in students:
            # Проверяем время
            if not is_appropriate_time(student['timezone']):
                skipped_count += 1
                print(f"[SKIP] Student {student['telegram_id']} - inappropriate time")
                continue
            
            # Получаем слова для практики
            session_words = get_session_words(student['telegram_id'], limit=5)
            
            # Генерируем промпт
            prompt = generate_practice_prompt(
                student['first_name'],
                student['language_level'],
                student['preferred_topics'],
                session_words
            )
            
            # Генерируем сообщение через YandexGPT
            try:
                message = call_yandex_gpt(prompt)
                print(f"[DEBUG] Generated message for {student['telegram_id']}: {message[:50]}...")
            except Exception as e:
                print(f"[ERROR] Failed to generate message for {student['telegram_id']}: {e}")
                continue
            
            # Отправляем сообщение
            success = send_telegram_message(student['telegram_id'], message)
            
            if success:
                update_last_practice_time(student['telegram_id'])
                sent_count += 1
                print(f"[SUCCESS] Sent practice message to {student['telegram_id']}")
            else:
                print(f"[ERROR] Failed to send message to {student['telegram_id']}")
            
            # Ограничиваем количество отправок за один запуск
            if sent_count >= 20:
                print("[INFO] Reached limit of 20 messages per run")
                break
        
        result = {
            'status': 'completed',
            'sent': sent_count,
            'skipped': skipped_count,
            'total_candidates': len(students)
        }
        
        print(f"[INFO] Practice scheduler finished: {json.dumps(result)}")
        
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
