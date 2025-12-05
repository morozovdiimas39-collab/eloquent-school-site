import json
import os
import psycopg2
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class User:
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    role: str

def get_db_connection():
    """Создает подключение к БД"""
    return psycopg2.connect(os.environ['DATABASE_URL'])

def get_or_create_user(telegram_user: Dict[str, Any]) -> Optional[User]:
    """Получает или создает пользователя в БД"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    telegram_id = telegram_user['id']
    username = telegram_user.get('username')
    first_name = telegram_user.get('first_name')
    last_name = telegram_user.get('last_name')
    
    # Проверяем существование пользователя
    cur.execute(
        "SELECT telegram_id, username, first_name, last_name, role FROM users WHERE telegram_id = %s",
        (telegram_id,)
    )
    row = cur.fetchone()
    
    if row:
        user = User(
            telegram_id=row[0],
            username=row[1],
            first_name=row[2],
            last_name=row[3],
            role=row[4]
        )
        cur.close()
        conn.close()
        return user
    
    cur.close()
    conn.close()
    return None

def create_user(telegram_user: Dict[str, Any], role: str) -> User:
    """Создает нового пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    telegram_id = telegram_user['id']
    username = telegram_user.get('username')
    first_name = telegram_user.get('first_name')
    last_name = telegram_user.get('last_name')
    
    cur.execute(
        "INSERT INTO users (telegram_id, username, first_name, last_name, role) VALUES (%s, %s, %s, %s, %s)",
        (telegram_id, username, first_name, last_name, role)
    )
    conn.commit()
    
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        role=role
    )
    
    cur.close()
    conn.close()
    return user

def send_telegram_message(chat_id: int, text: str, reply_markup: Optional[Dict] = None):
    """Отправляет сообщение в Telegram"""
    import urllib.request
    import urllib.parse
    
    token = os.environ['TELEGRAM_BOT_TOKEN']
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    if reply_markup:
        data['reply_markup'] = json.dumps(reply_markup)
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def call_yandex_gpt(user_message: str, conversation_history: list) -> str:
    """Вызывает YandexGPT API"""
    import urllib.request
    
    api_key = os.environ['YANDEX_CLOUD_API_KEY']
    folder_id = os.environ['YANDEX_CLOUD_FOLDER_ID']
    
    messages = []
    for msg in conversation_history[-10:]:  # Последние 10 сообщений
        messages.append({
            'role': msg['role'],
            'text': msg['content']
        })
    
    messages.append({
        'role': 'user',
        'text': user_message
    })
    
    payload = {
        'modelUri': f'gpt://{folder_id}/yandexgpt-lite',
        'completionOptions': {
            'stream': False,
            'temperature': 0.7,
            'maxTokens': 2000
        },
        'messages': messages
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

def get_conversation_history(user_id: int) -> list:
    """Получает историю последнего диалога пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Находим последний диалог
    cur.execute(
        "SELECT id FROM conversations WHERE user_id = %s ORDER BY updated_at DESC LIMIT 1",
        (user_id,)
    )
    row = cur.fetchone()
    
    if not row:
        cur.close()
        conn.close()
        return []
    
    conversation_id = row[0]
    
    # Получаем историю сообщений
    cur.execute(
        "SELECT role, content FROM messages WHERE conversation_id = %s ORDER BY created_at ASC",
        (conversation_id,)
    )
    
    history = [{'role': row[0], 'content': row[1]} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    return history

def save_message(user_id: int, role: str, content: str):
    """Сохраняет сообщение в БД"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Находим или создаем диалог
    cur.execute(
        "SELECT id FROM conversations WHERE user_id = %s ORDER BY updated_at DESC LIMIT 1",
        (user_id,)
    )
    row = cur.fetchone()
    
    if row:
        conversation_id = row[0]
        cur.execute(
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (conversation_id,)
        )
    else:
        cur.execute(
            "INSERT INTO conversations (user_id, title) VALUES (%s, %s) RETURNING id",
            (user_id, 'Новый диалог')
        )
        conversation_id = cur.fetchone()[0]
    
    # Сохраняем сообщение
    cur.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
        (conversation_id, role, content)
    )
    
    conn.commit()
    cur.close()
    conn.close()

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Обрабатывает webhook от Telegram бота
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
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    try:
        body = json.loads(event.get('body', '{}'))
        
        # Обработка callback_query (выбор роли)
        if 'callback_query' in body:
            callback = body['callback_query']
            data = callback.get('data', '')
            chat_id = callback['message']['chat']['id']
            message_id = callback['message']['message_id']
            telegram_user = callback['from']
            
            if data.startswith('role_'):
                role = data.replace('role_', '')
                create_user(telegram_user, role)
                
                webapp_url = f"https://{os.environ.get('POEHALI_DOMAIN', 'localhost')}"
                
                import urllib.request
                token = os.environ['TELEGRAM_BOT_TOKEN']
                url = f'https://api.telegram.org/bot{token}/editMessageText'
                
                role_text = '👨‍🎓 Ученик' if role == 'student' else '👨‍🏫 Преподаватель'
                edit_data = {
                    'chat_id': chat_id,
                    'message_id': message_id,
                    'text': f'✅ Отлично! Ты зарегистрирован как <b>{role_text}</b>\n\n'
                            f'Теперь можешь задавать мне вопросы или открыть личный кабинет.',
                    'parse_mode': 'HTML',
                    'reply_markup': json.dumps({
                        'inline_keyboard': [
                            [{'text': '📱 Открыть личный кабинет', 'web_app': {'url': webapp_url}}]
                        ]
                    })
                }
                
                req = urllib.request.Request(
                    url,
                    data=json.dumps(edit_data).encode('utf-8'),
                    headers={'Content-Type': 'application/json'}
                )
                
                with urllib.request.urlopen(req) as response:
                    response.read()
            
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
        telegram_user = message['from']
        text = message.get('text', '')
        
        # Проверяем пользователя
        user = get_or_create_user(telegram_user)
        
        if not user:
            # Новый пользователь - показываем выбор роли
            if text == '/start':
                keyboard = {
                    'inline_keyboard': [
                        [{'text': '👨‍🎓 Я ученик', 'callback_data': 'role_student'}],
                        [{'text': '👨‍🏫 Я преподаватель', 'callback_data': 'role_teacher'}]
                    ]
                }
                send_telegram_message(
                    chat_id,
                    '👋 Привет! Я AnyaGPT - твой AI-помощник.\n\nВыбери свою роль:',
                    keyboard
                )
            else:
                send_telegram_message(
                    chat_id,
                    'Пожалуйста, начни с команды /start'
                )
        else:
            # Существующий пользователь
            if text == '/start':
                webapp_url = f"https://{os.environ.get('POEHALI_DOMAIN', 'localhost')}"
                keyboard = {
                    'inline_keyboard': [
                        [{'text': '📱 Открыть личный кабинет', 'web_app': {'url': webapp_url}}]
                    ]
                }
                send_telegram_message(
                    chat_id,
                    f'С возвращением, {user.first_name}! 👋\n\nЗадай мне любой вопрос или открой личный кабинет.',
                    keyboard
                )
            else:
                # Обрабатываем сообщение через YandexGPT
                history = get_conversation_history(user.telegram_id)
                
                # Сохраняем сообщение пользователя
                save_message(user.telegram_id, 'user', text)
                
                # Получаем ответ от AI
                ai_response = call_yandex_gpt(text, history)
                
                # Сохраняем ответ AI
                save_message(user.telegram_id, 'assistant', ai_response)
                
                # Отправляем ответ
                send_telegram_message(chat_id, ai_response)
        
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