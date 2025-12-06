-- Добавляем таблицу для достижений
CREATE TABLE IF NOT EXISTS t_p86463701_eloquent_school_site.achievements (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    title_en VARCHAR(200) NOT NULL,
    title_ru VARCHAR(200) NOT NULL,
    description_en TEXT,
    description_ru TEXT,
    emoji VARCHAR(10),
    points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Добавляем таблицу для достижений пользователей
CREATE TABLE IF NOT EXISTS t_p86463701_eloquent_school_site.user_achievements (
    id SERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL,
    achievement_code VARCHAR(50) NOT NULL,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, achievement_code)
);

-- Добавляем таблицу для streak (дней подряд)
CREATE TABLE IF NOT EXISTS t_p86463701_eloquent_school_site.practice_streaks (
    student_id BIGINT PRIMARY KEY,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_practice_date DATE,
    total_practice_days INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Добавляем таблицу для ежедневной статистики
CREATE TABLE IF NOT EXISTS t_p86463701_eloquent_school_site.daily_stats (
    id SERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL,
    practice_date DATE NOT NULL,
    messages_sent INTEGER DEFAULT 0,
    words_practiced INTEGER DEFAULT 0,
    errors_corrected INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, practice_date)
);

-- Вставляем базовые достижения
INSERT INTO t_p86463701_eloquent_school_site.achievements (code, title_en, title_ru, description_en, description_ru, emoji, points) VALUES
('first_message', 'First Steps', 'Первые шаги', 'Sent your first message to Anya', 'Отправил первое сообщение Ане', '👋', 10),
('day_3_streak', '3-Day Streak', '3 дня подряд', 'Practiced 3 days in a row', 'Практиковался 3 дня подряд', '🔥', 50),
('day_7_streak', 'Week Warrior', 'Недельный воин', 'Practiced 7 days in a row', 'Практиковался 7 дней подряд', '⚡', 100),
('day_30_streak', 'Monthly Master', 'Мастер месяца', 'Practiced 30 days in a row', 'Практиковался 30 дней подряд', '🏆', 500),
('words_10', 'Word Explorer', 'Исследователь слов', 'Learned 10 words', 'Выучил 10 слов', '📚', 50),
('words_50', 'Vocabulary Builder', 'Строитель словаря', 'Learned 50 words', 'Выучил 50 слов', '📖', 200),
('words_100', 'Word Master', 'Мастер слов', 'Learned 100 words', 'Выучил 100 слов', '🎓', 500),
('messages_10', 'Chatty Starter', 'Говорун-новичок', 'Sent 10 messages', 'Отправил 10 сообщений', '💬', 30),
('messages_100', 'Conversation Pro', 'Профи разговоров', 'Sent 100 messages', 'Отправил 100 сообщений', '🗣️', 300),
('perfect_day', 'Perfect Day', 'Идеальный день', 'Used 5 new words in one day', 'Использовал 5 новых слов за день', '⭐', 100)
ON CONFLICT (code) DO NOTHING;