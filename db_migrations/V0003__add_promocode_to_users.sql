ALTER TABLE t_p86463701_eloquent_school_site.users 
ADD COLUMN IF NOT EXISTS promocode VARCHAR(50);

CREATE INDEX IF NOT EXISTS idx_users_promocode 
ON t_p86463701_eloquent_school_site.users(promocode);