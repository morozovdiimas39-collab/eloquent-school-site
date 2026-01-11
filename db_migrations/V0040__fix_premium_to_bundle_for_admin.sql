-- Fix subscription: change premium to bundle for user 7515380522
UPDATE t_p86463701_eloquent_school_site.subscription_payments 
SET period = 'bundle', updated_at = CURRENT_TIMESTAMP 
WHERE telegram_id = 7515380522 AND status = 'paid' AND period = 'premium';