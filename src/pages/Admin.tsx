import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
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
}

interface Teacher extends User {
  students_count?: number;
}

const API_URL = funcUrls['webapp-api'];

export default function Admin() {
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [students, setStudents] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'teachers' | 'students' | 'vocabulary'>('teachers');

  useEffect(() => {
    loadData();
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

      const teachersData = await teachersRes.json();
      const studentsData = await studentsRes.json();

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
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center">
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2 flex items-center gap-3">
            <Icon name="Shield" size={36} className="text-blue-600" />
            Панель администратора
          </h1>
          <p className="text-gray-600 text-lg">Управление преподавателями и учениками</p>
        </div>

        <div className="mb-6 flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <Input
              type="text"
              placeholder="Поиск по имени, username или промокоду..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-12 text-base"
            />
          </div>
          <div className="flex gap-2 flex-wrap">
            <Button
              onClick={() => setActiveTab('teachers')}
              variant={activeTab === 'teachers' ? 'default' : 'outline'}
              className="flex-1 sm:flex-none h-12"
            >
              <Icon name="GraduationCap" size={20} className="mr-2" />
              Преподаватели ({teachers.length})
            </Button>
            <Button
              onClick={() => setActiveTab('students')}
              variant={activeTab === 'students' ? 'default' : 'outline'}
              className="flex-1 sm:flex-none h-12"
            >
              <Icon name="BookOpen" size={20} className="mr-2" />
              Ученики ({students.length})
            </Button>
            <Button
              onClick={() => setActiveTab('vocabulary')}
              variant={activeTab === 'vocabulary' ? 'default' : 'outline'}
              className="flex-1 sm:flex-none h-12"
            >
              <Icon name="Book" size={20} className="mr-2" />
              Словарь
            </Button>
          </div>
        </div>

        {activeTab === 'teachers' && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredTeachers.map((teacher) => {
              const teacherName = teacher.first_name || teacher.username || 'Преподаватель';
              const teacherUsername = teacher.username ? `@${teacher.username}` : null;

              return (
                <Card key={teacher.telegram_id} className="border-2 border-indigo-200 shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-center gap-3">
                      <Avatar className="h-14 w-14 bg-gradient-to-br from-indigo-500 to-purple-600 ring-2 ring-indigo-200">
                        <AvatarFallback className="text-white text-xl font-bold">
                          {teacherName.charAt(0).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1">
                        <CardTitle className="text-lg">{teacherName}</CardTitle>
                        {teacherUsername && (
                          <p className="text-sm text-gray-600">{teacherUsername}</p>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Промокод:</span>
                      <Badge className="bg-indigo-100 text-indigo-700 font-mono text-sm">
                        {teacher.promocode || 'Нет'}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Учеников:</span>
                      <Badge className="bg-blue-100 text-blue-700">
                        {teacher.students_count || 0}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">ID:</span>
                      <span className="text-sm font-mono text-gray-900">{teacher.telegram_id}</span>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
            {filteredTeachers.length === 0 && (
              <div className="col-span-full">
                <Card className="border-2 border-dashed border-gray-300">
                  <CardContent className="py-12 text-center">
                    <Icon name="Search" size={48} className="mx-auto mb-4 text-gray-400" />
                    <p className="text-gray-600 text-lg">Преподаватели не найдены</p>
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
                <Card key={student.telegram_id} className="border-2 border-blue-200 shadow-lg hover:shadow-xl transition-shadow">
                  <CardHeader className="pb-3">
                    <div className="flex items-center gap-3">
                      <Avatar className="h-14 w-14 bg-gradient-to-br from-blue-500 to-cyan-600 ring-2 ring-blue-200">
                        <AvatarFallback className="text-white text-xl font-bold">
                          {studentName.charAt(0).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex-1">
                        <CardTitle className="text-lg">{studentName}</CardTitle>
                        {studentUsername && (
                          <p className="text-sm text-gray-600">{studentUsername}</p>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">Преподаватель:</span>
                      {teacherInfo ? (
                        <Badge className="bg-green-100 text-green-700">
                          {teacherInfo.first_name || teacherInfo.username || 'Есть'}
                        </Badge>
                      ) : (
                        <Badge className="bg-gray-100 text-gray-600">
                          Нет
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600">ID:</span>
                      <span className="text-sm font-mono text-gray-900">{student.telegram_id}</span>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
            {filteredStudents.length === 0 && (
              <div className="col-span-full">
                <Card className="border-2 border-dashed border-gray-300">
                  <CardContent className="py-12 text-center">
                    <Icon name="Search" size={48} className="mx-auto mb-4 text-gray-400" />
                    <p className="text-gray-600 text-lg">Ученики не найдены</p>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        )}

        {activeTab === 'vocabulary' && (
          <VocabularyManager />
        )}
      </div>
    </div>
  );
}