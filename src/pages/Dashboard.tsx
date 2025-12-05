import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
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

interface Message {
  role: 'user' | 'assistant';
  content: string;
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

  useEffect(() => {
    // Инициализация Telegram WebApp
    if (window.Telegram?.WebApp) {
      const tg = window.Telegram.WebApp;
      tg.ready();
      tg.expand();
      
      const telegramUser = tg.initDataUnsafe.user;
      if (telegramUser) {
        setUser(telegramUser);
        checkUser(telegramUser.id);
      }
    } else {
      // Демо-режим
      const demoUser = {
        id: 123456,
        first_name: 'Демо',
        username: 'demo_user'
      };
      setUser(demoUser);
      setShowRegistration(true);
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



  const userName = user?.first_name || user?.username || 'Пользователь';
  const roleIcon = role === 'teacher' ? 'GraduationCap' : 'BookOpen';
  const roleText = role === 'teacher' ? 'Преподаватель' : 'Ученик';

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50">
      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-10 shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Avatar className="h-10 w-10 bg-gradient-to-br from-purple-500 to-blue-500">
                <AvatarFallback className="text-white">
                  {userName.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div>
                <h2 className="font-semibold text-lg">{userName}</h2>
                {role && (
                  <Badge variant="secondary" className="flex items-center gap-1 w-fit">
                    <Icon name={roleIcon} size={12} />
                    <span className="text-xs">{roleText}</span>
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6 max-w-4xl">
        {/* Role Selector */}
        <Card className="shadow-lg mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Icon name="UserCog" size={24} />
              Настройки профиля
            </CardTitle>
            <CardDescription>
              Выбери свою роль в системе
            </CardDescription>
          </CardHeader>
          <CardContent className="flex gap-3">
            <Button
              onClick={() => changeRole('student')}
              disabled={loading}
              variant={role === 'student' ? 'default' : 'outline'}
              className={`flex-1 h-16 ${
                role === 'student'
                  ? 'bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600'
                  : ''
              }`}
            >
              <Icon name="BookOpen" size={20} className="mr-2" />
              Ученик
            </Button>
            <Button
              onClick={() => changeRole('teacher')}
              disabled={loading}
              variant={role === 'teacher' ? 'default' : 'outline'}
              className={`flex-1 h-16 ${
                role === 'teacher'
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600'
                  : ''
              }`}
            >
              <Icon name="GraduationCap" size={20} className="mr-2" />
              Преподаватель
            </Button>
          </CardContent>
        </Card>

        {/* History */}
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Icon name="History" size={24} />
              История диалогов
            </CardTitle>
            <CardDescription>
              Все твои разговоры с AI-помощником
            </CardDescription>
          </CardHeader>
          <CardContent>
            {conversations.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Icon name="MessageCircle" size={48} className="mx-auto mb-4 opacity-50" />
                <p>У тебя пока нет диалогов</p>
                <p className="text-sm mt-2">Начни общаться с ботом в Telegram</p>
              </div>
            ) : (
              <ScrollArea className="h-[400px] pr-4">
                <div className="space-y-4">
                  {conversations.map((conv) => (
                    <Card key={conv.id} className="border-2">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-base flex items-center gap-2">
                          <Icon name="MessageSquare" size={16} />
                          {conv.title}
                        </CardTitle>
                        <CardDescription className="text-xs">
                          {new Date(conv.updated_at).toLocaleString('ru-RU')}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {conv.messages.slice(0, 3).map((msg: any, idx: number) => (
                            <div
                              key={idx}
                              className={`text-sm p-2 rounded ${
                                msg.role === 'user'
                                  ? 'bg-blue-100 text-blue-900'
                                  : 'bg-gray-100 text-gray-900'
                              }`}
                            >
                              <span className="font-semibold">
                                {msg.role === 'user' ? '👤 Вы' : '🤖 AI'}:
                              </span>{' '}
                              {msg.content.substring(0, 100)}
                              {msg.content.length > 100 && '...'}
                            </div>
                          ))}
                          {conv.messages.length > 3 && (
                            <p className="text-xs text-gray-500 text-center">
                              + еще {conv.messages.length - 3} сообщений
                            </p>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}