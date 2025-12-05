import json
import os
import psycopg2
from typing import Dict, Any, List

def get_db_connection():
    """Создает подключение к БД"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.autocommit = True
    return conn

def get_user_info(telegram_id: int) -> Dict[str, Any]:
    """Получает информацию о пользователе"""
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

def change_user_role(telegram_id: int, new_role: str) -> bool:
    """Изменяет роль пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"UPDATE users SET role = '{new_role}', updated_at = CURRENT_TIMESTAMP WHERE telegram_id = {telegram_id}")
    
    cur.close()
    conn.close()
    return True

def get_full_history(telegram_id: int) -> List[Dict[str, Any]]:
    """Получает полную историю всех диалогов пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT c.id, c.title, c.created_at, c.updated_at "
        f"FROM conversations c "
        f"WHERE c.user_id = {telegram_id} "
        f"ORDER BY c.updated_at DESC"
    )
    
    conversations = []
    for row in cur.fetchall():
        conv_id = row[0]
        
        cur.execute(
            f"SELECT role, content, created_at FROM messages "
            f"WHERE conversation_id = {conv_id} "
            f"ORDER BY created_at ASC"
        )
        
        messages = [
            {
                'role': msg_row[0],
                'content': msg_row[1],
                'created_at': msg_row[2].isoformat() if msg_row[2] else None
            }
            for msg_row in cur.fetchall()
        ]
        
        conversations.append({
            'id': conv_id,
            'title': row[1],
            'created_at': row[2].isoformat() if row[2] else None,
            'updated_at': row[3].isoformat() if row[3] else None,
            'messages': messages
        })
    
    cur.close()
    conn.close()
    return conversations

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    API для WebApp личного кабинета
    Действия: get_user, change_role, get_history
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
        action = body.get('action')
        telegram_id = body.get('telegram_id')
        
        if not telegram_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'telegram_id is required'}),
                'isBase64Encoded': False
            }
        
        if action == 'get_user':
            user = get_user_info(telegram_id)
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'user': user}),
                'isBase64Encoded': False
            }
        
        elif action == 'change_role':
            new_role = body.get('role')
            if new_role not in ['student', 'teacher']:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'Invalid role'}),
                    'isBase64Encoded': False
                }
            
            change_user_role(telegram_id, new_role)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'success': True, 'role': new_role}),
                'isBase64Encoded': False
            }
        
        elif action == 'get_history':
            history = get_full_history(telegram_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'conversations': history}),
                'isBase64Encoded': False
            }
        
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Unknown action'}),
                'isBase64Encoded': False
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }
