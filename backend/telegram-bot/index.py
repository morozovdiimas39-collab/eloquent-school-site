import json
import os
import psycopg2
import urllib.request
import urllib.parse
from typing import Dict, Any, List

def get_db_connection():
    """Создает подключение к БД"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.autocommit = True
    return conn

def get_user(telegram_id: int):
    """Получает пользователя из БД"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"SELECT telegram_id, username, first_name, last_name, role FROM users WHERE telegram_id = {telegram_id}")
    row = cur.fetchone()
    
    cur.close()
    conn.close()
    
    if row:
        return {
            'telegram_id': row[0],
            'username': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'role': row[4]
        }
    return None

def create_user(telegram_id: int, username: str, first_name: str, last_name: str, role: str):
    """Создает пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    username = username.replace("'", "''") if username else ''
    first_name = first_name.replace("'", "''") if first_name else ''
    last_name = last_name.replace("'", "''") if last_name else ''
    
    cur.execute(
        f"INSERT INTO users (telegram_id, username, first_name, last_name, role) "
        f"VALUES ({telegram_id}, '{username}', '{first_name}', '{last_name}', '{role}')"
    )
    
    cur.close()
    conn.close()

def get_conversation_history(user_id: int) -> List[Dict[str, str]]:
    """Получает историю диалога"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"SELECT id FROM conversations WHERE user_id = {user_id} ORDER BY updated_at DESC LIMIT 1")
    row = cur.fetchone()
    
    if not row:
        cur.close()
        conn.close()
        return []
    
    conversation_id = row[0]
    
    cur.execute(f"SELECT role, content FROM messages WHERE conversation_id = {conversation_id} ORDER BY created_at ASC LIMIT 20")
    
    history = [{'role': row[0], 'content': row[1]} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    return history

def save_message(user_id: int, role: str, content: str):
    """Сохраняет сообщение"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"SELECT id FROM conversations WHERE user_id = {user_id} ORDER BY updated_at DESC LIMIT 1")
    row = cur.fetchone()
    
    if row:
        conversation_id = row[0]
        cur.execute(f"UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = {conversation_id}")
    else:
        cur.execute(f"INSERT INTO conversations (user_id, title) VALUES ({user_id}, 'Новый диалог') RETURNING id")
        conversation_id = cur.fetchone()[0]
    
    content = content.replace("'", "''")
    cur.execute(f"INSERT INTO messages (conversation_id, role, content) VALUES ({conversation_id}, '{role}', '{content}')")
    
    cur.close()
    conn.close()

def call_yandex_gpt(user_message: str, history: List[Dict[str, str]]) -> str:
    """Вызывает YandexGPT API"""
    api_key = os.environ['YANDEX_CLOUD_API_KEY']
    folder_id = os.environ['YANDEX_CLOUD_FOLDER_ID']
    
    messages = []
    for msg in history[-10:]:
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

def send_telegram_message(chat_id: int, text: str, reply_markup=None):
    """Отправляет сообщение в Telegram"""
    token = os.environ['TELEGRAM_BOT_TOKEN']
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    
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

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Обработчик Telegram webhook - бот отвечает прямо в чате
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
        body = json.loads(event.get('body', '{}'))
        print(f"[DEBUG] Received update: {json.dumps(body)}")
        
        # Обработка callback_query (выбор роли)
        if 'callback_query' in body:
            callback = body['callback_query']
            data = callback.get('data', '')
            chat_id = callback['message']['chat']['id']
            message_id = callback['message']['message_id']
            user = callback['from']
            
            if data.startswith('role_'):
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
        
        # Команда /start
        if text == '/start':
            existing_user = get_user(user['id'])
            
            if not existing_user:
                # Регистрируем нового пользователя как ученика по умолчанию
                create_user(
                    user['id'],
                    user.get('username', ''),
                    user.get('first_name', ''),
                    user.get('last_name', ''),
                    'student'
                )
            
            # Отправляем приветствие с кнопкой открытия WebApp
            keyboard = {
                'inline_keyboard': [
                    [{'text': '📱 Открыть личный кабинет', 'web_app': {'url': 'https://anyagpt.poehali.dev'}}]
                ]
            }
            send_telegram_message(
                chat_id,
                '👋 Привет! Я AnyaGPT - AI-помощник на базе YandexGPT.\n\n'
                'Задавай мне любые вопросы прямо здесь в чате, и я отвечу!\n\n'
                'Чтобы изменить роль или посмотреть историю - открой личный кабинет 👇',
                keyboard
            )
        else:
            # Любое другое сообщение - обрабатываем через YandexGPT
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
            
            # Получаем ответ от YandexGPT
            history = get_conversation_history(user['id'])
            
            # Сохраняем вопрос пользователя
            save_message(user['id'], 'user', text)
            
            # Получаем ответ AI
            ai_response = call_yandex_gpt(text, history)
            
            # Сохраняем ответ AI
            save_message(user['id'], 'assistant', ai_response)
            
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