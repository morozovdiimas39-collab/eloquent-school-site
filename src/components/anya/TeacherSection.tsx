import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import { useNavigate } from 'react-router-dom';

const teacherFeatures = [
  {
    icon: 'Users',
    title: 'Управляй учениками',
    description: 'Видь всех своих учеников в одном месте. Отслеживай их прогресс и активность.'
  },
  {
    icon: 'BookOpen',
    title: 'Назначай слова',
    description: 'Выбирай персональные слова для каждого ученика. Аня будет включать их в диалоги.'
  },
  {
    icon: 'BarChart',
    title: 'Статистика в реальном времени',
    description: 'Смотри сколько времени ученик практикуется, какие темы даются сложнее.'
  },
  {
    icon: 'MessageSquare',
    title: 'Обратная связь',
    description: 'Получай уведомления о прогрессе учеников и их достижениях.'
  }
];

export default function TeacherSection() {
  const navigate = useNavigate();

  return (
    <section className="container mx-auto px-4 py-20 bg-gradient-to-br from-indigo-50 to-blue-50">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-100 text-blue-700 font-medium text-sm border border-blue-200 mb-6">
            <Icon name="GraduationCap" size={16} />
            <span>Для учителей</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Работай эффективнее
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Ты репетитор? anyaGPT станет твоим помощником для домашней практики
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-12">
          {teacherFeatures.map((feature, idx) => (
            <Card key={idx} className="border-2 border-blue-200 hover:shadow-xl transition-all">
              <CardContent className="p-6 flex gap-4">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-100 to-indigo-100 flex items-center justify-center flex-shrink-0">
                  <Icon name={feature.icon as any} size={28} className="text-blue-600" />
                </div>
                <div>
                  <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                  <p className="text-gray-600">{feature.description}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <Card className="border-4 border-blue-500 bg-gradient-to-br from-white to-blue-50 shadow-2xl">
          <CardContent className="p-8 md:p-12">
            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div>
                <h3 className="text-3xl font-bold mb-4">
                  Промокоды для твоих учеников
                </h3>
                <p className="text-gray-600 mb-6 leading-relaxed">
                  Создай свой промокод и дай его ученикам. Они привяжутся к тебе, 
                  и ты сможешь назначать им персональные слова для изучения, видеть их прогресс 
                  и получать 30% от их подписок.
                </p>
                <div className="space-y-3 mb-6">
                  <div className="flex items-center gap-3">
                    <Icon name="Check" size={20} className="text-green-600" />
                    <span className="text-gray-700">Бесплатно для всех репетиторов</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Icon name="Check" size={20} className="text-green-600" />
                    <span className="text-gray-700">Получай 30% от подписок учеников</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Icon name="Check" size={20} className="text-green-600" />
                    <span className="text-gray-700">Персональный кабинет учителя</span>
                  </div>
                </div>
                <Button
                  onClick={() => navigate('/app')}
                  size="lg"
                  className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 font-semibold text-lg h-14 px-8 shadow-xl"
                >
                  Стать учителем
                  <Icon name="ArrowRight" size={20} className="ml-2" />
                </Button>
              </div>

              <div className="relative">
                <Card className="bg-white border-2 border-blue-200 shadow-lg">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center">
                        <Icon name="GraduationCap" size={24} className="text-white" />
                      </div>
                      <div>
                        <h4 className="font-bold">Мария Иванова</h4>
                        <p className="text-sm text-gray-600">Репетитор английского</p>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                        <span className="font-medium">Промокод:</span>
                        <code className="bg-white px-3 py-1 rounded border border-blue-200 font-mono text-blue-600">
                          MARIA2024
                        </code>
                      </div>
                      <div className="grid grid-cols-3 gap-3">
                        <div className="text-center p-3 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg">
                          <div className="text-2xl font-bold text-blue-600">24</div>
                          <div className="text-xs text-gray-600">Учеников</div>
                        </div>
                        <div className="text-center p-3 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg">
                          <div className="text-2xl font-bold text-blue-600">89%</div>
                          <div className="text-xs text-gray-600">Активность</div>
                        </div>
                        <div className="text-center p-3 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg">
                          <div className="text-2xl font-bold text-blue-600">3.6K</div>
                          <div className="text-xs text-gray-600">Слов выучено</div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}