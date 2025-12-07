import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import funcUrls from '../../../backend/func2url.json';

const API_URL = funcUrls['webapp-api'];

interface Achievement {
  code: string;
  title_en: string;
  title_ru: string;
  description_ru: string;
  emoji: string;
  points: number;
  unlocked_at?: string;
}

interface AchievementsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  studentId: number;
}

export default function AchievementsDialog({ open, onOpenChange, studentId }: AchievementsDialogProps) {
  const [loading, setLoading] = useState(true);
  const [unlockedAchievements, setUnlockedAchievements] = useState<Achievement[]>([]);
  const [availableAchievements, setAvailableAchievements] = useState<Achievement[]>([]);
  const [totalPoints, setTotalPoints] = useState(0);

  useEffect(() => {
    if (open) {
      loadData();
    }
  }, [open, studentId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsRes, availableRes] = await Promise.all([
        fetch(API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            action: 'get_student_progress_stats',
            student_id: studentId
          })
        }),
        fetch(API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            action: 'get_available_achievements'
          })
        })
      ]);

      const statsData = await statsRes.json();
      const availableData = await availableRes.json();

      setUnlockedAchievements(statsData.achievements || []);
      setAvailableAchievements(availableData.achievements || []);
      setTotalPoints(statsData.total_points || 0);
    } catch (error) {
      console.error('Ошибка загрузки достижений:', error);
    } finally {
      setLoading(false);
    }
  };

  const unlockedCodes = new Set(unlockedAchievements.map(a => a.code));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Icon name="Trophy" size={24} className="text-yellow-600" />
            Достижения
          </DialogTitle>
          <div className="mt-2 flex items-center gap-2">
            <Badge className="bg-gradient-to-r from-yellow-500 to-orange-500 text-white px-3 py-1">
              ⭐ {totalPoints} очков
            </Badge>
            <span className="text-sm text-muted-foreground">
              {unlockedAchievements.length} из {availableAchievements.length}
            </span>
          </div>
        </DialogHeader>

        {loading ? (
          <div className="flex justify-center py-8">
            <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : (
          <div className="space-y-3 pt-4">
            {availableAchievements.map((achievement) => {
              const isUnlocked = unlockedCodes.has(achievement.code);
              const unlockedData = unlockedAchievements.find(a => a.code === achievement.code);

              return (
                <Card
                  key={achievement.code}
                  className={`transition-all ${
                    isUnlocked
                      ? 'border-yellow-300 bg-gradient-to-r from-yellow-50 to-orange-50'
                      : 'border-gray-200 bg-gray-50/50 opacity-60'
                  }`}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start gap-3">
                      <div className="text-4xl flex-shrink-0">
                        {isUnlocked ? achievement.emoji : '🔒'}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className={`font-bold ${isUnlocked ? 'text-gray-900' : 'text-gray-500'}`}>
                            {achievement.title_ru}
                          </h3>
                          <Badge 
                            variant="secondary" 
                            className={`text-xs ${
                              isUnlocked 
                                ? 'bg-yellow-100 text-yellow-800 border-yellow-300' 
                                : 'bg-gray-100 text-gray-500'
                            }`}
                          >
                            +{achievement.points} очков
                          </Badge>
                        </div>
                        <p className={`text-sm ${isUnlocked ? 'text-gray-600' : 'text-gray-400'}`}>
                          {achievement.description_ru || achievement.title_en}
                        </p>
                        {isUnlocked && unlockedData?.unlocked_at && (
                          <p className="text-xs text-gray-500 mt-2">
                            Получено: {new Date(unlockedData.unlocked_at).toLocaleDateString('ru-RU')}
                          </p>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
