#!/bin/bash
curl -X POST "https://api.telegram.org/bot8586405236:AAGSeZXHACvWk5u5DNgL95fMzvij-wbVASc/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://functions.poehali.dev/92013b11-9080-40b5-8b24-10317e48a4f7","allowed_updates":["message","callback_query","pre_checkout_query","successful_payment"],"max_connections":40}'
