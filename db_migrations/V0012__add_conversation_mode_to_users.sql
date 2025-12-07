-- Добавляем поле conversation_mode для хранения режима обучения
ALTER TABLE t_p86463701_eloquent_school_site.users 
ADD COLUMN conversation_mode VARCHAR(50) DEFAULT 'dialog';

-- Добавляем поле для хранения текущего слова в режиме упражнений
ALTER TABLE t_p86463701_eloquent_school_site.users 
ADD COLUMN current_exercise_word_id BIGINT;

-- Добавляем поле для хранения правильного ответа в режиме упражнений
ALTER TABLE t_p86463701_eloquent_school_site.users 
ADD COLUMN current_exercise_answer TEXT;

COMMENT ON COLUMN t_p86463701_eloquent_school_site.users.conversation_mode IS 'Режим обучения: dialog, sentence, context, association, translation';
COMMENT ON COLUMN t_p86463701_eloquent_school_site.users.current_exercise_word_id IS 'ID текущего слова для упражнения';
COMMENT ON COLUMN t_p86463701_eloquent_school_site.users.current_exercise_answer IS 'Правильный ответ для текущего упражнения';