-- ⚠️ КРИТИЧНО: ПРАВИЛЬНІ ЦІНИ (600₽/800₽/1190₽)
UPDATE t_p86463701_eloquent_school_site.pricing_plans 
SET 
  price_rub = CASE plan_key
    WHEN 'basic' THEN 600
    WHEN 'premium' THEN 800
    WHEN 'bundle' THEN 1190
  END,
  price_kop = CASE plan_key
    WHEN 'basic' THEN 60000
    WHEN 'premium' THEN 80000
    WHEN 'bundle' THEN 119000
  END,
  updated_at = CURRENT_TIMESTAMP;