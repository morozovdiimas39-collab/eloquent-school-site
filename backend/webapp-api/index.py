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
    
    cur.execute(f"SELECT telegram_id, username, first_name, last_name, role, promocode, teacher_id, language_level, preferred_topics, timezone, phone, card_number, bank_name FROM {SCHEMA}.users WHERE telegram_id = {telegram_id}")
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
            'teacher_id': row[6],
            'language_level': row[7],
            'preferred_topics': row[8] if row[8] else [],
            'timezone': row[9],
            'phone': row[10],
            'card_number': row[11],
            'bank_name': row[12]
        }
    return None

def change_user_role(telegram_id: int, new_role: str, username: str = '', first_name: str = '', last_name: str = '') -> bool:
    """Изменяет роль пользователя (или создает если не существует) и генерирует промокод для учителя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Проверяем существует ли пользователь
    cur.execute(f"SELECT telegram_id FROM {SCHEMA}.users WHERE telegram_id = {telegram_id}")
    user_exists = cur.fetchone()
    
    if not user_exists:
        # Создаем нового пользователя
        username_escaped = username.replace("'", "''") if username else ''
        first_name_escaped = first_name.replace("'", "''") if first_name else ''
        last_name_escaped = last_name.replace("'", "''") if last_name else ''
        
        if new_role == 'teacher':
            promocode = generate_promocode()
            cur.execute(
                f"INSERT INTO {SCHEMA}.users (telegram_id, username, first_name, last_name, role, promocode) "
                f"VALUES ({telegram_id}, '{username_escaped}', '{first_name_escaped}', '{last_name_escaped}', '{new_role}', '{promocode}')"
            )
        else:
            cur.execute(
                f"INSERT INTO {SCHEMA}.users (telegram_id, username, first_name, last_name, role) "
                f"VALUES ({telegram_id}, '{username_escaped}', '{first_name_escaped}', '{last_name_escaped}', '{new_role}')"
            )
    else:
        # Обновляем существующего пользователя
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
        f"u.phone, u.card_number, u.bank_name, u.photo_url, "
        f"COUNT(s.telegram_id) as students_count "
        f"FROM {SCHEMA}.users u "
        f"LEFT JOIN {SCHEMA}.users s ON s.teacher_id = u.telegram_id AND s.role = 'student' "
        f"WHERE u.role = 'teacher' "
        f"GROUP BY u.telegram_id, u.username, u.first_name, u.last_name, u.promocode, u.created_at, "
        f"u.phone, u.card_number, u.bank_name, u.photo_url "
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
            'phone': row[6],
            'card_number': row[7],
            'bank_name': row[8],
            'photo_url': row[9],
            'students_count': row[10]
        })
    
    cur.close()
    conn.close()
    return teachers

def get_all_students() -> List[Dict[str, Any]]:
    """Получает список всех учеников"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT telegram_id, username, first_name, last_name, teacher_id, created_at, "
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
            'role': 'student',
            'teacher_id': row[4],
            'created_at': row[5].isoformat() if row[5] else None,
            'language_level': row[6],
            'preferred_topics': row[7] if row[7] else [],
            'timezone': row[8],
            'photo_url': row[9]
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
        f"INSERT INTO {SCHEMA}.categories (name, description) VALUES ('{name_escaped}', {desc_value})"
        f" RETURNING id, name, description, created_at"
    )
    
    row = cur.fetchone()
    category = {
        'id': row[0],
        'name': row[1],
        'description': row[2],
        'created_at': row[3].isoformat() if row[3] else None
    }
    
    cur.close()
    conn.close()
    return category

