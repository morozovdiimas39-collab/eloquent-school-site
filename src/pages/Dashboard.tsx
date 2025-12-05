import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
        showAlert: (message: string) => void;
      };
    };
  }
}

const API_URL = funcUrls['webapp-api'];

export default function Dashboard() {
  const [user, setUser] = useState<TelegramUser | null>(null);
  const [role, setRole] = useState<'student' | 'teacher' | null>(null);
  const [promocode, setPromocode] = useState<string | null>(null);
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
        if (data.user.role === 'teacher' && data.user.promocode) {
          setPromocode(data.user.promocode);
        }
      }
    } catch (error) {
      console.error('Error checking user:', error);
      setError('Ошибка загрузки данных');
    }
  };

  const selectRole = async (newRole: 'student' | 'teacher') => {
    if (!user || role !== null) return;
    
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
        if (newRole === 'teacher' && data.user?.promocode) {
          setPromocode(data.user.promocode);
        }
      }
    } catch (error) {
      console.error('Error selecting role:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyPromocode = () => {
    if (promocode) {
      navigator.clipboard.writeText(promocode);
      const tg = window.Telegram?.WebApp;
      if (tg) {
        tg.showAlert('Промокод скопирован в буфер обмена!');
      }
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

  if (!user) {
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
      <div className="bg-[var(--tg-theme-secondary-bg-color,#f4f4f5)] border-b sticky top-0 z-10">
        <div className="px-4 py-4">
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

      <div className="px-4 py-4 space-y-4">
        {role === null && (
          <Card className="border-2 border-[var(--tg-theme-button-color,#3390ec)]">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Icon name="UserCog" size={20} />
                Выбери свою роль
              </CardTitle>
              <CardDescription className="text-sm">
                Выбери один раз — изменить потом нельзя
              </CardDescription>
            </CardHeader>
            <CardContent className="flex gap-2">
              <Button
                onClick={() => selectRole('student')}
                disabled={loading}
                variant="outline"
                className="flex-1 h-16 text-base hover:bg-[var(--tg-theme-button-color,#3390ec)] hover:text-white transition-colors"
              >
                <Icon name="BookOpen" size={20} className="mr-2" />
                Ученик
              </Button>
              <Button
                onClick={() => selectRole('teacher')}
                disabled={loading}
                variant="outline"
                className="flex-1 h-16 text-base hover:bg-[var(--tg-theme-button-color,#3390ec)] hover:text-white transition-colors"
              >
                <Icon name="GraduationCap" size={20} className="mr-2" />
                Учитель
              </Button>
            </CardContent>
          </Card>
        )}

        {role === 'teacher' && promocode && (
          <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Icon name="Tag" size={20} />
                Твой промокод
              </CardTitle>
              <CardDescription className="text-sm">
                Делись им с учениками для доступа к курсу
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="bg-white rounded-lg p-4 border-2 border-purple-300">
                <p className="text-2xl font-bold text-center text-purple-700 tracking-wider">
                  {promocode}
                </p>
              </div>
              <Button
                onClick={copyPromocode}
                className="w-full h-12 text-base bg-[var(--tg-theme-button-color,#3390ec)] text-[var(--tg-theme-button-text-color,#ffffff)] hover:opacity-90"
              >
                <Icon name="Copy" size={18} className="mr-2" />
                Скопировать промокод
              </Button>
            </CardContent>
          </Card>
        )}

        {role === 'student' && (
          <Card className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
            <CardContent className="pt-4 pb-4">
              <div className="flex items-start gap-3">
                <Icon name="Check" size={20} className="text-green-600 mt-0.5" />
                <div className="text-sm text-gray-700">
                  <p className="font-semibold mb-1">Твоя роль: Ученик</p>
                  <p className="text-xs text-gray-600">
                    Задавай вопросы боту прямо в чате Telegram. Если у тебя есть промокод от учителя, отправь его боту для доступа к курсу.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {role === 'teacher' && (
          <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
            <CardContent className="pt-4 pb-4">
              <div className="flex items-start gap-3">
                <Icon name="Info" size={20} className="text-purple-600 mt-0.5" />
                <div className="text-sm text-gray-700">
                  <p className="font-semibold mb-1">Как пользоваться:</p>
                  <ul className="space-y-1 text-xs text-gray-600">
                    <li>• Скопируй свой промокод выше</li>
                    <li>• Отправь его своим ученикам</li>
                    <li>• Они смогут использовать бота с твоим промокодом</li>
                    <li>• Задавай вопросы боту в Telegram</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {role === null && (
          <Card>
            <CardContent className="pt-4 pb-4">
              <div className="flex items-start gap-3">
                <Icon name="Sparkles" size={20} className="text-blue-600 mt-0.5" />
                <div className="text-sm text-gray-700">
                  <p className="font-semibold mb-1">Добро пожаловать!</p>
                  <p className="text-xs text-gray-600">
                    Выбери свою роль выше, чтобы начать пользоваться ботом. После выбора роли ты сможешь задавать вопросы прямо в чате.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
