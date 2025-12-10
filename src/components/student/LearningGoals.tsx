import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import { toast } from 'sonner';
import funcUrls from '../../../backend/func2url.json';

const API_URL = funcUrls['webapp-api'];

interface LearningGoal {
  id: number;
  goal_text: string;
  created_at: string;
  is_active: boolean;
}

interface LearningGoalsProps {
  studentId: number;
}

export default function LearningGoals({ studentId }: LearningGoalsProps) {
  const [goals, setGoals] = useState<LearningGoal[]>([]);
  const [newGoal, setNewGoal] = useState('');
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    loadGoals();
  }, [studentId]);

  const loadGoals = async () => {
    setLoading(true);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'get_learning_goals',
          student_id: studentId
        })
      });

      const data = await response.json();
      if (data.success) {
        setGoals(data.goals || []);
      }
    } catch (error) {
      console.error('Error loading goals:', error);
    } finally {
      setLoading(false);
    }
  };

  const addGoal = async () => {
    if (!newGoal.trim()) {
      toast.error('Введите цель обучения');
      return;
    }

    setAdding(true);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'add_learning_goal',
          student_id: studentId,
          goal_text: newGoal.trim()
        })
      });

      const data = await response.json();
      
      if (data.success) {
        toast.success(`Цель добавлена! Генерируем ${data.words_added} слов для изучения...`);
        setNewGoal('');
        await loadGoals();
      } else {
        toast.error(data.error || 'Ошибка добавления цели');
      }
    } catch (error) {
      console.error('Error adding goal:', error);
      toast.error('Ошибка добавления цели');
    } finally {
      setAdding(false);
    }
  };

  const removeGoal = async (goalId: number) => {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'deactivate_learning_goal',
          goal_id: goalId
        })
      });

      const data = await response.json();
      if (data.success) {
        toast.success('Цель удалена');
        await loadGoals();
      }
    } catch (error) {
      console.error('Error removing goal:', error);
      toast.error('Ошибка удаления цели');
    }
  };

  if (loading) {
    return (
      <Card className="border border-purple-200 shadow-sm bg-gradient-to-br from-purple-50 to-pink-50">
        <CardContent className="py-8">
          <div className="flex flex-col items-center gap-2">
            <div className="w-10 h-10 border-4 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-sm text-gray-600">Загрузка целей...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border border-purple-200 shadow-sm bg-gradient-to-br from-purple-50 to-pink-50">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg font-bold">
              <Icon name="Target" size={22} className="text-purple-600" />
              Мои цели обучения
            </CardTitle>
            <CardDescription className="text-sm mt-1">
              Добавь цели — получишь персональные слова для изучения
            </CardDescription>
          </div>
          <Badge className="bg-purple-600 text-white text-sm px-3 py-1 font-bold">
            {goals.length}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Input
            type="text"
            placeholder="Например: Поездка в Дубай"
            value={newGoal}
            onChange={(e) => setNewGoal(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && addGoal()}
            className="flex-1 h-11 text-sm bg-white"
          />
          <Button
            onClick={addGoal}
            disabled={adding || !newGoal.trim()}
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 h-11 px-6 text-white font-semibold"
          >
            {adding ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                Добавляю...
              </>
            ) : (
              <>
                <Icon name="Plus" size={18} className="mr-2" />
                Добавить
              </>
            )}
          </Button>
        </div>

        {goals.length === 0 ? (
          <div className="text-center py-8 bg-white rounded-lg border-2 border-dashed border-purple-200">
            <Icon name="Target" size={56} className="mx-auto mb-3 text-purple-300" />
            <p className="text-base font-semibold text-gray-700 mb-1">
              Пока нет целей
            </p>
            <p className="text-sm text-gray-500">
              Добавь свою первую цель обучения выше
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {goals.map((goal) => (
              <div
                key={goal.id}
                className="p-4 rounded-lg bg-white border border-purple-200 hover:border-purple-300 hover:shadow-sm transition-all"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Icon name="Target" size={16} className="text-purple-600 flex-shrink-0" />
                      <p className="text-base font-semibold text-gray-900">
                        {goal.goal_text}
                      </p>
                    </div>
                    <p className="text-xs text-gray-500">
                      Добавлено: {new Date(goal.created_at).toLocaleDateString('ru-RU', {
                        day: 'numeric',
                        month: 'long',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeGoal(goal.id)}
                    className="h-8 w-8 p-0 text-gray-400 hover:text-red-600 hover:bg-red-50 flex-shrink-0"
                  >
                    <Icon name="Trash2" size={16} />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="pt-3 border-t border-purple-200">
          <div className="flex items-start gap-2 text-xs text-gray-600 bg-purple-50/50 p-3 rounded-lg">
            <Icon name="Sparkles" size={14} className="text-purple-600 flex-shrink-0 mt-0.5" />
            <p>
              <strong>Как это работает:</strong> После добавления цели, ИИ автоматически подберет 5-7 подходящих английских слов и пришлет уведомление в Telegram
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
