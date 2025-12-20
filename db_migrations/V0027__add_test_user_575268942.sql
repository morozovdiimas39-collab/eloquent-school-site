-- Создаем пользователя для telegram_id=575268942
INSERT INTO t_p86463701_eloquent_school_site.users (telegram_id, username, first_name, role, language_level)
VALUES (575268942, 'test_user', 'Test', 'student', 'A1')
ON CONFLICT (telegram_id) DO NOTHING;