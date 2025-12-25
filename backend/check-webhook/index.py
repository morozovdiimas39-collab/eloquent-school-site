"""Проверяет текущий статус webhook Telegram бота"""
import json
import os
import urllib.request

def handler(event, context):
    """Получает информацию о текущем webhook"""
    
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not token:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'TELEGRAM_BOT_TOKEN not found'})
        }
    
    try:
        # Получаем информацию о webhook
        url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
        
        req = urllib.request.Request(url, method='GET')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            webhook_info = result.get('result', {})
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'webhook_url': webhook_info.get('url'),
                    'has_custom_certificate': webhook_info.get('has_custom_certificate'),
                    'pending_update_count': webhook_info.get('pending_update_count'),
                    'last_error_date': webhook_info.get('last_error_date'),
                    'last_error_message': webhook_info.get('last_error_message'),
                    'max_connections': webhook_info.get('max_connections'),
                    'allowed_updates': webhook_info.get('allowed_updates'),
                    'full_info': webhook_info
                }, indent=2)
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
