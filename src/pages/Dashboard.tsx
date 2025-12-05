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

const API_URL = funcUrls['api-chat'];

export default function Dashboard() {
  const [user, setUser] = useState<TelegramUser | null>(null);
  const [role, setRole] = useState<'student' | 'teacher' | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [showRegistration, setShowRegistration] = useState(false);

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
      } else {
        setShowRegistration(true);
      }
    } catch (error) {
      console.error('Error checking user:', error);
      setShowRegistration(true);
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
      
      if (data.history && data.history.length > 0) {
        setMessages(data.history);
      } else {
        setMessages([
          {
            role: 'assistant',
            content: 'Привет! Я твой AI-помощник. Задавай любые вопросы!'
          }
        ]);
      }
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };

  const registerUser = async (selectedRole: 'student' | 'teacher') => {
    if (!user) return;
    
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'register',
          user: user,
          role: selectedRole
        })
      });
      
      const data = await response.json();
      
      if (data.success) {
        setRole(selectedRole);
        setShowRegistration(false);
        setMessages([
          {
            role: 'assistant',
            content: 'Отлично! Регистрация завершена. Задавай любые вопросы!'
          }
        ]);
      }
    } catch (error) {
      console.error('Error registering user:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || loading || !user) return;

    const userMessage: Message = {
      role: 'user',
      content: inputMessage
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'send_message',
          telegram_id: user.id,
          message: inputMessage
        })
      });
      
      const data = await response.json();
      
      const aiMessage: Message = {
        role: 'assistant',
        content: data.response
      };
      
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Извините, произошла ошибка. Попробуйте еще раз.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const userName = user?.first_name || user?.username || 'Пользователь';
  const roleIcon = role === 'teacher' ? 'GraduationCap' : 'BookOpen';
  const roleText = role === 'teacher' ? 'Преподаватель' : 'Ученик';

  // Экран регистрации
  if (showRegistration) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-2xl">
          <CardHeader className="text-center">
            <div className="mx-auto mb-4 w-20 h-20 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
              <Icon name="Sparkles" size={40} className="text-white" />
            </div>
            <CardTitle className="text-2xl">Добро пожаловать в AnyaGPT!</CardTitle>
            <CardDescription>
              Выберите свою роль для начала работы
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button
              onClick={() => registerUser('student')}
              className="w-full h-20 text-lg bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
            >
              <Icon name="BookOpen" size={24} className="mr-3" />
              Я ученик
            </Button>
            <Button
              onClick={() => registerUser('teacher')}
              className="w-full h-20 text-lg bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600"
            >
              <Icon name="GraduationCap" size={24} className="mr-3" />
              Я преподаватель
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Главный экран с чатом
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-pink-50">
      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-10 shadow-sm">
        <div className="container mx-auto px-4 py-4">
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

      {/* Chat */}
      <div className="container mx-auto px-4 py-6 max-w-4xl">
        <Card className="shadow-lg">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Icon name="MessageCircle" size={24} />
              Чат с YandexGPT
            </CardTitle>
            <CardDescription>
              Задавай вопросы и получай ответы от AI
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[500px] pr-4 mb-4">
              <div className="space-y-4">
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex gap-3 ${
                      msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                    }`}
                  >
                    <Avatar className={`h-8 w-8 flex-shrink-0 ${
                      msg.role === 'user' 
                        ? 'bg-gradient-to-br from-blue-500 to-purple-500' 
                        : 'bg-gradient-to-br from-pink-500 to-orange-500'
                    }`}>
                      <AvatarFallback className="text-white text-sm">
                        {msg.role === 'user' ? 'Я' : 'AI'}
                      </AvatarFallback>
                    </Avatar>
                    <div
                      className={`rounded-2xl px-4 py-3 max-w-[80%] ${
                        msg.role === 'user'
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-900'
                      }`}
                    >
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex gap-3">
                    <Avatar className="h-8 w-8 bg-gradient-to-br from-pink-500 to-orange-500">
                      <AvatarFallback className="text-white text-sm">AI</AvatarFallback>
                    </Avatar>
                    <div className="bg-gray-100 rounded-2xl px-4 py-3">
                      <div className="flex gap-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>

            {/* Input */}
            <div className="flex gap-2">
              <Textarea
                placeholder="Напиши сообщение..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                className="resize-none"
                rows={2}
              />
              <Button
                onClick={sendMessage}
                disabled={!inputMessage.trim() || loading}
                size="icon"
                className="h-auto bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600"
              >
                <Icon name="Send" size={20} />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
