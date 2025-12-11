-- Добавляем уникальное ограничение для student_words
-- Это предотвратит дублирование одного слова у одного студента

ALTER TABLE t_p86463701_eloquent_school_site.student_words
ADD CONSTRAINT student_words_student_word_unique UNIQUE (student_id, word_id);