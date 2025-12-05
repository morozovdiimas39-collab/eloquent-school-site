-- Добавляем колонку teacher_id к таблице users для связи ученика с учителем
ALTER TABLE t_p86463701_eloquent_school_site.users 
ADD COLUMN IF NOT EXISTS teacher_id INTEGER;

-- Создаем индекс для быстрого поиска учеников по учителю
CREATE INDEX IF NOT EXISTS idx_users_teacher_id 
ON t_p86463701_eloquent_school_site.users(teacher_id);