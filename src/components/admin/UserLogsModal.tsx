import { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import { funcUrls } from '@/config/funcUrls';

interface UserLog {
  id: number;
  telegram_id: number;
  event_type: string;
  event_data: any;
  user_state: any;
  error_message: string | null;
  created_at: string;
}

interface UserLogsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  telegramId: number;
  userName: string;
}

const API_URL = funcUrls['webapp-api'];

// Маппинг типов событий на читаемые названия
const EVENT_TYPE_LABELS: Record<string, string> = {
  'onboarding_start': '🚀 Начало онбординга',
  'learning_mode_selected': '📚 Выбор режима обучения',
  'level_test': '📝 Тест уровня',
  'interests_selected': '🎯 Выбор интересов',
  'subscription_check': '💳 Проверка подписки',
  'message_sent': '💬 Отправка сообщения',
  'message_received': '📩 Входящее сообщение',
  'gemini_response': '🤖 Ответ Gemini',
  'gemini_error': '⚠️ Ошибка Gemini',
  'error_occurred': '❌ Ошибка',
  'callback_query': '🔘 Нажатие кнопки',
  'voice_message': '🎤 Голосовое сообщение',
  'user_created': '✅ Пользователь создан',
  'subscription_activated': '🎉 Подписка активирована',
};

// Цвета для разных типов событий
const EVENT_TYPE_COLORS: Record<string, string> = {
  'onboarding_start': 'bg-blue-100 text-blue-700',
  'learning_mode_selected': 'bg-green-100 text-green-700',
  'level_test': 'bg-purple-100 text-purple-700',
  'interests_selected': 'bg-pink-100 text-pink-700',
  'subscription_check': 'bg-yellow-100 text-yellow-700',
  'message_sent': 'bg-gray-100 text-gray-700',
  'message_received': 'bg-blue-50 text-blue-600',
  'gemini_response': 'bg-green-50 text-green-600',
  'gemini_error': 'bg-orange-100 text-orange-700',
  'error_occurred': 'bg-red-100 text-red-700',
  'callback_query': 'bg-indigo-100 text-indigo-700',
  'voice_message': 'bg-teal-100 text-teal-700',
  'user_created': 'bg-emerald-100 text-emerald-700',
  'subscription_activated': 'bg-orange-100 text-orange-700',
};

export default function UserLogsModal({ open, onOpenChange, telegramId, userName }: UserLogsModalProps) {
  const [logs, setLogs] = useState<UserLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedLog, setExpandedLog] = useState<number | null>(null);

  useEffect(() => {
    if (open && telegramId) {
      loadLogs();
    }
  }, [open, telegramId]);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'get_user_logs',
          telegram_id: telegramId,
          limit: 200
        })
      });

      const data = await response.json();
      if (data.success) {
        setLogs(data.logs);
      }
    } catch (error) {
      console.error('Error loading logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const toggleExpand = (logId: number) => {
    setExpandedLog(expandedLog === logId ? null : logId);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-xl flex items-center gap-2">
            <Icon name="ScrollText" size={24} className="text-blue-600" />
            Логи пользователя: {userName}
          </DialogTitle>
          <DialogDescription>
            ID: {telegramId} • Показано последних {logs.length} событий
          </DialogDescription>
        </DialogHeader>

        <div className="flex gap-2 mb-3">
          <Button onClick={loadLogs} disabled={loading} size="sm" variant="outline">
            <Icon name="RefreshCw" size={14} className={`mr-2 ${loading ? 'animate-spin' : ''}`} />
            Обновить
          </Button>
        </div>

        {loading && logs.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : (
          <div className="overflow-y-auto flex-1 space-y-2 pr-2">
            {logs.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Icon name="Inbox" size={48} className="mx-auto mb-3 text-gray-400" />
                <p>Логов пока нет</p>
              </div>
            ) : (
              logs.map((log) => (
                <div
                  key={log.id}
                  className={`border rounded-lg p-3 ${log.error_message ? 'border-red-300 bg-red-50' : 'border-gray-200 bg-white'}`}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2 flex-1">
                      <Badge className={`text-xs px-2 py-1 ${EVENT_TYPE_COLORS[log.event_type] || 'bg-gray-100 text-gray-700'}`}>
                        {EVENT_TYPE_LABELS[log.event_type] || log.event_type}
                      </Badge>
                      <span className="text-xs text-gray-500">{formatDate(log.created_at)}</span>
                    </div>
                    <Button
                      onClick={() => toggleExpand(log.id)}
                      size="sm"
                      variant="ghost"
                      className="h-6 px-2"
                    >
                      <Icon
                        name={expandedLog === log.id ? 'ChevronUp' : 'ChevronDown'}
                        size={16}
                      />
                    </Button>
                  </div>

                  {log.error_message && (
                    <div className="mb-2 p-2 bg-red-100 border border-red-300 rounded text-xs text-red-700">
                      <Icon name="AlertCircle" size={14} className="inline mr-1" />
                      <strong>Ошибка:</strong> {log.error_message}
                    </div>
                  )}

                  {expandedLog === log.id && (
                    <div className="mt-2 space-y-2">
                      {log.event_data && Object.keys(log.event_data).length > 0 && (
                        <div>
                          <div className="text-xs font-semibold text-gray-700 mb-1">📊 Данные события:</div>
                          <pre className="text-xs bg-gray-50 p-2 rounded border border-gray-200 overflow-x-auto">
                            {JSON.stringify(log.event_data, null, 2)}
                          </pre>
                        </div>
                      )}

                      {log.user_state && Object.keys(log.user_state).length > 0 && (
                        <div>
                          <div className="text-xs font-semibold text-gray-700 mb-1">👤 Состояние пользователя:</div>
                          <pre className="text-xs bg-blue-50 p-2 rounded border border-blue-200 overflow-x-auto">
                            {JSON.stringify(log.user_state, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}