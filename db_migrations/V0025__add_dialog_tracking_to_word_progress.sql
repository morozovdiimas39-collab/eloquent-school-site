-- Добавляем поле для отслеживания использований слова Аней в диалогах
ALTER TABLE t_p86463701_eloquent_school_site.word_progress 
ADD COLUMN dialog_uses INTEGER DEFAULT 0,
ADD COLUMN needs_check BOOLEAN DEFAULT FALSE;