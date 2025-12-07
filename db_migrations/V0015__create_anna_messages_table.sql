-- Таблица для логирования проактивных сообщений от Ани
CREATE TABLE IF NOT EXISTS t_p86463701_eloquent_school_site.anna_messages (
  id SERIAL PRIMARY KEY,
  student_id BIGINT NOT NULL,
  message_type VARCHAR(50) NOT NULL,
  sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Индекс для быстрого подсчета сообщений за день
CREATE INDEX IF NOT EXISTS idx_anna_messages_student_date 
ON t_p86463701_eloquent_school_site.anna_messages(student_id, sent_at);