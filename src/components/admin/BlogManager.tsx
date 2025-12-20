import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import { funcUrls } from '@/config/funcUrls';

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

const API_URL = funcUrls['webapp-api'];

export default function BlogManager() {
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingPost, setEditingPost] = useState<BlogPost | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    slug: '',
    excerpt: '',
    content: '',
    cover_image: '',
    author: 'Команда Anya',
    published: false,
    reading_time: 5
  });

  useEffect(() => {
    loadPosts();
  }, []);

  const loadPosts = async () => {
    if (!API_URL) {
      console.error('📝 BlogManager: API_URL is not defined');
      setLoading(false);
      return;
    }

    try {
      console.log('📝 BlogManager: Loading posts from', API_URL);
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'get_blog_posts', published_only: false })
      });

      console.log('📝 BlogManager: Response status', response.status);
      const data = await response.json();
      console.log('📝 BlogManager: Response data', data);
      
      if (data.success) {
        setPosts(data.posts);
        console.log('📝 BlogManager: Loaded', data.posts.length, 'posts');
      } else {
        console.error('📝 BlogManager: Failed to load posts', data);
      }
    } catch (error) {
      console.error('📝 BlogManager: Error loading posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setIsCreating(true);
    setEditingPost(null);
    setFormData({
      title: '',
      slug: '',
      excerpt: '',
      content: '',
      cover_image: '',
      author: 'Команда Anya',
      published: false,
      reading_time: 5
    });
  };

  const handleEdit = (post: BlogPost) => {
    setEditingPost(post);
    setIsCreating(false);
    setFormData({
      title: post.title,
      slug: post.slug,
      excerpt: post.excerpt,
      content: post.content,
      cover_image: post.cover_image,
      author: post.author,
      published: post.published,
      reading_time: post.reading_time
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const action = editingPost ? 'update_blog_post' : 'create_blog_post';
      const payload: any = {
        action,
        ...formData
      };

      if (editingPost) {
        payload.post_id = editingPost.id;
      }

      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await response.json();
      if (data.success) {
        await loadPosts();
        setEditingPost(null);
        setIsCreating(false);
      }
    } catch (error) {
      console.error('Error saving post:', error);
    }
  };

  const handleDelete = async (postId: number) => {
    if (!confirm('Вы уверены, что хотите удалить эту статью?')) return;

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'delete_blog_post', post_id: postId })
      });

      const data = await response.json();
      if (data.success) {
        await loadPosts();
      }
    } catch (error) {
      console.error('Error deleting post:', error);
    }
  };

  const handleCancel = () => {
    setEditingPost(null);
    setIsCreating(false);
  };

  const generateSlug = (title: string) => {
    return title
      .toLowerCase()
      .replace(/[^а-яa-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .trim();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (isCreating || editingPost) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">
            {editingPost ? 'Редактировать статью' : 'Создать статью'}
          </h2>
          <Button variant="outline" onClick={handleCancel}>
            <Icon name="X" size={16} className="mr-2" />
            Отмена
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Основная информация</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Заголовок</label>
                <Input
                  value={formData.title}
                  onChange={(e) => {
                    const newTitle = e.target.value;
                    if (!editingPost) {
                      setFormData({ ...formData, title: newTitle, slug: generateSlug(newTitle) });
                    } else {
                      setFormData({ ...formData, title: newTitle });
                    }
                  }}
                  placeholder="Как учить английский с ИИ-репетитором"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Slug (URL)</label>
                <Input
                  value={formData.slug}
                  onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                  placeholder="kak-uchit-angliyskiy-s-ii"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  URL статьи: /blog/{formData.slug}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Краткое описание</label>
                <textarea
                  value={formData.excerpt}
                  onChange={(e) => setFormData({ ...formData, excerpt: e.target.value })}
                  placeholder="Узнайте, как современные технологии ИИ помогают учить английский..."
                  className="w-full px-3 py-2 border rounded-lg resize-none h-20"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Обложка (URL)</label>
                <Input
                  value={formData.cover_image}
                  onChange={(e) => setFormData({ ...formData, cover_image: e.target.value })}
                  placeholder="https://images.unsplash.com/..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Автор</label>
                  <Input
                    value={formData.author}
                    onChange={(e) => setFormData({ ...formData, author: e.target.value })}
                    placeholder="Команда Anya"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Время чтения (мин)</label>
                  <Input
                    type="number"
                    value={formData.reading_time}
                    onChange={(e) => setFormData({ ...formData, reading_time: Number(e.target.value) })}
                    min="1"
                    max="60"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="published"
                  checked={formData.published}
                  onChange={(e) => setFormData({ ...formData, published: e.target.checked })}
                  className="w-4 h-4 text-indigo-600 rounded"
                />
                <label htmlFor="published" className="text-sm font-medium">
                  Опубликовать статью
                </label>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Контент статьи</CardTitle>
              <CardDescription>
                Используйте Markdown для форматирования (## заголовки, **жирный**, *курсив*)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <textarea
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                placeholder="## Введение&#10;&#10;Искусственный интеллект революционизирует изучение языков..."
                className="w-full px-3 py-2 border rounded-lg resize-none font-mono text-sm"
                rows={20}
                required
              />
            </CardContent>
          </Card>

          <div className="flex justify-end gap-3">
            <Button type="button" variant="outline" onClick={handleCancel}>
              Отмена
            </Button>
            <Button type="submit" className="bg-indigo-600 hover:bg-indigo-700">
              <Icon name="Save" size={16} className="mr-2" />
              {editingPost ? 'Сохранить изменения' : 'Создать статью'}
            </Button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Управление блогом</h2>
          <p className="text-gray-600">Всего статей: {posts.length}</p>
        </div>
        <Button onClick={handleCreate} className="bg-indigo-600 hover:bg-indigo-700">
          <Icon name="Plus" size={16} className="mr-2" />
          Создать статью
        </Button>
      </div>

      <div className="grid gap-4">
        {posts.map((post) => (
          <Card key={post.id}>
            <CardContent className="p-6">
              <div className="flex gap-6">
                {post.cover_image && (
                  <div className="w-48 h-32 rounded-lg overflow-hidden flex-shrink-0">
                    <img
                      src={post.cover_image}
                      alt={post.title}
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}

                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4 mb-2">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-xl font-bold mb-1 truncate">{post.title}</h3>
                      <p className="text-sm text-gray-500 mb-2">/{post.slug}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {post.published ? (
                        <Badge className="bg-green-100 text-green-700">Опубликовано</Badge>
                      ) : (
                        <Badge className="bg-gray-100 text-gray-700">Черновик</Badge>
                      )}
                    </div>
                  </div>

                  <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                    {post.excerpt}
                  </p>

                  <div className="flex items-center gap-6 text-sm text-gray-500 mb-4">
                    <div className="flex items-center gap-1">
                      <Icon name="User" size={14} />
                      <span>{post.author}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Icon name="Eye" size={14} />
                      <span>{post.views_count} просмотров</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Icon name="Clock" size={14} />
                      <span>{post.reading_time} мин</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Icon name="Calendar" size={14} />
                      <span>{new Date(post.created_at).toLocaleDateString('ru-RU')}</span>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEdit(post)}
                    >
                      <Icon name="Edit" size={14} className="mr-1" />
                      Редактировать
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDelete(post.id)}
                      className="text-red-600 hover:text-red-700 hover:border-red-300"
                    >
                      <Icon name="Trash2" size={14} className="mr-1" />
                      Удалить
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {posts.length === 0 && (
          <Card>
            <CardContent className="p-12 text-center">
              <Icon name="FileText" size={48} className="mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-semibold mb-2">Нет статей</h3>
              <p className="text-gray-600 mb-4">Создайте первую статью для блога</p>
              <Button onClick={handleCreate} className="bg-indigo-600 hover:bg-indigo-700">
                <Icon name="Plus" size={16} className="mr-2" />
                Создать статью
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}