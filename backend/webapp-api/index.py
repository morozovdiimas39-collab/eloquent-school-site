import json
import os
import psycopg2
import random
import string
from typing import Dict, Any, List

SCHEMA = 't_p86463701_eloquent_school_site'

def get_db_connection():
    """Создает подключение к БД"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.autocommit = True
    return conn

def generate_promocode() -> str:
    """Генерирует уникальный промокод"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def get_user_info(telegram_id: int) -> Dict[str, Any]:
    """Получает информацию о пользователе"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"SELECT telegram_id, username, first_name, last_name, role, promocode, teacher_id FROM {SCHEMA}.users WHERE telegram_id = {telegram_id}")
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
            'promocode': row[5],
            'teacher_id': row[6]
        }
    return None

def change_user_role(telegram_id: int, new_role: str) -> bool:
    """Изменяет роль пользователя и генерирует промокод для учителя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    if new_role == 'teacher':
        promocode = generate_promocode()
        cur.execute(f"UPDATE {SCHEMA}.users SET role = '{new_role}', promocode = '{promocode}', updated_at = CURRENT_TIMESTAMP WHERE telegram_id = {telegram_id}")
    else:
        cur.execute(f"UPDATE {SCHEMA}.users SET role = '{new_role}', updated_at = CURRENT_TIMESTAMP WHERE telegram_id = {telegram_id}")
    
    cur.close()
    conn.close()
    return True

def bind_teacher(telegram_id: int, promocode: str) -> Dict[str, Any]:
    """Привязывает ученика к учителю по промокоду"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Находим учителя по промокоду
    cur.execute(f"SELECT telegram_id FROM {SCHEMA}.users WHERE promocode = '{promocode}' AND role = 'teacher'")
    teacher_row = cur.fetchone()
    
    if not teacher_row:
        cur.close()
        conn.close()
        return {'success': False, 'error': 'Промокод не найден или недействителен'}
    
    teacher_id = teacher_row[0]
    
    # Привязываем ученика к учителю
    cur.execute(f"UPDATE {SCHEMA}.users SET teacher_id = {teacher_id}, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = {telegram_id}")
    
    cur.close()
    conn.close()
    return {'success': True, 'teacher_id': teacher_id}

def get_students(teacher_id: int) -> List[Dict[str, Any]]:
    """Получает список всех учеников преподавателя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT telegram_id, username, first_name, last_name, created_at "
        f"FROM {SCHEMA}.users "
        f"WHERE teacher_id = {teacher_id} AND role = 'student' "
        f"ORDER BY created_at DESC"
    )
    
    students = []
    for row in cur.fetchall():
        students.append({
            'telegram_id': row[0],
            'username': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'created_at': row[4].isoformat() if row[4] else None
        })
    
    cur.close()
    conn.close()
    return students

def get_all_teachers() -> List[Dict[str, Any]]:
    """Получает список всех преподавателей с количеством учеников"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT u.telegram_id, u.username, u.first_name, u.last_name, u.promocode, u.created_at, "
        f"COUNT(s.telegram_id) as students_count "
        f"FROM {SCHEMA}.users u "
        f"LEFT JOIN {SCHEMA}.users s ON s.teacher_id = u.telegram_id AND s.role = 'student' "
        f"WHERE u.role = 'teacher' "
        f"GROUP BY u.telegram_id, u.username, u.first_name, u.last_name, u.promocode, u.created_at "
        f"ORDER BY u.created_at DESC"
    )
    
    teachers = []
    for row in cur.fetchall():
        teachers.append({
            'telegram_id': row[0],
            'username': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'role': 'teacher',
            'promocode': row[4],
            'created_at': row[5].isoformat() if row[5] else None,
            'students_count': row[6]
        })
    
    cur.close()
    conn.close()
    return teachers

def get_all_students() -> List[Dict[str, Any]]:
    """Получает список всех учеников"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT telegram_id, username, first_name, last_name, teacher_id, created_at "
        f"FROM {SCHEMA}.users "
        f"WHERE role = 'student' "
        f"ORDER BY created_at DESC"
    )
    
    students = []
    for row in cur.fetchall():
        students.append({
            'telegram_id': row[0],
            'username': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'role': 'student',
            'teacher_id': row[4],
            'created_at': row[5].isoformat() if row[5] else None
        })
    
    cur.close()
    conn.close()
    return students

def get_full_history(telegram_id: int) -> List[Dict[str, Any]]:
    """Получает полную историю всех диалогов пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT c.id, c.title, c.created_at, c.updated_at "
        f"FROM {SCHEMA}.conversations c "
        f"WHERE c.user_id = {telegram_id} "
        f"ORDER BY c.updated_at DESC"
    )
    
    conversations = []
    for row in cur.fetchall():
        conv_id = row[0]
        
        cur.execute(
            f"SELECT role, content, created_at FROM {SCHEMA}.messages "
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
    Действия: get_user, change_role, get_history, bind_teacher, get_students, get_all_teachers, get_all_students
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
        
        if not telegram_id and action not in ['get_all_teachers', 'get_all_students']:
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
            updated_user = get_user_info(telegram_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'success': True, 'user': updated_user}),
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
        
        elif action == 'bind_teacher':
            promocode = body.get('promocode')
            if not promocode:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'Промокод обязателен'}),
                    'isBase64Encoded': False
                }
            
            result = bind_teacher(telegram_id, promocode)
            
            if result['success']:
                updated_user = get_user_info(telegram_id)
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'success': True, 'user': updated_user}),
                    'isBase64Encoded': False
                }
            else:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps(result),
                    'isBase64Encoded': False
                }
        
        elif action == 'get_students':
            students = get_students(telegram_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'students': students}),
                'isBase64Encoded': False
            }
        
        elif action == 'get_all_teachers':
            teachers = get_all_teachers()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'teachers': teachers}),
                'isBase64Encoded': False
            }
        
        elif action == 'get_all_students':
            students = get_all_students()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'students': students}),
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