def update_category(category_id: int, name: str, description: str = None) -> Dict[str, Any]:
    """Обновляет категорию"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    name_escaped = name.replace("'", "''")
    if description is None:
        desc_value = 'NULL'
    else:
        desc_escaped = description.replace("'", "''")
        desc_value = f"'{desc_escaped}'"
    
    cur.execute(
        f"UPDATE {SCHEMA}.categories SET name = '{name_escaped}', "
        f"description = {desc_value} "
        f"WHERE id = {category_id} RETURNING id, name, description, created_at"
    )
    
    row = cur.fetchone()
    category = {
        'id': row[0],
        'name': row[1],
        'description': row[2],
        'created_at': row[3].isoformat() if row[3] else None
    }
    
    cur.close()
    conn.close()
    return category

def search_words(search_query: str = None, category_id: int = None, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """Поиск слов с пагинацией"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    where_parts = []
    if search_query:
        search_escaped = search_query.replace("'", "''")
        where_parts.append(f"(english_text ILIKE '%{search_escaped}%' OR russian_translation ILIKE '%{search_escaped}%')")
    
    if category_id is not None:
        if category_id == 0:
            where_parts.append("category_id IS NULL")
        else:
            where_parts.append(f"category_id = {category_id}")
    
    where_clause = " AND ".join(where_parts) if where_parts else "1=1"
    
    cur.execute(
        f"SELECT COUNT(*) FROM {SCHEMA}.words WHERE {where_clause}"
    )
    total_count = cur.fetchone()[0]
    
    cur.execute(
        f"SELECT id, category_id, english_text, russian_translation, created_at "
        f"FROM {SCHEMA}.words WHERE {where_clause} "
        f"ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}"
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
    
    return {
        'words': words,
        'total': total_count,
        'limit': limit,
        'offset': offset
    }

def create_word(english_text: str, russian_translation: str, category_id: int = None) -> Dict[str, Any]:
    """Создает новое слово"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    english_text_escaped = english_text.replace("'", "''")
    russian_translation_escaped = russian_translation.replace("'", "''")
    
    if category_id is None or category_id == 0:
        cat_value = 'NULL'
    else:
        cat_value = str(category_id)
    
    cur.execute(
        f"INSERT INTO {SCHEMA}.words (category_id, english_text, russian_translation) "
        f"VALUES ({cat_value}, '{english_text_escaped}', '{russian_translation_escaped}') "
        f"RETURNING id, category_id, english_text, russian_translation, created_at"
    )
    
    row = cur.fetchone()
    word = {
        'id': row[0],
        'category_id': row[1],
        'english_text': row[2],
        'russian_translation': row[3],
        'created_at': row[4].isoformat() if row[4] else None
    }
    
    cur.close()
    conn.close()
    return word

def update_word(word_id: int, english_text: str, russian_translation: str) -> Dict[str, Any]:
    """Обновляет слово"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    english_text_escaped = english_text.replace("'", "''")
    russian_translation_escaped = russian_translation.replace("'", "''")
    
    cur.execute(
        f"UPDATE {SCHEMA}.words SET english_text = '{english_text_escaped}', "
        f"russian_translation = '{russian_translation_escaped}' "
        f"WHERE id = {word_id} "
        f"RETURNING id, category_id, english_text, russian_translation, created_at"
    )
    
    row = cur.fetchone()
    word = {
        'id': row[0],
        'category_id': row[1],
        'english_text': row[2],
        'russian_translation': row[3],
        'created_at': row[4].isoformat() if row[4] else None
    }
    
    cur.close()
    conn.close()
    return word

def assign_words_to_student(teacher_id: int, student_id: int, word_ids: List[int]) -> Dict[str, Any]:
    """Назначает слова ученику от преподавателя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    assigned_count = 0
    for word_id in word_ids:
        try:
            cur.execute(
                f"INSERT INTO {SCHEMA}.student_words (student_id, word_id, teacher_id) "
                f"VALUES ({student_id}, {word_id}, {teacher_id}) "
                f"ON CONFLICT (student_id, word_id) DO NOTHING"
            )
            assigned_count += 1
        except Exception:
            pass
    
    cur.close()
    conn.close()
    return {'success': True, 'assigned_count': assigned_count}

def assign_category_to_student(teacher_id: int, student_id: int, category_id: int) -> Dict[str, Any]:
    """Назначает все слова из категории ученику"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT id FROM {SCHEMA}.words WHERE category_id = {category_id}"
    )
    
    word_ids = [row[0] for row in cur.fetchall()]
    
    assigned_count = 0
    for word_id in word_ids:
        try:
            cur.execute(
                f"INSERT INTO {SCHEMA}.student_words (student_id, word_id, teacher_id) "
                f"VALUES ({student_id}, {word_id}, {teacher_id}) "
                f"ON CONFLICT (student_id, word_id) DO NOTHING"
            )
            assigned_count += 1
        except Exception:
            pass
    
    cur.close()
    conn.close()
    return {'success': True, 'assigned_count': assigned_count}

