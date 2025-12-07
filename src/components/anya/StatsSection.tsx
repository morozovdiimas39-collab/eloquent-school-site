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
    <section className="container mx-auto px-4 py-16 bg-white">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map((stat, idx) => (
            <Card key={idx} className="border-2 border-blue-100 hover:border-blue-300 transition-all hover:shadow-xl">
              <CardContent className="p-6 text-center">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-100 to-indigo-100 flex items-center justify-center mb-4 mx-auto">
                  <Icon name={stat.icon as any} size={28} className="text-blue-600" />
                </div>
                <div className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-2">
                  {stat.value}
                </div>
                <p className="text-gray-600 text-sm">{stat.label}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
