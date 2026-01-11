-- Revert bundle back to premium for user 7515380522
UPDATE t_p86463701_eloquent_school_site.subscription_payments 
SET period = 'premium', updated_at = CURRENT_TIMESTAMP 
WHERE id = 8 AND telegram_id = 7515380522 AND status = 'paid' AND period = 'bundle';