def get_student_words(student_id: int) -> List[Dict[str, Any]]:
    """Получает все назначенные слова для ученика с прогрессом"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT sw.id, sw.word_id, w.english_text, w.russian_translation, "
        f"w.category_id, sw.assigned_at, sw.status, "
        f"COALESCE(wp.mastery_score, 0) as mastery_score, "
        f"COALESCE(wp.attempts, 0) as attempts, "
        f"COALESCE(wp.correct_uses, 0) as correct_uses, "
        f"COALESCE(wp.status, 'new') as progress_status "
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
            'mastery_score': float(row[7]),
            'attempts': row[8],
            'correct_uses': row[9],
            'progress_status': row[10]
        })
    
    cur.close()
    conn.close()
    return words

def get_session_words(student_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Формирует пул слов для практики в сессии по алгоритму интервального повторения
    40% новые, 40% на повторение, 20% освоенные
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Инициализируем прогресс для слов, которые еще не были в практике
    cur.execute(
        f"INSERT INTO {SCHEMA}.word_progress (student_id, word_id) "
        f"SELECT sw.student_id, sw.word_id FROM {SCHEMA}.student_words sw "
        f"WHERE sw.student_id = {student_id} "
        f"AND NOT EXISTS (SELECT 1 FROM {SCHEMA}.word_progress wp WHERE wp.student_id = sw.student_id AND wp.word_id = sw.word_id)"
    )
    
    # Новые слова (40%)
    new_limit = max(1, int(limit * 0.4))
    cur.execute(
        f"SELECT w.id, w.english_text, w.russian_translation, w.category_id, wp.status, wp.mastery_score "
        f"FROM {SCHEMA}.word_progress wp "
        f"JOIN {SCHEMA}.words w ON w.id = wp.word_id "
        f"WHERE wp.student_id = {student_id} AND wp.status = 'new' "
        f"ORDER BY wp.created_at ASC LIMIT {new_limit}"
    )
    new_words = cur.fetchall()
    
    # Слова на повторение (40%)
    review_limit = max(1, int(limit * 0.4))
    cur.execute(
        f"SELECT w.id, w.english_text, w.russian_translation, w.category_id, wp.status, wp.mastery_score "
        f"FROM {SCHEMA}.word_progress wp "
        f"JOIN {SCHEMA}.words w ON w.id = wp.word_id "
        f"WHERE wp.student_id = {student_id} "
        f"AND wp.status IN ('learning', 'learned') "
        f"AND wp.next_review_date <= CURRENT_TIMESTAMP "
        f"ORDER BY wp.next_review_date ASC LIMIT {review_limit}"
    )
    review_words = cur.fetchall()
    
    # Освоенные слова для поддержания (20%)
    mastered_limit = max(1, limit - len(new_words) - len(review_words))
    cur.execute(
        f"SELECT w.id, w.english_text, w.russian_translation, w.category_id, wp.status, wp.mastery_score "
        f"FROM {SCHEMA}.word_progress wp "
        f"JOIN {SCHEMA}.words w ON w.id = wp.word_id "
        f"WHERE wp.student_id = {student_id} AND wp.status = 'mastered' "
        f"ORDER BY wp.last_practiced ASC NULLS FIRST LIMIT {mastered_limit}"
    )
    mastered_words = cur.fetchall()
    
    all_words = list(new_words) + list(review_words) + list(mastered_words)
    
    words = []
    for row in all_words:
        words.append({
            'id': row[0],
            'english_text': row[1],
            'russian_translation': row[2],
            'category_id': row[3],
            'status': row[4],
            'mastery_score': float(row[5])
        })
    
    cur.close()
    conn.close()
    return words

def record_word_usage(student_id: int, word_id: int, is_correct: bool, context: str = None) -> Dict[str, Any]:
    """
    Записывает использование слова учеником и обновляет прогресс
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Инициализируем запись если её нет
    cur.execute(
        f"INSERT INTO {SCHEMA}.word_progress (student_id, word_id) "
        f"VALUES ({student_id}, {word_id}) "
        f"ON CONFLICT (student_id, word_id) DO NOTHING"
    )
    
    # Обновляем статистику
    if is_correct:
        cur.execute(
            f"UPDATE {SCHEMA}.word_progress SET "
            f"attempts = attempts + 1, "
            f"correct_uses = correct_uses + 1, "
            f"last_practiced = CURRENT_TIMESTAMP, "
            f"updated_at = CURRENT_TIMESTAMP "
            f"WHERE student_id = {student_id} AND word_id = {word_id}"
        )
    else:
        cur.execute(
            f"UPDATE {SCHEMA}.word_progress SET "
            f"attempts = attempts + 1, "
            f"last_practiced = CURRENT_TIMESTAMP, "
            f"updated_at = CURRENT_TIMESTAMP "
            f"WHERE student_id = {student_id} AND word_id = {word_id}"
        )
    
    # Получаем текущие данные для пересчета
    cur.execute(
        f"SELECT attempts, correct_uses, status FROM {SCHEMA}.word_progress "
        f"WHERE student_id = {student_id} AND word_id = {word_id}"
    )
    row = cur.fetchone()
    attempts, correct_uses, current_status = row[0], row[1], row[2]
    
    # Рассчитываем mastery_score
    if attempts > 0:
        mastery_score = min(100, (correct_uses / attempts) * 100)
    else:
        mastery_score = 0
    
    # Определяем новый статус
    new_status = current_status
    if mastery_score >= 75 and correct_uses >= 5:
        new_status = 'mastered'
    elif mastery_score >= 50:
        new_status = 'learned'
    elif attempts > 0:
        new_status = 'learning'
    
    # Рассчитываем интервал до следующего повторения (spaced repetition)
    if new_status == 'mastered':
        interval_days = 30
    elif new_status == 'learned':
        interval_days = 7
    elif new_status == 'learning':
        interval_days = 3 if is_correct else 1
    else:
        interval_days = 1
    
    # Обновляем прогресс
    cur.execute(
        f"UPDATE {SCHEMA}.word_progress SET "
        f"mastery_score = {mastery_score}, "
        f"status = '{new_status}', "
        f"next_review_date = CURRENT_TIMESTAMP + INTERVAL '{interval_days} days', "
        f"updated_at = CURRENT_TIMESTAMP "
        f"WHERE student_id = {student_id} AND word_id = {word_id}"
    )
    
    cur.close()
    conn.close()
    
    return {
        'success': True,
        'mastery_score': mastery_score,
        'status': new_status,
        'next_review_days': interval_days
    }

