import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import funcUrls from '../../backend/func2url.json';
import AssignWords from '@/components/teacher/AssignWords';
import MyWords from '@/components/student/MyWords';

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

interface Student {
  telegram_id: number;
  username?: string;
  first_name?: string;
  last_name?: string;
  created_at?: string;
}

export default function Dashboard() {
  const [user, setUser] = useState<TelegramUser | null>(null);
  const [role, setRole] = useState<'student' | 'teacher' | null>(null);
  const [promocode, setPromocode] = useState<string | null>(null);
  const [teacherId, setTeacherId] = useState<number | null>(null);
  const [promocodeInput, setPromocodeInput] = useState('');
  const [students, setStudents] = useState<Student[]>([]);
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
        if (data.user.promocode) {
          setPromocode(data.user.promocode);
        }
        if (data.user.teacher_id) {
          setTeacherId(data.user.teacher_id);
        }
        if (data.user.role === 'teacher') {
          loadStudents(telegramId);
        }
      }
    } catch (error) {
      console.error('Error checking user:', error);
      setError('Ошибка загрузки данных');
    }
  };

  const selectRole = async (newRole: 'student' | 'teacher') => {
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
      
      if (data.success && data.user) {
        setRole(data.user.role);
        if (data.user.promocode) {
          setPromocode(data.user.promocode);
        }
        if (data.user.teacher_id) {
          setTeacherId(data.user.teacher_id);
        }
        if (data.user.role === 'teacher' && user) {
          loadStudents(user.id);
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

  const loadStudents = async (teacherId: number) => {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'get_students',
          telegram_id: teacherId
        })
      });
      
      const data = await response.json();
      
      if (data.students) {
        setStudents(data.students);
      }
    } catch (error) {
      console.error('Error loading students:', error);
    }
  };

  const bindTeacher = async () => {
    if (!user || !promocodeInput.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'bind_teacher',
          telegram_id: user.id,
          promocode: promocodeInput.trim().toUpperCase()
        })
      });
      
      const data = await response.json();
      
      if (data.success && data.user) {
        setTeacherId(data.user.teacher_id);
        setPromocodeInput('');
        const tg = window.Telegram?.WebApp;
        if (tg) {
          tg.showAlert('Преподаватель успешно привязан!');
        }
      } else {
        const tg = window.Telegram?.WebApp;
        if (tg) {
          tg.showAlert(data.error || 'Ошибка при привязке преподавателя');
        }
      }
    } catch (error) {
      console.error('Error binding teacher:', error);
      const tg = window.Telegram?.WebApp;
      if (tg) {
        tg.showAlert('Ошибка сети');
      }
    } finally {
      setLoading(false);
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
  const roleIcon = role === 'teacher' ? 'GraduationCap' : 'BookOpen';
  const roleText = role === 'teacher' ? 'Преподаватель' : 'Ученик';

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 font-sans">
      <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-10">
        <div className="px-5 py-5">
          <div className="flex items-center gap-4">
            <Avatar className="h-14 w-14 bg-gradient-to-br from-blue-500 to-indigo-600 ring-2 ring-blue-200">
              <AvatarFallback className="text-white text-xl font-bold">
                {userName.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div>
              <h1 className="font-bold text-2xl text-gray-900">
                {userName}
              </h1>
              {role && (
                <Badge 
                  className="flex items-center gap-1.5 w-fit mt-1.5 bg-blue-100 text-blue-700 border-blue-300"
                >
                  <Icon name={roleIcon} size={14} />
                  <span className="text-sm font-medium">{roleText}</span>
                </Badge>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="px-5 py-6 space-y-5">
        {role === null && (
          <Card className="border-2 border-blue-300 shadow-lg">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2.5 text-xl font-bold text-gray-900">
                <Icon name="UserCog" size={24} />
                Выбери свою роль
              </CardTitle>
              <CardDescription className="text-base text-gray-600">
                Это всегда можно изменить в любой момент
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <Button
                onClick={() => selectRole('student')}
                disabled={loading}
                className="h-16 text-lg font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-md transition-all"
              >
                <Icon name="BookOpen" size={22} className="mr-2" />
                Я ученик
              </Button>
              <Button
                onClick={() => selectRole('teacher')}
                disabled={loading}
                className="h-16 text-lg font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-md transition-all"
              >
                <Icon name="GraduationCap" size={22} className="mr-2" />
                Я преподаватель
              </Button>
            </CardContent>
          </Card>
        )}

        {role === 'student' && !teacherId && (
          <Card className="border-2 border-blue-300 shadow-lg">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2.5 text-xl font-bold text-gray-900">
                <Icon name="UserPlus" size={24} />
                Привязать преподавателя
              </CardTitle>
              <CardDescription className="text-base text-gray-600">
                Введи промокод от своего преподавателя
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <input
                type="text"
                value={promocodeInput}
                onChange={(e) => setPromocodeInput(e.target.value.toUpperCase())}
                placeholder="Например: ABC12345"
                className="w-full h-12 px-4 text-lg font-mono border-2 border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none transition-colors"
                maxLength={8}
              />
              <Button
                onClick={bindTeacher}
                disabled={loading || !promocodeInput.trim()}
                className="w-full h-12 text-base font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-md transition-all"
              >
                <Icon name="Link" size={20} className="mr-2" />
                Привязать
              </Button>
            </CardContent>
          </Card>
        )}

        {role === 'student' && teacherId && (
          <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-300 shadow-lg">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2.5 text-xl font-bold text-gray-900">
                <Icon name="CheckCircle" size={24} className="text-green-600" />
                Преподаватель привязан
              </CardTitle>
              <CardDescription className="text-base text-gray-700">
                Ты успешно привязан к преподавателю
              </CardDescription>
            </CardHeader>
          </Card>
        )}

        {role && (
          <Card className="border-2 border-gray-200 shadow-lg">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2.5 text-xl font-bold text-gray-900">
                <Icon name="Settings" size={24} />
                Настройки
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Button
                onClick={() => {
                  setRole(null);
                  setPromocode(null);
                  setTeacherId(null);
                }}
                variant="outline"
                className="w-full h-12 text-base font-semibold border-2 hover:bg-gray-50 transition-all"
              >
                <Icon name="RefreshCw" size={20} className="mr-2" />
                Сменить роль
              </Button>
            </CardContent>
          </Card>
        )}

        {role === 'teacher' && promocode && (
          <Card className="bg-gradient-to-br from-indigo-50 to-purple-50 border-2 border-indigo-300 shadow-lg">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-2.5 text-xl font-bold text-gray-900">
                <Icon name="Tag" size={24} />
                Твой промокод
              </CardTitle>
              <CardDescription className="text-base text-gray-700">
                Делись им с учениками для доступа к курсу
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-white rounded-xl p-6 border-2 border-indigo-400 shadow-inner">
                <p className="text-3xl font-bold text-center text-indigo-700 tracking-widest">
                  {promocode}
                </p>
              </div>
              <Button
                onClick={copyPromocode}
                className="w-full h-14 text-lg font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-md transition-all"
              >
                <Icon name="Copy" size={20} className="mr-2" />
                Скопировать промокод
              </Button>
            </CardContent>
          </Card>
        )}

        {role === 'student' && teacherId && user && (
          <MyWords studentId={user.id} />
        )}

        {role === 'student' && !teacherId && (
          <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-300 shadow-lg">
            <CardContent className="pt-5 pb-5">
              <div className="flex items-start gap-4">
                <div className="bg-green-100 p-2.5 rounded-full">
                  <Icon name="Check" size={24} className="text-green-600" />
                </div>
                <div>
                  <p className="font-bold text-lg text-gray-900 mb-2">Твоя роль: Ученик</p>
                  <p className="text-base text-gray-700 leading-relaxed">
                    Задавай вопросы боту прямо в чате Telegram. Если у тебя есть промокод от учителя, отправь его боту для доступа к курсу.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {role === 'teacher' && (
          <>
            <Card className="border-2 border-indigo-300 shadow-lg">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-2.5 text-xl font-bold text-gray-900">
                  <Icon name="Users" size={24} />
                  Мои ученики
                  <Badge className="ml-auto bg-indigo-100 text-indigo-700">
                    {students.length}
                  </Badge>
                </CardTitle>
                <CardDescription className="text-base text-gray-600">
                  Ученики, которые привязали твой промокод
                </CardDescription>
              </CardHeader>
              <CardContent>
                {students.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Icon name="UserX" size={48} className="mx-auto mb-3 opacity-50" />
                    <p className="text-base">Пока нет учеников</p>
                    <p className="text-sm mt-1">Поделись промокодом с учениками</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {students.map((student) => {
                      const studentName = student.first_name || student.username || 'Ученик';
                      const studentUsername = student.username ? `@${student.username}` : null;
                      
                      return (
                        <div
                          key={student.telegram_id}
                          className="flex items-center gap-3 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200 hover:shadow-md transition-shadow"
                        >
                          <Avatar className="h-12 w-12 bg-gradient-to-br from-blue-500 to-indigo-600 ring-2 ring-blue-200">
                            <AvatarFallback className="text-white text-lg font-bold">
                              {studentName.charAt(0).toUpperCase()}
                            </AvatarFallback>
                          </Avatar>
                          <div className="flex-1">
                            <p className="font-semibold text-gray-900 text-base">{studentName}</p>
                            {studentUsername && (
                              <p className="text-sm text-gray-600">{studentUsername}</p>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>

            {user && <AssignWords teacherId={user.id} />}
          </>
        )}

        {role === null && (
          <Card className="bg-white border border-gray-200 shadow-lg">
            <CardContent className="pt-5 pb-5">
              <div className="flex items-start gap-4">
                <div className="bg-yellow-100 p-2.5 rounded-full">
                  <Icon name="Sparkles" size={24} className="text-yellow-600" />
                </div>
                <div>
                  <p className="font-bold text-lg text-gray-900 mb-2">Добро пожаловать!</p>
                  <p className="text-base text-gray-700 leading-relaxed">
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