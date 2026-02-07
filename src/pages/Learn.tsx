import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import Icon from '@/components/ui/icon';

interface Article {
  id: number;
  title: string;
  description: string;
  category: string;
  duration: string;
  level: 'Начинающий' | 'Средний' | 'Продвинутый';
  image: string;
}

interface Exercise {
  id: number;
  title: string;
  type: string;
  questions: number;
  completed: boolean;
}

interface Video {
  id: number;
  title: string;
  duration: string;
  views: number;
  thumbnail: string;
}

const articles: Article[] = [
  {
    id: 1,
    title: 'Основы английской грамматики',
    description: 'Изучите основы английской грамматики с практическими примерами',
    category: 'Грамматика',
    duration: '15 мин',
    level: 'Начинающий',
    image: 'https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8'
  },
  {
    id: 2,
    title: 'Деловая лексика',
    description: 'Необходимая лексика для профессионального общения',
    category: 'Словарный запас',
    duration: '20 мин',
    level: 'Средний',
    image: 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40'
  },
  {
    id: 3,
    title: 'Продвинутые навыки разговора',
    description: 'Улучшите беглость речи с помощью продвинутых техник',
    category: 'Разговорная речь',
    duration: '25 мин',
    level: 'Продвинутый',
    image: 'https://images.unsplash.com/photo-1577896851905-4356475b22e8'
  },
  {
    id: 4,
    title: 'Стратегии написания IELTS',
    description: 'Проверенные стратегии для успешной сдачи письменной части IELTS',
    category: 'Письмо',
    duration: '30 мин',
    level: 'Продвинутый',
    image: 'https://images.unsplash.com/photo-1455390582262-044cdead277a'
  }
];

const exercises: Exercise[] = [
  { id: 1, title: 'Present Simple vs Present Continuous', type: 'Грамматика', questions: 15, completed: false },
  { id: 2, title: 'Деловые идиомы', type: 'Словарный запас', questions: 20, completed: true },
  { id: 3, title: 'Понимание на слух: Подкаст', type: 'Аудирование', questions: 10, completed: false },
  { id: 4, title: 'Фразовые глаголы', type: 'Словарный запас', questions: 25, completed: false }
];

const videos: Video[] = [
  {
    id: 1,
    title: 'Как звучать естественно на английском',
    duration: '12:34',
    views: 15420,
    thumbnail: 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3'
  },
  {
    id: 2,
    title: 'Распространенные ошибки в произношении',
    duration: '8:15',
    views: 9876,
    thumbnail: 'https://images.unsplash.com/photo-1485846234645-a62644f84728'
  },
  {
    id: 3,
    title: 'Освоение английских времен',
    duration: '18:42',
    views: 23451,
    thumbnail: 'https://images.unsplash.com/photo-1434030216411-0b793f4b4173'
  }
];

