-- Исправляем цены: Базовый 600₽, Премиум 900₽
UPDATE t_p86463701_eloquent_school_site.pricing_plans 
SET price_rub = 600 
WHERE plan_key = 'basic';

UPDATE t_p86463701_eloquent_school_site.pricing_plans 
SET price_rub = 900 
WHERE plan_key = 'premium';