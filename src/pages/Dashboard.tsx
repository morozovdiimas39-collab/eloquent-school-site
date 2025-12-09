import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import Icon from '@/components/ui/icon';
import { useNavigate } from 'react-router-dom';
import funcUrls from '../../backend/func2url.json';
import StudentSettings from '@/components/student/StudentSettings';
import AssignWordsDialog from '@/components/teacher/AssignWordsDialog';
import PartnerProgram from '@/components/teacher/PartnerProgram';
import TeacherSettings from '@/components/teacher/TeacherSettings';
import ImprovedMyWords from '@/components/student/ImprovedMyWords';
import TeacherCard from '@/components/student/TeacherCard';
import AchievementsDialog from '@/components/student/AchievementsDialog';
import ProgressStats from '@/components/student/ProgressStats';

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

interface Student {
  telegram_id: number;
  username?: string;
  first_name?: string;
  last_name?: string;
  created_at?: string;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState<TelegramUser | null>(null);
  const [role, setRole] = useState<'student' | 'teacher' | null>(null);
  const [promocode, setPromocode] = useState<string | null>(null);
  const [teacherId, setTeacherId] = useState<number | null>(null);
  const [promocodeInput, setPromocodeInput] = useState('');
  const [students, setStudents] = useState<Student[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [assignWordsOpen, setAssignWordsOpen] = useState(false);
  const [languageLevel, setLanguageLevel] = useState('A1');
  const [preferredTopics, setPreferredTopics] = useState<Array<{emoji: string, topic: string}>>([]);
  const [timezone, setTimezone] = useState('UTC');
  const [phone, setPhone] = useState<string | null>(null);
  const [cardNumber, setCardNumber] = useState<string | null>(null);
  const [bankName, setBankName] = useState<string | null>(null);
  const [achievementsOpen, setAchievementsOpen] = useState(false);
  const [bindTeacherOpen, setBindTeacherOpen] = useState(false);

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
        console.log('✅ User role:', data.user.role);
        setRole(data.user.role);
        if (data.user.promocode) {
          setPromocode(data.user.promocode);
        }
        if (data.user.teacher_id) {
          setTeacherId(data.user.teacher_id);
        }
        if (data.user.language_level) {
          setLanguageLevel(data.user.language_level);
        }
        if (data.user.preferred_topics) {
          setPreferredTopics(data.user.preferred_topics);
        }
        if (data.user.timezone) {
          setTimezone(data.user.timezone);
        }
        if (data.user.phone) {
          setPhone(data.user.phone);
        }
        if (data.user.card_number) {
          setCardNumber(data.user.card_number);
        }
        if (data.user.bank_name) {
          setBankName(data.user.bank_name);
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
              {role && (
                <Badge 
                  className="inline-flex items-center gap-1 mt-0.5 px-2 py-0.5 bg-blue-50 text-blue-700 border border-blue-200/50 font-medium text-xs"
                >
                  <Icon name={roleIcon} size={11} />
                  <span>{roleText}</span>
                </Badge>
              )}
            </div>
            {role && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSettingsOpen(true)}
                className="h-9 w-9 p-0 shrink-0"
              >
                <Icon name="Settings" size={18} className="text-gray-600" />
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="px-4 sm:px-6 py-5 space-y-4 max-w-3xl mx-auto">
        {role === null && (
          <Card className="border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg font-bold text-gray-900">
                <Icon name="UserCog" size={20} />
                Выбери свою роль
              </CardTitle>
              <CardDescription className="text-sm text-gray-600">
                Это всегда можно изменить в любой момент
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-2.5">
              <Button
                onClick={() => selectRole('student')}
                disabled={loading}
                className="h-14 text-base font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow transition-all"
              >
                <Icon name="BookOpen" size={18} className="mr-2" />
                Я ученик
              </Button>
              <Button
                onClick={() => selectRole('teacher')}
                disabled={loading}
                className="h-14 text-base font-semibold bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm hover:shadow transition-all"
              >
                <Icon name="GraduationCap" size={18} className="mr-2" />
                Я преподаватель
              </Button>
            </CardContent>
          </Card>
        )}

        {role === 'student' && user && (
          <>
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

            <TeacherCard 
              teacherId={teacherId} 
              onBindTeacher={() => setBindTeacherOpen(true)}
            />

            <ProgressStats studentId={user.id} />

            <ImprovedMyWords
              studentId={user.id}
              teacherId={teacherId}
              languageLevel={languageLevel}
            />
          </>
        )}

        <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Icon name="Settings" size={20} />
                Настройки
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 pt-2">
              {role === 'student' && user && (
                <StudentSettings
                  studentId={user.id}
                  currentLevel={languageLevel}
                  currentTopics={preferredTopics}
                  currentTimezone={timezone}
                  username={user.username}
                  firstName={user.first_name}
                  lastName={user.last_name}
                  photoUrl={user.photo_url}
                />
              )}
              {role === 'teacher' && user && (
                <TeacherSettings
                  teacherId={user.id}
                  username={user.username}
                  firstName={user.first_name}
                  lastName={user.last_name}
                  photoUrl={user.photo_url}
                  currentPhone={phone}
                  currentCardNumber={cardNumber}
                  currentBankName={bankName}
                />
              )}
              <div className="border-t pt-4">
                <Button
                  onClick={() => {
                    setRole(null);
                    setPromocode(null);
                    setTeacherId(null);
                    setSettingsOpen(false);
                  }}
                  variant="outline"
                  className="w-full h-11 text-sm font-medium"
                >
                  <Icon name="RefreshCw" size={16} className="mr-2" />
                  Сменить роль
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {role === 'teacher' && promocode && (
          <Card className="bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-200 shadow-sm">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg font-bold text-gray-900">
                <Icon name="Tag" size={20} />
                Твой промокод
              </CardTitle>
              <CardDescription className="text-sm text-gray-700">
                Делись им с учениками для доступа к курсу
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="bg-white rounded-xl p-5 border border-indigo-300 shadow-sm">
                <p className="text-2xl font-bold text-center text-indigo-700 tracking-widest">
                  {promocode}
                </p>
              </div>
              <Button
                onClick={copyPromocode}
                className="w-full h-12 text-base font-semibold bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow transition-all"
              >
                <Icon name="Copy" size={18} className="mr-2" />
                Скопировать промокод
              </Button>
            </CardContent>
          </Card>
        )}

        {role === 'student' && !teacherId && (
          <Card className="bg-gradient-to-br from-blue-50/50 to-indigo-50/50 border border-blue-200 shadow-sm">
            <CardContent className="pt-4 pb-4">
              <div className="flex items-start gap-3">
                <div className="bg-blue-100 p-2 rounded-lg">
                  <Icon name="Info" size={18} className="text-blue-600" />
                </div>
                <div>
                  <p className="font-semibold text-sm text-gray-900 mb-1">Твоя роль: Ученик</p>
                  <p className="text-sm text-gray-600 leading-relaxed">
                    Задавай вопросы боту прямо в чате Telegram. Если у тебя есть промокод от учителя, введи его выше.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {role === 'teacher' && (
          <>
            <Card className="border border-gray-200 shadow-sm">
              <Accordion type="single" collapsible className="w-full">
                <AccordionItem value="students" className="border-none">
                  <CardHeader className="pb-2">
                    <AccordionTrigger className="hover:no-underline py-2">
                      <CardTitle className="flex items-center gap-2 text-base font-bold text-gray-900">
                        <Icon name="Users" size={18} />
                        Мои ученики
                        <Badge className="ml-2 bg-indigo-100 text-indigo-700 text-xs font-semibold">
                          {students.length}
                        </Badge>
                      </CardTitle>
                    </AccordionTrigger>
                  </CardHeader>
                  <AccordionContent>
                    <CardContent className="pt-2 pb-4">
                      {students.length === 0 ? (
                        <div className="text-center py-4 text-sm text-gray-600 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                          <Icon name="Users" size={32} className="mx-auto mb-2 text-gray-400 opacity-40" />
                          <p className="font-medium">Пока нет учеников</p>
                          <p className="text-xs text-gray-500 mt-1">Поделись промокодом</p>
                        </div>
                      ) : (
                        <div className="space-y-1.5">
                          {students.map((student) => {
                            const studentName = student.first_name || student.username || `ID: ${student.telegram_id}`;
                            return (
                              <div
                                key={student.telegram_id}
                                className="flex items-center gap-2.5 p-2.5 rounded-lg border border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50/30 transition-all"
                              >
                                <Avatar className="h-9 w-9 bg-gradient-to-br from-blue-500 to-cyan-500 ring-1 ring-blue-200">
                                  <AvatarFallback className="text-white text-sm font-semibold">
                                    {studentName.charAt(0).toUpperCase()}
                                  </AvatarFallback>
                                </Avatar>
                                <div className="flex-1 min-w-0">
                                  <p className="font-semibold text-sm text-gray-900 truncate">{studentName}</p>
                                  {student.username && (
                                    <p className="text-xs text-gray-500 truncate">@{student.username}</p>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </CardContent>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </Card>

            <Card className="border border-indigo-200 bg-gradient-to-br from-indigo-50 to-purple-50 shadow-sm">
              <CardContent className="pt-5 pb-5">
                <Button
                  onClick={() => setAssignWordsOpen(true)}
                  className="w-full h-12 text-base font-semibold bg-indigo-600 hover:bg-indigo-700 shadow-sm"
                >
                  <Icon name="BookPlus" size={18} className="mr-2" />
                  Назначить слова ученику
                </Button>
              </CardContent>
            </Card>

            <PartnerProgram teacherId={user.id} />
          </>
        )}

        {role === null && (
          <Card className="bg-gradient-to-br from-blue-50/50 to-indigo-50/50 border border-blue-200 shadow-sm">
            <CardContent className="pt-4 pb-4">
              <div className="flex items-start gap-3">
                <div className="bg-blue-100 p-2 rounded-lg">
                  <Icon name="Sparkles" size={18} className="text-blue-600" />
                </div>
                <div>
                  <p className="font-semibold text-sm text-gray-900 mb-1">Добро пожаловать!</p>
                  <p className="text-sm text-gray-600 leading-relaxed">
                    Выбери свою роль выше, чтобы начать пользоваться ботом.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {user && role === 'student' && (
        <>
          <AchievementsDialog
            open={achievementsOpen}
            onOpenChange={setAchievementsOpen}
            studentId={user.id}
          />

          <Dialog open={bindTeacherOpen} onOpenChange={setBindTeacherOpen}>
            <DialogContent className="max-w-md">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Icon name="UserPlus" size={20} />
                  Привязать преподавателя
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-4 pt-2">
                <p className="text-sm text-gray-600">
                  Введи промокод от своего преподавателя, чтобы он мог назначать тебе слова и отслеживать прогресс
                </p>
                <input
                  type="text"
                  value={promocodeInput}
                  onChange={(e) => setPromocodeInput(e.target.value.toUpperCase())}
                  placeholder="Например: ABC12345"
                  className="w-full h-12 px-4 text-base font-mono border border-gray-300 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none transition-all"
                  maxLength={8}
                />
                <Button
                  onClick={() => {
                    bindTeacher();
                    setBindTeacherOpen(false);
                  }}
                  disabled={loading || !promocodeInput.trim()}
                  className="w-full h-12 text-base font-semibold bg-blue-600 hover:bg-blue-700"
                >
                  <Icon name="Link" size={18} className="mr-2" />
                  Привязать
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </>
      )}

      {user && role === 'teacher' && (
        <AssignWordsDialog
          open={assignWordsOpen}
          onOpenChange={setAssignWordsOpen}
          teacherId={user.id}
        />
      )}
    </div>
  );
}