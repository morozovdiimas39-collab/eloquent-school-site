import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import Icon from '@/components/ui/icon';
import { funcUrls } from '@/config/funcUrls';
import ProxyManager from '@/components/admin/webapp/ProxyManager';
import BlogManager from '@/components/admin/webapp/BlogManager';
import PromptsManager from '@/components/admin/webapp/PromptsManager';
import PricingManager from '@/components/admin/webapp/PricingManager';

interface User {
  telegram_id: number;
  username?: string;
  first_name?: string;
  last_name?: string;
  role: 'student' | 'teacher';
  promocode?: string;
  teacher_id?: number;
  created_at?: string;
  photo_url?: string;
  language_level?: string;
  preferred_topics?: string[];
  timezone?: string;
  subscription_active?: boolean;
  subscription_expires_at?: string;
  voice_subscription_active?: boolean;
  voice_subscription_expires_at?: string;
}



const API_URL = funcUrls['webapp-api'];
const SCHEDULER_URL = funcUrls['practice-scheduler'];

const ALLOWED_IDS = [994807644, 7515380522];
const ADMIN_PASSWORD = 'AnyaGPT2025!';

export default function Admin() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [authLoading, setAuthLoading] = useState(true);
  const [telegramId, setTelegramId] = useState('');
  const [password, setPassword] = useState('');
  const [authError, setAuthError] = useState('');


  const [students, setStudents] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'students' | 'analytics' | 'proxies' | 'blog' | 'prompts' | 'pricing'>('students');

  const [analytics, setAnalytics] = useState<any>(null);
  const [schedulerRunning, setSchedulerRunning] = useState(false);
  const [schedulerResult, setSchedulerResult] = useState<any>(null);
  const [processingSubscription, setProcessingSubscription] = useState<number | null>(null);

  useEffect(() => {
    const savedAuth = localStorage.getItem('admin_auth');
    if (savedAuth) {
      try {
        const { id, pass, timestamp } = JSON.parse(savedAuth);
        const hoursPassed = (Date.now() - timestamp) / (1000 * 60 * 60);
        
        if (hoursPassed < 24 && ALLOWED_IDS.includes(Number(id)) && pass === ADMIN_PASSWORD) {
          setIsAuthenticated(true);
        } else {
          localStorage.removeItem('admin_auth');
        }
      } catch {
        localStorage.removeItem('admin_auth');
      }
    }
    setAuthLoading(false);
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
      loadAnalytics();
    }
  }, [isAuthenticated]);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError('');

    const id = Number(telegramId);
    
    if (!ALLOWED_IDS.includes(id)) {
      setAuthError('Доступ запрещен');
      return;
    }

    if (password !== ADMIN_PASSWORD) {
      setAuthError('Неверный пароль');
      return;
    }

    const authData = {
      id: telegramId,
      pass: password,
      timestamp: Date.now()
    };
    
    localStorage.setItem('admin_auth', JSON.stringify(authData));
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_auth');
    setIsAuthenticated(false);
    setTelegramId('');
    setPassword('');
  };

  const loadData = async () => {
    setLoading(true);
    try {
      const studentsRes = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'get_all_students' })
      });

      const studentsData = await studentsRes.json();

      if (studentsData.students) {
        setStudents(studentsData.students);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAnalytics = async () => {
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'get_financial_analytics' })
      });
      const data = await res.json();
      if (data.analytics) {
        setAnalytics(data.analytics);
      }
    } catch (error) {
      console.error('Error loading analytics:', error);
    }
  };

  const runScheduler = async () => {
    setSchedulerRunning(true);
    setSchedulerResult(null);
    try {
      const res = await fetch(SCHEDULER_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      const data = await res.json();
      setSchedulerResult(data);
    } catch (error) {
      console.error('Error running scheduler:', error);
      setSchedulerResult({ error: 'Ошибка запуска' });
    } finally {
      setSchedulerRunning(false);
    }
  };

  const toggleSubscription = async (telegramId: number, active: boolean, days: number = 30, subscriptionType: 'basic' | 'premium' = 'basic') => {
    setProcessingSubscription(telegramId);
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'toggle_subscription',
          telegram_id: telegramId,
          active,
          days,
          subscription_type: subscriptionType
        })
      });
      await res.json();
      await loadData();
    } catch (error) {
      console.error('Error toggling subscription:', error);
    } finally {
      setProcessingSubscription(null);
    }
  };



  const filteredStudents = students.filter(s => {
    const searchLower = searchQuery.toLowerCase();
    return (
      s.first_name?.toLowerCase().includes(searchLower) ||
      s.username?.toLowerCase().includes(searchLower)
    );
  });

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-sm">
          <CardContent className="pt-6 pb-6">
            <div className="flex flex-col items-center gap-3">
              <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-gray-700 text-base font-medium">Проверка доступа...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-lg">
          <CardHeader className="text-center">
            <div className="flex justify-center mb-3">
              <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center">
                <Icon name="Shield" size={32} className="text-white" />
              </div>
            </div>
            <CardTitle className="text-2xl">Вход в админку</CardTitle>
            <CardDescription>Введите Telegram ID и пароль</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Telegram ID
                </label>
                <Input
                  type="text"
                  value={telegramId}
                  onChange={(e) => setTelegramId(e.target.value)}
                  placeholder="994807644"
                  className="h-11"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Пароль
                </label>
                <Input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="h-11"
                  required
                />
              </div>
              {authError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {authError}
                </div>
              )}
              <Button type="submit" className="w-full h-11 text-base font-medium">
                Войти
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-sm">
          <CardContent className="pt-6 pb-6">
            <div className="flex flex-col items-center gap-3">
              <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-gray-700 text-base font-medium">Загрузка...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 py-6 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6 flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-1 flex items-center gap-2.5">
              <Icon name="Shield" size={28} className="text-blue-600" />
              Панель администратора
            </h1>
            <p className="text-gray-600 text-base">Управление проектом AnyaGPT</p>
          </div>
          <Button onClick={handleLogout} variant="outline" className="h-10">
            <Icon name="LogOut" size={16} className="mr-2" />
            Выйти
          </Button>
        </div>

        <div className="mb-5 flex flex-col sm:flex-row gap-3">
          <div className="flex-1">
            <Input
              type="text"
              placeholder="Поиск по имени или username..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-11 text-sm"
            />
          </div>
          <div className="flex gap-2 flex-wrap">
            <Button
              onClick={() => setActiveTab('students')}
              variant={activeTab === 'students' ? 'default' : 'outline'}
              className="flex-1 sm:flex-none h-11 text-sm font-medium"
            >
              <Icon name="BookOpen" size={16} className="mr-1.5" />
              Ученики ({students.length})
            </Button>
            <Button
              onClick={() => setActiveTab('analytics')}
              variant={activeTab === 'analytics' ? 'default' : 'outline'}
              className="flex-1 sm:flex-none h-11 text-sm font-medium"
            >
              <Icon name="BarChart3" size={16} className="mr-1.5" />
              Финансы
            </Button>
            <Button
              onClick={() => setActiveTab('proxies')}
              variant={activeTab === 'proxies' ? 'default' : 'outline'}
              className="flex-1 sm:flex-none h-11 text-sm font-medium"
            >
              <Icon name="Globe" size={16} className="mr-1.5" />
              Прокси
            </Button>
            <Button
              onClick={() => setActiveTab('blog')}
              variant={activeTab === 'blog' ? 'default' : 'outline'}
              className="flex-1 sm:flex-none h-11 text-sm font-medium"
            >
              <Icon name="FileText" size={16} className="mr-1.5" />
              Блог
            </Button>
            <Button
              onClick={() => setActiveTab('prompts')}
              variant={activeTab === 'prompts' ? 'default' : 'outline'}
              className="flex-1 sm:flex-none h-11 text-sm font-medium"
            >
              <Icon name="MessageSquare" size={16} className="mr-1.5" />
              Промпты
            </Button>
            <Button
              onClick={() => setActiveTab('pricing')}
              variant={activeTab === 'pricing' ? 'default' : 'outline'}
              className="flex-1 sm:flex-none h-11 text-sm font-medium"
            >
              <Icon name="DollarSign" size={16} className="mr-1.5" />
              Цены
            </Button>
          </div>
        </div>



        {activeTab === 'students' && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredStudents.map((student) => {
              const studentName = student.first_name || student.username || 'Ученик';
              const studentUsername = student.username ? `@${student.username}` : null;

              return (
                <Card key={student.telegram_id} className="border border-blue-200 shadow-sm hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-start gap-3">
                      <Avatar className="w-12 h-12 border-2 border-blue-300">
                        <AvatarImage src={student.photo_url} />
                        <AvatarFallback className="bg-blue-100 text-blue-700 font-semibold">
                          {studentName.slice(0, 2).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-base font-semibold text-gray-900 leading-tight">
                          {studentName}
                        </CardTitle>
                        {studentUsername && (
                          <p className="text-xs text-gray-500 mt-0.5">{studentUsername}</p>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-2.5">
                    {student.language_level && (
                      <div className="flex items-center gap-2">
                        <Icon name="BookOpen" size={14} className="text-blue-600 flex-shrink-0" />
                        <Badge variant="outline" className="text-xs px-2 py-0.5">
                          {student.language_level}
                        </Badge>
                      </div>
                    )}
                    {student.timezone && (
                      <div className="flex items-center gap-2 text-sm">
                        <Icon name="Clock" size={14} className="text-gray-600 flex-shrink-0" />
                        <span className="text-gray-700">{student.timezone}</span>
                      </div>
                    )}
                    
                    <div className="pt-2 border-t border-gray-200 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-600 font-medium">💬 Базовая:</span>
                        {student.subscription_active ? (
                          <Badge className="text-xs bg-green-100 text-green-700 border-green-300">
                            <Icon name="CheckCircle" size={12} className="mr-1" />
                            Активна
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-xs bg-red-50 text-red-700 border-red-300">
                            <Icon name="XCircle" size={12} className="mr-1" />
                            Неактивна
                          </Badge>
                        )}
                      </div>
                      
                      {student.subscription_active && student.subscription_expires_at && (
                        <div className="text-xs text-gray-500">
                          До: {new Date(student.subscription_expires_at).toLocaleDateString('ru-RU', {
                            day: '2-digit',
                            month: '2-digit',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </div>
                      )}
                      
                      <div className="flex gap-2">
                        {student.subscription_active ? (
                          <Button
                            onClick={() => toggleSubscription(student.telegram_id, false, 0, 'basic')}
                            disabled={processingSubscription === student.telegram_id}
                            variant="outline"
                            size="sm"
                            className="flex-1 h-8 text-xs border-red-300 text-red-700 hover:bg-red-50"
                          >
                            {processingSubscription === student.telegram_id ? (
                              <div className="w-3 h-3 border-2 border-red-700 border-t-transparent rounded-full animate-spin" />
                            ) : (
                              <>
                                <Icon name="XCircle" size={12} className="mr-1" />
                                Отменить
                              </>
                            )}
                          </Button>
                        ) : (
                          <Button
                            onClick={() => toggleSubscription(student.telegram_id, true, 30, 'basic')}
                            disabled={processingSubscription === student.telegram_id}
                            variant="outline"
                            size="sm"
                            className="flex-1 h-8 text-xs border-green-300 text-green-700 hover:bg-green-50"
                          >
                            {processingSubscription === student.telegram_id ? (
                              <div className="w-3 h-3 border-2 border-green-700 border-t-transparent rounded-full animate-spin" />
                            ) : (
                              <>
                                <Icon name="Plus" size={12} className="mr-1" />
                                +30 дней
                              </>
                            )}
                          </Button>
                        )}
                      </div>
                    </div>
                    
                    <div className="pt-2 border-t border-gray-200 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-600 font-medium">🎤 Голосовая:</span>
                        {student.voice_subscription_active ? (
                          <Badge className="text-xs bg-purple-100 text-purple-700 border-purple-300">
                            <Icon name="CheckCircle" size={12} className="mr-1" />
                            Активна
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-xs bg-red-50 text-red-700 border-red-300">
                            <Icon name="XCircle" size={12} className="mr-1" />
                            Неактивна
                          </Badge>
                        )}
                      </div>
                      
                      {student.voice_subscription_active && student.voice_subscription_expires_at && (
                        <div className="text-xs text-gray-500">
                          До: {new Date(student.voice_subscription_expires_at).toLocaleDateString('ru-RU', {
                            day: '2-digit',
                            month: '2-digit',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </div>
                      )}
                      
                      <div className="flex gap-2">
                        {student.voice_subscription_active ? (
                          <Button
                            onClick={() => toggleSubscription(student.telegram_id, false, 0, 'premium')}
                            disabled={processingSubscription === student.telegram_id}
                            variant="outline"
                            size="sm"
                            className="flex-1 h-8 text-xs border-red-300 text-red-700 hover:bg-red-50"
                          >
                            {processingSubscription === student.telegram_id ? (
                              <div className="w-3 h-3 border-2 border-red-700 border-t-transparent rounded-full animate-spin" />
                            ) : (
                              <>
                                <Icon name="XCircle" size={12} className="mr-1" />
                                Отменить
                              </>
                            )}
                          </Button>
                        ) : (
                          <Button
                            onClick={() => toggleSubscription(student.telegram_id, true, 30, 'premium')}
                            disabled={processingSubscription === student.telegram_id}
                            variant="outline"
                            size="sm"
                            className="flex-1 h-8 text-xs border-purple-300 text-purple-700 hover:bg-purple-50"
                          >
                            {processingSubscription === student.telegram_id ? (
                              <div className="w-3 h-3 border-2 border-purple-700 border-t-transparent rounded-full animate-spin" />
                            ) : (
                              <>
                                <Icon name="Plus" size={12} className="mr-1" />
                                +30 дней
                              </>
                            )}
                          </Button>
                        )}
                      </div>
                    </div>
                    
                    {student.created_at && (
                      <div className="text-xs text-gray-500 pt-2 border-t border-gray-200">
                        Регистрация: {new Date(student.created_at).toLocaleDateString('ru-RU')}
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}



        {activeTab === 'proxies' && <ProxyManager />}

        {activeTab === 'blog' && <BlogManager />}

        {activeTab === 'prompts' && <PromptsManager />}

        {activeTab === 'pricing' && <PricingManager />}

        {activeTab === 'analytics' && (
          <div className="space-y-4">
            <Card className="border border-green-200 shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Icon name="DollarSign" size={20} className="text-green-600" />
                  Финансовая статистика
                </CardTitle>
              </CardHeader>
              <CardContent>
                {analytics ? (
                  <div className="space-y-6">
                    <div className="grid gap-4 md:grid-cols-4">
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <p className="text-xs text-gray-600 mb-1 font-medium">💰 Всего заработано</p>
                        <p className="text-3xl font-bold text-green-700">{analytics.total_revenue?.toLocaleString('ru-RU')}₽</p>
                        <p className="text-xs text-gray-500 mt-1">{analytics.total_payments || 0} платежей</p>
                      </div>
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <p className="text-xs text-gray-600 mb-1 font-medium">📅 За месяц</p>
                        <p className="text-3xl font-bold text-blue-700">{analytics.month_revenue?.toLocaleString('ru-RU')}₽</p>
                        <p className="text-xs text-gray-500 mt-1">Текущий месяц</p>
                      </div>
                      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                        <p className="text-xs text-gray-600 mb-1 font-medium">🔥 За неделю</p>
                        <p className="text-3xl font-bold text-purple-700">{analytics.week_revenue?.toLocaleString('ru-RU')}₽</p>
                        <p className="text-xs text-gray-500 mt-1">Последние 7 дней</p>
                      </div>
                      <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                        <p className="text-xs text-gray-600 mb-1 font-medium">💳 Средний чек</p>
                        <p className="text-3xl font-bold text-orange-700">{analytics.avg_check?.toLocaleString('ru-RU')}₽</p>
                        <p className="text-xs text-gray-500 mt-1">На платёж</p>
                      </div>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="bg-gradient-to-br from-green-50 to-blue-50 border border-green-200 rounded-lg p-4">
                        <p className="text-sm text-gray-700 mb-3 font-semibold">📊 Активные подписки</p>
                        <div className="space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">💬 Базовая:</span>
                            <span className="text-lg font-bold text-green-700">{analytics.active_basic || 0}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">🎤 Премиум:</span>
                            <span className="text-lg font-bold text-purple-700">{analytics.active_premium || 0}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">🔥 Всё сразу:</span>
                            <span className="text-lg font-bold text-orange-700">{analytics.active_bundle || 0}</span>
                          </div>
                          <div className="border-t border-gray-300 pt-2 mt-2 flex justify-between items-center">
                            <span className="text-sm font-semibold text-gray-700">Всего активных:</span>
                            <span className="text-xl font-bold text-blue-700">{analytics.total_active_subscriptions || 0}</span>
                          </div>
                        </div>
                      </div>

                      <div className="bg-gradient-to-br from-purple-50 to-pink-50 border border-purple-200 rounded-lg p-4">
                        <p className="text-sm text-gray-700 mb-3 font-semibold">💎 Статистика по тарифам</p>
                        <div className="space-y-2">
                          {analytics.plan_stats && Object.entries(analytics.plan_stats).map(([key, stats]: [string, any]) => (
                            <div key={key} className="bg-white/70 rounded p-2">
                              <div className="flex justify-between items-center mb-1">
                                <span className="text-xs font-medium text-gray-700">
                                  {key === 'basic' && '💬 Базовая'}
                                  {key === 'premium' && '🎤 Премиум'}
                                  {key === 'bundle' && '🔥 Всё сразу'}
                                </span>
                              </div>
                              <div className="flex justify-between text-xs text-gray-600">
                                <span>{stats.total_purchases} покупок</span>
                                <span className="font-semibold text-green-600">{stats.total_revenue?.toLocaleString('ru-RU')}₽</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <p className="text-sm text-gray-700 mb-3 font-semibold">📈 Динамика платежей (последние 30 дней)</p>
                      {analytics.daily_revenue && analytics.daily_revenue.length > 0 ? (
                        <div className="space-y-1">
                          {analytics.daily_revenue.slice(-10).map((day: any, idx: number) => (
                            <div key={idx} className="flex justify-between items-center text-xs">
                              <span className="text-gray-600">{new Date(day.date).toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' })}</span>
                              <div className="flex items-center gap-2">
                                <span className="text-gray-500">{day.count} платежей</span>
                                <span className="font-semibold text-green-600">{day.revenue?.toLocaleString('ru-RU')}₽</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-gray-500">Нет данных за последние 30 дней</p>
                      )}
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
                        <p className="text-sm text-gray-600 mb-1">👥 Всего студентов</p>
                        <p className="text-2xl font-bold text-indigo-700">{analytics.total_students || 0}</p>
                      </div>
                      <div className="bg-teal-50 border border-teal-200 rounded-lg p-4">
                        <p className="text-sm text-gray-600 mb-1">📊 Конверсия в подписку</p>
                        <p className="text-2xl font-bold text-teal-700">
                          {analytics.total_students > 0 
                            ? ((analytics.total_active_subscriptions / analytics.total_students) * 100).toFixed(1)
                            : 0}%
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-600">Загрузка статистики...</p>
                )}
              </CardContent>
            </Card>

            <Card className="border border-orange-200 shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Icon name="Zap" size={20} className="text-orange-600" />
                  Планировщик практики
                </CardTitle>
                <CardDescription>
                  Запускает отправку проактивных сообщений от Ани студентам
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  onClick={runScheduler}
                  disabled={schedulerRunning}
                  className="h-11 font-medium"
                >
                  {schedulerRunning ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                      Запуск...
                    </>
                  ) : (
                    <>
                      <Icon name="Play" size={16} className="mr-2" />
                      Запустить сейчас
                    </>
                  )}
                </Button>
                
                {schedulerResult && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                      {JSON.stringify(schedulerResult, null, 2)}
                    </pre>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {selectedTeacher && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
            <Card className="w-full max-w-2xl max-h-[80vh] overflow-y-auto shadow-xl">
              <CardHeader className="border-b border-gray-200 sticky top-0 bg-white z-10">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-xl">
                      Ученики преподавателя {selectedTeacher.first_name}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      Всего: {selectedTeacher.students_count || 0}
                    </CardDescription>
                  </div>
                  <Button
                    onClick={() => setSelectedTeacher(null)}
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0"
                  >
                    <Icon name="X" size={18} />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="pt-4">
                <div className="space-y-3">
                  {students
                    .filter(s => s.teacher_id === selectedTeacher.telegram_id)
                    .map(student => {
                      const studentName = student.first_name || student.username || 'Ученик';
                      return (
                        <div key={student.telegram_id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                          <Avatar className="w-10 h-10">
                            <AvatarImage src={student.photo_url} />
                            <AvatarFallback className="bg-blue-100 text-blue-700 text-sm font-semibold">
                              {studentName.slice(0, 2).toUpperCase()}
                            </AvatarFallback>
                          </Avatar>
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-gray-900 text-sm leading-tight">{studentName}</p>
                            {student.username && (
                              <p className="text-xs text-gray-500 mt-0.5">@{student.username}</p>
                            )}
                          </div>
                          {student.language_level && (
                            <Badge variant="outline" className="text-xs px-2 py-0.5">
                              {student.language_level}
                            </Badge>
                          )}
                        </div>
                      );
                    })}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}