import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import funcUrls from '../../../../backend/func2url.json';

interface Proxy {
  id: number;
  host: string;
  port: number;
  username?: string;
  password?: string;
  is_active: boolean;
  created_at: string;
  total_requests?: number;
  successful_requests?: number;
  failed_requests?: number;
  last_used_at?: string;
  last_error?: string;
  last_error_at?: string;
}

const API_URL = funcUrls['webapp-api'];

export default function ProxyManager() {
  const [proxies, setProxies] = useState<Proxy[]>([]);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);
  const [newProxy, setNewProxy] = useState({ host: '', port: '', username: '', password: '' });

  useEffect(() => {
    loadProxies();
  }, []);

  const loadProxies = async () => {
    setLoading(true);
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'get_proxies' })
      });
      const data = await res.json();
      if (data.proxies) {
        setProxies(data.proxies);
      }
    } catch (error) {
      console.error('Error loading proxies:', error);
    } finally {
      setLoading(false);
    }
  };

  const addProxy = async () => {
    if (!newProxy.host || !newProxy.port) {
      alert('Укажите хост и порт');
      return;
    }

    setAdding(true);
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'add_proxy',
          host: newProxy.host,
          port: parseInt(newProxy.port),
          username: newProxy.username || null,
          password: newProxy.password || null
        })
      });
      const data = await res.json();
      if (data.success) {
        setNewProxy({ host: '', port: '', username: '', password: '' });
        await loadProxies();
      } else {
        alert('Ошибка добавления прокси');
      }
    } catch (error) {
      console.error('Error adding proxy:', error);
      alert('Ошибка добавления прокси');
    } finally {
      setAdding(false);
    }
  };

  const toggleProxy = async (id: number, isActive: boolean) => {
    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'toggle_proxy',
          proxy_id: id,
          is_active: !isActive
        })
      });
      const data = await res.json();
      if (data.success) {
        await loadProxies();
      }
    } catch (error) {
      console.error('Error toggling proxy:', error);
    }
  };

  const deleteProxy = async (id: number) => {
    if (!confirm('Удалить прокси?')) return;

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'delete_proxy',
          proxy_id: id
        })
      });
      const data = await res.json();
      if (data.success) {
        await loadProxies();
      }
    } catch (error) {
      console.error('Error deleting proxy:', error);
    }
  };

  const resetProxyStats = async (id: number) => {
    if (!confirm('Сбросить статистику прокси?')) return;

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'reset_proxy_stats',
          proxy_id: id
        })
      });
      const data = await res.json();
      if (data.success) {
        await loadProxies();
      }
    } catch (error) {
      console.error('Error resetting proxy stats:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const totalRequests = proxies.reduce((sum, p) => sum + (p.total_requests || 0), 0);
  const totalSuccess = proxies.reduce((sum, p) => sum + (p.successful_requests || 0), 0);
  const totalFailed = proxies.reduce((sum, p) => sum + (p.failed_requests || 0), 0);
  const overallRate = totalRequests > 0 ? ((totalSuccess / totalRequests) * 100).toFixed(1) : '0.0';
  const activeProxies = proxies.filter(p => p.is_active).length;

  return (
    <div className="space-y-6">
      {proxies.length > 0 && totalRequests > 0 && (
        <Card className="border-green-200 shadow-sm bg-gradient-to-br from-green-50 to-blue-50">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Icon name="Activity" size={20} className="text-green-600" />
              Общая статистика прокси
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center">
                <p className="text-xs text-gray-600 mb-1">Всего прокси</p>
                <p className="text-2xl font-bold text-gray-900">{proxies.length}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-gray-600 mb-1">Активных</p>
                <p className="text-2xl font-bold text-green-600">{activeProxies}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-gray-600 mb-1">Всего запросов</p>
                <p className="text-2xl font-bold text-blue-600">{totalRequests}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-gray-600 mb-1">Успешных</p>
                <p className="text-2xl font-bold text-green-600">{totalSuccess}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-gray-600 mb-1">Успешность</p>
                <p className={`text-2xl font-bold ${
                  parseFloat(overallRate) >= 80 ? 'text-green-600' : 
                  parseFloat(overallRate) >= 50 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {overallRate}%
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="border-indigo-200 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <Icon name="Globe" size={22} className="text-blue-600" />
            Добавить прокси
          </CardTitle>
          <CardDescription>Прокси используются ботом для запросов к Gemini</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
            <Input
              placeholder="Хост (ip или домен)"
              value={newProxy.host}
              onChange={(e) => setNewProxy({ ...newProxy, host: e.target.value })}
            />
            <Input
              type="number"
              placeholder="Порт"
              value={newProxy.port}
              onChange={(e) => setNewProxy({ ...newProxy, port: e.target.value })}
            />
            <Input
              placeholder="Username (опционально)"
              value={newProxy.username}
              onChange={(e) => setNewProxy({ ...newProxy, username: e.target.value })}
            />
            <Input
              type="password"
              placeholder="Password (опционально)"
              value={newProxy.password}
              onChange={(e) => setNewProxy({ ...newProxy, password: e.target.value })}
            />
          </div>
          <Button onClick={addProxy} disabled={adding} className="w-full">
            <Icon name="Plus" size={16} className="mr-2" />
            {adding ? 'Добавление...' : 'Добавить прокси'}
          </Button>
        </CardContent>
      </Card>

      <Card className="border-indigo-200 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <Icon name="List" size={22} className="text-blue-600" />
            Список прокси ({proxies.length})
          </CardTitle>
          <CardDescription>Активные прокси используются ботом по очереди</CardDescription>
        </CardHeader>
        <CardContent>
          {proxies.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Icon name="Globe" size={48} className="mx-auto mb-3 opacity-30" />
              <p className="text-base">Прокси не добавлены</p>
            </div>
          ) : (
            <div className="space-y-3">
              {proxies.map((proxy) => {
                const totalReq = proxy.total_requests || 0;
                const successReq = proxy.successful_requests || 0;
                const failedReq = proxy.failed_requests || 0;
                const successRate = totalReq > 0 ? (successReq / totalReq * 100).toFixed(1) : '0.0';
                
                return (
                  <div
                    key={proxy.id}
                    className="border border-gray-200 rounded-lg p-4 hover:border-indigo-300 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-mono text-sm font-medium">
                            {proxy.host}:{proxy.port}
                          </span>
                          <Badge variant={proxy.is_active ? 'default' : 'secondary'} className="text-xs">
                            {proxy.is_active ? 'Активен' : 'Выключен'}
                          </Badge>
                        </div>
                        {proxy.username && (
                          <p className="text-xs text-gray-500">
                            Авторизация: {proxy.username}
                          </p>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => toggleProxy(proxy.id, proxy.is_active)}
                        >
                          <Icon name={proxy.is_active ? 'Power' : 'PowerOff'} size={16} />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => deleteProxy(proxy.id)}
                          className="text-red-600 hover:bg-red-50"
                        >
                          <Icon name="Trash2" size={16} />
                        </Button>
                      </div>
                    </div>

                    {totalReq > 0 && (
                      <div className="pt-3 border-t">
                        <div className="flex items-center justify-between mb-3">
                          <p className="text-xs font-semibold text-gray-700">Статистика использования</p>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => resetProxyStats(proxy.id)}
                            className="h-7 text-xs text-gray-500 hover:text-red-600"
                          >
                            <Icon name="RotateCcw" size={14} className="mr-1" />
                            Сбросить
                          </Button>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          <div className="text-center">
                            <p className="text-xs text-gray-500 mb-1">Всего запросов</p>
                            <p className="text-lg font-semibold text-gray-900">{totalReq}</p>
                          </div>
                          <div className="text-center">
                            <p className="text-xs text-gray-500 mb-1">Успешных</p>
                            <p className="text-lg font-semibold text-green-600">{successReq}</p>
                          </div>
                          <div className="text-center">
                            <p className="text-xs text-gray-500 mb-1">Ошибок</p>
                            <p className="text-lg font-semibold text-red-600">{failedReq}</p>
                          </div>
                          <div className="text-center">
                            <p className="text-xs text-gray-500 mb-1">Успешность</p>
                            <p className={`text-lg font-semibold ${
                              parseFloat(successRate) >= 80 ? 'text-green-600' : 
                              parseFloat(successRate) >= 50 ? 'text-yellow-600' : 'text-red-600'
                            }`}>
                              {successRate}%
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {proxy.last_used_at && (
                      <p className="text-xs text-gray-400 mt-2">
                        Последний запрос: {new Date(proxy.last_used_at).toLocaleString('ru-RU')}
                      </p>
                    )}

                    {proxy.last_error && (
                      <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-xs">
                        <p className="font-semibold text-red-700 mb-1 flex items-center gap-1">
                          <Icon name="AlertCircle" size={14} />
                          Последняя ошибка:
                        </p>
                        <p className="text-red-600 font-mono truncate">{proxy.last_error}</p>
                        {proxy.last_error_at && (
                          <p className="text-red-500 mt-1">
                            {new Date(proxy.last_error_at).toLocaleString('ru-RU')}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}