-- Добавляем колонки прогресса в word_progress для веб-аппа и статистики
ALTER TABLE t_p86463701_eloquent_school_site.word_progress
  ADD COLUMN IF NOT EXISTS mastery_score NUMERIC(5,2) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS attempts INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS correct_uses INTEGER DEFAULT 0,
  ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'new',
  ADD COLUMN IF NOT EXISTS last_practiced TIMESTAMP,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
