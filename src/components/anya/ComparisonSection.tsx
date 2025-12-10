import { Card, CardContent } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

const benefits = [
  {
    icon: 'MessageCircle',
    title: 'Практика 24/7',
    description: 'Общайся с Аней в любое время — утром по дороге на работу или поздно вечером перед сном',
    color: 'from-blue-500 to-indigo-600',
    stat: '24/7',
    statLabel: 'доступность'
  },
  {
    icon: 'Zap',
    title: 'Мгновенные ответы',
    description: 'Не нужно ждать урока с репетитором — Аня отвечает сразу и помогает исправить ошибки здесь и сейчас',
    color: 'from-purple-500 to-pink-600',
    stat: '<1 сек',
    statLabel: 'время ответа'
  },
  {
    icon: 'Target',
    title: 'Персональный подход',
    description: 'Аня запоминает твой уровень, интересы и ошибки. Подбирает темы и упражнения специально для тебя',
    color: 'from-green-500 to-emerald-600',
    stat: '100%',
    statLabel: 'персонализация'
  },
  {
    icon: 'TrendingUp',
    title: 'Видимый прогресс',
    description: 'Отслеживай, сколько слов выучил, как улучшился твой уровень и какие темы уже освоил',
    color: 'from-orange-500 to-red-600',
    stat: '+247',
    statLabel: 'слов в месяц'
  }
];

const learningFlow = [
  {
    icon: 'BookOpen',
    title: 'Репетитор',
    description: 'Объясняет грамматику, разбирает сложные темы',
    role: 'Структура и база'
  },
  {
    icon: 'Plus',
    color: 'text-blue-600'
  },
  {
    icon: 'Bot',
    title: 'anyaGPT',
    description: 'Ежедневная практика и закрепление материала',
    role: 'Практика и навык'
  },
  {
    icon: 'ArrowRight',
    color: 'text-green-600'
  },
  {
    icon: 'Trophy',
    title: 'Результат',
    description: 'Свободное владение английским языком',
    role: 'Твоя цель'
  }
];

export default function ComparisonSection() {
  return (
    <section className="relative py-24 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-white via-indigo-50 to-purple-50"></div>
      <div className="absolute top-20 right-20 w-96 h-96 bg-indigo-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob"></div>
      <div className="absolute bottom-20 left-20 w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-blob animation-delay-2000"></div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-16">
            <div className="inline-block mb-4">
              <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 backdrop-blur-sm text-indigo-700 font-medium text-sm border border-indigo-200 shadow-lg">
                <Icon name="Sparkles" size={16} />
                Как это работает
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-gray-900 to-indigo-600 bg-clip-text text-transparent">
              anyaGPT дополняет твоё обучение
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Не заменяет репетитора, а усиливает результат — практикуйся каждый день и достигай целей быстрее
            </p>
          </div>

          {/* Learning Flow Diagram */}
          <div className="mb-20">
            <Card className="border-2 border-indigo-200 bg-white/80 backdrop-blur-sm shadow-2xl">
              <CardContent className="p-8">
                <div className="grid md:grid-cols-5 gap-6 items-center">
                  {learningFlow.map((item, idx) => (
                    <div key={idx} className="flex flex-col items-center text-center">
                      {item.title ? (
                        <>
                          <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${
                            idx === 0 ? 'from-blue-500 to-indigo-600' :
                            idx === 2 ? 'from-purple-500 to-indigo-600' :
                            'from-green-500 to-emerald-600'
                          } flex items-center justify-center mb-4 shadow-xl transform hover:scale-110 transition-transform duration-300`}>
                            <Icon name={item.icon as any} size={36} className="text-white" />
                          </div>
                          <h4 className="font-bold text-lg mb-2 text-gray-900">{item.title}</h4>
                          <p className="text-sm text-gray-600 mb-2">{item.description}</p>
                          <span className="inline-block px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-xs font-medium">
                            {item.role}
                          </span>
                        </>
                      ) : (
                        <div className="hidden md:block">
                          <Icon name={item.icon as any} size={32} className={item.color} />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Benefits Grid */}
          <div className="grid md:grid-cols-2 gap-6 mb-16">
            {benefits.map((benefit, idx) => (
              <Card 
                key={idx}
                className="group border-2 border-gray-200 hover:border-indigo-300 transition-all duration-300 bg-white/90 backdrop-blur-sm hover:shadow-2xl hover:-translate-y-2"
              >
                <CardContent className="p-8">
                  <div className="flex items-start gap-6">
                    <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${benefit.color} flex items-center justify-center flex-shrink-0 shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                      <Icon name={benefit.icon as any} size={28} className="text-white" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-bold mb-2 text-gray-900 group-hover:text-indigo-600 transition-colors">
                        {benefit.title}
                      </h3>
                      <p className="text-gray-600 leading-relaxed mb-4">
                        {benefit.description}
                      </p>
                      <div className="flex items-baseline gap-2">
                        <span className={`text-3xl font-bold bg-gradient-to-r ${benefit.color} bg-clip-text text-transparent`}>
                          {benefit.stat}
                        </span>
                        <span className="text-sm text-gray-500">{benefit.statLabel}</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Bottom CTA Card */}
          <div className="flex justify-center">
            <Card className="max-w-4xl border-2 border-indigo-200 bg-gradient-to-br from-white via-indigo-50 to-purple-50 shadow-2xl">
              <CardContent className="p-8">
                <div className="flex flex-col md:flex-row items-center gap-6">
                  <div className="flex-shrink-0">
                    <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-pink-500 to-rose-600 flex items-center justify-center shadow-xl">
                      <Icon name="Heart" size={48} className="text-white" />
                    </div>
                  </div>
                  <div className="flex-1 text-center md:text-left">
                    <h3 className="text-2xl font-bold mb-3 bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                      Идеально работает вместе!
                    </h3>
                    <p className="text-gray-700 text-lg leading-relaxed mb-4">
                      Занимайся с репетитором для структуры и базы, а с anyaGPT — для ежедневной практики. 
                      Так ты будешь погружён в язык постоянно и результат придёт в 3-5 раз быстрее.
                    </p>
                    <div className="flex flex-wrap gap-3 justify-center md:justify-start">
                      <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/80 backdrop-blur-sm rounded-xl shadow-md border border-indigo-100">
                        <Icon name="Check" size={16} className="text-green-600" />
                        <span className="text-sm font-medium text-gray-700">Репетитор: 2 раза в неделю</span>
                      </div>
                      <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/80 backdrop-blur-sm rounded-xl shadow-md border border-purple-100">
                        <Icon name="Check" size={16} className="text-purple-600" />
                        <span className="text-sm font-medium text-gray-700">anyaGPT: каждый день</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
}
