-- CRITICAL FIX: Remove eternal free subscriptions
-- Problem: DEFAULT 'active' gave all new users active subscription without payment

-- Step 1: Deactivate ALL users with subscription_status = 'active' WITHOUT payment records
UPDATE t_p86463701_eloquent_school_site.users u
SET 
    subscription_status = 'inactive',
    subscription_expires_at = NULL,
    updated_at = CURRENT_TIMESTAMP
WHERE 
    u.subscription_status = 'active'
    AND NOT EXISTS (
        SELECT 1 
        FROM t_p86463701_eloquent_school_site.subscription_payments sp
        WHERE sp.telegram_id = u.telegram_id 
        AND sp.status = 'paid'
        AND sp.expires_at > CURRENT_TIMESTAMP
    )
    AND u.telegram_id != 7515380522;

-- Step 2: Change DEFAULT from 'active' to 'inactive'
ALTER TABLE t_p86463701_eloquent_school_site.users 
ALTER COLUMN subscription_status SET DEFAULT 'inactive';