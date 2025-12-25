CREATE TABLE IF NOT EXISTS t_p86463701_eloquent_school_site.pricing_plans (
  plan_key VARCHAR(50) PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  description TEXT NOT NULL,
  price_rub INTEGER NOT NULL,
  price_kop INTEGER NOT NULL,
  duration_days INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Вставляем текущие тарифы
INSERT INTO t_p86463701_eloquent_school_site.pricing_plans (plan_key, name, description, price_rub, price_kop, duration_days)
VALUES 
  ('basic', '💬 Базовый', '• Диалог с Аней\n• Предложения, Контекст, Ассоциации, Перевод\n• Персональный словарь\n• Отслеживание прогресса', 600, 60000, 30),
  ('premium', '🎤 Премиум', '• Голосовой режим с Аней\n• Аня отвечает голосом', 800, 80000, 30),
  ('bundle', '🔥 Всё сразу', '• Все режимы Базового\n• Голосовой режим\n• Скидка 15%', 1190, 119000, 30)
ON CONFLICT (plan_key) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  price_rub = EXCLUDED.price_rub,
  price_kop = EXCLUDED.price_kop,
  duration_days = EXCLUDED.duration_days,
  updated_at = CURRENT_TIMESTAMP;