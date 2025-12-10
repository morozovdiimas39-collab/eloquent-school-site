import { Card, CardContent } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

const features = [
  {
    icon: 'MessageCircle',
    title: 'Живые диалоги',
    description: 'Общайся с Аней на любые темы — от хобби до путешествий. Никаких шаблонных фраз, только живое общение.'
  },
  {
    icon: 'BookOpen',
    title: 'Умные исправления',
    description: 'Аня видит твои ошибки и объясняет, как правильно. Но делает это тактично, не перебивая беседу.'
  },
  {
    icon: 'Brain',
    title: 'Персональный словарь',
    description: 'Все новые слова автоматически сохраняются. Повторяй их в упражнениях и запоминай навсегда.'
  },
  {
    icon: 'Target',
    title: 'Твой уровень',
    description: 'Аня подстраивается под твой уровень — от A1 до C2. Говорит понятно, но помогает расти.'
  },
  {
    icon: 'Zap',
    title: 'Мгновенные ответы',
    description: 'Не нужно ждать репетитора. Аня отвечает сразу, в любое время дня и ночи.'
  },
  {
    icon: 'TrendingUp',
    title: 'Прогресс виден',
    description: 'Смотри статистику: сколько слов выучил, как улучшился твой английский за неделю.'
  }
];

export default function FeaturesSection() {
  return (
    <section id="features" className="relative py-20 bg-gradient-to-b from-white via-blue-50/30 to-white overflow-hidden">
      {/* Decorative elements */}
      <div className="absolute top-0 left-0 w-full h-full opacity-40">
        <div className="absolute top-20 right-20 w-64 h-64 bg-blue-200 rounded-full filter blur-3xl"></div>
        <div className="absolute bottom-20 left-20 w-64 h-64 bg-indigo-200 rounded-full filter blur-3xl"></div>
      </div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <div className="inline-block mb-4">
              <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-100 text-blue-700 font-medium text-sm border border-blue-200">
                <Icon name="Sparkles" size={16} />
                Возможности
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
              Почему anyaGPT — это круто
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Мы объединили лучшее от репетитора и современных технологий
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, idx) => (
              <Card 
                key={idx} 
                className="group border-2 border-gray-200 hover:border-blue-400 transition-all duration-300 hover:shadow-2xl hover:-translate-y-1 bg-white/80 backdrop-blur-sm"
              >
                <CardContent className="p-6">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300 shadow-lg">
                    <Icon name={feature.icon as any} size={28} className="text-white" />
                  </div>
                  <h3 className="text-xl font-bold mb-2 text-gray-900 group-hover:text-blue-600 transition-colors">{feature.title}</h3>
                  <p className="text-gray-600 leading-relaxed">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}