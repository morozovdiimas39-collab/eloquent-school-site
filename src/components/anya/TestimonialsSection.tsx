import { Card, CardContent } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

const testimonials = [
  {
    name: 'Алексей',
    role: 'Студент, уровень B1',
    avatar: '👨‍💼',
    text: 'Раньше стеснялся говорить с людьми на английском. С Аней практикуюсь каждый день без стресса. За 3 месяца уверенность выросла в разы!',
    rating: 5
  },
  {
    name: 'Мария',
    role: 'Школьница, уровень A2',
    avatar: '👧',
    text: 'Аня объясняет грамматику понятнее, чем учебник! Теперь оценки по английскому улучшились. Мама довольна 😊',
    rating: 5
  },
  {
    name: 'Дмитрий',
    role: 'Программист, уровень B2',
    avatar: '👨‍💻',
    text: 'Нужно было подтянуть английский для работы. anyaGPT помог быстро освоить техническую лексику. Очень удобно заниматься в метро.',
    rating: 5
  },
  {
    name: 'Елена',
    role: 'Репетитор английского',
    avatar: '👩‍🏫',
    text: 'Рекомендую своим ученикам для домашней практики. Вижу их прогресс в реальном времени. Отличное дополнение к урокам!',
    rating: 5
  },
  {
    name: 'Игорь',
    role: 'Менеджер, уровень C1',
    avatar: '🧑‍💼',
    text: 'Готовлюсь к IELTS. Аня помогает с speaking practice каждый день. Уже чувствую, что стал говорить быстрее и увереннее.',
    rating: 5
  },
  {
    name: 'Анна',
    role: 'Дизайнер, уровень A1',
    avatar: '👩‍🎨',
    text: 'Только начала учить английский. Аня терпеливая и всё объясняет простыми словами. Не стыдно делать ошибки!',
    rating: 5
  }
];

export default function TestimonialsSection() {
  return (
    <section className="container mx-auto px-4 py-20 bg-white">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Что говорят ученики
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Больше 50,000 человек уже учат английский с anyaGPT
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {testimonials.map((testimonial, idx) => (
            <Card key={idx} className="border-2 border-blue-100 hover:border-blue-300 hover:shadow-xl transition-all">
              <CardContent className="p-6">
                <div className="flex items-start gap-3 mb-4">
                  <div className="text-4xl">{testimonial.avatar}</div>
                  <div className="flex-1">
                    <h4 className="font-bold text-lg">{testimonial.name}</h4>
                    <p className="text-sm text-gray-600">{testimonial.role}</p>
                  </div>
                </div>
                
                <div className="flex gap-1 mb-3">
                  {Array.from({ length: testimonial.rating }).map((_, i) => (
                    <Icon key={i} name="Star" size={16} className="text-yellow-500 fill-yellow-500" />
                  ))}
                </div>

                <p className="text-gray-700 leading-relaxed">
                  "{testimonial.text}"
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mt-12 text-center">
          <Card className="inline-block border-2 border-green-200 bg-gradient-to-br from-green-50 to-emerald-50 max-w-2xl">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <Icon name="MessageSquare" size={32} className="text-green-600 flex-shrink-0 mt-1" />
                <div className="text-left">
                  <h4 className="font-bold text-lg mb-2">Поделись своим опытом</h4>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    Уже пользуешься anyaGPT? Мы будем рады услышать твой отзыв! 
                    Напиши нам в Telegram — лучшие отзывы попадут на эту страницу.
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
