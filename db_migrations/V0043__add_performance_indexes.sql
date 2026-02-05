CREATE INDEX IF NOT EXISTS idx_subscription_payments_lookup ON t_p86463701_eloquent_school_site.subscription_payments(telegram_id, status, expires_at);
CREATE INDEX IF NOT EXISTS idx_users_telegram ON t_p86463701_eloquent_school_site.users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_student_words_lookup ON t_p86463701_eloquent_school_site.student_words(student_id);
CREATE INDEX IF NOT EXISTS idx_anna_messages_lookup ON t_p86463701_eloquent_school_site.anna_messages(student_id, sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_proxies_lookup ON t_p86463701_eloquent_school_site.proxies(is_active);