import { Card, CardContent } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

const stats = [
  {
    icon: 'Users',
    value: '50,000+',
    label: 'Учеников уже учатся'
  },
  {
    icon: 'MessageSquare',
    value: '2M+',
    label: 'Сообщений обработано'
  },
  {
    icon: 'BookOpen',
    value: '500K+',
    label: 'Слов выучено'
  },
  {
    icon: 'Star',
    value: '4.9/5',
    label: 'Средняя оценка'
  }
];

export default function StatsSection() {
  return (
    <section className="relative py-20 bg-gradient-to-br from-indigo-600 via-blue-600 to-purple-600 overflow-hidden">
      {/* Animated background pattern */}
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
              anyaGPT в цифрах
            </h2>
            <p className="text-blue-100 text-lg">
              Присоединяйся к тысячам людей, которые уже улучшили свой английский
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((stat, idx) => (
              <Card 
                key={idx} 
                className="group border-0 bg-white/10 backdrop-blur-md hover:bg-white/20 transition-all duration-300 hover:scale-105 hover:shadow-2xl"
              >
                <CardContent className="p-6 text-center">
                  <div className="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center mb-4 mx-auto group-hover:scale-110 transition-transform duration-300">
                    <Icon name={stat.icon as any} size={32} className="text-white" />
                  </div>
                  <div className="text-4xl md:text-5xl font-bold text-white mb-2">
                    {stat.value}
                  </div>
                  <p className="text-blue-100 text-sm font-medium">{stat.label}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}