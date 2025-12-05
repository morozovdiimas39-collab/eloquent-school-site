import json
import os
import psycopg2
from typing import Dict, Any

def get_db_connection():
    """Создает подключение к БД"""
    return psycopg2.connect(os.environ['DATABASE_URL'])

def create_user(telegram_user: Dict[str, Any], role: str):
    """Создает нового пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    telegram_id = telegram_user['id']
    username = telegram_user.get('username')
    first_name = telegram_user.get('first_name')
    last_name = telegram_user.get('last_name')
    
    cur.execute(
        "INSERT INTO users (telegram_id, username, first_name, last_name, role) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (telegram_id) DO UPDATE SET role = EXCLUDED.role",
        (telegram_id, username, first_name, last_name, role)
    )
    conn.commit()
    cur.close()
    conn.close()

def send_telegram_message(chat_id: int, text: str, message_id: int = None):
    """Отправляет или редактирует сообщение в Telegram"""
    import urllib.request
    
    token = os.environ['TELEGRAM_BOT_TOKEN']
    
    if message_id:
        url = f'https://api.telegram.org/bot{token}/editMessageText'
        data = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': 'HTML'
        }
    else:
        url = f'https://api.telegram.org/bot{token}/sendMessage'
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
    
    webapp_url = f"https://{os.environ.get('POEHALI_DOMAIN', 'localhost')}"
    data['reply_markup'] = json.dumps({
        'inline_keyboard': [
            [{'text': '📱 Открыть личный кабинет', 'web_app': {'url': webapp_url}}]
        ]
    })
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Обрабатывает callback_query от Telegram (выбор роли)
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
        
        if 'callback_query' not in body:
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'ok': True}),
                'isBase64Encoded': False
            }
        
        callback = body['callback_query']
        data = callback.get('data', '')
        chat_id = callback['message']['chat']['id']
        message_id = callback['message']['message_id']
        telegram_user = callback['from']
        
        if data.startswith('role_'):
            role = data.replace('role_', '')
            create_user(telegram_user, role)
            
            role_text = '👨‍🎓 Ученик' if role == 'student' else '👨‍🏫 Преподаватель'
            send_telegram_message(
                chat_id,
                f'✅ Отлично! Ты зарегистрирован как <b>{role_text}</b>\n\n'
                f'Теперь можешь задавать мне вопросы или открыть личный кабинет.',
                message_id
            )
        
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
