import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

const comparisonData = [
  {
    feature: 'Доступность',
    traditional: { text: '1-2 раза в неделю', icon: 'Clock' },
    anya: { text: '24/7 в любое время', icon: 'Zap' }
  },
  {
    feature: 'Стоимость',
    traditional: { text: 'от 1500₽ за урок', icon: 'DollarSign' },
    anya: { text: 'от 0₽ (бесплатно)', icon: 'Gift' }
  },
  {
    feature: 'Практика',
    traditional: { text: '45-60 минут в неделю', icon: 'Timer' },
    anya: { text: 'Сколько хочешь', icon: 'Infinity' }
  },
  {
    feature: 'Ошибки',
    traditional: { text: 'Могут стесняться', icon: 'Frown' },
    anya: { text: 'Никакого стеснения', icon: 'Smile' }
  },
  {
    feature: 'Темы',
    traditional: { text: 'По программе', icon: 'BookMarked' },
    anya: { text: 'Любые интересные тебе', icon: 'Sparkles' }
  },
  {
    feature: 'Прогресс',
    traditional: { text: 'Тетрадь и заметки', icon: 'FileText' },
    anya: { text: 'Автоматическая статистика', icon: 'BarChart' }
  }
];

export default function ComparisonSection() {
  return (
    <section className="container mx-auto px-4 py-20 bg-gradient-to-br from-blue-50 to-indigo-50">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            anyaGPT vs Обычный репетитор
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Мы любим репетиторов, но ИИ даёт некоторые преимущества
          </p>
        </div>

        <div className="grid gap-4">
          <div className="grid grid-cols-3 gap-4 mb-2">
            <div></div>
            <Card className="border-2 border-gray-200 bg-white">
              <CardHeader className="pb-3 pt-4">
                <CardTitle className="text-center text-lg">👨‍🏫 Репетитор</CardTitle>
              </CardHeader>
            </Card>
            <Card className="border-4 border-blue-500 bg-gradient-to-br from-blue-50 to-indigo-50">
              <CardHeader className="pb-3 pt-4">
                <CardTitle className="text-center text-lg">🤖 anyaGPT</CardTitle>
              </CardHeader>
            </Card>
          </div>

          {comparisonData.map((item, idx) => (
            <div key={idx} className="grid grid-cols-3 gap-4 items-center">
              <div className="font-bold text-gray-900 text-right pr-4">
                {item.feature}
              </div>
              <Card className="border-2 border-gray-200">
                <CardContent className="p-4 flex items-center gap-3">
                  <Icon name={item.traditional.icon as any} size={20} className="text-gray-400 flex-shrink-0" />
                  <span className="text-gray-700 text-sm">{item.traditional.text}</span>
                </CardContent>
              </Card>
              <Card className="border-2 border-blue-200 bg-gradient-to-br from-white to-blue-50">
                <CardContent className="p-4 flex items-center gap-3">
                  <Icon name={item.anya.icon as any} size={20} className="text-blue-600 flex-shrink-0" />
                  <span className="text-gray-900 font-medium text-sm">{item.anya.text}</span>
                </CardContent>
              </Card>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <Card className="inline-block border-2 border-blue-200 bg-white max-w-2xl">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <Icon name="Heart" size={32} className="text-red-500 flex-shrink-0 mt-1" />
                <div className="text-left">
                  <h4 className="font-bold text-lg mb-2">Идеально вместе!</h4>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    anyaGPT не заменяет живого репетитора, а дополняет его. Практикуйся с Аней каждый день, 
                    а с репетитором разбирай сложные темы. Так прогресс будет в разы быстрее!
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
