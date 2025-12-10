import { Card, CardContent } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

const steps = [
  {
    icon: 'UserPlus',
    title: 'Открой бота в Telegram',
    description: 'Найди @anyagpt_bot и нажми "Старт"',
    visual: (
      <div className="w-full bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 border-2 border-blue-200">
        <div className="bg-white rounded-lg shadow-sm p-3 mb-2">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold">A</div>
            <div>
              <div className="font-bold text-xs">Anya AI Tutor</div>
              <div className="text-xs text-gray-500">@anyagpt_bot</div>
            </div>
          </div>
          <div className="text-xs text-gray-600 mb-2">👋 Привет! Я Аня, твой ИИ-репетитор английского</div>
          <button className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-xs font-bold py-2 rounded-lg">
            Старт
          </button>
        </div>
      </div>
    )
  },
  {
    icon: 'MessageSquare',
    title: 'Начни общаться',
    description: 'Пиши на английском — Аня поддержит диалог',
    visual: (
      <div className="w-full bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-4 border-2 border-purple-200">
        <div className="space-y-2">
          <div className="flex gap-2">
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">A</div>
            <div className="bg-white rounded-xl rounded-tl-sm px-3 py-2 shadow-sm text-xs max-w-[80%]">
              What's your hobby? 🎨
            </div>
          </div>
          <div className="flex gap-2 justify-end">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl rounded-tr-sm px-3 py-2 shadow-sm text-xs max-w-[80%]">
              I like to draw
            </div>
          </div>
          <div className="flex gap-2">
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-purple-500 to-pink-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">A</div>
            <div className="bg-white rounded-xl rounded-tl-sm px-3 py-2 shadow-sm text-xs max-w-[80%]">
              Cool! What do you draw? ✏️
            </div>
          </div>
        </div>
      </div>
    )
  },
  {
    icon: 'BookMarked',
    title: 'Учи новые слова',
    description: 'Незнакомое слово? Аня объяснит и сохранит',
    visual: (
      <div className="w-full bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-4 border-2 border-green-200">
        <div className="space-y-2">
          <div className="flex gap-2 justify-end">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl rounded-tr-sm px-3 py-2 shadow-sm text-xs">
              What is "gorgeous"?
            </div>
          </div>
          <div className="flex gap-2">
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">A</div>
            <div className="bg-white rounded-xl rounded-tl-sm px-3 py-2 shadow-sm text-xs">
              <div className="font-bold text-green-700 mb-1">gorgeous</div>
              <div className="text-gray-600 mb-1">очень красивый, великолепный</div>
              <div className="text-xs text-gray-500">✅ Добавлено в словарь</div>
            </div>
          </div>
        </div>
      </div>
    )
  },
  {
    icon: 'Trophy',
    title: 'Отслеживай прогресс',
    description: 'Смотри статистику и радуйся росту',
    visual: (
      <div className="w-full bg-gradient-to-br from-orange-50 to-yellow-50 rounded-xl p-4 border-2 border-orange-200">
        <div className="bg-white rounded-lg shadow-sm p-3">
          <div className="text-xs font-bold mb-3 text-gray-700">📊 Твоя статистика</div>
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-600">Слов изучено</span>
              <span className="text-sm font-bold text-blue-600">127</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1.5">
              <div className="bg-gradient-to-r from-blue-500 to-indigo-600 h-1.5 rounded-full" style={{ width: '65%' }}></div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-600">Уровень</span>
              <span className="text-sm font-bold text-green-600">B1 → B2</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-600">Диалогов</span>
              <span className="text-sm font-bold text-purple-600">43</span>
            </div>
          </div>
        </div>
      </div>
    )
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
        <div className="max-w-7xl mx-auto">
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
                  <div className="absolute -top-4 -left-4 w-12 h-12 rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 text-white font-bold flex items-center justify-center text-xl shadow-xl group-hover:scale-110 transition-transform z-10">
                    {idx + 1}
                  </div>
                  
                  <div className="mt-4 space-y-4">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mb-4 shadow-lg group-hover:scale-110 group-hover:rotate-3 transition-all duration-300">
                      <Icon name={step.icon as any} size={32} className="text-white" />
                    </div>
                    <h3 className="text-lg font-bold mb-2 text-gray-900 group-hover:text-indigo-600 transition-colors">{step.title}</h3>
                    <p className="text-gray-600 text-sm leading-relaxed mb-4">{step.description}</p>
                    
                    {/* Visual mockup */}
                    <div className="animate-fade-in">
                      {step.visual}
                    </div>
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
