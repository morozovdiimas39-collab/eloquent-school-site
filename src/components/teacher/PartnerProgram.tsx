import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import Icon from '@/components/ui/icon';
import funcUrls from '../../../backend/func2url.json';

const API_URL = funcUrls['webapp-api'];

interface PartnerStats {
  total_students: number;
  active_students: number;
  total_earnings: number;
  current_balance: number;
  phone: string | null;
  card_number: string | null;
  bank_name: string | null;
  commission_rate: number;
}

interface PartnerProgramProps {
  teacherId: number;
}

export default function PartnerProgram({ teacherId }: PartnerProgramProps) {
  const [stats, setStats] = useState<PartnerStats | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadStats();
  }, [teacherId]);

  const loadStats = async () => {
    setLoading(true);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'get_partner_stats',
          telegram_id: teacherId
        })
      });

      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Ошибка загрузки статистики:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !stats) {
    return <div className="flex items-center justify-center p-8">Загрузка...</div>;
  }

  if (!stats) return null;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Icon name="TrendingUp" className="h-5 w-5" />
            Партнерская программа
          </CardTitle>
          <CardDescription>
            Получайте {stats.commission_rate}% с каждой оплаты ваших учеников
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">{stats.total_students}</div>
                <p className="text-xs text-muted-foreground">Всего учеников</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">{stats.active_students}</div>
                <p className="text-xs text-muted-foreground">С подпиской</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">{stats.total_earnings.toFixed(2)} ₽</div>
                <p className="text-xs text-muted-foreground">Всего заработано</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold text-green-600">{stats.current_balance.toFixed(2)} ₽</div>
                <p className="text-xs text-muted-foreground">Текущий баланс</p>
              </CardContent>
            </Card>
          </div>

          <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <Icon name="Info" className="h-5 w-5 text-blue-600 mt-0.5" />
                <div className="space-y-2 text-sm">
                  <p className="font-medium">Как работает партнерская программа?</p>
                  <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                    <li>Вы получаете {stats.commission_rate}% с каждого платежа ученика</li>
                    <li>Деньги приходят на баланс автоматически после оплаты</li>
                    <li>Платежные данные можно настроить в настройках профиля (кнопка с шестеренкой справа вверху)</li>
                  </ul>
                  <div className="flex items-center gap-2 mt-3 pt-3 border-t border-blue-200 dark:border-blue-800">
                    <Icon name="MessageCircle" className="h-4 w-4" />
                    <span>Вопросы? Напишите в телеграм: </span>
                    <a href="https://t.me/mooz26" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline font-medium">
                      @mooz26
                    </a>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </CardContent>
      </Card>
    </div>
  );
}