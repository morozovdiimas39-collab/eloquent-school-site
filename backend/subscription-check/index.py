import json
import os
import psycopg2
import requests
from typing import Dict, Any
from datetime import datetime

SCHEMA = 't_p86463701_eloquent_school_site'

def get_db_connection():
    """Создает подключение к БД"""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.autocommit = True
    return conn

def check_subscription(telegram_id: int) -> bool:
    """Проверяет активна ли подписка пользователя"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT subscription_status, subscription_expires_at "
        f"FROM {SCHEMA}.users WHERE telegram_id = {telegram_id}"
    )
    row = cur.fetchone()
    
    cur.close()
    conn.close()
    
    if not row:
        return False
    
    subscription_status = row[0]
    subscription_expires_at = row[1]
    
    # Проверяем статус и дату истечения
    if subscription_status == 'active':
        if subscription_expires_at:
            # Проверяем не истекла ли подписка
            if subscription_expires_at > datetime.now():
                return True
        else:
            return True
    
    return False

def get_active_proxy_from_db() -> tuple:
    """Получает случайный активный прокси из БД"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        f"SELECT id, host, port, username, password "
        f"FROM {SCHEMA}.proxies WHERE is_active = TRUE "
        f"ORDER BY RANDOM() LIMIT 1"
    )
    
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        return None, None
    
    proxy_id, host, port, username, password = row
    
    if username and password:
        proxy_url = f"{username}:{password}@{host}:{port}"
    else:
        proxy_url = f"{host}:{port}"
    
    return proxy_id, proxy_url

def send_subscription_required_message(chat_id: int):
    """Отправляет сообщение о необходимости подписки"""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        return
    
    text = (
        "🔒 <b>Подписка истекла</b>\n\n"
        "Твой доступ к AnyaGPT закончился, но ты можешь продолжить "
        "обучение прямо сейчас!\n\n"
        "<b>Что ты получаешь с подпиской:</b>\n\n"
        "💬 <b>Диалог с Аней</b> — неограниченное общение с AI-учителем\n"
        "✍️ <b>5 режимов практики</b> — предложения, контекст, ассоциации, перевод\n"
        "📚 <b>Персональный словарь</b> — слова подбираются под твой уровень\n"
        "🎯 <b>Отслеживание прогресса</b> — видишь как растёшь каждый день\n"
        "🎤 <b>Голосовой режим</b> — Аня отвечает голосом (в тарифе \"Премиум\")\n\n"
        "<b>Выбери свой тариф:</b>"
    )
    
    keyboard = {
        'inline_keyboard': [
            [
                {'text': '💬 Базовый — 600₽/мес', 'callback_data': 'subscribe_basic'}
            ],
            [
                {'text': '🎤 Премиум — 900₽/мес', 'callback_data': 'subscribe_premium'}
            ],
            [
                {'text': '🔥 Всё сразу со скидкой 15% — 1275₽/мес', 'callback_data': 'subscribe_all'}
            ]
        ]
    }
    
    try:
        proxy_id, proxy_url = get_active_proxy_from_db()
        proxies = None
        if proxy_url:
            proxies = {
                'http': f'http://{proxy_url}',
                'https': f'http://{proxy_url}'
            }
        
        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML',
            'reply_markup': keyboard
        }
        
        response = requests.post(url, json=payload, proxies=proxies, timeout=30)
        
        if response.status_code != 200:
            print(f"[ERROR] Failed to send subscription message: {response.text}")
    
    except Exception as e:
        print(f"[ERROR] Exception sending subscription message: {e}")

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Проверяет подписку пользователя и отправляет сообщение если неактивна
    Args: event с telegram_id в body
    Returns: {"has_subscription": true/false}
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
        telegram_id = body_data.get('telegram_id')
        
        if not telegram_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'telegram_id required'}),
                'isBase64Encoded': False
            }
        
        has_subscription = check_subscription(telegram_id)
        
        # Если подписки нет - отправляем сообщение
        if not has_subscription:
            send_subscription_required_message(telegram_id)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': True,
                'has_subscription': has_subscription
            }),
            'isBase64Encoded': False
        }
    
    except Exception as e:
        print(f"[ERROR] Exception in subscription check: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }