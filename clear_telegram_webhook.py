#!/usr/bin/env python3
"""
Временный скрипт для очистки Telegram webhook и pending updates
"""
import requests
import os

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

if not BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
    print("Установи его через: export TELEGRAM_BOT_TOKEN='your_token_here'")
    exit(1)

# API методы
DELETE_WEBHOOK_URL = f'https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook'
GET_WEBHOOK_INFO_URL = f'https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo'
SET_WEBHOOK_URL = f'https://api.telegram.org/bot{BOT_TOKEN}/setWebhook'

# Функция URL бота
WEBHOOK_URL = 'https://functions.poehali.dev/92013b11-9080-40b5-8b24-10317e48a4f7'

print("🔧 Telegram Webhook Cleaner\n")
print("=" * 50)

# 1. Проверяем текущий статус webhook
print("\n1️⃣ Проверяю текущий webhook...")
response = requests.get(GET_WEBHOOK_INFO_URL)
webhook_info = response.json()

if webhook_info.get('ok'):
    result = webhook_info['result']
    print(f"   URL: {result.get('url', 'не установлен')}")
    print(f"   Pending updates: {result.get('pending_update_count', 0)}")
    print(f"   Last error: {result.get('last_error_message', 'нет ошибок')}")
else:
    print(f"   ❌ Ошибка: {webhook_info}")

# 2. Удаляем webhook с drop_pending_updates=true
print("\n2️⃣ Удаляю webhook и все pending updates...")
response = requests.post(
    DELETE_WEBHOOK_URL,
    json={'drop_pending_updates': True}
)
result = response.json()

if result.get('ok'):
    print("   ✅ Webhook удален, все старые updates удалены!")
else:
    print(f"   ❌ Ошибка: {result}")

# 3. Устанавливаем webhook заново
print("\n3️⃣ Устанавливаю webhook заново...")
response = requests.post(
    SET_WEBHOOK_URL,
    json={
        'url': WEBHOOK_URL,
        'drop_pending_updates': True,
        'max_connections': 40,
        'allowed_updates': ['message', 'callback_query', 'my_chat_member']
    }
)
result = response.json()

if result.get('ok'):
    print(f"   ✅ Webhook установлен: {WEBHOOK_URL}")
else:
    print(f"   ❌ Ошибка: {result}")

# 4. Проверяем финальный статус
print("\n4️⃣ Проверяю финальный статус...")
response = requests.get(GET_WEBHOOK_INFO_URL)
webhook_info = response.json()

if webhook_info.get('ok'):
    result = webhook_info['result']
    print(f"   URL: {result.get('url', 'не установлен')}")
    print(f"   Pending updates: {result.get('pending_update_count', 0)}")
    print(f"   Last error: {result.get('last_error_message', 'нет ошибок')}")
else:
    print(f"   ❌ Ошибка: {webhook_info}")

print("\n" + "=" * 50)
print("✅ Готово! Теперь попробуй написать /start боту заново.")
print("   Все старые сообщения должны быть удалены из очереди.")
