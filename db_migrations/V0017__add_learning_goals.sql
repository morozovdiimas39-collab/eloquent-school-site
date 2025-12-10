-- Добавляем поля для целей обучения
ALTER TABLE t_p86463701_eloquent_school_site.users 
ADD COLUMN IF NOT EXISTS learning_goal VARCHAR(100),
ADD COLUMN IF NOT EXISTS learning_goal_details TEXT;

-- Комментарии
COMMENT ON COLUMN t_p86463701_eloquent_school_site.users.learning_goal IS 'Цель изучения английского: work_it, work_business, work_medicine, travel, exams, relocation, personal';
COMMENT ON COLUMN t_p86463701_eloquent_school_site.users.learning_goal_details IS 'Детальное описание цели от студента';
