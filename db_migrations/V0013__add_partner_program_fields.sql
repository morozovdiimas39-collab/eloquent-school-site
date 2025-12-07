-- Добавляем поля для партнерской программы учителей
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
ALTER TABLE users ADD COLUMN IF NOT EXISTS card_number VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS bank_name VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS total_earnings DECIMAL(10, 2) DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS current_balance DECIMAL(10, 2) DEFAULT 0;

-- Таблица для отслеживания платежей учеников (для расчета 30%)
CREATE TABLE IF NOT EXISTS student_payments (
    id BIGSERIAL PRIMARY KEY,
    student_id BIGINT NOT NULL REFERENCES users(telegram_id),
    teacher_id BIGINT REFERENCES users(telegram_id),
    amount DECIMAL(10, 2) NOT NULL,
    teacher_commission DECIMAL(10, 2) NOT NULL,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'cancelled'))
);

-- Таблица для истории выплат учителям
CREATE TABLE IF NOT EXISTS teacher_payouts (
    id BIGSERIAL PRIMARY KEY,
    teacher_id BIGINT NOT NULL REFERENCES users(telegram_id),
    amount DECIMAL(10, 2) NOT NULL,
    payout_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'rejected')),
    notes TEXT
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_student_payments_student_id ON student_payments(student_id);
CREATE INDEX IF NOT EXISTS idx_student_payments_teacher_id ON student_payments(teacher_id);
CREATE INDEX IF NOT EXISTS idx_teacher_payouts_teacher_id ON teacher_payouts(teacher_id);