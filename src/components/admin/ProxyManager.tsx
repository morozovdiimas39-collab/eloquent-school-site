import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import funcUrls from '../../../backend/func2url.json';

interface Proxy {
  id: number;
  host: string;
  port: number;
  username?: string;
  password?: string;
  is_active: boolean;
  created_at: string;
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

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
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
              {proxies.map((proxy) => (
                <div
                  key={proxy.id}
                  className="border border-gray-200 rounded-lg p-4 flex items-center justify-between hover:border-indigo-300 transition-colors"
                >
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
                    <p className="text-xs text-gray-400 mt-1">
                      Добавлен: {new Date(proxy.created_at).toLocaleString('ru-RU')}
                    </p>
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
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
