-- ⚡ PERFORMANCE OPTIMIZATION: добавляем индексы для горячих запросов
-- Эти индексы критичны для работы с нагрузкой 100k пользователей

-- subscription_payments - проверка подписки (самый частый запрос!)
CREATE INDEX IF NOT EXISTS idx_subscription_payments_telegram_status_expires 
ON t_p86463701_eloquent_school_site.subscription_payments(telegram_id, status, expires_at);

-- users - поиск по telegram_id
CREATE INDEX IF NOT EXISTS idx_users_telegram_id 
ON t_p86463701_eloquent_school_site.users(telegram_id);

-- student_words - получение слов студента
CREATE INDEX IF NOT EXISTS idx_student_words_student_id 
ON t_p86463701_eloquent_school_site.student_words(student_id);

-- anna_messages - история диалогов
CREATE INDEX IF NOT EXISTS idx_anna_messages_user_created 
ON t_p86463701_eloquent_school_site.anna_messages(user_telegram_id, created_at DESC);

-- proxies - выбор активных прокси
CREATE INDEX IF NOT EXISTS idx_proxies_active 
ON t_p86463701_eloquent_school_site.proxies(is_active) WHERE is_active = TRUE;

-- practice_sessions - активные сессии пользователя
CREATE INDEX IF NOT EXISTS idx_practice_sessions_user_active 
ON t_p86463701_eloquent_school_site.practice_sessions(user_telegram_id, is_active);
