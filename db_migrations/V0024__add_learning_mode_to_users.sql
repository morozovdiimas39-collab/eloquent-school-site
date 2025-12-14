-- Add learning_mode field to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS learning_mode VARCHAR(50);

COMMENT ON COLUMN users.learning_mode IS 'Режим обучения: standard (обычное), specific_topic (конкретная тема), urgent_task (срочная задача)';