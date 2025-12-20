-- Сброс счётчика dialog_uses для слова "no" чтобы Аня снова начала его использовать
UPDATE t_p86463701_eloquent_school_site.word_progress
SET dialog_uses = 0, needs_check = FALSE
WHERE student_id = 7515380522 AND word_id = 8;
