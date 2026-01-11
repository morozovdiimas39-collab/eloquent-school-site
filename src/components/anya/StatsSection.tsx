import { Card, CardContent } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { Button } from '@/components/ui/button';

const benefits = [
  {
    icon: 'Zap',
    title: 'Быстрый старт',
    description: 'Начни практиковать английский прямо сейчас — без регистрации и сложных настроек'
  },
  {
    icon: 'Clock',
    title: 'Гибкий график',
    description: 'Занимайся когда удобно — утром, днём или поздно вечером'
  },
  {
    icon: 'Target',
    title: 'Персональный подход',
    description: 'Аня подстраивается под твой уровень и помогает именно там, где нужно'
  },
  {
    icon: 'TrendingUp',
    title: 'Видимый прогресс',
    description: 'Отслеживай свои достижения и видь, как растёт твой словарный запас'
  }
];

export default function StatsSection() {
  return (
    <section className="relative py-20 bg-gradient-to-br from-indigo-600 via-blue-600 to-purple-600 overflow-hidden">
      <div className="absolute inset-0 opacity-10">
        <div className="absolute top-0 left-0 w-full h-full">
          <div className="absolute top-10 left-20 w-40 h-40 bg-white rounded-full filter blur-3xl animate-blob"></div>
          <div className="absolute top-40 right-20 w-40 h-40 bg-white rounded-full filter blur-3xl animate-blob animation-delay-2000"></div>
          <div className="absolute bottom-10 left-1/2 w-40 h-40 bg-white rounded-full filter blur-3xl animate-blob animation-delay-4000"></div>
        </div>
      </div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-3">
              Почему выбирают anyaGPT
            </h2>
            <p className="text-blue-100 text-lg">
              Учи английский в удобном темпе с помощью ИИ-репетитора
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {benefits.map((benefit, idx) => (
              <Card 
                key={idx} 
                className="group border-0 bg-white/10 backdrop-blur-md hover:bg-white/20 transition-all duration-300 hover:scale-105 hover:shadow-2xl"
              >
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="w-14 h-14 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform duration-300">
                      <Icon name={benefit.icon as any} size={28} className="text-white" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white mb-2">
                        {benefit.title}
                      </h3>
                      <p className="text-blue-100 leading-relaxed">
                        {benefit.description}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <div className="text-center">
            <Button
              onClick={() => window.open('https://t.me/eloquent_school_bot', '_blank')}
              size="lg"
              className="bg-white text-indigo-600 hover:bg-blue-50 font-bold text-lg px-8 py-6 shadow-2xl"
            >
              Начать бесплатно
              <Icon name="ArrowRight" size={20} className="ml-2" />
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}