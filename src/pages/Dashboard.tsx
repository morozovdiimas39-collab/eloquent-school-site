import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import funcUrls from '../../backend/func2url.json';

interface TelegramUser {
  id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
}

declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        initDataUnsafe: {
          user?: TelegramUser;
        };
        ready: () => void;
        expand: () => void;
        MainButton: {
          text: string;
          show: () => void;
          hide: () => void;
          onClick: (callback: () => void) => void;
        };
        BackButton: {
          show: () => void;
          hide: () => void;
          onClick: (callback: () => void) => void;
        };
        themeParams: {
          bg_color?: string;
          text_color?: string;
          hint_color?: string;
          link_color?: string;
          button_color?: string;
          button_text_color?: string;
        };
      };
    };
  }
}

const API_URL = funcUrls['webapp-api'];

export default function Dashboard() {
  const [user, setUser] = useState<TelegramUser | null>(null);
  const [role, setRole] = useState<'student' | 'teacher' | null>(null);
  const [conversations, setConversations] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    
    if (tg) {
      tg.ready();
      tg.expand();
      
      const telegramUser = tg.initDataUnsafe.user;
      if (telegramUser) {
        setUser(telegramUser);
        checkUser(telegramUser.id);
      } else {
        setError('Не удалось получить данные пользователя Telegram');
      }
    } else {
      setError('Откройте это приложение через Telegram');
    }
  }, []);

  const checkUser = async (telegramId: number) => {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'get_user',
          telegram_id: telegramId
        })
      });
      
      const data = await response.json();
      
      if (data.user) {
        setRole(data.user.role);
        loadHistory(telegramId);
      }
    } catch (error) {
      console.error('Error checking user:', error);
      setError('Ошибка загрузки данных');
    }
  };

  const loadHistory = async (telegramId: number) => {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'get_history',
          telegram_id: telegramId
        })
      });
      
      const data = await response.json();
      
      if (data.conversations) {
        setConversations(data.conversations);
      }
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };

  const changeRole = async (newRole: 'student' | 'teacher') => {
    if (!user) return;
    
    setLoading(true);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'change_role',
          telegram_id: user.id,
          role: newRole
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setRole(newRole);
      }
    } catch (error) {
      console.error('Error changing role:', error);
    } finally {
      setLoading(false);
    }
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <Icon name="AlertCircle" size={24} />
              Ошибка
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700">{error}</p>
            <p className="text-sm text-gray-500 mt-4">
              Откройте это приложение через бота в Telegram
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!user || role === null) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center gap-4">
              <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-gray-600">Загрузка...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const userName = user.first_name || user.username || 'Пользователь';
  const roleIcon = role === 'teacher' ? 'GraduationCap' : 'BookOpen';
  const roleText = role === 'teacher' ? 'Преподаватель' : 'Ученик';

  return (
    <div className="min-h-screen bg-[var(--tg-theme-bg-color,#ffffff)]">
      {/* Header */}
      <div className="bg-[var(--tg-theme-secondary-bg-color,#f4f4f5)] border-b sticky top-0 z-10">
        <div className="px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Avatar className="h-12 w-12 bg-gradient-to-br from-purple-500 to-blue-500">
                <AvatarFallback className="text-white text-lg">
                  {userName.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div>
                <h1 className="font-bold text-xl text-[var(--tg-theme-text-color,#000000)]">
                  {userName}
                </h1>
                {role && (
                  <Badge 
                    variant="secondary" 
                    className="flex items-center gap-1 w-fit mt-1"
                  >
                    <Icon name={roleIcon} size={14} />
                    <span className="text-sm">{roleText}</span>
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="px-4 py-4 space-y-4">
        {/* Role Selector */}
        <Card className="border-2 border-[var(--tg-theme-button-color,#3390ec)]">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Icon name="UserCog" size={20} />
              Выбор роли
            </CardTitle>
            <CardDescription className="text-sm">
              Измени роль в системе
            </CardDescription>
          </CardHeader>
          <CardContent className="flex gap-2">
            <Button
              onClick={() => changeRole('student')}
              disabled={loading}
              variant={role === 'student' ? 'default' : 'outline'}
              className={`flex-1 h-14 text-base ${
                role === 'student'
                  ? 'bg-[var(--tg-theme-button-color,#3390ec)] text-[var(--tg-theme-button-text-color,#ffffff)] hover:opacity-90'
                  : ''
              }`}
            >
              <Icon name="BookOpen" size={18} className="mr-2" />
              Ученик
            </Button>
            <Button
              onClick={() => changeRole('teacher')}
              disabled={loading}
              variant={role === 'teacher' ? 'default' : 'outline'}
              className={`flex-1 h-14 text-base ${
                role === 'teacher'
                  ? 'bg-[var(--tg-theme-button-color,#3390ec)] text-[var(--tg-theme-button-text-color,#ffffff)] hover:opacity-90'
                  : ''
              }`}
            >
              <Icon name="GraduationCap" size={18} className="mr-2" />
              Учитель
            </Button>
          </CardContent>
        </Card>

        {/* History */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Icon name="History" size={20} />
              История диалогов
            </CardTitle>
            <CardDescription className="text-sm">
              Все твои разговоры с AI
            </CardDescription>
          </CardHeader>
          <CardContent>
            {conversations.length === 0 ? (
              <div className="text-center py-8 text-[var(--tg-theme-hint-color,#999999)]">
                <Icon name="MessageCircle" size={40} className="mx-auto mb-3 opacity-50" />
                <p className="text-sm">У тебя пока нет диалогов</p>
                <p className="text-xs mt-1">Начни общаться с ботом в Telegram</p>
              </div>
            ) : (
              <ScrollArea className="h-[400px]">
                <div className="space-y-3 pr-4">
                  {conversations.map((conv) => (
                    <Card 
                      key={conv.id} 
                      className="border border-gray-200 shadow-sm"
                    >
                      <CardHeader className="pb-2">
                        <div className="flex items-start justify-between">
                          <CardTitle className="text-sm font-semibold flex items-center gap-2">
                            <Icon name="MessageSquare" size={14} />
                            {conv.title}
                          </CardTitle>
                          <Badge variant="outline" className="text-xs">
                            {conv.messages.length} сообщ.
                          </Badge>
                        </div>
                        <CardDescription className="text-xs">
                          {new Date(conv.updated_at).toLocaleString('ru-RU', {
                            day: 'numeric',
                            month: 'short',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="pt-0">
                        <div className="space-y-1.5">
                          {conv.messages.slice(-2).map((msg: any, idx: number) => (
                            <div
                              key={idx}
                              className={`text-xs p-2 rounded ${
                                msg.role === 'user'
                                  ? 'bg-blue-50 text-blue-900 border border-blue-200'
                                  : 'bg-gray-50 text-gray-900 border border-gray-200'
                              }`}
                            >
                              <span className="font-semibold">
                                {msg.role === 'user' ? '👤 Вы' : '🤖 AI'}:
                              </span>{' '}
                              {msg.content.substring(0, 80)}
                              {msg.content.length > 80 && '...'}
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>

        {/* Info Card */}
        <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
          <CardContent className="pt-4 pb-4">
            <div className="flex items-start gap-3">
              <Icon name="Info" size={20} className="text-purple-600 mt-0.5" />
              <div className="text-sm text-gray-700">
                <p className="font-semibold mb-1">Как пользоваться:</p>
                <ul className="space-y-1 text-xs text-gray-600">
                  <li>• Задавай вопросы боту прямо в чате Telegram</li>
                  <li>• Здесь ты можешь изменить свою роль</li>
                  <li>• Вся история диалогов сохраняется автоматически</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
