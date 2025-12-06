-- Делаем category_id необязательным для слов, удаляя и пересоздавая таблицу
CREATE TABLE IF NOT EXISTS t_p86463701_eloquent_school_site.words_new (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES t_p86463701_eloquent_school_site.categories(id),
    english_text TEXT NOT NULL,
    russian_translation TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Копируем данные если есть
INSERT INTO t_p86463701_eloquent_school_site.words_new (id, category_id, english_text, russian_translation, created_at, updated_at)
SELECT id, category_id, english_text, russian_translation, created_at, updated_at
FROM t_p86463701_eloquent_school_site.words;

-- Удаляем старую таблицу и переименовываем новую
ALTER TABLE t_p86463701_eloquent_school_site.words RENAME TO words_old;
ALTER TABLE t_p86463701_eloquent_school_site.words_new RENAME TO words;

-- Восстанавливаем индексы
CREATE INDEX IF NOT EXISTS idx_words_category_id ON t_p86463701_eloquent_school_site.words(category_id);
CREATE INDEX IF NOT EXISTS idx_words_english_text ON t_p86463701_eloquent_school_site.words(english_text);