def get_student_progress_stats(student_id: int) -> Dict[str, Any]:
    """Получает общую статистику прогресса ученика"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Инициализируем прогресс для слов, которые еще не были в практике
    cur.execute(
        f"INSERT INTO {SCHEMA}.word_progress (student_id, word_id) "
        f"SELECT sw.student_id, sw.word_id FROM {SCHEMA}.student_words sw "
        f"WHERE sw.student_id = {student_id} "
        f"AND NOT EXISTS (SELECT 1 FROM {SCHEMA}.word_progress wp WHERE wp.student_id = sw.student_id AND wp.word_id = sw.word_id)"
    )
    
    # Общее количество назначенных слов
    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.student_words WHERE student_id = {student_id}")
    total_words = cur.fetchone()[0]
    
    # Статистика по статусам
    cur.execute(
        f"SELECT status, COUNT(*) FROM {SCHEMA}.word_progress "
        f"WHERE student_id = {student_id} GROUP BY status"
    )
    status_counts = {row[0]: row[1] for row in cur.fetchall()}
    
    # Средний mastery_score
    cur.execute(
        f"SELECT AVG(mastery_score) FROM {SCHEMA}.word_progress WHERE student_id = {student_id}"
    )
    avg_mastery_result = cur.fetchone()[0]
    avg_mastery = float(avg_mastery_result) if avg_mastery_result is not None else 0.0
    
    # Streak данные
    cur.execute(
        f"SELECT current_streak, longest_streak, total_practice_days FROM {SCHEMA}.practice_streaks "
        f"WHERE student_id = {student_id}"
    )
    streak_row = cur.fetchone()
    if streak_row:
        current_streak = streak_row[0]
        longest_streak = streak_row[1]
        total_practice_days = streak_row[2]
    else:
        current_streak = 0
        longest_streak = 0
        total_practice_days = 0
    
    # Статистика за последние 7 дней
    cur.execute(
        f"SELECT practice_date, messages_sent, words_practiced, errors_corrected "
        f"FROM {SCHEMA}.daily_stats "
        f"WHERE student_id = {student_id} AND practice_date >= CURRENT_DATE - INTERVAL '7 days' "
        f"ORDER BY practice_date DESC"
    )
    daily_stats = []
    for row in cur.fetchall():
        daily_stats.append({
            'date': row[0].isoformat(),
            'messages': row[1],
            'words': row[2],
            'errors': row[3]
        })
    
    # Достижения
    cur.execute(
        f"SELECT a.code, a.title_en, a.title_ru, a.emoji, a.points, ua.unlocked_at "
        f"FROM {SCHEMA}.user_achievements ua "
        f"JOIN {SCHEMA}.achievements a ON a.code = ua.achievement_code "
        f"WHERE ua.student_id = {student_id} "
        f"ORDER BY ua.unlocked_at DESC"
    )
    achievements = []
    total_points = 0
    for row in cur.fetchall():
        achievements.append({
            'code': row[0],
            'title_en': row[1],
            'title_ru': row[2],
            'emoji': row[3],
            'points': row[4],
            'unlocked_at': row[5].isoformat() if row[5] else None
        })
        total_points += row[4]
    
    cur.close()
    conn.close()
    
    return {
        'total_words': total_words,
        'new': status_counts.get('new', 0),
        'learning': status_counts.get('learning', 0),
        'learned': status_counts.get('learned', 0),
        'mastered': status_counts.get('mastered', 0),
        'average_mastery': avg_mastery,
        'current_streak': current_streak,
        'longest_streak': longest_streak,
        'total_practice_days': total_practice_days,
        'daily_stats': daily_stats,
        'achievements': achievements,
        'total_points': total_points
    }

def update_student_settings(telegram_id: int, language_level: str = None, preferred_topics: List[Dict[str, str]] = None, timezone: str = None) -> Dict[str, Any]:
    """Обновляет настройки ученика"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    updates = []
    if language_level:
        updates.append(f"language_level = '{language_level}'")
    if preferred_topics is not None:
        topics_json = json.dumps(preferred_topics).replace("'", "''")
        updates.append(f"preferred_topics = '{topics_json}'::jsonb")
    if timezone:
        timezone_escaped = timezone.replace("'", "''")
        updates.append(f"timezone = '{timezone_escaped}'")
    
    if updates:
        update_sql = ", ".join(updates)
        cur.execute(f"UPDATE {SCHEMA}.users SET {update_sql}, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = {telegram_id}")
    
    cur.close()
    conn.close()
    return {'success': True}

