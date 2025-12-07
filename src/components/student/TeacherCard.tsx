import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';

interface TeacherCardProps {
  teacherId?: number | null;
  onBindTeacher: () => void;
}

export default function TeacherCard({ teacherId, onBindTeacher }: TeacherCardProps) {
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
    window.open(`https://t.me/user?id=${teacherId}`, '_blank');
  };

  return (
    <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base font-bold">
          <Icon name="GraduationCap" size={20} className="text-green-600" />
          Мой преподаватель
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-3">
          <Avatar className="h-12 w-12 bg-gradient-to-br from-green-500 to-emerald-500 ring-2 ring-green-200">
            <AvatarFallback className="text-white text-lg font-bold">
              T
            </AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-gray-900">Преподаватель</p>
            <p className="text-xs text-gray-600">ID: {teacherId}</p>
          </div>
          <Button
            onClick={openTelegramChat}
            size="sm"
            className="bg-green-600 hover:bg-green-700 h-9 px-3"
          >
            <Icon name="MessageCircle" size={16} className="mr-1.5" />
            Написать
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
