import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import Icon from '@/components/ui/icon';
import funcUrls from '../../backend/func2url.json';
import VocabularyManager from '@/components/admin/VocabularyManager';

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
}

interface Teacher extends User {
  students_count?: number;
  phone?: string;
  card_number?: string;
  bank_name?: string;
}

const API_URL = funcUrls['webapp-api'];
const SCHEDULER_URL = funcUrls['practice-scheduler'];

export default function Admin() {
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [students, setStudents] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'teachers' | 'students' | 'vocabulary' | 'analytics'>('teachers');
  const [selectedTeacher, setSelectedTeacher] = useState<Teacher | null>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [schedulerRunning, setSchedulerRunning] = useState(false);
  const [schedulerResult, setSchedulerResult] = useState<any>(null);

  useEffect(() => {
    loadData();
    loadAnalytics();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [teachersRes, studentsRes] = await Promise.all([
        fetch(API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'get_all_teachers' })
        }),
        fetch(API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ action: 'get_all_students' })
        })
      ]);

      console.log('Teachers response status:', teachersRes.status);
      console.log('Students response status:', studentsRes.status);

      const teachersData = await teachersRes.json();
      const studentsData = await studentsRes.json();

      console.log('Teachers data:', teachersData);
      console.log('Students data:', studentsData);

      if (teachersData.teachers) {
        setTeachers(teachersData.teachers);
      }
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
        body: JSON.stringify({ action: 'get_analytics' })
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

  const filteredTeachers = teachers.filter(t => {
    const searchLower = searchQuery.toLowerCase();
    return (
      t.first_name?.toLowerCase().includes(searchLower) ||
      t.username?.toLowerCase().includes(searchLower) ||
      t.promocode?.toLowerCase().includes(searchLower)
    );
  });

  const filteredStudents = students.filter(s => {
    const searchLower = searchQuery.toLowerCase();
    return (
      s.first_name?.toLowerCase().includes(searchLower) ||
      s.username?.toLowerCase().includes(searchLower)
    );
  });

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
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-1 flex items-center gap-2.5">
            <Icon name="Shield" size={28} className="text-blue-600" />
            Панель администратора
          </h1>
          <p className="text-gray-600 text-base">Управление преподавателями и учениками</p>
        </div>

        <div className="mb-5 flex flex-col sm:flex-row gap-3">
          <div className="flex-1">
            <Input
              type="text"
              placeholder="Поиск по имени, username или промокоду..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-11 text-sm"
            />
          </div>
          <div className="flex gap-2 flex-wrap">
            <Button
              onClick={() => setActiveTab('teachers')}
              variant={activeTab === 'teachers' ? 'default' : 'outline'}
              className="flex-1 sm:flex-none h-11 text-sm font-medium"
            >
              <Icon name="GraduationCap" size={16} className="mr-1.5" />
              Преподаватели ({teachers.length})
            </Button>
            <Button
              onClick={() => setActiveTab('students')}
              variant={activeTab === 'students' ? 'default' : 'outline'}
              className="flex-1 sm:flex-none h-11 text-sm font-medium"
            >
              <Icon name="BookOpen" size={16} className="mr-1.5" />
              Ученики ({students.length})
            </Button>
            <Button
              onClick={() => setActiveTab('vocabulary')}
              variant={activeTab === 'vocabulary' ? 'default' : 'outline'}
              className="flex-1 sm:flex-none h-11 text-sm font-medium"
            >
              <Icon name="Book" size={16} className="mr-1.5" />
              Словарь
            </Button>
            <Button
              onClick={() => setActiveTab('analytics')}
              variant={activeTab === 'analytics' ? 'default' : 'outline'}
              className="flex-1 sm:flex-none h-11 text-sm font-medium"
            >
              <Icon name="BarChart3" size={16} className="mr-1.5" />
              Финансы
            </Button>
          </div>
        </div>

        {activeTab === 'teachers' && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredTeachers.map((teacher) => {
              const teacherName = teacher.first_name || teacher.username || 'Преподаватель';
              const teacherUsername = teacher.username ? `@${teacher.username}` : null;

              return (
                <Card key={teacher.telegram_id} className="border border-indigo-200 shadow-sm hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-center gap-3">
                      <Avatar className="h-12 w-12 bg-gradient-to-br from-indigo-600 to-purple-600 ring-2 ring-indigo-500/20 shadow-sm">
                        {teacher.photo_url && <AvatarImage src={teacher.photo_url} alt={teacherName} />}
                        <AvatarFallback className="text-white text-base font-semibold">
                          {teacherName.charAt(0).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-base font-bold truncate">{teacherName}</CardTitle>
                        {teacherUsername && (
                          <p className="text-xs text-gray-500 truncate">{teacherUsername}</p>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-600">Промокод:</span>
                      <Badge className="bg-indigo-100 text-indigo-700 font-mono text-xs font-semibold">
                        {teacher.promocode || 'Нет'}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-600">Учеников:</span>
                      <Badge className="bg-blue-100 text-blue-700 text-xs font-semibold">
                        {teacher.students_count || 0}
                      </Badge>
                    </div>
                    {teacher.phone && (
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-600">Телефон:</span>
                        <span className="text-xs text-gray-700">{teacher.phone}</span>
                      </div>
                    )}
                    {teacher.card_number && (
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-600">Карта:</span>
                        <span className="text-xs font-mono text-gray-700">{teacher.card_number}</span>
                      </div>
                    )}
                    {teacher.bank_name && (
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-600">Банк:</span>
                        <span className="text-xs text-gray-700">{teacher.bank_name}</span>
                      </div>
                    )}
                    <div className="flex items-center justify-between pt-1 border-t">
                      <span className="text-xs text-gray-600">ID:</span>
                      <span className="text-xs font-mono text-gray-700">{teacher.telegram_id}</span>
                    </div>
                    <Button
                      onClick={() => setSelectedTeacher(teacher)}
                      variant="outline"
                      size="sm"
                      className="w-full mt-2 h-9 text-xs"
                    >
                      <Icon name="Eye" size={14} className="mr-1.5" />
                      Подробнее
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
            {filteredTeachers.length === 0 && (
              <div className="col-span-full">
                <Card className="border-2 border-dashed border-gray-300">
                  <CardContent className="py-8 text-center">
                    <Icon name="Search" size={40} className="mx-auto mb-3 text-gray-400 opacity-50" />
                    <p className="text-gray-600 text-sm font-medium">Преподаватели не найдены</p>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        )}

        {activeTab === 'students' && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredStudents.map((student) => {
              const studentName = student.first_name || student.username || 'Ученик';
              const studentUsername = student.username ? `@${student.username}` : null;
              const teacherInfo = student.teacher_id 
                ? teachers.find(t => t.telegram_id === student.teacher_id)
                : null;

              return (
                <Card key={student.telegram_id} className="border border-blue-200 shadow-sm hover:shadow-md transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-center gap-3">
                      <Avatar className="h-12 w-12 bg-gradient-to-br from-blue-600 to-cyan-600 ring-2 ring-blue-500/20 shadow-sm">
                        {student.photo_url && <AvatarImage src={student.photo_url} alt={studentName} />}
                        <AvatarFallback className="text-white text-base font-semibold">
                          {studentName.charAt(0).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-base font-bold truncate">{studentName}</CardTitle>
                        {studentUsername && (
                          <p className="text-xs text-gray-500 truncate">{studentUsername}</p>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-600">Преподаватель:</span>
                      {teacherInfo ? (
                        <Badge className="bg-green-100 text-green-700 text-xs font-semibold truncate max-w-[150px]">
                          {teacherInfo.first_name || teacherInfo.username || 'Есть'}
                        </Badge>
                      ) : (
                        <Badge className="bg-gray-100 text-gray-600 text-xs font-semibold">
                          Самостоятельно
                        </Badge>
                      )}
                    </div>
                    {student.language_level && (
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-600">Уровень:</span>
                        <Badge className="bg-purple-100 text-purple-700 text-xs font-semibold">
                          {student.language_level}
                        </Badge>
                      </div>
                    )}
                    {student.timezone && (
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-600">Часовой пояс:</span>
                        <span className="text-xs text-gray-700">{student.timezone}</span>
                      </div>
                    )}
                    {student.preferred_topics && student.preferred_topics.length > 0 && (
                      <div>
                        <span className="text-xs text-gray-600 block mb-1">Интересы:</span>
                        <div className="flex flex-wrap gap-1">
                          {student.preferred_topics.slice(0, 3).map((topic, idx) => (
                            <Badge key={idx} className="bg-blue-50 text-blue-700 text-xs">
                              {topic}
                            </Badge>
                          ))}
                          {student.preferred_topics.length > 3 && (
                            <Badge className="bg-gray-100 text-gray-600 text-xs">
                              +{student.preferred_topics.length - 3}
                            </Badge>
                          )}
                        </div>
                      </div>
                    )}
                    <div className="flex items-center justify-between pt-1 border-t">
                      <span className="text-xs text-gray-600">ID:</span>
                      <span className="text-xs font-mono text-gray-700">{student.telegram_id}</span>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
            {filteredStudents.length === 0 && (
              <div className="col-span-full">
                <Card className="border-2 border-dashed border-gray-300">
                  <CardContent className="py-8 text-center">
                    <Icon name="Search" size={40} className="mx-auto mb-3 text-gray-400 opacity-50" />
                    <p className="text-gray-600 text-sm font-medium">Ученики не найдены</p>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        )}

        {activeTab === 'vocabulary' && (
          <VocabularyManager />
        )}

        {activeTab === 'analytics' && analytics && (
          <div className="space-y-4">
            <Card className="border border-indigo-200 shadow-sm">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                    <Icon name="Send" size={16} className="text-indigo-600" />
                    Управление рассылкой от Ани
                  </CardTitle>
                  <Button
                    onClick={runScheduler}
                    disabled={schedulerRunning}
                    size="sm"
                    variant="outline"
                    className="h-9"
                  >
                    {schedulerRunning ? (
                      <>
                        <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin mr-2"></div>
                        Запуск...
                      </>
                    ) : (
                      <>
                        <Icon name="Play" size={16} className="mr-2" />
                        Запустить сейчас
                      </>
                    )}
                  </Button>
                </div>
              </CardHeader>
              {schedulerResult && (
                <CardContent>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                    {schedulerResult.error ? (
                      <div className="flex items-center gap-2 text-red-600">
                        <Icon name="AlertCircle" size={20} />
                        <span className="font-medium">{schedulerResult.error}</span>
                      </div>
                    ) : (
                      <>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">Отправлено сообщений:</span>
                          <Badge className="bg-green-100 text-green-700">{schedulerResult.sent}</Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">Пропущено:</span>
                          <Badge className="bg-gray-100 text-gray-700">{schedulerResult.skipped}</Badge>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-gray-600">Всего студентов:</span>
                          <Badge className="bg-blue-100 text-blue-700">{schedulerResult.total_students}</Badge>
                        </div>
                      </>
                    )}
                  </div>
                </CardContent>
              )}
            </Card>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <Card className="border border-green-200 shadow-sm">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                    <Icon name="Users" size={16} className="text-green-600" />
                    Всего подписчиков
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold text-green-700">{analytics.total_subscribers}</p>
                </CardContent>
              </Card>

            <Card className="border border-blue-200 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Icon name="UserCheck" size={16} className="text-blue-600" />
                  Активные подписчики
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold text-blue-700">{analytics.active_subscribers}</p>
              </CardContent>
            </Card>

            <Card className="border border-purple-200 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Icon name="DollarSign" size={16} className="text-purple-600" />
                  К выплате преподавателям
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold text-purple-700">{analytics.teacher_payouts.toLocaleString('ru-RU')} ₽</p>
              </CardContent>
            </Card>

            <Card className="border border-emerald-200 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Icon name="TrendingUp" size={16} className="text-emerald-600" />
                  Прибыль
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold text-emerald-700">{analytics.profit.toLocaleString('ru-RU')} ₽</p>
              </CardContent>
            </Card>
            </div>
          </div>
        )}

        {selectedTeacher && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50" onClick={() => setSelectedTeacher(null)}>
            <Card className="max-w-2xl w-full max-h-[90vh] overflow-auto" onClick={(e) => e.stopPropagation()}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Avatar className="h-16 w-16 bg-gradient-to-br from-indigo-600 to-purple-600 ring-2 ring-indigo-500/20">
                      {selectedTeacher.photo_url && <AvatarImage src={selectedTeacher.photo_url} />}
                      <AvatarFallback className="text-white text-xl font-semibold">
                        {(selectedTeacher.first_name || selectedTeacher.username || 'Т').charAt(0).toUpperCase()}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <CardTitle className="text-xl">{selectedTeacher.first_name || selectedTeacher.username || 'Преподаватель'}</CardTitle>
                      {selectedTeacher.username && (
                        <CardDescription>@{selectedTeacher.username}</CardDescription>
                      )}
                    </div>
                  </div>
                  <Button variant="ghost" size="icon" onClick={() => setSelectedTeacher(null)}>
                    <Icon name="X" size={20} />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-3">
                  <div className="flex items-center justify-between py-2 border-b">
                    <span className="text-sm font-medium text-gray-600">Telegram ID</span>
                    <span className="text-sm font-mono text-gray-900">{selectedTeacher.telegram_id}</span>
                  </div>
                  <div className="flex items-center justify-between py-2 border-b">
                    <span className="text-sm font-medium text-gray-600">Промокод</span>
                    <Badge className="bg-indigo-100 text-indigo-700 font-mono">{selectedTeacher.promocode || 'Нет'}</Badge>
                  </div>
                  <div className="flex items-center justify-between py-2 border-b">
                    <span className="text-sm font-medium text-gray-600">Количество учеников</span>
                    <Badge className="bg-blue-100 text-blue-700">{selectedTeacher.students_count || 0}</Badge>
                  </div>
                  {selectedTeacher.phone && (
                    <div className="flex items-center justify-between py-2 border-b">
                      <span className="text-sm font-medium text-gray-600">Телефон</span>
                      <a href={`tel:${selectedTeacher.phone}`} className="text-sm text-blue-600 hover:underline">
                        {selectedTeacher.phone}
                      </a>
                    </div>
                  )}
                  {selectedTeacher.card_number && (
                    <div className="flex items-center justify-between py-2 border-b">
                      <span className="text-sm font-medium text-gray-600">Номер карты</span>
                      <span className="text-sm font-mono text-gray-900">{selectedTeacher.card_number}</span>
                    </div>
                  )}
                  {selectedTeacher.bank_name && (
                    <div className="flex items-center justify-between py-2 border-b">
                      <span className="text-sm font-medium text-gray-600">Банк</span>
                      <span className="text-sm text-gray-900">{selectedTeacher.bank_name}</span>
                    </div>
                  )}
                  {selectedTeacher.created_at && (
                    <div className="flex items-center justify-between py-2">
                      <span className="text-sm font-medium text-gray-600">Дата регистрации</span>
                      <span className="text-sm text-gray-900">{new Date(selectedTeacher.created_at).toLocaleDateString('ru-RU')}</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}