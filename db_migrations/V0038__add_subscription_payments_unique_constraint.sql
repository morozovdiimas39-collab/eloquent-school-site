-- Заполняем amount_kop для записей где он NULL
UPDATE t_p86463701_eloquent_school_site.subscription_payments
SET amount_kop = CAST(COALESCE(amount, 0) * 100 AS INTEGER)
WHERE amount_kop IS NULL;

-- Заполняем amount для записей где он NULL (обратное преобразование)
UPDATE t_p86463701_eloquent_school_site.subscription_payments
SET amount = COALESCE(amount_kop, 0) / 100.0
WHERE amount IS NULL;

-- Добавляем уникальный constraint на (telegram_id, period)
ALTER TABLE t_p86463701_eloquent_school_site.subscription_payments
ADD CONSTRAINT subscription_payments_telegram_period_unique 
UNIQUE (telegram_id, period);