def update_daily_stats(student_id: int, messages: int = 0, words: int = 0, errors: int = 0):
    """Обновляет ежедневную статистику студента"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"INSERT INTO {SCHEMA}.daily_stats (student_id, practice_date, messages_sent, words_practiced, errors_corrected) "
        f"VALUES ({student_id}, CURRENT_DATE, {messages}, {words}, {errors}) "
        f"ON CONFLICT (student_id, practice_date) DO UPDATE SET "
        f"messages_sent = {SCHEMA}.daily_stats.messages_sent + {messages}, "
        f"words_practiced = {SCHEMA}.daily_stats.words_practiced + {words}, "
        f"errors_corrected = {SCHEMA}.daily_stats.errors_corrected + {errors}"
    )
    
    cur.close()
    conn.close()

def update_practice_streak(student_id: int):
    """Обновляет streak студента"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Получаем текущий streak
    cur.execute(
        f"SELECT current_streak, longest_streak, last_practice_date, total_practice_days "
        f"FROM {SCHEMA}.practice_streaks WHERE student_id = {student_id}"
    )
    row = cur.fetchone()
    
    if row:
        current_streak = row[0]
        longest_streak = row[1]
        last_practice_date = row[2]
        total_practice_days = row[3]
        
        # Проверяем дату последней практики
        from datetime import date, timedelta
        today = date.today()
        
        if last_practice_date == today:
            # Уже практиковался сегодня, ничего не делаем
            cur.close()
            conn.close()
            return current_streak
        elif last_practice_date == today - timedelta(days=1):
            # Практиковался вчера, увеличиваем streak
            current_streak += 1
            total_practice_days += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            # Пропустил дни, сбрасываем streak
            current_streak = 1
            total_practice_days += 1
        
        cur.execute(
            f"UPDATE {SCHEMA}.practice_streaks SET "
            f"current_streak = {current_streak}, "
            f"longest_streak = {longest_streak}, "
            f"last_practice_date = CURRENT_DATE, "
            f"total_practice_days = {total_practice_days}, "
            f"updated_at = CURRENT_TIMESTAMP "
            f"WHERE student_id = {student_id}"
        )
    else:
        # Первая практика
        current_streak = 1
        cur.execute(
            f"INSERT INTO {SCHEMA}.practice_streaks (student_id, current_streak, longest_streak, last_practice_date, total_practice_days) "
            f"VALUES ({student_id}, 1, 1, CURRENT_DATE, 1)"
        )
    
    cur.close()
    conn.close()
    return current_streak

