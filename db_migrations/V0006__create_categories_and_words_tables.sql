-- Создание таблицы категорий для группировки слов
CREATE TABLE IF NOT EXISTS t_p86463701_eloquent_school_site.categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы слов и фраз
CREATE TABLE IF NOT EXISTS t_p86463701_eloquent_school_site.words (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES t_p86463701_eloquent_school_site.categories(id),
    english_text TEXT NOT NULL,
    russian_translation TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_words_category_id ON t_p86463701_eloquent_school_site.words(category_id);
CREATE INDEX IF NOT EXISTS idx_categories_name ON t_p86463701_eloquent_school_site.categories(name);
CREATE INDEX IF NOT EXISTS idx_words_english_text ON t_p86463701_eloquent_school_site.words(english_text);