-- Добавляем колонку amount_kop для хранения суммы в копейках
ALTER TABLE t_p86463701_eloquent_school_site.subscription_payments 
ADD COLUMN IF NOT EXISTS amount_kop INTEGER;

-- Заполняем amount_kop из amount (конвертируем рубли в копейки)
UPDATE t_p86463701_eloquent_school_site.subscription_payments 
SET amount_kop = CAST(amount * 100 AS INTEGER)
WHERE amount_kop IS NULL;

-- Добавляем колонку payment_method для отслеживания способа оплаты
ALTER TABLE t_p86463701_eloquent_school_site.subscription_payments 
ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50) DEFAULT 'telegram';

-- Добавляем колонку updated_at для отслеживания изменений
ALTER TABLE t_p86463701_eloquent_school_site.subscription_payments 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;