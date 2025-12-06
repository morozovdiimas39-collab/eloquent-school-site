-- Таблица для назначения слов ученикам
CREATE TABLE IF NOT EXISTS t_p86463701_eloquent_school_site.student_words (
    id SERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL,
    word_id INTEGER NOT NULL REFERENCES t_p86463701_eloquent_school_site.words(id),
    teacher_id BIGINT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'assigned',
    CONSTRAINT unique_student_word UNIQUE (student_id, word_id)
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_student_words_student_id ON t_p86463701_eloquent_school_site.student_words(student_id);
CREATE INDEX IF NOT EXISTS idx_student_words_teacher_id ON t_p86463701_eloquent_school_site.student_words(teacher_id);
CREATE INDEX IF NOT EXISTS idx_student_words_word_id ON t_p86463701_eloquent_school_site.student_words(word_id);