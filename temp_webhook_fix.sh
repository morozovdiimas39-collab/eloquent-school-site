#!/bin/bash
curl -X POST "https://api.telegram.org/bot8586405236:AAGSeZXHACvWk5u5DNgL95fMzvij-wbVASc/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://functions.yandexcloud.net/d4eb3ckc7i9h81v7gcre","allowed_updates":["message","callback_query","pre_checkout_query","successful_payment"],"max_connections":40}'
