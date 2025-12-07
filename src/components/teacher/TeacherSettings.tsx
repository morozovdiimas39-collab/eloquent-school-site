import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import Icon from '@/components/ui/icon';
import { toast } from 'sonner';
import funcUrls from '../../../backend/func2url.json';

const API_URL = funcUrls['webapp-api'];

interface TeacherSettingsProps {
  teacherId: number;
  username?: string;
  firstName?: string;
  lastName?: string;
  photoUrl?: string;
  currentPhone?: string;
  currentCardNumber?: string;
  currentBankName?: string;
}

export default function TeacherSettings({ 
  teacherId,
  username,
  firstName,
  lastName,
  photoUrl,
  currentPhone,
  currentCardNumber,
  currentBankName
}: TeacherSettingsProps) {
  const [phone, setPhone] = useState(currentPhone || '');
  const [cardNumber, setCardNumber] = useState(currentCardNumber || '');
  const [bankName, setBankName] = useState(currentBankName || '');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setPhone(currentPhone || '');
    setCardNumber(currentCardNumber || '');
    setBankName(currentBankName || '');
  }, [currentPhone, currentCardNumber, currentBankName]);

  const savePayoutInfo = async () => {
    setSaving(true);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'update_payout_info',
          telegram_id: teacherId,
          phone,
          card_number: cardNumber,
          bank_name: bankName
        })
      });

      const data = await response.json();

      if (data.success) {
        toast.success('Платежные данные сохранены!');
      } else {
        toast.error('Ошибка сохранения');
      }
    } catch (error) {
      console.error(error);
      toast.error('Ошибка сети');
    } finally {
      setSaving(false);
    }
  };

  const displayName = [firstName, lastName].filter(Boolean).join(' ') || username || 'Пользователь';
  const initials = [firstName?.[0], lastName?.[0]].filter(Boolean).join('').toUpperCase() || username?.[0]?.toUpperCase() || 'U';

  return (
    <div className="space-y-6">
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg font-bold">
            <Icon name="User" size={20} />
            Мой профиль
          </CardTitle>
          <CardDescription className="text-sm">
            Информация о вашем аккаунте
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="flex items-center gap-4">
            <Avatar className="h-16 w-16">
              <AvatarImage src={photoUrl} alt={displayName} />
              <AvatarFallback className="bg-blue-500 text-white text-xl">
                {initials}
              </AvatarFallback>
            </Avatar>
            <div>
              <p className="font-semibold text-lg">{displayName}</p>
              {username && <p className="text-sm text-gray-500">@{username}</p>}
            </div>
          </div>

          <div className="border-t pt-4">
            <p className="text-xs text-gray-500 mb-2">
              Telegram ID: <span className="font-mono">{teacherId}</span>
            </p>
          </div>
        </CardContent>
      </Card>

      <Card className="border border-gray-200 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg font-bold">
            <Icon name="CreditCard" size={20} />
            Платежные данные
          </CardTitle>
          <CardDescription className="text-sm">
            Укажите данные для получения выплат по партнерской программе
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="phone">Номер телефона</Label>
            <Input
              id="phone"
              placeholder="+7 (999) 123-45-67"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="h-11"
            />
            <p className="text-xs text-gray-500">
              Для связи при выплатах
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="card">Номер карты</Label>
            <Input
              id="card"
              placeholder="2200 1234 5678 9012"
              value={cardNumber}
              onChange={(e) => setCardNumber(e.target.value)}
              className="h-11"
            />
            <p className="text-xs text-gray-500">
              Карта для получения выплат
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="bank">Банк</Label>
            <Input
              id="bank"
              placeholder="Сбербанк"
              value={bankName}
              onChange={(e) => setBankName(e.target.value)}
              className="h-11"
            />
            <p className="text-xs text-gray-500">
              Название банка, выпустившего карту
            </p>
          </div>

          <Button 
            onClick={savePayoutInfo} 
            disabled={saving}
            className="w-full h-11"
          >
            <Icon name="Save" className="mr-2 h-4 w-4" />
            {saving ? 'Сохранение...' : 'Сохранить платежные данные'}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
