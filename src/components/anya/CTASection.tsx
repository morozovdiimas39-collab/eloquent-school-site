import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { useNavigate } from 'react-router-dom';

export default function CTASection() {
  const navigate = useNavigate();

  return (
    <section className="container mx-auto px-4 py-20 bg-white">
      <div className="max-w-5xl mx-auto">
        <Card className="border-4 border-blue-500 bg-gradient-to-br from-blue-600 to-indigo-700 shadow-2xl overflow-hidden">
          <CardContent className="p-12 md:p-16 text-center text-white">
            <div className="max-w-3xl mx-auto space-y-8">
              <div className="w-20 h-20 rounded-full bg-white/20 flex items-center justify-center mx-auto backdrop-blur-sm">
                <Icon name="Rocket" size={40} className="text-white" />
              </div>

              <h2 className="text-4xl md:text-6xl font-bold leading-tight">
                Начни говорить на английском уже сегодня
              </h2>

              <p className="text-xl md:text-2xl text-blue-100 leading-relaxed">
                Больше 50,000 человек уже учат английский с Аней. 
                Присоединяйся к ним и получи первые 20 сообщений бесплатно!
              </p>

              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
                <Button
                  onClick={() => navigate('/app')}
                  size="lg"
                  className="bg-white text-blue-600 hover:bg-blue-50 font-bold text-xl h-16 px-10 shadow-2xl"
                >
                  Попробовать бесплатно
                  <Icon name="ArrowRight" size={24} className="ml-3" />
                </Button>
                <Button
                  onClick={() => navigate('/pricing')}
                  size="lg"
                  variant="outline"
                  className="border-2 border-white text-white hover:bg-white/10 font-bold text-xl h-16 px-10"
                >
                  Смотреть тарифы
                </Button>
              </div>

              <div className="flex flex-wrap items-center justify-center gap-8 pt-8 text-blue-100">
                <div className="flex items-center gap-2">
                  <Icon name="Check" size={20} />
                  <span>Без регистрации</span>
                </div>
                <div className="flex items-center gap-2">
                  <Icon name="Check" size={20} />
                  <span>Без банковской карты</span>
                </div>
                <div className="flex items-center gap-2">
                  <Icon name="Check" size={20} />
                  <span>Начни за 30 секунд</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid md:grid-cols-3 gap-6 mt-12">
          <Card className="border-2 border-blue-100">
            <CardContent className="p-6 text-center">
              <Icon name="Shield" size={32} className="text-blue-600 mx-auto mb-3" />
              <h4 className="font-bold mb-2">Безопасно</h4>
              <p className="text-gray-600 text-sm">
                Твои данные защищены. Мы не храним личную информацию.
              </p>
            </CardContent>
          </Card>

          <Card className="border-2 border-blue-100">
            <CardContent className="p-6 text-center">
              <Icon name="Clock" size={32} className="text-blue-600 mx-auto mb-3" />
              <h4 className="font-bold mb-2">Быстрый старт</h4>
              <p className="text-gray-600 text-sm">
                Открой бота и начни практику за 30 секунд.
              </p>
            </CardContent>
          </Card>

          <Card className="border-2 border-blue-100">
            <CardContent className="p-6 text-center">
              <Icon name="Heart" size={32} className="text-blue-600 mx-auto mb-3" />
              <h4 className="font-bold mb-2">Без обязательств</h4>
              <p className="text-gray-600 text-sm">
                Попробуй бесплатно. Отмени в любой момент.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}
