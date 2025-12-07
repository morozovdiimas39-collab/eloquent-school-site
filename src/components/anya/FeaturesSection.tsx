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
    <section id="features" className="container mx-auto px-4 py-20 bg-white">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Почему anyaGPT — это круто
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Мы объединили лучшее от репетитора и современных технологий
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, idx) => (
            <Card key={idx} className="border-2 hover:border-blue-200 transition-all hover:shadow-xl">
              <CardContent className="p-6">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-100 to-indigo-100 flex items-center justify-center mb-4">
                  <Icon name={feature.icon as any} size={28} className="text-blue-600" />
                </div>
                <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}