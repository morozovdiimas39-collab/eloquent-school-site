"""Обновляет Telegram webhook с поддержкой платежей"""
import json
import os
import urllib.request

def handler(event, context):
    """Обновляет webhook Telegram бота с правильными allowed_updates"""
    
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'TELEGRAM_BOT_TOKEN not found'})
        }
    
    # Webhook URL бота
    webhook_url = "https://functions.poehali.dev/92013b11-9080-40b5-8b24-10317e48a4f7"
    
    # КРИТИЧНО: добавляем pre_checkout_query и successful_payment для платежей!
    allowed_updates = ["message", "callback_query", "pre_checkout_query"]
    
    try:
        # Вызываем Telegram API для обновления webhook
        url = f"https://api.telegram.org/bot{token}/setWebhook"
        
        payload = {
            "url": webhook_url,
            "allowed_updates": allowed_updates
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': True,
                    'telegram_response': result,
                    'webhook_url': webhook_url,
                    'allowed_updates': allowed_updates
                })
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'error': str(e),
                'webhook_url': webhook_url,
                'allowed_updates': allowed_updates
            })
        }
