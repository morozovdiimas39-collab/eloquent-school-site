import json
import os
import psycopg2
import urllib.request
from typing import Dict, Any, List

def get_db_connection():
    """Создает подключение к БД"""
    return psycopg2.connect(os.environ['DATABASE_URL'])

def get_user(telegram_id: int) -> Dict[str, Any]:
    """Получает данные пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        "SELECT telegram_id, username, first_name, last_name, role FROM users WHERE telegram_id = %s",
        (telegram_id,)
    )
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
    """Создает нового пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        "INSERT INTO users (telegram_id, username, first_name, last_name, role) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (telegram_id) DO UPDATE SET role = EXCLUDED.role",
        (telegram_id, username, first_name, last_name, role)
    )
    conn.commit()
    
    cur.close()
    conn.close()

def get_conversation_history(user_id: int) -> List[Dict[str, str]]:
    """Получает историю диалога"""
    conn = get_db_connection()
    cur = conn.cursor()
    
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
    
    cur.execute(
        "SELECT role, content FROM messages WHERE conversation_id = %s ORDER BY created_at ASC LIMIT 20",
        (conversation_id,)
    )
    
    history = [{'role': row[0], 'content': row[1]} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    return history

def save_message(user_id: int, role: str, content: str):
    """Сохраняет сообщение"""
    conn = get_db_connection()
    cur = conn.cursor()
    
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
    
    cur.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
        (conversation_id, role, content)
    )
    
    conn.commit()
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

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    API для работы с чатом: регистрация, отправка сообщений, получение истории
    """
    method = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-Telegram-User',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    try:
        body = json.loads(event.get('body', '{}'))
        action = body.get('action')
        
        # Регистрация пользователя
        if action == 'register':
            user_data = body.get('user', {})
            role = body.get('role')
            
            if not user_data.get('id') or not role:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Missing user data or role'}),
                    'isBase64Encoded': False
                }
            
            create_user(
                user_data['id'],
                user_data.get('username', ''),
                user_data.get('first_name', ''),
                user_data.get('last_name', ''),
                role
            )
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'role': role}),
                'isBase64Encoded': False
            }
        
        # Получение данных пользователя
        if action == 'get_user':
            telegram_id = body.get('telegram_id')
            if not telegram_id:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Missing telegram_id'}),
                    'isBase64Encoded': False
                }
            
            user = get_user(telegram_id)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'user': user}),
                'isBase64Encoded': False
            }
        
        # Отправка сообщения
        if action == 'send_message':
            telegram_id = body.get('telegram_id')
            message = body.get('message')
            
            if not telegram_id or not message:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Missing telegram_id or message'}),
                    'isBase64Encoded': False
                }
            
            # Сохраняем сообщение пользователя
            save_message(telegram_id, 'user', message)
            
            # Получаем историю
            history = get_conversation_history(telegram_id)
            
            # Получаем ответ от YandexGPT
            ai_response = call_yandex_gpt(message, history)
            
            # Сохраняем ответ AI
            save_message(telegram_id, 'assistant', ai_response)
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'response': ai_response}),
                'isBase64Encoded': False
            }
        
        # Получение истории
        if action == 'get_history':
            telegram_id = body.get('telegram_id')
            if not telegram_id:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Missing telegram_id'}),
                    'isBase64Encoded': False
                }
            
            history = get_conversation_history(telegram_id)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'history': history}),
                'isBase64Encoded': False
            }
        
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Unknown action'}),
            'isBase64Encoded': False
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }
