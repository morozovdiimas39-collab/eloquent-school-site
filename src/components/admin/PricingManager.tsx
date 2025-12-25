import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import Icon from '@/components/ui/icon';
import { funcUrls } from '@/config/funcUrls';

interface PricingPlan {
  key: string;
  name: string;
  description: string;
  price_rub: number;
  duration_days: number;
}

const API_URL = funcUrls['webapp-api'];

export default function PricingManager() {
  const [plans, setPlans] = useState<PricingPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editingPlan, setEditingPlan] = useState<string | null>(null);

  useEffect(() => {
    loadPlans();
  }, []);

  const loadPlans = async () => {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'get_pricing_plans'
        })
      });

      const data = await response.json();
      if (data.success && data.plans) {
        setPlans(data.plans);
      }
    } catch (error) {
      console.error('Failed to load pricing plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const savePlan = async (plan: PricingPlan) => {
    setSaving(true);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'update_pricing_plan',
          plan: plan
        })
      });

      const data = await response.json();
      if (data.success) {
        await loadPlans();
        setEditingPlan(null);
      } else {
        alert('Ошибка сохранения: ' + (data.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Failed to save plan:', error);
      alert('Ошибка сохранения');
    } finally {
      setSaving(false);
    }
  };

  const updatePlanField = (key: string, field: keyof PricingPlan, value: any) => {
    setPlans(plans.map(p => 
      p.key === key ? { ...p, [field]: value } : p
    ));
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-8">
            <Icon name="Loader2" className="animate-spin text-gray-400" size={32} />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Icon name="DollarSign" size={24} />
            Управление ценами тарифов
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <div className="flex items-start gap-3">
              <Icon name="Info" size={20} className="text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-blue-900">
                <p className="font-medium mb-1">Изменения применяются сразу</p>
                <p className="text-blue-700">
                  После сохранения новые цены будут отображаться в боте и на сайте. 
                  Не забудь синхронизировать backend после изменений!
                </p>
              </div>
            </div>
          </div>

          {plans.map((plan) => (
            <Card key={plan.key} className="border-2">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{plan.name}</CardTitle>
                  {editingPlan === plan.key ? (
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        onClick={() => savePlan(plan)}
                        disabled={saving}
                      >
                        {saving ? (
                          <Icon name="Loader2" className="animate-spin" size={16} />
                        ) : (
                          <Icon name="Save" size={16} />
                        )}
                        <span className="ml-2">Сохранить</span>
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setEditingPlan(null);
                          loadPlans();
                        }}
                      >
                        <Icon name="X" size={16} />
                      </Button>
                    </div>
                  ) : (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditingPlan(plan.key)}
                    >
                      <Icon name="Edit" size={16} />
                      <span className="ml-2">Редактировать</span>
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor={`name-${plan.key}`}>Название тарифа</Label>
                    <Input
                      id={`name-${plan.key}`}
                      value={plan.name}
                      onChange={(e) => updatePlanField(plan.key, 'name', e.target.value)}
                      disabled={editingPlan !== plan.key}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label htmlFor={`price-${plan.key}`}>Цена (₽)</Label>
                    <Input
                      id={`price-${plan.key}`}
                      type="number"
                      value={plan.price_rub}
                      onChange={(e) => updatePlanField(plan.key, 'price_rub', Number(e.target.value))}
                      disabled={editingPlan !== plan.key}
                      className="mt-1"
                    />
                  </div>
                </div>
                <div>
                  <Label htmlFor={`description-${plan.key}`}>Описание</Label>
                  <Textarea
                    id={`description-${plan.key}`}
                    value={plan.description}
                    onChange={(e) => updatePlanField(plan.key, 'description', e.target.value)}
                    disabled={editingPlan !== plan.key}
                    rows={4}
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor={`duration-${plan.key}`}>Длительность (дней)</Label>
                  <Input
                    id={`duration-${plan.key}`}
                    type="number"
                    value={plan.duration_days}
                    onChange={(e) => updatePlanField(plan.key, 'duration_days', Number(e.target.value))}
                    disabled={editingPlan !== plan.key}
                    className="mt-1"
                  />
                </div>
              </CardContent>
            </Card>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
