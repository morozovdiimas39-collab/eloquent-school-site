-- Обнуляем teacher-связанные поля для всех пользователей
UPDATE t_p86463701_eloquent_school_site.users 
SET 
  promocode = NULL,
  teacher_id = NULL,
  phone = NULL,
  card_number = NULL,
  bank_name = NULL,
  total_earnings = 0,
  current_balance = 0;

-- Делаем всех пользователей студентами
UPDATE t_p86463701_eloquent_school_site.users 
SET role = 'student' 
WHERE role = 'teacher' OR role IS NULL;

-- Комментарий
COMMENT ON TABLE t_p86463701_eloquent_school_site.users IS 'Users table - только студенты, teacher-поля deprecated';
