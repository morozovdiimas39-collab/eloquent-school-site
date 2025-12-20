import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import { funcUrls } from '@/config/funcUrls';

const API_URL = funcUrls['webapp-api'];

const TIMEZONES = [
  { name: 'Калининград', zone: 'Europe/Kaliningrad', utc: 'UTC+2', emoji: '🏰' },
  { name: 'Москва, Санкт-Петербург', zone: 'Europe/Moscow', utc: 'UTC+3', emoji: '🏛️' },
  { name: 'Самара', zone: 'Europe/Samara', utc: 'UTC+4', emoji: '🌆' },
  { name: 'Екатеринбург', zone: 'Asia/Yekaterinburg', utc: 'UTC+5', emoji: '🏔️' },
  { name: 'Омск', zone: 'Asia/Omsk', utc: 'UTC+6', emoji: '🌄' },
  { name: 'Красноярск, Новосибирск', zone: 'Asia/Krasnoyarsk', utc: 'UTC+7', emoji: '🌲' },
  { name: 'Иркутск', zone: 'Asia/Irkutsk', utc: 'UTC+8', emoji: '🏞️' },
  { name: 'Якутск', zone: 'Asia/Yakutsk', utc: 'UTC+9', emoji: '❄️' },
  { name: 'Владивосток', zone: 'Asia/Vladivostok', utc: 'UTC+10', emoji: '🌊' },
  { name: 'Магадан', zone: 'Asia/Magadan', utc: 'UTC+11', emoji: '🦭' },
  { name: 'Камчатка', zone: 'Asia/Kamchatka', utc: 'UTC+12', emoji: '🌋' }
];

export default function TimezoneSetup() {
  const [selectedTimezone, setSelectedTimezone] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    if (!selectedTimezone) return;

    setSaving(true);
    try {
      const tg = (window as any).Telegram?.WebApp;
      const telegramId = tg?.initDataUnsafe?.user?.id;

      if (!telegramId) {
        console.error('No Telegram ID');
        setSaving(false);
        return;
      }

      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'update_student_settings',
          telegram_id: telegramId,
          timezone: selectedTimezone
        })
      });

      const data = await response.json();
      
      if (data.success) {
        setSaved(true);
        setTimeout(() => {
          if (tg) {
            tg.close();
          }
        }, 1500);
      }
    } catch (error) {
      console.error('Error saving timezone:', error);
    } finally {
      setSaving(false);
    }
  };

  if (saved) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-lg">
          <CardContent className="pt-8 pb-8 text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
              <Icon name="Check" size={32} className="text-green-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Готово!</h2>
            <p className="text-gray-600">Часовой пояс сохранен</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-6 px-4">
      <div className="max-w-2xl mx-auto">
        <Card className="shadow-lg">
          <CardHeader>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-full flex items-center justify-center">
                <Icon name="Clock" size={24} className="text-white" />
              </div>
              <div>
                <CardTitle className="text-2xl">Выбери свой часовой пояс</CardTitle>
                <CardDescription className="text-base mt-1">
                  Это нужно, чтобы Аня не будила тебя ночью 😴
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm text-gray-600 mb-4">
              Аня будет писать тебе 4-5 раз в день с 9:00 до 21:00 по твоему местному времени
            </p>
            
            <div className="grid gap-2">
              {TIMEZONES.map((tz) => (
                <Button
                  key={tz.zone}
                  onClick={() => setSelectedTimezone(tz.zone)}
                  variant={selectedTimezone === tz.zone ? 'default' : 'outline'}
                  className="w-full h-auto py-3 px-4 justify-start text-left"
                >
                  <span className="text-xl mr-3">{tz.emoji}</span>
                  <div className="flex-1">
                    <div className="font-semibold">{tz.name}</div>
                    <div className="text-xs opacity-70">{tz.utc}</div>
                  </div>
                  {selectedTimezone === tz.zone && (
                    <Icon name="Check" size={20} className="ml-2" />
                  )}
                </Button>
              ))}
            </div>

            <Button
              onClick={handleSave}
              disabled={!selectedTimezone || saving}
              className="w-full h-12 text-base font-semibold mt-6"
            >
              {saving ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Сохраняю...
                </>
              ) : (
                <>
                  <Icon name="Save" size={20} className="mr-2" />
                  Сохранить
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}