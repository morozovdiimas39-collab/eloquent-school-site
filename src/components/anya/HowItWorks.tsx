import { Card, CardContent } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

const steps = [
  {
    icon: 'UserPlus',
    title: 'Открой бота в Telegram',
    description: 'Просто нажми "Начать" и расскажи Ане о своём уровне английского и интересах.'
  },
  {
    icon: 'MessageSquare',
    title: 'Начни общаться',
    description: 'Пиши Ане на английском о чём угодно. Она поддержит беседу и подскажет, если ошибёшься.'
  },
  {
    icon: 'BookMarked',
    title: 'Учи новые слова',
    description: 'Встретил незнакомое слово? Аня объяснит его и добавит в твой персональный словарь.'
  },
  {
    icon: 'Trophy',
    title: 'Отслеживай прогресс',
    description: 'Смотри статистику, выполняй упражнения и радуйся росту — английский становится лучше!'
  }
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="container mx-auto px-4 py-20 bg-gradient-to-br from-violet-50 to-purple-50">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Как начать учиться
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Всего 4 простых шага отделяют тебя от свободного английского
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, idx) => (
            <div key={idx} className="relative">
              <Card className="border-2 hover:shadow-xl transition-all h-full bg-white">
                <CardContent className="p-6">
                  <div className="relative">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-600 to-purple-600 flex items-center justify-center mb-4 shadow-lg">
                      <Icon name={step.icon as any} size={28} className="text-white" />
                    </div>
                    <div className="absolute -top-3 -right-3 w-10 h-10 rounded-full bg-violet-600 text-white font-bold flex items-center justify-center text-lg shadow-lg">
                      {idx + 1}
                    </div>
                  </div>
                  <h3 className="text-lg font-bold mb-2">{step.title}</h3>
                  <p className="text-gray-600 text-sm">{step.description}</p>
                </CardContent>
              </Card>
              {idx < steps.length - 1 && (
                <div className="hidden lg:block absolute top-1/2 -right-3 transform -translate-y-1/2 z-10">
                  <Icon name="ArrowRight" size={24} className="text-violet-400" />
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <Card className="inline-block border-2 border-violet-200 bg-gradient-to-br from-white to-violet-50">
            <CardContent className="p-6 flex items-center gap-4">
              <Icon name="Sparkles" size={32} className="text-violet-600" />
              <div className="text-left">
                <h4 className="font-bold text-lg mb-1">Начни прямо сейчас!</h4>
                <p className="text-gray-600 text-sm">20 сообщений в день бесплатно. Без карты, без регистрации.</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}
