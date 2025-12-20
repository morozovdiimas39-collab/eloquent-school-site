import { useParams, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import Header from '@/components/anya/Header';
import Footer from '@/components/anya/Footer';
import { funcUrls } from '@/config/funcUrls';

const API_URL = funcUrls['webapp-api'];

interface BlogPost {
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

export default function BlogPost() {
  const { id: slug } = useParams();
  const navigate = useNavigate();
  const [post, setPost] = useState<BlogPost | null>(null);
  const [loading, setLoading] = useState(true);
  const [otherPosts, setOtherPosts] = useState<BlogPost[]>([]);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' });
    loadPost();
  }, [slug]);

  const loadPost = async () => {
    if (!slug) return;

    if (!API_URL) {
      console.error('BlogPost: API_URL is not defined');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'get_blog_post', slug })
      });

      const data = await response.json();
      if (data.success && data.post) {
        setPost(data.post);
        loadOtherPosts();
      }
    } catch (error) {
      console.error('Error loading post:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadOtherPosts = async () => {
    if (!API_URL) {
      console.error('BlogPost: API_URL is not defined for loadOtherPosts');
      return;
    }

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'get_blog_posts', published_only: true })
      });

      const data = await response.json();
      if (data.success) {
        setOtherPosts(data.posts.filter((p: BlogPost) => p.slug !== slug).slice(0, 3));
      }
    } catch (error) {
      console.error('Error loading other posts:', error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
        <Header />
        <div className="flex items-center justify-center h-screen">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600"></div>
        </div>
      </div>
    );
  }

  if (!post) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="p-12 text-center">
            <div className="w-20 h-20 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-6">
              <Icon name="FileQuestion" size={40} className="text-gray-400" />
            </div>
            <h2 className="text-2xl font-bold mb-4">Статья не найдена</h2>
            <p className="text-gray-600 mb-6">К сожалению, такой статьи не существует</p>
            <Button onClick={() => navigate('/blog')} className="bg-gradient-to-r from-purple-600 to-blue-600">
              Вернуться к блогу
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Header />
      
      <article className="pt-20">
        <div className="container mx-auto px-4 py-12 max-w-4xl">
          <Button
            variant="ghost"
            onClick={() => navigate('/blog')}
            className="mb-8 hover:bg-purple-50"
          >
            <Icon name="ArrowLeft" size={20} className="mr-2" />
            Назад к блогу
          </Button>

          <div className="mb-8">
            <Badge className="mb-6 text-sm px-4 py-2">
              {post.author}
            </Badge>
            
            <h1 className="text-4xl md:text-5xl font-bold mb-6 leading-tight text-gray-900">
              {post.title}
            </h1>

            <div className="flex items-center gap-6 text-gray-600">
              <div className="flex items-center gap-2">
                <Icon name="Calendar" size={18} />
                {new Date(post.created_at).toLocaleDateString('ru-RU', {
                  day: 'numeric',
                  month: 'long',
                  year: 'numeric'
                })}
              </div>
              <div className="flex items-center gap-2">
                <Icon name="Clock" size={18} />
                {post.reading_time} мин
              </div>
              <div className="flex items-center gap-2">
                <Icon name="Eye" size={18} />
                {post.views_count} просмотров
              </div>
            </div>
          </div>

          {post.cover_image && (
            <div className="relative rounded-3xl overflow-hidden shadow-2xl mb-12">
              <img 
                src={post.cover_image} 
                alt={post.title}
                className="w-full h-[400px] object-cover"
              />
            </div>
          )}

          <Card className="border-2 border-gray-200 shadow-xl mb-12">
            <CardContent className="p-8 md:p-12">
              <div className="prose prose-lg max-w-none">
                {post.content.split('\n\n').map((paragraph, idx) => {
                  if (paragraph.startsWith('**') && paragraph.endsWith('**')) {
                    return (
                      <h3 key={idx} className="text-2xl font-bold mt-8 mb-4 text-gray-900">
                        {paragraph.replace(/\*\*/g, '')}
                      </h3>
                    );
                  }
                  
                  if (paragraph.includes('**')) {
                    const parts = paragraph.split(/(\*\*.*?\*\*)/g);
                    return (
                      <p key={idx} className="text-gray-700 leading-relaxed mb-6">
                        {parts.map((part, i) => 
                          part.startsWith('**') && part.endsWith('**') 
                            ? <strong key={i} className="text-gray-900 font-bold">{part.replace(/\*\*/g, '')}</strong>
                            : part
                        )}
                      </p>
                    );
                  }

                  if (paragraph.startsWith('❌') || paragraph.startsWith('✅')) {
                    return (
                      <div key={idx} className="bg-gray-50 rounded-lg p-4 mb-4 border-l-4 border-purple-400">
                        <p className="text-gray-800 font-mono text-sm">{paragraph}</p>
                      </div>
                    );
                  }

                  if (paragraph.startsWith('-')) {
                    const items = paragraph.split('\n');
                    return (
                      <ul key={idx} className="space-y-3 mb-6">
                        {items.map((item, i) => (
                          <li key={i} className="flex items-start gap-3 text-gray-700">
                            <Icon name="CheckCircle2" size={20} className="text-purple-600 flex-shrink-0 mt-1" />
                            <span>{item.replace(/^- /, '')}</span>
                          </li>
                        ))}
                      </ul>
                    );
                  }

                  return (
                    <p key={idx} className="text-gray-700 leading-relaxed mb-6 text-lg">
                      {paragraph}
                    </p>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          <Card className="border-4 border-purple-500 bg-gradient-to-br from-purple-50 to-blue-50 shadow-2xl mb-12">
            <CardContent className="p-8 text-center">
              <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center mx-auto mb-6">
                <Icon name="Sparkles" size={32} className="text-white" />
              </div>
              <h3 className="text-2xl font-bold mb-4">Готов попробовать anyaGPT?</h3>
              <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
                Начни практиковать английский прямо сейчас с персональным ИИ-репетитором в Telegram
              </p>
              <Button
                onClick={() => navigate('/')}
                size="lg"
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 font-semibold text-lg h-14 px-8 shadow-xl"
              >
                Попробовать бесплатно
                <Icon name="ArrowRight" size={20} className="ml-2" />
              </Button>
            </CardContent>
          </Card>

          {otherPosts.length > 0 && (
            <div>
              <h3 className="text-3xl font-bold mb-8">Читайте также</h3>
              <div className="grid md:grid-cols-3 gap-6">
                {otherPosts.map((otherPost) => (
                  <Card 
                    key={otherPost.id}
                    className="group overflow-hidden border-2 border-gray-200 hover:border-purple-400 transition-all duration-300 hover:shadow-xl hover:-translate-y-2 cursor-pointer"
                    onClick={() => {
                      navigate(`/blog/${otherPost.slug}`);
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }}
                  >
                    {otherPost.cover_image && (
                      <div className="relative h-40 overflow-hidden">
                        <img 
                          src={otherPost.cover_image} 
                          alt={otherPost.title}
                          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                        />
                      </div>
                    )}
                    <CardContent className="p-4">
                      <h4 className="font-bold mb-2 text-gray-900 group-hover:text-purple-600 transition-colors line-clamp-2">
                        {otherPost.title}
                      </h4>
                      <p className="text-sm text-gray-600 line-clamp-2">
                        {otherPost.excerpt}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      </article>

      <Footer />
    </div>
  );
}