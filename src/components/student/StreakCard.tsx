import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { funcUrls } from '@/config/funcUrls';

const API_URL = funcUrls['webapp-api'];

interface StreakCardProps {
  studentId: number;
}

export default function StreakCard({ studentId }: StreakCardProps) {
  const [loading, setLoading] = useState(true);
  const [currentStreak, setCurrentStreak] = useState(0);
  const [longestStreak, setLongestStreak] = useState(0);
  const [totalDays, setTotalDays] = useState(0);

  useEffect(() => {
    loadStats();
  }, [studentId]);

  const loadStats = async () => {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'get_student_progress_stats',
          student_id: studentId
        })
      });

      const data = await response.json();
      setCurrentStreak(data.current_streak || 0);
      setLongestStreak(data.longest_streak || 0);
      setTotalDays(data.total_practice_days || 0);
    } catch (error) {
      console.error('Ошибка загрузки streak:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="border border-gray-200 shadow-sm">
        <CardContent className="py-6">
          <div className="flex justify-center">
            <div className="w-6 h-6 border-2 border-orange-600 border-t-transparent rounded-full animate-spin"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-gradient-to-br from-orange-50 to-red-50 border border-orange-200 shadow-sm">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base font-bold">
          🔥 Streak
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-white rounded-lg p-2.5 text-center border border-orange-100">
            <div className="text-xl font-bold text-orange-600">{currentStreak}</div>
            <div className="text-xs text-gray-600 mt-0.5">Текущий</div>
          </div>
          <div className="bg-white rounded-lg p-2.5 text-center border border-orange-100">
            <div className="text-xl font-bold text-orange-600">{longestStreak}</div>
            <div className="text-xs text-gray-600 mt-0.5">Рекорд</div>
          </div>
          <div className="bg-white rounded-lg p-2.5 text-center border border-orange-100">
            <div className="text-xl font-bold text-orange-600">{totalDays}</div>
            <div className="text-xs text-gray-600 mt-0.5">Всего дней</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}