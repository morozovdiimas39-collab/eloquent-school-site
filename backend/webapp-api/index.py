import json
import os
import psycopg2
import requests
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
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
    
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
    """Получает список всех студентов"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT telegram_id, username, first_name, last_name, created_at, "
        f"language_level, preferred_topics, timezone, photo_url "
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
            'created_at': row[4].isoformat() if row[4] else None,
            'language_level': row[5] or 'A1',
            'preferred_topics': row[6] if row[6] else [],
            'timezone': row[7] or 'UTC',
            'photo_url': row[8]
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
        f"COALESCE(wp.progress_status, 'new') as progress_status "
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
            'mastery_score': row[7],
            'attempts': row[8],
            'correct_uses': row[9],
            'progress_status': row[10]
        })
    
    cur.close()
    conn.close()
    return words

def get_student_progress_stats(student_id: int) -> Dict[str, Any]:
    """Получает статистику прогресса студента"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT "
        f"COUNT(*) as total_words, "
        f"COUNT(CASE WHEN COALESCE(wp.progress_status, 'new') = 'new' THEN 1 END) as new, "
        f"COUNT(CASE WHEN wp.progress_status = 'learning' THEN 1 END) as learning, "
        f"COUNT(CASE WHEN wp.progress_status = 'learned' THEN 1 END) as learned, "
        f"COUNT(CASE WHEN wp.progress_status = 'mastered' THEN 1 END) as mastered, "
        f"COALESCE(AVG(wp.mastery_score), 0) as average_mastery "
        f"FROM {SCHEMA}.student_words sw "
        f"LEFT JOIN {SCHEMA}.word_progress wp ON wp.student_id = sw.student_id AND wp.word_id = sw.word_id "
        f"WHERE sw.student_id = {student_id}"
    )
    
    row = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return {
        'total_words': row[0],
        'new': row[1],
        'learning': row[2],
        'learned': row[3],
        'mastered': row[4],
        'average_mastery': float(row[5]) if row[5] else 0.0
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
        
        elif action == 'get_student_words':
            student_id = body_data.get('student_id')
            words = get_student_words(student_id)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'words': words}),
                'isBase64Encoded': False
            }
        
        elif action == 'get_progress_stats':
            student_id = body_data.get('student_id')
            stats = get_student_progress_stats(student_id)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'success': True, 'stats': stats}),
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
        
        elif action == 'suggest_learning_goal':
            user_input = body_data.get('user_input', '')
            result = generate_learning_goal_suggestions(user_input)
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result),
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