import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import { useNavigate } from 'react-router-dom';

export default function Pricing() {
  const navigate = useNavigate();
  const [currentPlan] = useState<'free' | 'premium'>('free');

  const plans = [
    {
      id: 'free',
      name: 'Бесплатный',
      price: 0,
      period: 'навсегда',
      description: 'Для начинающих учеников',
      features: [
        { text: '20 сообщений в день с Аней', icon: 'MessageCircle', included: true },
        { text: 'Базовые упражнения', icon: 'BookOpen', included: true },
        { text: 'Отслеживание прогресса', icon: 'TrendingUp', included: true },
        { text: 'Персональные слова от учителя', icon: 'User', included: false },
        { text: 'Безлимитные сообщения', icon: 'Infinity', included: false },
        { text: 'Приоритетная поддержка', icon: 'Headphones', included: false }
      ],
      badge: null,
      buttonText: 'Текущий план',
      buttonVariant: 'outline' as const,
      buttonDisabled: true
    },
    {
      id: 'premium',
      name: 'Премиум',
      price: 500,
      period: 'в месяц',
      description: 'Для серьезного изучения',
      features: [
        { text: 'Безлимитные сообщения с Аней', icon: 'Infinity', included: true },
        { text: 'Персональные слова от учителя', icon: 'User', included: true },
        { text: 'Полная статистика прогресса', icon: 'BarChart3', included: true },
        { text: 'Достижения и streak', icon: 'Award', included: true },
        { text: 'Приоритетная поддержка', icon: 'Headphones', included: true },
        { text: 'Новые функции первыми', icon: 'Zap', included: true }
      ],
      badge: 'Популярный',
      buttonText: 'Оформить Premium',
      buttonVariant: 'default' as const,
      buttonDisabled: false
    }
  ];

  const handleSubscribe = (planId: string) => {
    if (planId === 'premium') {
      const tg = window.Telegram?.WebApp;
      if (tg) {
        tg.showAlert('Оплата подписки будет доступна в ближайшее время! 🚀');
      } else {
        alert('Оплата подписки будет доступна в ближайшее время! 🚀');
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-6 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <Button
            onClick={() => navigate('/app')}
            variant="ghost"
            size="sm"
            className="mb-4"
          >
            <Icon name="ArrowLeft" size={16} className="mr-2" />
            Назад
          </Button>
          
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Выбери свой план</h1>
            <p className="text-gray-600 text-base">Начни учить английский с Аней уже сегодня</p>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2 max-w-4xl mx-auto">
          {plans.map((plan) => {
            const isCurrentPlan = currentPlan === plan.id;
            
            return (
              <Card 
                key={plan.id} 
                className={`relative shadow-lg transition-all hover:shadow-xl ${
                  plan.id === 'premium' 
                    ? 'border-2 border-indigo-500 ring-2 ring-indigo-500/20' 
                    : 'border border-gray-200'
                }`}
              >
                {plan.badge && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <Badge className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-4 py-1">
                      {plan.badge}
                    </Badge>
                  </div>
                )}
                
                <CardHeader className="text-center pb-4">
                  <CardTitle className="text-2xl font-bold mb-1">{plan.name}</CardTitle>
                  <CardDescription className="text-sm mb-4">{plan.description}</CardDescription>
                  
                  <div className="flex items-baseline justify-center gap-2">
                    <span className="text-4xl font-bold text-gray-900">{plan.price}</span>
                    <span className="text-xl text-gray-600">₽</span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">{plan.period}</p>
                </CardHeader>

                <CardContent className="space-y-6">
                  <div className="space-y-3">
                    {plan.features.map((feature, index) => (
                      <div 
                        key={index} 
                        className={`flex items-start gap-3 ${
                          feature.included ? 'text-gray-900' : 'text-gray-400'
                        }`}
                      >
                        <div className={`mt-0.5 ${
                          feature.included 
                            ? 'text-green-600' 
                            : 'text-gray-300'
                        }`}>
                          {feature.included ? (
                            <Icon name="CheckCircle2" size={20} />
                          ) : (
                            <Icon name="XCircle" size={20} />
                          )}
                        </div>
                        <div className="flex items-center gap-2 flex-1">
                          <Icon 
                            name={feature.icon as any} 
                            size={16} 
                            className={feature.included ? 'text-indigo-600' : 'text-gray-400'}
                          />
                          <span className="text-sm">{feature.text}</span>
                        </div>
                      </div>
                    ))}
                  </div>

                  <Button
                    onClick={() => handleSubscribe(plan.id)}
                    disabled={isCurrentPlan || plan.buttonDisabled}
                    variant={plan.buttonVariant}
                    className="w-full h-12 text-base font-semibold"
                  >
                    {isCurrentPlan ? (
                      <>
                        <Icon name="Check" size={20} className="mr-2" />
                        {plan.buttonText}
                      </>
                    ) : (
                      <>
                        <Icon name="CreditCard" size={20} className="mr-2" />
                        {plan.buttonText}
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="mt-8 max-w-2xl mx-auto">
          <Card className="border border-blue-200 bg-blue-50/50">
            <CardContent className="pt-6 pb-6">
              <div className="flex items-start gap-3">
                <Icon name="Info" size={24} className="text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Как работает подписка?</h3>
                  <ul className="space-y-1.5 text-sm text-gray-700">
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600 mt-1">•</span>
                      <span>Оплата происходит автоматически каждый месяц</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600 mt-1">•</span>
                      <span>Вы можете отменить подписку в любое время</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600 mt-1">•</span>
                      <span>70% от подписки идет вашему преподавателю</span>
                    </li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
