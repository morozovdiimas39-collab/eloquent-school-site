-- Активируем пробный период для администратора
UPDATE t_p86463701_eloquent_school_site.users 
SET 
    subscription_status = 'active',
    subscription_expires_at = (CURRENT_TIMESTAMP + INTERVAL '30 days'),
    trial_used = true
WHERE telegram_id = 7515380522;