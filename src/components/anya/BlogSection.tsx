import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import { useNavigate } from 'react-router-dom';
import funcUrls from '../../../backend/func2url.json';

const API_URL = funcUrls['webapp-api'];

export interface BlogPost {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  content: string;
  cover_image: string;
  author: string;
  published: boolean;
  views_count: number;
  reading_time: number;
  created_at: string;
  updated_at: string;
}

// Удалено: статичные данные заменены на загрузку из API
const oldBlogPosts: BlogPost[] = [
  {
    id: '1',
    title: '5 ошибок, которые делают все при изучении английского',
    excerpt: 'Разбираем самые частые ошибки новичков и как их избежать. Спойлер: дело не в грамматике.',
    content: `Многие начинают учить английский с грамматики, но это не самый эффективный путь. Вот 5 ошибок, которые мешают прогрессу:

**1. Зубрёжка без практики**
Заучивание слов списками не работает. Мозг запоминает слова только в контексте реальных ситуаций. Вместо этого — используй новые слова в диалогах сразу же.

**2. Страх ошибок**
Многие боятся говорить, пока не выучат всю грамматику. Но язык — это не экзамен, это инструмент общения. Ошибки — это нормально и необходимо для прогресса.

**3. Фокус только на грамматике**
Правила важны, но без живой практики они бесполезны. Язык нужно использовать, а не изучать теоретически.

**4. Нерегулярные занятия**
15 минут каждый день лучше, чем 2 часа раз в неделю. Мозгу нужна регулярность, чтобы формировать навык.

**5. Игнорирование аудирования**
Чтение и письмо — это половина дела. Без понимания на слух реальный английский будет недоступен.

**Что делать?**
- Практикуй язык ежедневно в живых диалогах
- Не бойся ошибаться — это часть процесса
- Используй новые слова сразу в разговоре
- Слушай английскую речь каждый день

anyaGPT помогает избежать этих ошибок: ты практикуешь язык в диалогах, получаешь мгновенные исправления и учишь слова в контексте. Без страха и давления.`,
    image: 'https://cdn.poehali.dev/projects/b7f7b2d5-b36c-4ecd-924a-51eec76a70ee/files/76b97d35-f634-41b9-b662-459c657672c8.jpg',
    date: '5 декабря 2024',
    readTime: '5 мин',
    category: 'Обучение',
    categoryColor: 'from-blue-500 to-indigo-600'
  },
  {
    id: '2',
    title: 'Как AI-репетитор может заменить реального преподавателя',
    excerpt: 'Технологии меняют образование. Узнай, чем ИИ-репетитор лучше обычного и где он проигрывает.',
    content: `Искусственный интеллект в образовании — это не фантастика, а реальность. Но может ли AI полностью заменить живого репетитора?

**Преимущества AI-репетитора:**

**1. Доступность 24/7**
В отличие от реального преподавателя, AI доступен в любое время. Захотел практиковать в 2 часа ночи? Без проблем.

**2. Персонализация**
AI адаптируется под твой уровень мгновенно. Запоминает твои ошибки и слабые места, чтобы работать над ними.

**3. Цена**
AI-репетитор стоит в разы дешевле, чем частные уроки. При этом можешь заниматься сколько угодно.

**4. Без стеснения**
Многие стесняются говорить с реальным человеком. С AI можно делать любые ошибки без страха осуждения.

**5. Мгновенная обратная связь**
AI исправляет ошибки сразу, не дожидаясь конца урока.

**Где AI проигрывает:**

**1. Эмоциональная связь**
Реальный преподаватель может мотивировать, поддержать, найти индивидуальный подход на эмоциональном уровне.

**2. Сложные темы**
Некоторые грамматические нюансы лучше объясняет человек, который сам проходил через это обучение.

**3. Культурный контекст**
Живой носитель языка может рассказать о тонкостях культуры и сленга.

**Идеальная формула:**
AI-репетитор + живой преподаватель = максимальный результат.

Используй AI для ежедневной практики и закрепления, а к реальному репетитору ходи для разбора сложных тем и мотивации.`,
    image: 'https://cdn.poehali.dev/projects/b7f7b2d5-b36c-4ecd-924a-51eec76a70ee/files/ef77a661-65be-4ce2-8212-866da3225e94.jpg',
    date: '3 декабря 2024',
    readTime: '7 мин',
    category: 'Технологии',
    categoryColor: 'from-purple-500 to-pink-600'
  },
  {
    id: '3',
    title: 'Почему Telegram — идеальная платформа для изучения языков',
    excerpt: 'Разбираемся, почему мессенджер удобнее, чем специальные приложения для языков.',
    content: `Существуют сотни приложений для изучения английского. Но почему anyaGPT работает в Telegram, а не как отдельное приложение?

**1. Ты уже там**
Telegram у тебя уже установлен и открыт весь день. Не нужно скачивать новое приложение, регистрироваться и привыкать к новому интерфейсу.

**2. Меньше отвлечений**
В отдельных приложениях куча рекламы, геймификации, уведомлений. В Telegram — просто чат с репетитором.

**3. Естественное общение**
Ты привык общаться в мессенджерах. Это самый естественный способ практиковать язык — как будто переписываешься с другом.

**4. Мгновенные уведомления**
Telegram-уведомления работают лучше всех. Ты никогда не пропустишь напоминание о практике.

**5. Кроссплатформенность**
Начал на телефоне, продолжил на компьютере. Вся история синхронизирована автоматически.

**6. Голосовые сообщения**
Можешь практиковать произношение через голосовые — это проще и естественнее, чем в специальных приложениях.

**7. Приватность**
Telegram известен защитой данных. Твои диалоги и прогресс в безопасности.

**8. Скорость**
Telegram — один из самых быстрых мессенджеров. Сообщения приходят мгновенно, даже при плохом интернете.

**Итог:**
Не нужно изобретать велосипед. Используй инструменты, которые уже работают и привычны. Telegram + AI = идеальная комбинация для изучения языков.

anyaGPT интегрируется в твою повседневную жизнь, а не отвлекает от неё.`,
    image: 'https://cdn.poehali.dev/projects/b7f7b2d5-b36c-4ecd-924a-51eec76a70ee/files/5591be92-d8e5-4da4-9a21-54b51113dfd7.jpg',
    date: '1 декабря 2024',
    readTime: '6 мин',
    category: 'Платформы',
    categoryColor: 'from-green-500 to-teal-600'
  },
  {
    id: '4',
    title: 'Как выучить 1000 слов за месяц: проверенная методика',
    excerpt: 'Пошаговый план, который реально работает. Без зубрёжки и скучных списков.',
    content: `1000 слов в месяц — это реально? Да, если использовать правильную методику.

**Неправильный подход:**
Открыть список "1000 самых важных слов" и учить по 35 слов в день. Через неделю забудешь все.

**Правильный подход:**

**1. Интервальные повторения (10 мин/день)**
Учи 10 новых слов в день, но повторяй старые по системе: через 1 день, 3 дня, 7 дней, 14 дней, 30 дней.

**2. Контекст, а не перевод**
Не учи "apple — яблоко". Учи "I ate a red apple yesterday" — "Я съел красное яблоко вчера". Мозг запоминает истории, а не слова.

**3. Используй сразу**
Выучил слово "gorgeous"? Составь 3 предложения с ним прямо сейчас. Используй в разговоре сегодня же.

**4. Визуализация**
Представь картинку к каждому слову. "Thunder" — вспомни звук грома и молнию. Образы запоминаются лучше текста.

**5. Группировка по темам**
Не учи случайные слова. Неделя — тема "Путешествия", следующая — "Еда", потом "Эмоции". Так мозгу легче.

**6. Практика в диалогах**
Самое важное: используй новые слова в реальных диалогах. anyaGPT автоматически включает твои слова в разговоры.

**План на месяц:**
- День 1-7: 10 слов/день + повторения = 70 новых слов
- День 8-14: ещё 70 слов + повторения предыдущих
- День 15-21: ещё 70 слов + повторения
- День 22-30: ещё 90 слов + повторения

Итого: 300 новых слов выучено, 700+ повторений. Реальное запоминание — 80-90%.

**Секрет:**
Регулярность важнее количества. Лучше 10 слов каждый день, чем 100 раз в неделю.`,
    image: 'https://cdn.poehali.dev/projects/b7f7b2d5-b36c-4ecd-924a-51eec76a70ee/files/2680f0d0-4cf4-41e7-a970-ab6da0db3137.jpg',
    date: '28 ноября 2024',
    readTime: '8 мин',
    category: 'Методики',
    categoryColor: 'from-orange-500 to-red-600'
  },
  {
    id: '5',
    title: 'B1 → B2 за 3 месяца: реальная история ученика',
    excerpt: 'Интервью с Максимом, который перешёл с B1 на B2 за 90 дней практики с anyaGPT.',
    content: `Максим, 27 лет, программист из Москвы. Три месяца назад его английский был B1, сейчас — уверенный B2.

**До anyaGPT:**
"Я читал техническую документацию без проблем, но разговорный английский был слабым. На собеседованиях в зарубежные компании терялся и не мог связать двух слов."

**Что делал:**
"Каждый день 20-30 минут общался с Аней. Утром в метро, днём в обед, вечером перед сном. Говорили обо всём: о работе, хобби, новостях."

**Первые результаты (2 недели):**
"Начал думать на английском. Раньше я переводил фразы с русского, а теперь они просто приходят в голову сразу на английском."

**Через месяц:**
"Словарный запас вырос с 2000 до 3500 слов. Аня автоматически добавляла новые слова в мой личный словарь и включала их в диалоги."

**Через 2 месяца:**
"Прошёл пробное собеседование на английском в американскую компанию. Первый раз не потерялся! Говорил уверенно, хотя и делал ошибки."

**Через 3 месяца:**
"Сдал тест на уровень — B2! Получил оффер от компании в Берлине. Без anyaGPT это заняло бы минимум год с обычным репетитором."

**Секрет успеха:**
"Регулярность. Я не пропускал ни одного дня. Даже 10 минут в день лучше, чем ничего. И Аня не давала расслабиться — всегда исправляла ошибки и заставляла думать."

**Сколько потратил:**
"Подписка 990₽/мес × 3 = 2970₽. Обычный репетитор — 1500₽/час × 12 часов = 18000₽/месяц. Сэкономил больше 50 000₽!"

**Совет новичкам:**
"Не ждите идеального момента. Начните сегодня. Занимайтесь каждый день. Результат будет, даже если вы в это не верите."`,
    image: 'https://cdn.poehali.dev/projects/b7f7b2d5-b36c-4ecd-924a-51eec76a70ee/files/934a5f47-b916-4215-9c60-8f8797613777.jpg',
    date: '25 ноября 2024',
    readTime: '6 мин',
    category: 'Истории',
    categoryColor: 'from-cyan-500 to-blue-600'
  },
  {
    id: '6',
    title: 'Английский для IT: что нужно знать программисту',
    excerpt: 'Специфика английского в IT-сфере. Как быстро прокачать технический английский для работы.',
    content: `Технический английский — это отдельный навык. Даже с хорошим общим уровнем можно теряться на созвонах с командой.

**Что отличает технический английский:**

**1. Специфичная лексика**
Deploy, merge, commit, pull request, refactoring — эти слова не встретишь в обычном учебнике.

**2. Сокращения и сленг**
ASAP, FYI, IMO, WIP, EOD — нужно не просто знать, но и использовать естественно.

**3. Презентация идей**
Уметь объяснить техническое решение простыми словами — ключевой навык для работы в международной команде.

**Топ-50 фраз для IT:**
- "Let's jump on a call" — Давайте созвонимся
- "Can you share your screen?" — Можешь показать экран?
- "I'll push the changes" — Я загружу изменения
- "This bug is critical" — Этот баг критичный
- "Let's schedule a meeting" — Давайте назначим встречу

**Как прокачать технический английский:**

**1. Читай документацию вслух**
Не просто читай GitHub issues, а проговаривай их. Так тренируешь произношение терминов.

**2. Смотри доклады с конференций**
YouTube полон докладов с конференций Google I/O, AWS Summit. Включай субтитры и повторяй за спикерами.

**3. Практикуй ежедневно**
anyaGPT знает IT-терминологию. Можешь обсуждать с Аней свой код, задачи, технологии.

**4. Участвуй в Open Source**
Комментарии в PR на английском — отличная практика письменного технического английского.

**5. Слушай подкасты**
Software Engineering Daily, Syntax.fm — для привыкания к технической речи.

**Частые ошибки:**

❌ "I will do deploy" → ✅ "I will deploy"
❌ "We need refactor this code" → ✅ "We need to refactor this code"
❌ "Let's make meeting" → ✅ "Let's schedule a meeting"

**Итог:**
Технический английский учится быстрее общего, если ты уже работаешь в IT. Просто начни использовать его в работе каждый день.`,
    image: 'https://cdn.poehali.dev/projects/b7f7b2d5-b36c-4ecd-924a-51eec76a70ee/files/672f8c61-0c64-487e-aeb4-e8e9a9d49d92.jpg',
    date: '22 ноября 2024',
    readTime: '7 мин',
    category: 'IT & Tech',
    categoryColor: 'from-violet-500 to-purple-600'
  }
];

