import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

const levels = [
  {
    level: 'A1-A2',
    title: 'Начинающий',
    description: 'Только начинаешь учить английский',
    features: [
      'Простые фразы и базовые слова',
      'Медленная речь с переводами',
      'Много примеров и объяснений',
      'Поддержка на русском'
    ],
    icon: 'Sprout',
    color: 'green'
  },
  {
    level: 'B1-B2',
    title: 'Средний',
    description: 'Знаешь основы, хочешь говорить свободнее',
    features: [
      'Разговоры на повседневные темы',
      'Исправление частых ошибок',
      'Расширение словарного запаса',
      'Практика грамматики в контексте'
    ],
    icon: 'Flame',
    color: 'orange'
  },
  {
    level: 'C1-C2',
    title: 'Продвинутый',
    description: 'Говоришь хорошо, нужна практика',
    features: [
      'Сложные темы и дискуссии',
      'Идиомы и разговорные выражения',
      'Нюансы и оттенки значений',
      'Подготовка к экзаменам'
    ],
    icon: 'Trophy',
    color: 'blue'
  }
];

export default function LevelSection() {
  const getColorClasses = (color: string) => {
    const colors = {
      green: {
        bg: 'from-green-100 to-emerald-100',
        icon: 'text-green-600',
        border: 'border-green-200'
      },
      orange: {
        bg: 'from-orange-100 to-amber-100',
        icon: 'text-orange-600',
        border: 'border-orange-200'
      },
      blue: {
        bg: 'from-blue-100 to-indigo-100',
        icon: 'text-blue-600',
        border: 'border-blue-200'
      }
    };
    return colors[color as keyof typeof colors];
  };

  return (
    <section className="container mx-auto px-4 py-20 bg-white">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Аня для любого уровня
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            От первых слов до свободного общения — Аня подстраивается под твой уровень
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {levels.map((level, idx) => {
            const colors = getColorClasses(level.color);
            return (
              <Card key={idx} className={`border-2 ${colors.border} hover:shadow-xl transition-all`}>
                <CardHeader className="pb-4">
                  <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${colors.bg} flex items-center justify-center mb-4`}>
                    <Icon name={level.icon as any} size={32} className={colors.icon} />
                  </div>
                  <div className="text-sm font-bold text-gray-500 mb-1">{level.level}</div>
                  <CardTitle className="text-2xl font-bold mb-2">{level.title}</CardTitle>
                  <p className="text-gray-600 text-sm">{level.description}</p>
                </CardHeader>
                <CardContent className="space-y-3">
                  {level.features.map((feature, featureIdx) => (
                    <div key={featureIdx} className="flex items-start gap-2">
                      <Icon name="Check" size={18} className={`${colors.icon} flex-shrink-0 mt-0.5`} />
                      <span className="text-gray-700 text-sm">{feature}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="mt-12 text-center">
          <Card className="inline-block border-2 border-blue-200 bg-gradient-to-br from-blue-50 to-white max-w-2xl">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <Icon name="Lightbulb" size={32} className="text-blue-600 flex-shrink-0 mt-1" />
                <div className="text-left">
                  <h4 className="font-bold text-lg mb-2">Не знаешь свой уровень?</h4>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    Не переживай! При первом запуске Аня задаст тебе несколько вопросов и сама определит 
                    твой уровень. Потом будет постепенно усложнять задания по мере твоего прогресса.
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
