import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';

export default function ScreenshotsSection() {
  const features = [
    {
      title: 'Живые диалоги',
      description: 'Общайся с Аней на английском о чем угодно - она поддержит любую тему',
      icon: 'MessageSquare',
      color: 'from-blue-500 to-indigo-500'
    },
    {
      title: 'Исправление ошибок',
      description: 'Аня тактично исправляет ошибки и объясняет правила на русском',
      icon: 'CheckCircle',
      color: 'from-green-500 to-emerald-500'
    },
    {
      title: 'Запоминание слов',
      description: 'Новые слова автоматически добавляются в твой личный словарь',
      icon: 'BookOpen',
      color: 'from-purple-500 to-pink-500'
    },
    {
      title: 'Упражнения',
      description: 'Интерактивные задания для закрепления выученных слов',
      icon: 'Target',
      color: 'from-orange-500 to-red-500'
    },
    {
      title: 'Голосовая практика',
      description: 'Практикуй произношение с помощью голосовых сообщений',
      icon: 'Mic',
      color: 'from-cyan-500 to-blue-500'
    },
    {
      title: 'Отслеживание прогресса',
      description: 'Смотри статистику и следи за своим развитием',
      icon: 'TrendingUp',
      color: 'from-indigo-500 to-purple-500'
    }
  ];

  return (
    <section className="relative py-20 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-white via-indigo-50 to-purple-50"></div>
      <div className="absolute top-20 right-10 w-96 h-96 bg-indigo-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
      <div className="absolute bottom-20 left-10 w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-16">
            <div className="inline-block mb-4">
              <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 backdrop-blur-sm text-indigo-700 font-medium text-sm border border-indigo-200 shadow-lg">
                <Icon name="Sparkles" size={16} />
                Возможности Ани
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-gray-900 to-indigo-600 bg-clip-text text-transparent">
              Увидь Аню в действии
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Полноценный AI-репетитор, который помогает учить английский естественно и эффективно
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
            {features.map((feature, index) => (
              <div
                key={index}
                className="group bg-white rounded-2xl p-6 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 border-2 border-gray-100 hover:border-indigo-200"
              >
                <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4 shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                  <Icon name={feature.icon as any} size={28} className="text-white" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>

          {/* Screenshot Example */}
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-3xl shadow-2xl overflow-hidden border-2 border-indigo-100">
              <div className="grid md:grid-cols-2">
                {/* Left: Phone mockup */}
                <div className="bg-gradient-to-br from-indigo-50 to-purple-50 p-8 flex items-center justify-center">
                  <div className="relative w-full max-w-xs">
                    <div className="bg-gray-900 rounded-[2.5rem] p-3 shadow-2xl">
                      <div className="bg-white rounded-[2rem] overflow-hidden">
                        <img
                          src="https://cdn.poehali.dev/files/Снимок экрана 2025-12-21 в 00.35.46.png"
                          alt="Диалог с Аней в Telegram"
                          className="w-full h-auto"
                        />
                      </div>
                    </div>
                    
                    {/* Floating badge */}
                    <div className="absolute -right-4 top-8 animate-float">
                      <div className="bg-white rounded-xl px-4 py-2 shadow-xl border-2 border-green-200">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                          <span className="text-sm font-semibold text-gray-700">Online 24/7</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right: Info */}
                <div className="p-8 flex flex-col justify-center">
                  <div className="space-y-6">
                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                        <Icon name="MessageSquare" size={20} className="text-blue-600" />
                      </div>
                      <div>
                        <h4 className="font-bold text-gray-900 mb-1">Естественное общение</h4>
                        <p className="text-gray-600 text-sm">Разговаривай как с настоящим учителем</p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                        <Icon name="CheckCircle" size={20} className="text-green-600" />
                      </div>
                      <div>
                        <h4 className="font-bold text-gray-900 mb-1">Мгновенная обратная связь</h4>
                        <p className="text-gray-600 text-sm">Ошибки исправляются прямо в диалоге</p>
                      </div>
                    </div>

                    <div className="flex items-start gap-3">
                      <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
                        <Icon name="Brain" size={20} className="text-purple-600" />
                      </div>
                      <div>
                        <h4 className="font-bold text-gray-900 mb-1">Адаптивное обучение</h4>
                        <p className="text-gray-600 text-sm">Аня подстраивается под твой уровень</p>
                      </div>
                    </div>
                  </div>

                  <Button
                    onClick={() => window.open('https://t.me/eloquent_school_bot', '_blank')}
                    className="mt-8 w-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 font-semibold h-12"
                  >
                    Попробовать бесплатно
                    <Icon name="ArrowRight" size={18} className="ml-2" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