interface BlogSectionProps {
  showAll?: boolean;
}

export default function BlogSection({ showAll = false }: BlogSectionProps) {
  const navigate = useNavigate();
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPosts();
  }, []);

  const loadPosts = async () => {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'get_blog_posts', published_only: true })
      });

      const data = await response.json();
      if (data.success) {
        setPosts(data.posts);
      }
    } catch (error) {
      console.error('Error loading blog posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const displayPosts = showAll ? posts : posts.slice(0, 3);

  const handleReadMore = (slug: string) => {
    navigate(`/blog/${slug}`);
  };

  if (loading) {
    return (
      <section className="relative py-20">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="relative py-20 overflow-hidden bg-gradient-to-b from-white via-purple-50/30 to-white">
      <div className="absolute top-0 right-0 w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <div className="inline-block mb-4">
              <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 backdrop-blur-sm text-purple-700 font-medium text-sm border border-purple-200 shadow-lg">
                <Icon name="BookOpen" size={16} />
                Блог
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-gray-900 to-purple-600 bg-clip-text text-transparent">
              Полезное об английском
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Советы, лайфхаки и истории успеха от пользователей anyaGPT
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-12">
            {displayPosts.map((post) => (
              <Card 
                key={post.id}
                className="group overflow-hidden border-2 border-gray-200 hover:border-purple-400 transition-all duration-300 hover:shadow-2xl hover:-translate-y-2 bg-white cursor-pointer"
                onClick={() => handleReadMore(post.slug)}
              >
                {post.cover_image && (
                  <div className="relative h-48 overflow-hidden">
                    <img 
                      src={post.cover_image} 
                      alt={post.title}
                      className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                    />
                    <div className="absolute top-4 right-4">
                      <Badge className="bg-white/90 text-gray-900 backdrop-blur-sm">
                        <Icon name="Clock" size={12} className="mr-1" />
                        {post.reading_time} мин
                      </Badge>
                    </div>
                  </div>
                )}
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 text-sm text-gray-500 mb-3">
                    <div className="flex items-center gap-1">
                      <Icon name="Calendar" size={14} />
                      {new Date(post.created_at).toLocaleDateString('ru-RU', {
                        day: 'numeric',
                        month: 'long',
                        year: 'numeric'
                      })}
                    </div>
                    <div className="flex items-center gap-1">
                      <Icon name="Eye" size={14} />
                      {post.views_count}
                    </div>
                  </div>
                  <h3 className="text-xl font-bold mb-3 text-gray-900 group-hover:text-purple-600 transition-colors line-clamp-2">
                    {post.title}
                  </h3>
                  <p className="text-gray-600 mb-4 line-clamp-3">
                    {post.excerpt}
                  </p>
                  <Button 
                    variant="ghost" 
                    className="text-purple-600 hover:text-purple-700 hover:bg-purple-50 font-semibold p-0 h-auto"
                  >
                    Читать далее
                    <Icon name="ArrowRight" size={16} className="ml-2 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>

          {!showAll && (
            <div className="text-center">
              <Button
                onClick={() => navigate('/blog')}
                size="lg"
                variant="outline"
                className="font-semibold text-lg h-14 px-8 border-2 border-purple-600 text-purple-600 hover:bg-purple-600 hover:text-white transition-all hover:scale-105 shadow-lg"
              >
                Все статьи блога
                <Icon name="ArrowRight" size={20} className="ml-2" />
              </Button>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}