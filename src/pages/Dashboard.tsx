import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import Icon from '@/components/ui/icon';
import { useNavigate } from 'react-router-dom';
import { funcUrls } from '@/config/funcUrls';
import StudentSettings from '@/components/student/StudentSettings';
import ImprovedMyWords from '@/components/student/ImprovedMyWords';

interface TelegramUser {
  id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
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
  const navigate = useNavigate();
  const [user, setUser] = useState<TelegramUser | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [languageLevel, setLanguageLevel] = useState('A1');
  const [preferredTopics, setPreferredTopics] = useState<Array<{emoji: string, topic: string}>>([]);
  const [timezone, setTimezone] = useState('UTC');
  const [learningGoal, setLearningGoal] = useState<string>('');
  const [learningGoalDetails, setLearningGoalDetails] = useState<string>('');

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    
    console.log('🔍 Telegram WebApp:', tg);
    console.log('🔍 initDataUnsafe:', tg?.initDataUnsafe);
    console.log('🔍 user:', tg?.initDataUnsafe?.user);
    
    if (tg) {
      tg.ready();
      tg.expand();
      
      const telegramUser = tg.initDataUnsafe.user;
      if (telegramUser) {
        console.log('✅ User found:', telegramUser);
        setUser(telegramUser);
        checkUser(telegramUser.id);
      } else {
        console.error('❌ User not found in initDataUnsafe');
        setError('Не удалось получить данные пользователя Telegram');
      }
    } else {
      console.error('❌ Telegram WebApp not found');
      setError('Откройте это приложение через Telegram');
    }
  }, []);

  const checkUser = async (telegramId: number) => {
    try {
      console.log('📡 Fetching user data for telegram_id:', telegramId);
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'get_user',
          telegram_id: telegramId
        })
      });
      
      const data = await response.json();
      console.log('📥 Received data:', data);
      
      if (data.user) {
        if (data.user.language_level) {
          setLanguageLevel(data.user.language_level);
        }
        if (data.user.preferred_topics) {
          setPreferredTopics(data.user.preferred_topics);
        }
        if (data.user.timezone) {
          setTimezone(data.user.timezone);
        }
        if (data.user.learning_goal) {
          setLearningGoal(data.user.learning_goal);
        }
        if (data.user.learning_goal_details) {
          setLearningGoalDetails(data.user.learning_goal_details);
        }
      }
    } catch (error) {
      console.error('Error checking user:', error);
      setError('Ошибка загрузки данных');
    }
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center p-5 font-sans">
        <Card className="w-full max-w-md shadow-xl">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-red-600 text-xl">
              <Icon name="AlertCircle" size={28} />
              Ошибка
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-800 text-base leading-relaxed">{error}</p>
            <p className="text-sm text-gray-600 mt-4 leading-relaxed">
              Откройте это приложение через бота в Telegram
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center p-5 font-sans">
        <Card className="w-full max-w-md shadow-xl">
          <CardContent className="pt-8">
            <div className="flex flex-col items-center gap-5">
              <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-gray-700 text-lg font-medium">Загрузка...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const userName = user.first_name || user.username || 'Пользователь';

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <div className="bg-white/80 backdrop-blur-md border-b border-gray-200/50 shadow-sm sticky top-0 z-10">
        <div className="px-4 sm:px-6 py-3">
          <div className="flex items-center gap-3">
            <Avatar className="h-11 w-11 bg-gradient-to-br from-blue-600 to-indigo-600 ring-2 ring-blue-500/20 shadow-lg">
              {user.photo_url && <AvatarImage src={user.photo_url} alt={userName} />}
              <AvatarFallback className="text-white text-base font-semibold">
                {userName.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <h1 className="font-bold text-lg text-gray-900 truncate">
                {userName}
              </h1>
              <Badge 
                className="inline-flex items-center gap-1 mt-0.5 px-2 py-0.5 bg-blue-50 text-blue-700 border border-blue-200/50 font-medium text-xs"
              >
                <Icon name="BookOpen" size={11} />
                <span>Ученик</span>
              </Badge>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSettingsOpen(true)}
              className="h-9 w-9 p-0 shrink-0"
            >
              <Icon name="Settings" size={18} className="text-gray-600" />
            </Button>
          </div>
        </div>
      </div>

      <div className="px-4 sm:px-6 py-5 space-y-4 max-w-3xl mx-auto">
        <Card className="border border-indigo-200 shadow-sm bg-gradient-to-br from-indigo-50 to-purple-50">
          <CardContent className="pt-5 pb-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center shadow-lg">
                  <Icon name="Crown" size={24} className="text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 text-base">Бесплатный план</h3>
                  <p className="text-sm text-gray-600">20 сообщений в день</p>
                </div>
              </div>
              <Button
                onClick={() => navigate('/pricing')}
                variant="default"
                className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 font-semibold"
              >
                Улучшить
                <Icon name="ArrowRight" size={16} className="ml-2" />
              </Button>
            </div>
          </CardContent>
        </Card>

        <ImprovedMyWords
          studentId={user.id}
          languageLevel={languageLevel}
        />

        <div className="mt-8 pt-6 pb-2 border-t border-gray-200 text-center">
          <a 
            href="https://anyagpt-dev.ru/oferta" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Публичная оферта
          </a>
        </div>
      </div>

      <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Icon name="Settings" size={20} />
              Настройки
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-2">
            {user && (
              <StudentSettings
                studentId={user.id}
                currentLevel={languageLevel}
                currentTopics={preferredTopics}
                currentTimezone={timezone}
                currentLearningGoal={learningGoal}
                currentLearningGoalDetails={learningGoalDetails}
                username={user.username}
                firstName={user.first_name}
                lastName={user.last_name}
                photoUrl={user.photo_url}
              />
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}