-- Добавляем уникальное ограничение на english_text в таблице words
-- Это предотвратит дублирование слов и позволит использовать ON CONFLICT

ALTER TABLE t_p86463701_eloquent_school_site.words
ADD CONSTRAINT words_english_text_unique UNIQUE (english_text);