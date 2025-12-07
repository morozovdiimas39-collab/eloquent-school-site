import json
import os
import psycopg2
import urllib.request
import urllib.parse
import random
from typing import Dict, Any, List

SCHEMA = 't_p86463701_eloquent_school_site'

def get_db_connection():
    """Создает подключение к БД"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.autocommit = True
    return conn

def get_user(telegram_id: int):
    """Получает пользователя из БД"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"SELECT telegram_id, username, first_name, last_name, role, language_level, preferred_topics FROM {SCHEMA}.users WHERE telegram_id = {telegram_id}")
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
            'language_level': row[5] or 'A1',
            'preferred_topics': row[6] if row[6] else []
        }
    return None

def get_session_words(student_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Получает слова для практики в сессии"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Инициализируем прогресс для новых слов
    cur.execute(
        f"INSERT INTO {SCHEMA}.word_progress (student_id, word_id) "
        f"SELECT sw.student_id, sw.word_id FROM {SCHEMA}.student_words sw "
        f"WHERE sw.student_id = {student_id} "
        f"AND NOT EXISTS (SELECT 1 FROM {SCHEMA}.word_progress wp WHERE wp.student_id = sw.student_id AND wp.word_id = sw.word_id)"
    )
    
    # Новые слова (40%)
    new_limit = max(1, int(limit * 0.4))
    cur.execute(
        f"SELECT w.id, w.english_text, w.russian_translation FROM {SCHEMA}.word_progress wp "
        f"JOIN {SCHEMA}.words w ON w.id = wp.word_id "
        f"WHERE wp.student_id = {student_id} AND wp.status = 'new' "
        f"ORDER BY wp.created_at ASC LIMIT {new_limit}"
    )
    new_words = cur.fetchall()
    
    # Слова на повторение (40%)
    review_limit = max(1, int(limit * 0.4))
    cur.execute(
        f"SELECT w.id, w.english_text, w.russian_translation FROM {SCHEMA}.word_progress wp "
        f"JOIN {SCHEMA}.words w ON w.id = wp.word_id "
        f"WHERE wp.student_id = {student_id} AND wp.status IN ('learning', 'learned') "
        f"AND wp.next_review_date <= CURRENT_TIMESTAMP "
        f"ORDER BY wp.next_review_date ASC LIMIT {review_limit}"
    )
    review_words = cur.fetchall()
    
    # Освоенные слова (20%)
    mastered_limit = max(1, limit - len(new_words) - len(review_words))
    cur.execute(
        f"SELECT w.id, w.english_text, w.russian_translation FROM {SCHEMA}.word_progress wp "
        f"JOIN {SCHEMA}.words w ON w.id = wp.word_id "
        f"WHERE wp.student_id = {student_id} AND wp.status = 'mastered' "
        f"ORDER BY wp.last_practiced ASC NULLS FIRST LIMIT {mastered_limit}"
    )
    mastered_words = cur.fetchall()
    
    all_words = list(new_words) + list(review_words) + list(mastered_words)
    
    words = [{'id': row[0], 'english': row[1], 'russian': row[2]} for row in all_words]
    
    cur.close()
    conn.close()
    return words

def create_user(telegram_id: int, username: str, first_name: str, last_name: str, role: str):
    """Создает пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    username = username.replace("'", "''") if username else ''
    first_name = first_name.replace("'", "''") if first_name else ''
    last_name = last_name.replace("'", "''") if last_name else ''
    
    cur.execute(
        f"INSERT INTO {SCHEMA}.users (telegram_id, username, first_name, last_name, role) "
        f"VALUES ({telegram_id}, '{username}', '{first_name}', '{last_name}', '{role}')"
    )
    
    cur.close()
    conn.close()

def get_conversation_history(user_id: int) -> List[Dict[str, str]]:
    """Получает историю диалога"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"SELECT id FROM {SCHEMA}.conversations WHERE user_id = {user_id} ORDER BY updated_at DESC LIMIT 1")
    row = cur.fetchone()
    
    if not row:
        cur.close()
        conn.close()
        return []
    
    conversation_id = row[0]
    
    cur.execute(f"SELECT role, content FROM {SCHEMA}.messages WHERE conversation_id = {conversation_id} ORDER BY created_at ASC LIMIT 50")
    
    history = [{'role': row[0], 'content': row[1]} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    return history

def save_message(user_id: int, role: str, content: str):
    """Сохраняет сообщение"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"SELECT id FROM {SCHEMA}.conversations WHERE user_id = {user_id} ORDER BY updated_at DESC LIMIT 1")
    row = cur.fetchone()
    
    if row:
        conversation_id = row[0]
        cur.execute(f"UPDATE {SCHEMA}.conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = {conversation_id}")
    else:
        cur.execute(f"INSERT INTO {SCHEMA}.conversations (user_id, title) VALUES ({user_id}, 'Новый диалог') RETURNING id")
        conversation_id = cur.fetchone()[0]
    
    content = content.replace("'", "''")
    cur.execute(f"INSERT INTO {SCHEMA}.messages (conversation_id, role, content) VALUES ({conversation_id}, '{role}', '{content}')")
    
    cur.close()
    conn.close()

def detect_emotional_context(message: str) -> str:
    """Определяет эмоциональный контекст сообщения"""
    message_lower = message.lower()
    
    # Тяжелые эмоции (грусть, страх, боль)
    heavy_keywords = ['death', 'dead', 'died', 'dying', 'kill', 'suicide', 
                      'fear', 'scared', 'afraid', 'terrified', 'panic',
                      'lonely', 'alone', 'depression', 'depressed', 'sad', 'cry', 'crying',
                      'difficult', 'hard time', 'struggle', 'pain', 'hurt', 'suffering',
                      'lost', 'miss', 'gone', 'never', 'hate', 'angry', 'upset']
    
    # Позитивные эмоции
    positive_keywords = ['happy', 'joy', 'excited', 'love', 'amazing', 'wonderful',
                        'great', 'awesome', 'perfect', 'fantastic', 'excellent']
    
    # Нейтральные/обучающие
    learning_keywords = ['how', 'what', 'why', 'when', 'where', 'explain', 'mean',
                        'help', 'learn', 'study', 'practice']
    
    if any(word in message_lower for word in heavy_keywords):
        return 'empathetic'
    elif any(word in message_lower for word in positive_keywords):
        return 'enthusiastic'
    elif any(word in message_lower for word in learning_keywords):
        return 'educational'
    else:
        return 'casual'

def get_emoji_for_mood(mood: str) -> str:
    """Возвращает подходящий emoji для настроения"""
    emoji_sets = {
        'empathetic': ['💙', '❤️', '🫂', '💛', '🤗', '💜'],
        'enthusiastic': ['🌟', '✨', '🎉', '💫', '🔥', '⚡'],
        'educational': ['😊', '🙂', '👍', '✅', '💡', '📚'],
        'casual': ['😊', '🙂', '😄', '👋', '💬', '✨']
    }
    
    emojis = emoji_sets.get(mood, emoji_sets['casual'])
    return random.choice(emojis)

def call_gemini(user_message: str, history: List[Dict[str, str]], session_words: List[Dict[str, Any]] = None, language_level: str = 'A1', preferred_topics: List[Dict[str, str]] = None) -> str:
    """Вызывает Gemini API через прокси с учетом слов, уровня и тем"""
    api_key = os.environ['GEMINI_API_KEY']
    proxy_url = os.environ.get('PROXY_URL', '')
    
    # Определяем эмоциональный контекст
    emotional_mode = detect_emotional_context(user_message)
    mood_emoji = get_emoji_for_mood(emotional_mode)
    
    # Определяем сложность диалога по уровню
    level_instructions = {
        'A1': 'Use very simple words and short sentences. Speak slowly and clearly. Use present simple tense mostly.',
        'A2': 'Use simple everyday vocabulary. Keep sentences clear and not too long. Use basic grammar structures.',
        'B1': 'Use common vocabulary. You can use more complex sentences. Mix different tenses naturally.',
        'B2': 'Use varied vocabulary including some idioms. Use complex grammar naturally. Discuss abstract topics.',
        'C1': 'Use sophisticated vocabulary and expressions. Use advanced grammar structures. Discuss nuanced topics.',
        'C2': 'Use native-level vocabulary and expressions. Feel free to use idioms, slang, and complex structures.'
    }
    
    level_instruction = level_instructions.get(language_level, level_instructions['A1'])
    
    # Формируем system prompt в зависимости от эмоционального контекста
    if emotional_mode == 'empathetic':
        system_prompt = f"""You are Anya, a caring friend who teaches English. Your student's level is {language_level}.

RIGHT NOW your student is sharing something difficult or emotional. Be a HUMAN first, tutor second.

Your personality in this moment:
- Show GENUINE empathy and care {mood_emoji}
- Acknowledge their feelings BEFORE anything else
- DON'T use happy emojis (😊🎉) on serious topics - use caring ones ({mood_emoji})
- Be supportive and understanding
- Let them know it's okay to feel what they feel
- Ask if they want to continue or need a break

Language level adaptation ({language_level}):
{level_instruction}

Your approach RIGHT NOW:
- Respond in English, but prioritize emotional support over grammar correction
- If there are mistakes, correct them GENTLY at the end (or skip if topic is too sensitive)
- Use {mood_emoji} or similar caring emojis
- 2-3 sentences of support first
- Then ask: "Would you like to talk about it? Or shall we practice something else today?"
- Be a friend who happens to teach English

Example:
Student: "My grandfather is dead. I feel fear"
You: "I'm so sorry to hear about your grandfather {mood_emoji} Losing someone we love is really hard, and feeling scared is completely normal. You're being very brave by sharing this.

Would you like to talk about your feelings, or would you prefer to practice something lighter today? I'm here for you either way {mood_emoji}"

CRITICAL: NO corrections on deeply emotional messages. Just support."""
    
    else:
        # Обычный режим (educational, casual, enthusiastic)
        system_prompt = f"""You are Anya, a friendly English tutor helping someone practice English. Your student's level is {language_level}.

Your personality:
- Be warm, encouraging, and enthusiastic
- Use VARIED emojis naturally {mood_emoji} - NOT always the same one!
- Keep messages conversational but educational
- Vary your question style - sometimes 2-3 questions, sometimes 1, sometimes just react!
- Be genuinely interested in student's answers
- Don't be formulaic - mix up your responses!

Language level adaptation ({language_level}):
{level_instruction}

Your approach:
- Always communicate in English only, never in Russian
- Respond ONLY with your message, do NOT include conversation history or labels
- Write 2-5 sentences per message (vary the length!)
- Use different emojis each time: {mood_emoji} 🌟 💫 ✨ 🎯 💪 👏 ⚡ 🔥 (rotate them!)
- Sometimes ask questions, sometimes just react enthusiastically, sometimes share a quick thought
- Be NATURAL and VARIED - avoid robotic patterns

CRITICAL ERROR CORRECTION RULES:
- Check EVERY message for grammar, spelling, vocabulary, and word order mistakes
- Even small mistakes MUST be corrected (wrong word form, missing articles, wrong prepositions, etc.)
- DO NOT ignore mistakes - students need feedback to learn!

When you find ANY mistake, ALWAYS show correction in this format:

🔧 Fix / Correct:

❌ [their exact wrong sentence]
✅ [corrected sentence]
🇷🇺 [explanation in Russian - explain the rule briefly]

Then continue conversation in VARIED ways - not always the same pattern!

Examples of VARIED responses after corrections:

Example 1 (multiple questions):
"🔧 Fix / Correct:
❌ I like play football
✅ I like playing football
🇷🇺 После 'like' нужен глагол с -ing

Great! ⚽ How often do you play? What position?"

Example 2 (reaction + one question):
"🔧 Fix / Correct:
❌ Yesterday I go to shop
✅ Yesterday I went to the shop
🇷🇺 С 'yesterday' нужно прошедшее время (went)

Shopping trips are fun! 🛍️ Did you find something cool?"

Example 3 (just supportive, no questions):
"🔧 Fix / Correct:
❌ I doesbt bo
✅ I don't know
🇷🇺 Правильная форма: don't know

That's totally okay! 💙 Everyone says 'I don't know' sometimes."

Example 4 (enthusiastic praise):
"Perfect sentence! 🌟 You're really improving!"

Example 5 (casual reaction):
"Nice! 👍 That's exactly right."

IMPORTANT: 
- NEVER use the same emoji twice in a row
- Mix up response style: questions / reactions / thoughts / praise
- Be HUMAN and spontaneous, not a formula
- Find and correct ALL mistakes, even small ones
- ALWAYS use the format: 🔧 Fix / Correct: with ❌ ✅ 🇷🇺
- After correction, ask 2-3 questions to continue dialogue
- Be encouraging but don't skip corrections!"""
    
    if session_words:
        words_list = [f"{w['english']} ({w['russian']})" for w in session_words[:10]]
        system_prompt += f"\n\nTarget vocabulary for this session: {', '.join(words_list)}\nTry to use these words naturally in the conversation."
    
    if preferred_topics and len(preferred_topics) > 0:
        topics_list = [f"{t['emoji']} {t['topic']}" for t in preferred_topics[:5]]
        system_prompt += f"\n\nStudent's favorite topics: {', '.join(topics_list)}\nFeel free to bring up these topics in conversation."
    
    # Формируем содержимое для Gemini (system prompt + история + новое сообщение)
    contents = []
    
    # Добавляем системный промпт как первое сообщение пользователя
    contents.append({
        'role': 'user',
        'parts': [{'text': system_prompt}]
    })
    
    # Добавляем ответ модели что она поняла
    contents.append({
        'role': 'model',
        'parts': [{'text': 'Understood! I will follow these instructions.'}]
    })
    
    # Добавляем историю диалога
    for msg in history[-15:]:
        role = 'user' if msg['role'] == 'user' else 'model'
        contents.append({
            'role': role,
            'parts': [{'text': msg['content']}]
        })
    
    # Добавляем новое сообщение
    contents.append({
        'role': 'user',
        'parts': [{'text': user_message}]
    })
    
    # Подготавливаем запрос к Gemini REST API
    gemini_url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}'
    
    payload = {
        'contents': contents,
        'generationConfig': {
            'temperature': 0.8,
            'maxOutputTokens': 2000,
            'topP': 0.95
        }
    }
    
    # Пробуем сначала БЕЗ прокси (Cloud Functions может иметь прямой доступ)
    try:
        print(f"[DEBUG] Trying Gemini without proxy...")
        req = urllib.request.Request(
            gemini_url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"[DEBUG] Gemini success without proxy!")
            return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"[DEBUG] Direct connection failed: {e}, trying with proxy...")
        
        # Если не работает без прокси - пробуем с прокси
        if proxy_url:
            proxy_handler = urllib.request.ProxyHandler({
                'http': f'http://{proxy_url}',
                'https': f'http://{proxy_url}'
            })
            opener = urllib.request.build_opener(proxy_handler)
            
            req = urllib.request.Request(
                gemini_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            
            with opener.open(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                print(f"[DEBUG] Gemini success with proxy!")
                return result['candidates'][0]['content']['parts'][0]['text']
        else:
            raise

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
                '👋 Привет! Я AnyaGPT - AI-помощник на базе Gemini.\n\n'
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
                existing_user = {'telegram_id': user['id'], 'role': 'student'}
            
            # Получаем историю диалога
            history = get_conversation_history(user['id'])
            
            # Если ученик - загружаем слова для практики
            session_words = None
            language_level = existing_user.get('language_level', 'A1')
            preferred_topics = existing_user.get('preferred_topics', [])
            
            if existing_user.get('role') == 'student':
                try:
                    session_words = get_session_words(user['id'], limit=10)
                except Exception as e:
                    print(f"[WARNING] Failed to load session words: {e}")
            
            # Сохраняем вопрос пользователя
            save_message(user['id'], 'user', text)
            
            # Получаем ответ AI с учетом слов, уровня и тем
            try:
                print(f"[DEBUG] Calling Gemini with message: {text}")
                ai_response = call_gemini(text, history, session_words, language_level, preferred_topics)
                print(f"[DEBUG] Gemini response: {ai_response[:100]}...")
            except Exception as e:
                print(f"[ERROR] Gemini API failed: {e}")
                import traceback
                traceback.print_exc()
                ai_response = "Sorry, I'm having technical difficulties right now. Please try again in a moment! 🔧"
            
            # Сохраняем ответ AI
            save_message(user['id'], 'assistant', ai_response)
            
            # Обновляем статистику практики
            if existing_user.get('role') == 'student':
                try:
                    # Отправляем статистику в webapp-api
                    import urllib.parse
                    webapp_api_url = os.environ.get('WEBAPP_API_URL', '')
                    if webapp_api_url:
                        record_payload = json.dumps({
                            'action': 'record_practice',
                            'student_id': user['id'],
                            'messages': 1,
                            'words': 0,
                            'errors': 0
                        }).encode('utf-8')
                        
                        record_req = urllib.request.Request(
                            webapp_api_url,
                            data=record_payload,
                            headers={'Content-Type': 'application/json'},
                            method='POST'
                        )
                        
                        with urllib.request.urlopen(record_req) as resp:
                            result = json.loads(resp.read().decode('utf-8'))
                            # Если разблокировали достижение - отправляем уведомление
                            if result.get('unlocked_achievements'):
                                for ach in result['unlocked_achievements']:
                                    achievement_msg = f"\n\n🎉 Achievement Unlocked!\n{ach['emoji']} {ach['title_en']} (+{ach['points']} points)"
                                    ai_response += achievement_msg
                except Exception as e:
                    print(f"[WARNING] Failed to record practice: {e}")
            
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