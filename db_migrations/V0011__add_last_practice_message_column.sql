-- Добавляем колонку для отслеживания последнего проактивного сообщения
ALTER TABLE t_p86463701_eloquent_school_site.users 
ADD COLUMN IF NOT EXISTS last_practice_message TIMESTAMP;