def check_and_unlock_achievements(student_id: int):
    """Проверяет и разблокирует достижения"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Получаем статистику
    cur.execute(
        f"SELECT current_streak, total_practice_days FROM {SCHEMA}.practice_streaks WHERE student_id = {student_id}"
    )
    streak_row = cur.fetchone()
    
    cur.execute(
        f"SELECT COUNT(*) FROM {SCHEMA}.word_progress WHERE student_id = {student_id} AND status IN ('learned', 'mastered')"
    )
    learned_words = cur.fetchone()[0]
    
    cur.execute(
        f"SELECT SUM(messages_sent) FROM {SCHEMA}.daily_stats WHERE student_id = {student_id}"
    )
    total_messages = cur.fetchone()[0] or 0
    
    cur.execute(
        f"SELECT words_practiced FROM {SCHEMA}.daily_stats WHERE student_id = {student_id} AND practice_date = CURRENT_DATE"
    )
    today_words = cur.fetchone()
    today_words = today_words[0] if today_words else 0
    
    # Список достижений для проверки
    achievements_to_check = []
    
    if total_messages >= 1:
        achievements_to_check.append('first_message')
    if streak_row and streak_row[0] >= 3:
        achievements_to_check.append('day_3_streak')
    if streak_row and streak_row[0] >= 7:
        achievements_to_check.append('day_7_streak')
    if streak_row and streak_row[0] >= 30:
        achievements_to_check.append('day_30_streak')
    if learned_words >= 10:
        achievements_to_check.append('words_10')
    if learned_words >= 50:
        achievements_to_check.append('words_50')
    if learned_words >= 100:
        achievements_to_check.append('words_100')
    if total_messages >= 10:
        achievements_to_check.append('messages_10')
    if total_messages >= 100:
        achievements_to_check.append('messages_100')
    if today_words >= 5:
        achievements_to_check.append('perfect_day')
    
    # Разблокируем достижения
    unlocked = []
    for achievement_code in achievements_to_check:
        try:
            cur.execute(
                f"INSERT INTO {SCHEMA}.user_achievements (student_id, achievement_code) "
                f"VALUES ({student_id}, '{achievement_code}') "
                f"ON CONFLICT (student_id, achievement_code) DO NOTHING "
                f"RETURNING achievement_code"
            )
            if cur.fetchone():
                # Получаем информацию о достижении
                cur.execute(
                    f"SELECT title_en, title_ru, emoji, points FROM {SCHEMA}.achievements WHERE code = '{achievement_code}'"
                )
                ach = cur.fetchone()
                if ach:
                    unlocked.append({
                        'code': achievement_code,
                        'title_en': ach[0],
                        'title_ru': ach[1],
                        'emoji': ach[2],
                        'points': ach[3]
                    })
        except Exception:
            pass
    
    cur.close()
    conn.close()
    return unlocked

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

def get_partner_stats(teacher_id: int) -> Dict[str, Any]:
    """Получает статистику по партнерской программе для учителя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Общее количество учеников
    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.users WHERE teacher_id = {teacher_id} AND role = 'student'")
    total_students = cur.fetchone()[0]
    
    # Количество активных учеников (с подпиской)
    # TODO: добавить проверку подписки когда будет платежная система
    active_students = 0
    
    # Получаем финансовые данные учителя
    cur.execute(
        f"SELECT phone, card_number, bank_name, total_earnings, current_balance "
        f"FROM {SCHEMA}.users WHERE telegram_id = {teacher_id}"
    )
    row = cur.fetchone()
    
    phone = row[0] if row else None
    card_number = row[1] if row else None
    bank_name = row[2] if row else None
    total_earnings = float(row[3]) if row and row[3] else 0.0
    current_balance = float(row[4]) if row and row[4] else 0.0
    
    cur.close()
    conn.close()
    
    return {
        'total_students': total_students,
        'active_students': active_students,
        'total_earnings': total_earnings,
        'current_balance': current_balance,
        'phone': phone,
        'card_number': card_number,
        'bank_name': bank_name,
        'commission_rate': 30  # 30% с каждой оплаты
    }

