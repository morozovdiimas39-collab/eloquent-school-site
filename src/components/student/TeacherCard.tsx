import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import funcUrls from '../../../backend/func2url.json';

const API_URL = funcUrls['webapp-api'];

interface TeacherInfo {
  telegram_id: number;
  username?: string;
  first_name?: string;
  last_name?: string;
  photo_url?: string;
}

interface TeacherCardProps {
  teacherId?: number | null;
  onBindTeacher: () => void;
}

export default function TeacherCard({ teacherId, onBindTeacher }: TeacherCardProps) {
  const [teacherInfo, setTeacherInfo] = useState<TeacherInfo | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (teacherId) {
      loadTeacherInfo();
    }
  }, [teacherId]);

  const loadTeacherInfo = async () => {
    if (!teacherId) return;
    setLoading(true);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'get_teacher',
          teacher_id: teacherId
        })
      });
      const data = await response.json();
      if (data.teacher) {
        setTeacherInfo(data.teacher);
      }
    } catch (error) {
      console.error('Ошибка загрузки преподавателя:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!teacherId) {
    return (
      <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border border-purple-200 shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base font-bold">
            <Icon name="Sparkles" size={20} className="text-purple-600" />
            Самостоятельное обучение
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-gray-700">
            Ты учишь английский самостоятельно с помощью бота Аня
          </p>
          <Button
            onClick={onBindTeacher}
            variant="outline"
            size="sm"
            className="w-full h-9 text-sm border-purple-300 hover:bg-purple-50"
          >
            <Icon name="UserPlus" size={16} className="mr-2" />
            Привязать преподавателя
          </Button>
        </CardContent>
      </Card>
    );
  }

  const openTelegramChat = () => {
    const username = teacherInfo?.username;
    const url = username 
      ? `https://t.me/${username}` 
      : `tg://user?id=${teacherId}`;
    window.open(url, '_blank');
  };

  const teacherName = teacherInfo?.first_name || teacherInfo?.username || 'Преподаватель';

  return (
    <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base font-bold">
          <Icon name="GraduationCap" size={20} className="text-green-600" />
          Мой преподаватель
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-4">
            <div className="w-6 h-6 border-2 border-green-600 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : (
          <div className="flex items-start gap-3">
            <Avatar className="h-14 w-14 shrink-0 bg-gradient-to-br from-green-500 to-emerald-500 ring-2 ring-green-200">
              {teacherInfo?.photo_url && <AvatarImage src={teacherInfo.photo_url} alt={teacherName} />}
              <AvatarFallback className="text-white text-lg font-bold">
                {teacherName.charAt(0).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-gray-900 truncate">{teacherName}</p>
              {teacherInfo?.username && (
                <p className="text-xs text-gray-600">@{teacherInfo.username}</p>
              )}
              <Button
                onClick={openTelegramChat}
                size="sm"
                className="bg-green-600 hover:bg-green-700 h-9 px-3 mt-2 w-full sm:w-auto"
              >
                <Icon name="MessageCircle" size={16} className="mr-1.5" />
                Написать
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}