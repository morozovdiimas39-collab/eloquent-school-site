-- Изменяем тип teacher_id на BIGINT для поддержки больших telegram_id
ALTER TABLE t_p86463701_eloquent_school_site.users 
ALTER COLUMN teacher_id TYPE BIGINT;