def update_payout_info(teacher_id: int, phone: str = None, card_number: str = None, bank_name: str = None) -> Dict[str, Any]:
    """Обновляет платежную информацию учителя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    updates = []
    if phone:
        phone_escaped = phone.replace("'", "''")
        updates.append(f"phone = '{phone_escaped}'")
    if card_number:
        card_escaped = card_number.replace("'", "''")
        updates.append(f"card_number = '{card_escaped}'")
    if bank_name:
        bank_escaped = bank_name.replace("'", "''")
        updates.append(f"bank_name = '{bank_escaped}'")
    
    if updates:
        update_sql = ", ".join(updates)
        cur.execute(f"UPDATE {SCHEMA}.users SET {update_sql}, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = {teacher_id}")
    
    cur.close()
    conn.close()
    return {'success': True}

def get_analytics() -> Dict[str, Any]:
    """Получает финансовую аналитику для администратора"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Всего подписчиков (students)
    cur.execute(f"SELECT COUNT(*) FROM {SCHEMA}.users WHERE role = 'student'")
    total_subscribers = cur.fetchone()[0]
    
    # Активные подписчики (практиковались за последние 7 дней)
    cur.execute(
        f"SELECT COUNT(DISTINCT student_id) FROM {SCHEMA}.daily_stats "
        f"WHERE practice_date >= CURRENT_DATE - INTERVAL '7 days'"
    )
    active_subscribers = cur.fetchone()[0]
    
    # К выплате преподавателям (70% от всех оплат - commission_rate 30%)
    # Предполагаем цену подписки 500 руб/мес
    subscription_price = 500
    teacher_payouts = int(total_subscribers * subscription_price * 0.7)
    
    # Прибыль платформы (30% от всех оплат)
    profit = int(total_subscribers * subscription_price * 0.3)
    
    cur.close()
    conn.close()
    
    return {
        'total_subscribers': total_subscribers,
        'active_subscribers': active_subscribers,
        'teacher_payouts': teacher_payouts,
        'profit': profit
    }

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    API для WebApp личного кабинета
    Действия: get_user, change_role, get_history, bind_teacher, get_students, get_all_teachers, get_all_students, get_analytics,
    get_categories, create_category, update_category, search_words, create_word, update_word,
    assign_words, assign_category, get_student_words, get_session_words, record_word_usage, get_student_progress_stats, update_student_settings,
    record_practice, get_available_achievements
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
        
        if not telegram_id and action not in ['get_all_teachers', 'get_all_students', 'get_analytics', 'get_categories', 'create_category', 'update_category', 'search_words', 'create_word', 'update_word', 'assign_words', 'assign_category', 'get_student_words', 'update_word_progress', 'get_student_progress_stats']:
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
            
            # Получаем данные пользователя из запроса (для создания если не существует)
            username = body.get('username', '')
            first_name = body.get('first_name', '')
            last_name = body.get('last_name', '')
            
            change_user_role(telegram_id, new_role, username, first_name, last_name)
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
        
        elif action == 'get_categories':
            categories = get_all_categories()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'categories': categories}),
                'isBase64Encoded': False
            }
        
        elif action == 'create_category':
            name = body.get('name')
            description = body.get('description')
            
            if not name:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'name is required'}),
                    'isBase64Encoded': False
                }
            
            category = create_category(name, description)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'category': category}),
                'isBase64Encoded': False
            }
        
        elif action == 'update_category':
            category_id = body.get('category_id')
            name = body.get('name')
            description = body.get('description')
            
            if not category_id or not name:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'category_id and name are required'}),
                    'isBase64Encoded': False
                }
            
            category = update_category(category_id, name, description)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'category': category}),
                'isBase64Encoded': False
            }
        
        elif action == 'search_words':
            search_query = body.get('search_query')
            category_id = body.get('category_id')
            limit = body.get('limit', 50)
            offset = body.get('offset', 0)
            
            result = search_words(search_query, category_id, limit, offset)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result),
                'isBase64Encoded': False
            }
        
        elif action == 'create_word':
            english_text = body.get('english_text')
            russian_translation = body.get('russian_translation')
            category_id = body.get('category_id')
            
            if not english_text or not russian_translation:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'english_text and russian_translation are required'}),
                    'isBase64Encoded': False
                }
            
            word = create_word(english_text, russian_translation, category_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'word': word}),
                'isBase64Encoded': False
            }
        
        elif action == 'update_word':
            word_id = body.get('word_id')
            english_text = body.get('english_text')
            russian_translation = body.get('russian_translation')
            
            if not word_id or not english_text or not russian_translation:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'word_id, english_text, and russian_translation are required'}),
                    'isBase64Encoded': False
                }
            
            word = update_word(word_id, english_text, russian_translation)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'word': word}),
                'isBase64Encoded': False
            }
        
        elif action == 'assign_words':
            teacher_id = body.get('teacher_id')
            student_id = body.get('student_id')
            word_ids = body.get('word_ids', [])
            
            if not teacher_id or not student_id or not word_ids:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'teacher_id, student_id, and word_ids are required'}),
                    'isBase64Encoded': False
                }
            
            result = assign_words_to_student(teacher_id, student_id, word_ids)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result),
                'isBase64Encoded': False
            }
        
        elif action == 'assign_category':
            teacher_id = body.get('teacher_id')
            student_id = body.get('student_id')
            category_id = body.get('category_id')
            
            if not teacher_id or not student_id or not category_id:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'teacher_id, student_id, and category_id are required'}),
                    'isBase64Encoded': False
                }
            
            result = assign_category_to_student(teacher_id, student_id, category_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result),
                'isBase64Encoded': False
            }
        
        elif action == 'get_student_words':
            student_id = body.get('student_id')
            
            if not student_id:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'student_id is required'}),
                    'isBase64Encoded': False
                }
            
            words = get_student_words(student_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'words': words}),
                'isBase64Encoded': False
            }
        
        elif action == 'get_session_words':
            student_id = body.get('student_id')
            limit = body.get('limit', 10)
            
            if not student_id:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'student_id is required'}),
                    'isBase64Encoded': False
                }
            
            words = get_session_words(student_id, limit)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'words': words, 'count': len(words)}),
                'isBase64Encoded': False
            }
        
        elif action == 'record_word_usage':
            student_id = body.get('student_id')
            word_id = body.get('word_id')
            is_correct = body.get('is_correct', True)
            context = body.get('context')
            
            if not student_id or not word_id:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'student_id and word_id are required'}),
                    'isBase64Encoded': False
                }
            
            result = record_word_usage(student_id, word_id, is_correct, context)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result),
                'isBase64Encoded': False
            }
        
        elif action == 'update_word_progress':
            # Алиас для record_word_usage (для telegram-bot)
            student_id = body.get('student_id')
            word_id = body.get('word_id')
            is_correct = body.get('is_correct', True)
            context = body.get('context')
            
            print(f"[DEBUG] update_word_progress request: student_id={student_id}, word_id={word_id}, is_correct={is_correct}")
            
            if not student_id or not word_id:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'student_id and word_id are required'}),
                    'isBase64Encoded': False
                }
            
            result = record_word_usage(student_id, word_id, is_correct, context)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result),
                'isBase64Encoded': False
            }
        
        elif action == 'get_student_progress_stats':
            student_id = body.get('student_id')
            
            if not student_id:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'student_id is required'}),
                    'isBase64Encoded': False
                }
            
            stats = get_student_progress_stats(student_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(stats),
                'isBase64Encoded': False
            }
        
        elif action == 'update_student_settings':
            language_level = body.get('language_level')
            preferred_topics = body.get('preferred_topics')
            timezone = body.get('timezone')
            
            result = update_student_settings(telegram_id, language_level, preferred_topics, timezone)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result),
                'isBase64Encoded': False
            }
        
        elif action == 'record_practice':
            student_id = body.get('student_id')
            messages = body.get('messages', 1)
            words = body.get('words', 0)
            errors = body.get('errors', 0)
            
            if not student_id:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({'error': 'student_id is required'}),
                    'isBase64Encoded': False
                }
            
            update_daily_stats(student_id, messages, words, errors)
            current_streak = update_practice_streak(student_id)
            unlocked = check_and_unlock_achievements(student_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'current_streak': current_streak,
                    'unlocked_achievements': unlocked
                }),
                'isBase64Encoded': False
            }
        
        elif action == 'get_available_achievements':
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute(
                f"SELECT code, title_en, title_ru, description_en, description_ru, emoji, points "
                f"FROM {SCHEMA}.achievements ORDER BY points ASC"
            )
            
            achievements = []
            for row in cur.fetchall():
                achievements.append({
                    'code': row[0],
                    'title_en': row[1],
                    'title_ru': row[2],
                    'description_en': row[3],
                    'description_ru': row[4],
                    'emoji': row[5],
                    'points': row[6]
                })
            
            cur.close()
            conn.close()
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'achievements': achievements}),
                'isBase64Encoded': False
            }
        
        elif action == 'get_partner_stats':
            stats = get_partner_stats(telegram_id)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(stats),
                'isBase64Encoded': False
            }
        
        elif action == 'update_payout_info':
            phone = body.get('phone')
            card_number = body.get('card_number')
            bank_name = body.get('bank_name')
            
            result = update_payout_info(telegram_id, phone, card_number, bank_name)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps(result),
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
        
        elif action == 'get_analytics':
            analytics = get_analytics()
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'analytics': analytics}),
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