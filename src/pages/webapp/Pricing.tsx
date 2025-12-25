import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import Icon from '@/components/ui/icon';
import { useNavigate } from 'react-router-dom';

export default function Pricing() {
  const navigate = useNavigate();
  const [currentPlan] = useState<'free' | 'exercises' | 'dialog' | 'bundle'>('free');
  const [selectedPlans, setSelectedPlans] = useState<Set<string>>(new Set());

  const plans = [
    {
      id: 'exercises',
      name: 'Упражнения + Диалог',
      price: 600,
      period: 'в месяц',
      description: 'Полная программа обучения',
      icon: 'BookOpen',
      color: 'from-blue-600 to-cyan-600',
      borderColor: 'border-blue-500',
      ringColor: 'ring-blue-500/20',
      features: [
        { text: 'Диалог с Аней без ограничений', icon: 'MessageCircle', included: true },
        { text: 'Все типы упражнений', icon: 'Layers', included: true },
        { text: 'Предложения, контекст, ассоциации', icon: 'Brain', included: true },
        { text: 'Перевод и проверка', icon: 'Languages', included: true },
        { text: 'Отслеживание прогресса', icon: 'TrendingUp', included: true },
        { text: 'Голосовые сообщения', icon: 'Mic', included: false }
      ],
      badge: 'Популярный',
      buttonText: 'Выбрать тариф'
    },
    {
      id: 'dialog',
      name: 'Голосовой режим',
      price: 800,
      period: 'в месяц',
      description: 'Практика разговорного английского',
      icon: 'Mic',
      color: 'from-purple-600 to-pink-600',
      borderColor: 'border-purple-500',
      ringColor: 'ring-purple-500/20',
      features: [
        { text: 'Голосовые сообщения с Аней', icon: 'Mic', included: true },
        { text: 'Распознавание речи', icon: 'AudioLines', included: true },
        { text: 'Исправление произношения', icon: 'CheckCircle2', included: true },
        { text: 'Персонализация под цели', icon: 'Target', included: true },
        { text: 'Упражнения', icon: 'BookOpen', included: false },
        { text: 'Текстовый диалог', icon: 'MessageSquare', included: false }
      ],
      badge: null,
      buttonText: 'Выбрать тариф'
    }
  ];

  const togglePlan = (planId: string) => {
    const newSelected = new Set(selectedPlans);
    if (newSelected.has(planId)) {
      newSelected.delete(planId);
    } else {
      newSelected.add(planId);
    }
    setSelectedPlans(newSelected);
  };

  const calculateTotal = () => {
    let total = 0;
    selectedPlans.forEach(planId => {
      const plan = plans.find(p => p.id === planId);
      if (plan) total += plan.price;
    });

    // Скидка 15% если выбраны оба плана
    if (selectedPlans.size === 2) {
      const discount = total * 0.15;
      return { total, discount, final: total - discount };
    }

    return { total, discount: 0, final: total };
  };

  const handleSubscribe = () => {
    if (selectedPlans.size === 0) {
      const tg = window.Telegram?.WebApp;
      if (tg) {
        tg.showAlert('Выберите хотя бы один тариф! 📝');
      } else {
        alert('Выберите хотя бы один тариф! 📝');
      }
      return;
    }

    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.showAlert('Оплата подписки будет доступна в ближайшее время! 🚀');
    } else {
      alert('Оплата подписки будет доступна в ближайшее время! 🚀');
    }
  };

  const pricing = calculateTotal();
  const hasDiscount = selectedPlans.size === 2;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 py-6 px-4">
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
            <p className="text-gray-600 text-base">Учи английский с Аней — выбирай то, что тебе нужно</p>
            {hasDiscount && (
              <Badge className="mt-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white px-4 py-1.5 text-sm">
                🎉 Скидка 15% при покупке обоих тарифов!
              </Badge>
            )}
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2 max-w-5xl mx-auto mb-6">
          {plans.map((plan) => {
            const isSelected = selectedPlans.has(plan.id);
            
            return (
              <Card 
                key={plan.id} 
                className={`relative shadow-lg transition-all cursor-pointer hover:shadow-xl ${
                  isSelected
                    ? `border-2 ${plan.borderColor} ring-2 ${plan.ringColor}` 
                    : 'border border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => togglePlan(plan.id)}
              >
                {plan.badge && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <Badge className={`bg-gradient-to-r ${plan.color} text-white px-4 py-1 shadow-lg`}>
                      {plan.badge}
                    </Badge>
                  </div>
                )}

                <div className="absolute top-4 right-4">
                  <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                    isSelected 
                      ? `${plan.borderColor} bg-gradient-to-r ${plan.color}` 
                      : 'border-gray-300 bg-white'
                  }`}>
                    {isSelected && (
                      <Icon name="Check" size={14} className="text-white" />
                    )}
                  </div>
                </div>
                
                <CardHeader className="text-center pb-4 pt-6">
                  <div className={`w-16 h-16 rounded-2xl bg-gradient-to-r ${plan.color} flex items-center justify-center mx-auto mb-4 shadow-lg`}>
                    <Icon name={plan.icon as any} size={32} className="text-white" />
                  </div>
                  
                  <CardTitle className="text-2xl font-bold mb-1">{plan.name}</CardTitle>
                  <CardDescription className="text-sm mb-4">{plan.description}</CardDescription>
                  
                  <div className="flex items-baseline justify-center gap-2">
                    <span className="text-4xl font-bold text-gray-900">{plan.price}</span>
                    <span className="text-xl text-gray-600">₽</span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">{plan.period}</p>
                </CardHeader>

                <CardContent className="space-y-4 pb-6">
                  <div className="space-y-2.5">
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
                            <Icon name="CheckCircle2" size={18} />
                          ) : (
                            <Icon name="XCircle" size={18} />
                          )}
                        </div>
                        <span className="text-sm flex-1">{feature.text}</span>
                      </div>
                    ))}
                  </div>

                  <div className={`pt-2 text-center text-sm font-medium ${
                    isSelected ? `bg-gradient-to-r ${plan.color} bg-clip-text text-transparent` : 'text-gray-500'
                  }`}>
                    {isSelected ? '✓ Выбрано' : 'Нажмите для выбора'}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Итоговая карточка с ценой */}
        {selectedPlans.size > 0 && (
          <div className="max-w-3xl mx-auto mb-6">
            <Card className="shadow-xl border-2 border-indigo-200 bg-gradient-to-br from-white to-indigo-50/30">
              <CardContent className="pt-6 pb-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between text-lg">
                    <span className="text-gray-700 font-medium">Итого:</span>
                    <span className="text-gray-900 font-semibold">{pricing.total} ₽</span>
                  </div>

                  {hasDiscount && (
                    <>
                      <div className="flex items-center justify-between text-base">
                        <span className="text-green-700 font-medium flex items-center gap-2">
                          <Icon name="Tag" size={18} />
                          Скидка 15%:
                        </span>
                        <span className="text-green-700 font-semibold">-{pricing.discount.toFixed(0)} ₽</span>
                      </div>
                      <div className="border-t pt-4 flex items-center justify-between">
                        <span className="text-xl text-gray-900 font-bold">К оплате:</span>
                        <div className="text-right">
                          <div className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                            {pricing.final.toFixed(0)} ₽
                          </div>
                          <div className="text-sm text-gray-500 line-through">
                            {pricing.total} ₽
                          </div>
                        </div>
                      </div>
                    </>
                  )}

                  <Button
                    onClick={handleSubscribe}
                    className="w-full h-14 text-lg font-semibold bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-lg"
                  >
                    <Icon name="CreditCard" size={22} className="mr-2" />
                    Оформить подписку
                  </Button>

                  {hasDiscount && (
                    <p className="text-center text-sm text-green-700 font-medium">
                      🎉 Вы экономите {pricing.discount.toFixed(0)} ₽ в месяц!
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Информационная карточка */}
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
                      <span>Выбери один или оба тарифа — получи скидку 15%</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600 mt-1">•</span>
                      <span>Оплата происходит автоматически каждый месяц</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600 mt-1">•</span>
                      <span>Можешь отменить подписку в любое время</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600 mt-1">•</span>
                      <span>70% от подписки идет твоему преподавателю</span>
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