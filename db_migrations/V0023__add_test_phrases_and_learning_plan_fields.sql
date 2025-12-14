-- Добавляем поля для хранения теста уровня и плана обучения

ALTER TABLE t_p86463701_eloquent_school_site.users 
ADD COLUMN IF NOT EXISTS test_phrases JSONB DEFAULT NULL,
ADD COLUMN IF NOT EXISTS learning_plan JSONB DEFAULT NULL;

COMMENT ON COLUMN t_p86463701_eloquent_school_site.users.test_phrases IS 'Фразы для проверки уровня английского (массив строк)';
COMMENT ON COLUMN t_p86463701_eloquent_school_site.users.learning_plan IS 'Полный месячный план обучения (массив недель с материалами)';