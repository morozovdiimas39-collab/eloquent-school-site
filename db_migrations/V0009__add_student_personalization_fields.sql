-- Добавляем поля для персонализации обучения
ALTER TABLE t_p86463701_eloquent_school_site.users
ADD COLUMN IF NOT EXISTS language_level VARCHAR(10) DEFAULT 'A1',
ADD COLUMN IF NOT EXISTS preferred_topics JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'UTC',
ADD COLUMN IF NOT EXISTS last_practice_message TIMESTAMP;

-- Создаем индекс для быстрого поиска учеников для практики
CREATE INDEX IF NOT EXISTS idx_users_last_practice ON t_p86463701_eloquent_school_site.users(last_practice_message) WHERE role = 'student';

COMMENT ON COLUMN t_p86463701_eloquent_school_site.users.language_level IS 'Уровень владения английским: A1, A2, B1, B2, C1, C2';
COMMENT ON COLUMN t_p86463701_eloquent_school_site.users.preferred_topics IS 'Массив тем с эмодзи для разговоров, например: [{"emoji": "⚽", "topic": "Sports"}, {"emoji": "🍕", "topic": "Food"}]';
COMMENT ON COLUMN t_p86463701_eloquent_school_site.users.timezone IS 'Часовой пояс ученика для определения времени практики';
COMMENT ON COLUMN t_p86463701_eloquent_school_site.users.last_practice_message IS 'Время последнего проактивного сообщения от Ани';