export default function Learn() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLevel, setSelectedLevel] = useState<string>('all');

  const filteredArticles = articles.filter(article => {
    const matchesSearch = article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         article.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesLevel = selectedLevel === 'all' || article.level === selectedLevel;
    return matchesSearch && matchesLevel;
  });

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'Начинающий': return 'bg-green-100 text-green-800';
      case 'Средний': return 'bg-blue-100 text-blue-800';
      case 'Продвинутый': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon name="GraduationCap" size={32} className="text-primary" />
              <h1 className="text-2xl font-bold">Образовательная платформа</h1>
            </div>
            <nav className="hidden md:flex gap-6">
              <a href="/app" className="text-muted-foreground hover:text-primary transition">Дашборд</a>
              <a href="/blog" className="text-muted-foreground hover:text-primary transition">Блог</a>
              <a href="/pricing" className="text-muted-foreground hover:text-primary transition">Тарифы</a>
            </nav>
          </div>
        </div>
      </header>

      <section className="py-16 px-4">
        <div className="container mx-auto text-center max-w-4xl">
          <h2 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Развивайте навыки английского
          </h2>
          <p className="text-xl text-muted-foreground mb-8">
            Доступ к учебным материалам, интерактивным упражнениям и видео-урокам от экспертов
          </p>
          <div className="flex gap-4 max-w-2xl mx-auto">
            <div className="relative flex-1">
              <Icon name="Search" className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={20} />
              <Input
                type="text"
                placeholder="Поиск статей, упражнений, видео..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button size="lg">
              <Icon name="Filter" size={20} className="mr-2" />
              Фильтры
            </Button>
          </div>
        </div>
      </section>

      <section className="pb-20 px-4">
        <div className="container mx-auto max-w-7xl">
          <Tabs defaultValue="articles" className="w-full">
            <TabsList className="grid w-full max-w-md mx-auto grid-cols-4 mb-8">
              <TabsTrigger value="articles">
                <Icon name="BookOpen" size={18} className="mr-2" />
                Статьи
              </TabsTrigger>
              <TabsTrigger value="exercises">
                <Icon name="PenTool" size={18} className="mr-2" />
                Упражнения
              </TabsTrigger>
              <TabsTrigger value="videos">
                <Icon name="Video" size={18} className="mr-2" />
                Видео
              </TabsTrigger>
              <TabsTrigger value="blog">
                <Icon name="FileText" size={18} className="mr-2" />
                Блог
              </TabsTrigger>
            </TabsList>

            <TabsContent value="articles" className="space-y-8">
              <div className="flex gap-2 flex-wrap">
                <Button
                  variant={selectedLevel === 'all' ? 'default' : 'outline'}
                  onClick={() => setSelectedLevel('all')}
                  size="sm"
                >
                  Все уровни
                </Button>
                <Button
                  variant={selectedLevel === 'Начинающий' ? 'default' : 'outline'}
                  onClick={() => setSelectedLevel('Начинающий')}
                  size="sm"
                >
                  Начинающий
                </Button>
                <Button
                  variant={selectedLevel === 'Средний' ? 'default' : 'outline'}
                  onClick={() => setSelectedLevel('Средний')}
                  size="sm"
                >
                  Средний
                </Button>
                <Button
                  variant={selectedLevel === 'Продвинутый' ? 'default' : 'outline'}
                  onClick={() => setSelectedLevel('Продвинутый')}
                  size="sm"
                >
                  Продвинутый
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredArticles.map((article) => (
                  <Card key={article.id} className="group hover:shadow-xl transition-all duration-300 overflow-hidden">
                    <div className="relative h-48 overflow-hidden">
                      <img
                        src={article.image}
                        alt={article.title}
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                      />
                      <Badge className={`absolute top-4 right-4 ${getLevelColor(article.level)}`}>
                        {article.level}
                      </Badge>
                    </div>
                    <CardHeader>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                        <Icon name="Clock" size={16} />
                        {article.duration}
                        <span className="mx-2">•</span>
                        <Badge variant="outline">{article.category}</Badge>
                      </div>
                      <CardTitle className="text-xl group-hover:text-primary transition">
                        {article.title}
                      </CardTitle>
                      <CardDescription>{article.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button className="w-full group-hover:bg-primary/90">
                        Читать статью
                        <Icon name="ArrowRight" size={16} className="ml-2" />
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="exercises" className="space-y-4">
              {exercises.map((exercise) => (
                <Card key={exercise.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0">
                    <div className="flex-1">
                      <CardTitle className="text-lg flex items-center gap-2">
                        {exercise.title}
                        {exercise.completed && (
                          <Icon name="CheckCircle2" size={20} className="text-green-600" />
                        )}
                      </CardTitle>
                      <CardDescription className="mt-2">
                        <Badge variant="outline">{exercise.type}</Badge>
                        <span className="ml-3">{exercise.questions} вопросов</span>
                      </CardDescription>
                    </div>
                    <Button variant={exercise.completed ? 'outline' : 'default'}>
                      {exercise.completed ? (
                        <>
                          <Icon name="RotateCw" size={16} className="mr-2" />
                          Повторить
                        </>
                      ) : (
                        <>
                          <Icon name="Play" size={16} className="mr-2" />
                          Начать
                        </>
                      )}
                    </Button>
                  </CardHeader>
                </Card>
              ))}
            </TabsContent>

            <TabsContent value="videos">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {videos.map((video) => (
                  <Card key={video.id} className="group hover:shadow-xl transition-all duration-300 overflow-hidden">
                    <div className="relative h-48 overflow-hidden">
                      <img
                        src={video.thumbnail}
                        alt={video.title}
                        className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300"
                      />
                      <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="w-16 h-16 rounded-full bg-white/90 flex items-center justify-center">
                          <Icon name="Play" size={32} className="text-primary ml-1" />
                        </div>
                      </div>
                      <Badge className="absolute bottom-4 right-4 bg-black/80 text-white">
                        {video.duration}
                      </Badge>
                    </div>
                    <CardHeader>
                      <CardTitle className="text-lg group-hover:text-primary transition">
                        {video.title}
                      </CardTitle>
                      <CardDescription className="flex items-center gap-2">
                        <Icon name="Eye" size={16} />
                        {video.views.toLocaleString()} просмотров
                      </CardDescription>
                    </CardHeader>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="blog">
              <div className="text-center py-12">
                <Icon name="FileText" size={64} className="mx-auto text-muted-foreground mb-4" />
                <h3 className="text-2xl font-bold mb-2">Наш блог</h3>
                <p className="text-muted-foreground mb-6">
                  Читайте последние советы, идеи и истории от экспертов по изучению английского
                </p>
                <Button size="lg" onClick={() => window.location.href = '/blog'}>
                  Перейти в блог
                  <Icon name="ArrowRight" size={20} className="ml-2" />
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </section>

      <section className="py-16 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Готовы улучшить свой английский?</h2>
          <p className="text-xl mb-8 opacity-90">
            Присоединяйтесь к тысячам учеников, совершенствующих свои навыки каждый день
          </p>
          <Button size="lg" variant="secondary">
            Начать бесплатно
            <Icon name="ArrowRight" size={20} className="ml-2" />
          </Button>
        </div>
      </section>
    </div>
  );
}
