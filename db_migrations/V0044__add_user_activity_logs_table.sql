-- Создаём таблицу для детальных логов пользователей
CREATE TABLE IF NOT EXISTS t_p86463701_eloquent_school_site.user_activity_logs (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    user_state JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_logs_telegram_id ON t_p86463701_eloquent_school_site.user_activity_logs(telegram_id);
CREATE INDEX IF NOT EXISTS idx_user_logs_created_at ON t_p86463701_eloquent_school_site.user_activity_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_user_logs_event_type ON t_p86463701_eloquent_school_site.user_activity_logs(event_type);

COMMENT ON TABLE t_p86463701_eloquent_school_site.user_activity_logs IS 'Детальные логи активности пользователей для отладки онбординга';
COMMENT ON COLUMN t_p86463701_eloquent_school_site.user_activity_logs.event_type IS 'Тип события: onboarding_start, learning_mode_selected, level_test, interests_selected';
COMMENT ON COLUMN t_p86463701_eloquent_school_site.user_activity_logs.event_data IS 'JSON с деталями события';
COMMENT ON COLUMN t_p86463701_eloquent_school_site.user_activity_logs.user_state IS 'JSON со состоянием пользователя';
COMMENT ON COLUMN t_p86463701_eloquent_school_site.user_activity_logs.error_message IS 'Текст ошибки если произошла';