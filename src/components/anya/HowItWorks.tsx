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
    <section id="how-it-works" className="relative py-20 overflow-hidden">
      {/* Background with gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-50 via-blue-50 to-purple-50"></div>
      
      {/* Decorative blobs */}
      <div className="absolute top-10 right-10 w-72 h-72 bg-blue-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
      <div className="absolute bottom-10 left-10 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <div className="inline-block mb-4">
              <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 backdrop-blur-sm text-indigo-700 font-medium text-sm border border-indigo-200 shadow-lg">
                <Icon name="Zap" size={16} />
                Просто и быстро
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-gray-900 to-indigo-600 bg-clip-text text-transparent">
              Как начать учиться
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Всего 4 простых шага отделяют тебя от свободного английского
            </p>
          </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {steps.map((step, idx) => (
            <div key={idx} className="relative group">
              <Card className="border-2 border-gray-200 hover:border-indigo-400 transition-all duration-300 h-full bg-white/90 backdrop-blur-sm hover:shadow-2xl hover:-translate-y-2">
                <CardContent className="p-6 relative">
                  {/* Step number badge */}
                  <div className="absolute -top-4 -left-4 w-12 h-12 rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 text-white font-bold flex items-center justify-center text-xl shadow-xl group-hover:scale-110 transition-transform">
                    {idx + 1}
                  </div>
                  
                  <div className="mt-4">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mb-4 shadow-lg group-hover:scale-110 group-hover:rotate-3 transition-all duration-300">
                      <Icon name={step.icon as any} size={32} className="text-white" />
                    </div>
                    <h3 className="text-lg font-bold mb-2 text-gray-900 group-hover:text-indigo-600 transition-colors">{step.title}</h3>
                    <p className="text-gray-600 text-sm leading-relaxed">{step.description}</p>
                  </div>
                </CardContent>
              </Card>
              
              {/* Arrow connector */}
              {idx < steps.length - 1 && (
                <div className="hidden lg:block absolute top-1/2 -right-4 transform -translate-y-1/2 z-10">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-r from-indigo-400 to-purple-400 flex items-center justify-center shadow-lg animate-pulse">
                    <Icon name="ArrowRight" size={18} className="text-white" />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-16 flex justify-center">
          <Card className="max-w-2xl border-2 border-indigo-200 bg-gradient-to-br from-white via-indigo-50 to-purple-50 shadow-2xl hover:shadow-3xl transition-all duration-300 hover:scale-105">
            <CardContent className="p-8 flex flex-col sm:flex-row items-center gap-6">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center shadow-xl flex-shrink-0">
                <Icon name="Sparkles" size={40} className="text-white" />
              </div>
              <div className="text-center sm:text-left">
                <h4 className="font-bold text-2xl mb-2 bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">Начни прямо сейчас!</h4>
                <p className="text-gray-700 text-lg">20 сообщений в день бесплатно</p>
                <p className="text-sm text-gray-500 mt-1">Без карты, без регистрации — просто открой Telegram</p>
              </div>
            </CardContent>
          </Card>
        </div>
        </div>
      </div>
    </section>
  );
}