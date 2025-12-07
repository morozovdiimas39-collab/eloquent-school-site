import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { useNavigate } from 'react-router-dom';

const plans = [
  {
    name: 'Бесплатный',
    price: '0₽',
    period: 'навсегда',
    description: 'Попробуй anyaGPT без ограничений по времени',
    features: [
      { text: '20 сообщений в день с Аней', included: true },
      { text: 'Базовые упражнения', included: true },
      { text: 'Отслеживание прогресса', included: true },
      { text: 'Персональные слова от учителя', included: false },
      { text: 'Полная статистика и достижения', included: false },
      { text: 'Приоритетная поддержка', included: false }
    ],
    buttonText: 'Начать бесплатно',
    popular: false
  },
  {
    name: 'Premium',
    price: '500₽',
    period: 'в месяц',
    description: 'Полный доступ ко всем возможностям anyaGPT',
    features: [
      { text: 'Безлимитные сообщения с Аней', included: true },
      { text: 'Все упражнения и тесты', included: true },
      { text: 'Персональные слова от учителя', included: true },
      { text: 'Полная статистика и достижения', included: true },
      { text: 'Детальный анализ ошибок', included: true },
      { text: 'Приоритетная поддержка', included: true }
    ],
    buttonText: 'Перейти на Premium',
    popular: true
  }
];

export default function PricingSection() {
  const navigate = useNavigate();

  return (
    <section id="pricing" className="container mx-auto px-4 py-20 bg-white">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Выбери свой план
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Начни бесплатно или сразу получи полный доступ
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {plans.map((plan, idx) => (
            <Card
              key={idx}
              className={`relative ${
                plan.popular
                  ? 'border-4 border-violet-600 shadow-2xl scale-105'
                  : 'border-2 hover:shadow-xl transition-all'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <div className="bg-gradient-to-r from-violet-600 to-purple-600 text-white px-6 py-2 rounded-full font-bold text-sm shadow-lg">
                    🔥 Популярный
                  </div>
                </div>
              )}

              <CardHeader className="text-center pb-4">
                <CardTitle className="text-2xl font-bold mb-2">{plan.name}</CardTitle>
                <div className="mb-3">
                  <span className="text-5xl font-bold bg-gradient-to-r from-violet-600 to-purple-600 bg-clip-text text-transparent">
                    {plan.price}
                  </span>
                  <span className="text-gray-600 text-lg ml-2">{plan.period}</span>
                </div>
                <p className="text-gray-600 text-sm">{plan.description}</p>
              </CardHeader>

              <CardContent className="space-y-6">
                <div className="space-y-3">
                  {plan.features.map((feature, featureIdx) => (
                    <div key={featureIdx} className="flex items-start gap-3">
                      {feature.included ? (
                        <Icon name="CheckCircle" size={20} className="text-green-600 flex-shrink-0 mt-0.5" />
                      ) : (
                        <Icon name="XCircle" size={20} className="text-gray-300 flex-shrink-0 mt-0.5" />
                      )}
                      <span className={feature.included ? 'text-gray-900' : 'text-gray-400'}>
                        {feature.text}
                      </span>
                    </div>
                  ))}
                </div>

                <Button
                  onClick={() => navigate('/app')}
                  className={`w-full font-semibold text-lg h-12 ${
                    plan.popular
                      ? 'bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 shadow-lg'
                      : 'bg-gray-900 hover:bg-gray-800'
                  }`}
                >
                  {plan.buttonText}
                  <Icon name="ArrowRight" size={18} className="ml-2" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mt-12 text-center">
          <Card className="inline-block border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-white max-w-2xl">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <Icon name="Info" size={24} className="text-blue-600 flex-shrink-0 mt-1" />
                <div className="text-left">
                  <h4 className="font-bold text-lg mb-2">Как работает подписка?</h4>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    Premium-подписка активируется автоматически после оплаты и продлевается каждый месяц. 
                    Ты можешь отменить её в любой момент в настройках Telegram. 
                    Первые 3 дня — пробный период с возможностью возврата средств.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}
