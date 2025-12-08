import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import funcUrls from '../../../backend/func2url.json';

const API_URL = funcUrls['webapp-api'];

interface Achievement {
  code: string;
  title_en: string;
  title_ru: string;
  emoji: string;
  points: number;
  unlocked_at?: string;
}

interface DailyStat {
  date: string;
  messages: number;
  words: number;
  errors: number;
}

interface ProgressStatsProps {
  studentId: number;
}

export default function ProgressStats({ studentId }: ProgressStatsProps) {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<any>(null);
  const [availableAchievements, setAvailableAchievements] = useState<Achievement[]>([]);

  useEffect(() => {
    loadStats();
    loadAvailableAchievements();
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
      setStats(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableAchievements = async () => {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'get_available_achievements'
        })
      });

      const data = await response.json();
      setAvailableAchievements(data.achievements || []);
    } catch (error) {
      console.error(error);
    }
  };

  if (loading) {
    return (
      <Card className="border border-gray-200 shadow-sm">
        <CardContent className="pt-8">
          <div className="flex justify-center">
            <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!stats) return null;

  const unlockedCodes = new Set(stats.achievements?.map((a: Achievement) => a.code) || []);

  return (
    <div className="space-y-4">
      {/* Words Progress */}
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg font-bold">
            <Icon name="BookOpen" size={20} />
            Слова
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Всего слов</span>
              <Badge className="bg-blue-100 text-blue-700 text-sm font-bold">
                {stats.total_words}
              </Badge>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2">
                  <span className="w-3 h-3 bg-gray-300 rounded-full"></span>
                  Новые
                </span>
                <span className="font-semibold">{stats.new}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2">
                  <span className="w-3 h-3 bg-yellow-400 rounded-full"></span>
                  Изучаю
                </span>
                <span className="font-semibold">{stats.learning}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2">
                  <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
                  Выучил
                </span>
                <span className="font-semibold">{stats.learned}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2">
                  <span className="w-3 h-3 bg-green-500 rounded-full"></span>
                  Освоил
                </span>
                <span className="font-semibold">{stats.mastered}</span>
              </div>
            </div>
            <div className="pt-2 border-t">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">Средний прогресс</span>
                <span className="font-bold text-blue-600">{Math.round(stats.average_mastery)}%</span>
              </div>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-green-500 h-2 rounded-full transition-all"
                  style={{ width: `${Math.round(stats.average_mastery)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Daily Stats */}
      {stats.daily_stats && stats.daily_stats.length > 0 && (
        <Card className="border border-gray-200 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg font-bold">
              <Icon name="BarChart3" size={20} />
              Активность за неделю
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {stats.daily_stats.map((day: DailyStat) => {
                const date = new Date(day.date);
                const dayName = date.toLocaleDateString('ru-RU', { weekday: 'short' });
                const maxMessages = Math.max(...stats.daily_stats.map((d: DailyStat) => d.messages));
                const barWidth = maxMessages > 0 ? (day.messages / maxMessages) * 100 : 0;

                return (
                  <div key={day.date} className="flex items-center gap-2">
                    <div className="w-12 text-xs text-gray-600 font-medium">{dayName}</div>
                    <div className="flex-1">
                      <div className="bg-gray-100 rounded-full h-6 relative overflow-hidden">
                        <div 
                          className="bg-gradient-to-r from-blue-500 to-indigo-500 h-6 rounded-full transition-all flex items-center justify-end px-2"
                          style={{ width: `${barWidth}%` }}
                        >
                          {day.messages > 0 && (
                            <span className="text-white text-xs font-bold">{day.messages}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Achievements */}
      <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border border-purple-200 shadow-sm">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg font-bold">
            🏆 Достижения
            <Badge className="ml-auto bg-purple-600 text-white text-sm font-bold">
              {stats.total_points} очков
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2">
            {availableAchievements.map((achievement) => {
              const isUnlocked = unlockedCodes.has(achievement.code);
              
              return (
                <div
                  key={achievement.code}
                  className={`p-3 rounded-lg border transition-all ${
                    isUnlocked
                      ? 'bg-white border-purple-300 shadow-sm'
                      : 'bg-gray-50 border-gray-200 opacity-60'
                  }`}
                >
                  <div className="text-2xl mb-1">{achievement.emoji}</div>
                  <div className="text-xs font-bold text-gray-900 leading-tight">
                    {achievement.title_ru}
                  </div>
                  <div className="text-xs text-purple-600 font-semibold mt-1">
                    {achievement.points} очков
                  </div>
                  {isUnlocked && (
                    <div className="mt-1">
                      <Badge className="bg-green-100 text-green-700 text-xs font-medium">
                        ✓ Открыто
                      </Badge>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}