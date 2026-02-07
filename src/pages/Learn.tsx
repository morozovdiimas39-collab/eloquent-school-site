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
  level: 'Beginner' | 'Intermediate' | 'Advanced';
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
    title: 'English Grammar Basics',
    description: 'Master the fundamentals of English grammar with practical examples',
    category: 'Grammar',
    duration: '15 min',
    level: 'Beginner',
    image: 'https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8'
  },
  {
    id: 2,
    title: 'Business English Vocabulary',
    description: 'Essential vocabulary for professional communication',
    category: 'Vocabulary',
    duration: '20 min',
    level: 'Intermediate',
    image: 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40'
  },
  {
    id: 3,
    title: 'Advanced Conversation Skills',
    description: 'Improve your speaking fluency with advanced techniques',
    category: 'Speaking',
    duration: '25 min',
    level: 'Advanced',
    image: 'https://images.unsplash.com/photo-1577896851905-4356475b22e8'
  },
  {
    id: 4,
    title: 'IELTS Writing Strategies',
    description: 'Proven strategies to ace your IELTS writing exam',
    category: 'Writing',
    duration: '30 min',
    level: 'Advanced',
    image: 'https://images.unsplash.com/photo-1455390582262-044cdead277a'
  }
];

const exercises: Exercise[] = [
  { id: 1, title: 'Present Simple vs Present Continuous', type: 'Grammar', questions: 15, completed: false },
  { id: 2, title: 'Business Idioms Quiz', type: 'Vocabulary', questions: 20, completed: true },
  { id: 3, title: 'Listening Comprehension: Podcast', type: 'Listening', questions: 10, completed: false },
  { id: 4, title: 'Phrasal Verbs Practice', type: 'Vocabulary', questions: 25, completed: false }
];

const videos: Video[] = [
  {
    id: 1,
    title: 'How to Sound More Natural in English',
    duration: '12:34',
    views: 15420,
    thumbnail: 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3'
  },
  {
    id: 2,
    title: 'Common Mistakes in English Pronunciation',
    duration: '8:15',
    views: 9876,
    thumbnail: 'https://images.unsplash.com/photo-1485846234645-a62644f84728'
  },
  {
    id: 3,
    title: 'Mastering English Tenses',
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
      case 'Beginner': return 'bg-green-100 text-green-800';
      case 'Intermediate': return 'bg-blue-100 text-blue-800';
      case 'Advanced': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon name="GraduationCap" size={32} className="text-primary" />
              <h1 className="text-2xl font-bold">Learning Hub</h1>
            </div>
            <nav className="hidden md:flex gap-6">
              <a href="/app" className="text-muted-foreground hover:text-primary transition">Dashboard</a>
              <a href="/blog" className="text-muted-foreground hover:text-primary transition">Blog</a>
              <a href="/pricing" className="text-muted-foreground hover:text-primary transition">Pricing</a>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-16 px-4">
        <div className="container mx-auto text-center max-w-4xl">
          <h2 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Expand Your English Skills
          </h2>
          <p className="text-xl text-muted-foreground mb-8">
            Access comprehensive learning materials, interactive exercises, and expert video lessons
          </p>
          <div className="flex gap-4 max-w-2xl mx-auto">
            <div className="relative flex-1">
              <Icon name="Search" className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={20} />
              <Input
                type="text"
                placeholder="Search articles, exercises, videos..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button size="lg">
              <Icon name="Filter" size={20} className="mr-2" />
              Filters
            </Button>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <section className="pb-20 px-4">
        <div className="container mx-auto max-w-7xl">
          <Tabs defaultValue="articles" className="w-full">
            <TabsList className="grid w-full max-w-md mx-auto grid-cols-4 mb-8">
              <TabsTrigger value="articles">
                <Icon name="BookOpen" size={18} className="mr-2" />
                Articles
              </TabsTrigger>
              <TabsTrigger value="exercises">
                <Icon name="PenTool" size={18} className="mr-2" />
                Exercises
              </TabsTrigger>
              <TabsTrigger value="videos">
                <Icon name="Video" size={18} className="mr-2" />
                Videos
              </TabsTrigger>
              <TabsTrigger value="blog">
                <Icon name="FileText" size={18} className="mr-2" />
                Blog
              </TabsTrigger>
            </TabsList>

            {/* Articles Tab */}
            <TabsContent value="articles" className="space-y-8">
              <div className="flex gap-2 flex-wrap">
                <Button
                  variant={selectedLevel === 'all' ? 'default' : 'outline'}
                  onClick={() => setSelectedLevel('all')}
                  size="sm"
                >
                  All Levels
                </Button>
                <Button
                  variant={selectedLevel === 'Beginner' ? 'default' : 'outline'}
                  onClick={() => setSelectedLevel('Beginner')}
                  size="sm"
                >
                  Beginner
                </Button>
                <Button
                  variant={selectedLevel === 'Intermediate' ? 'default' : 'outline'}
                  onClick={() => setSelectedLevel('Intermediate')}
                  size="sm"
                >
                  Intermediate
                </Button>
                <Button
                  variant={selectedLevel === 'Advanced' ? 'default' : 'outline'}
                  onClick={() => setSelectedLevel('Advanced')}
                  size="sm"
                >
                  Advanced
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
                        Read Article
                        <Icon name="ArrowRight" size={16} className="ml-2" />
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            {/* Exercises Tab */}
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
                        <span className="ml-3">{exercise.questions} questions</span>
                      </CardDescription>
                    </div>
                    <Button variant={exercise.completed ? 'outline' : 'default'}>
                      {exercise.completed ? (
                        <>
                          <Icon name="RotateCw" size={16} className="mr-2" />
                          Retry
                        </>
                      ) : (
                        <>
                          <Icon name="Play" size={16} className="mr-2" />
                          Start
                        </>
                      )}
                    </Button>
                  </CardHeader>
                </Card>
              ))}
            </TabsContent>

            {/* Videos Tab */}
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
                        {video.views.toLocaleString()} views
                      </CardDescription>
                    </CardHeader>
                  </Card>
                ))}
              </div>
            </TabsContent>

            {/* Blog Tab */}
            <TabsContent value="blog">
              <div className="text-center py-12">
                <Icon name="FileText" size={64} className="mx-auto text-muted-foreground mb-4" />
                <h3 className="text-2xl font-bold mb-2">Explore Our Blog</h3>
                <p className="text-muted-foreground mb-6">
                  Read latest insights, tips, and stories from English learning experts
                </p>
                <Button size="lg" onClick={() => window.location.href = '/blog'}>
                  Visit Blog
                  <Icon name="ArrowRight" size={20} className="ml-2" />
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Level Up Your English?</h2>
          <p className="text-xl mb-8 opacity-90">
            Join thousands of learners improving their skills every day
          </p>
          <Button size="lg" variant="secondary">
            Get Started Free
            <Icon name="ArrowRight" size={20} className="ml-2" />
          </Button>
        </div>
      </section>
    </div>
  );
}
