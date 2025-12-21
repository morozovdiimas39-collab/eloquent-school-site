import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import { funcUrls } from '@/config/funcUrls';

interface GeminiPrompt {
  id: number;
  code: string;
  name: string;
  description?: string;
  prompt_text: string;
  category: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

const API_URL = funcUrls['webapp-api'];

export default function PromptsManager() {
  const [prompts, setPrompts] = useState<GeminiPrompt[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingPrompt, setEditingPrompt] = useState<GeminiPrompt | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadPrompts();
  }, []);

  const loadPrompts = async () => {
    try {
      setLoading(true);
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'get_gemini_prompts' })
      });
      const data = await response.json();
      if (data.success) {
        setPrompts(data.prompts);
      }
    } catch (error) {
      console.error('Failed to load prompts:', error);
    } finally {
      setLoading(false);
    }
  };

  const savePrompt = async () => {
    if (!editingPrompt) return;
    
    try {
      setSaving(true);
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'update_gemini_prompt',
          prompt_id: editingPrompt.id,
          prompt_text: editingPrompt.prompt_text,
          description: editingPrompt.description,
          is_active: editingPrompt.is_active
        })
      });
      const data = await response.json();
      
      if (data.success) {
        await loadPrompts();
        setEditingPrompt(null);
      }
    } catch (error) {
      console.error('Failed to save prompt:', error);
    } finally {
      setSaving(false);
    }
  };

  const togglePromptActive = async (promptId: number, isActive: boolean) => {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'toggle_gemini_prompt',
          prompt_id: promptId,
          is_active: isActive
        })
      });
      const data = await response.json();
      
      if (data.success) {
        await loadPrompts();
      }
    } catch (error) {
      console.error('Failed to toggle prompt:', error);
    }
  };

  const filteredPrompts = prompts.filter(p =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.code.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      'emotional': 'bg-pink-500',
      'rules': 'bg-blue-500',
      'learning': 'bg-green-500',
      'general': 'bg-gray-500'
    };
    return colors[category] || 'bg-gray-500';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Icon name="Loader2" className="animate-spin" size={32} />
      </div>
    );
  }

  if (editingPrompt) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">{editingPrompt.name}</h2>
            <p className="text-sm text-gray-500">Код: {editingPrompt.code}</p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => setEditingPrompt(null)}
            >
              <Icon name="X" size={16} className="mr-2" />
              Отмена
            </Button>
            <Button
              onClick={savePrompt}
              disabled={saving}
            >
              {saving ? (
                <Icon name="Loader2" size={16} className="mr-2 animate-spin" />
              ) : (
                <Icon name="Save" size={16} className="mr-2" />
              )}
              Сохранить
            </Button>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Описание</CardTitle>
          </CardHeader>
          <CardContent>
            <Input
              value={editingPrompt.description || ''}
              onChange={(e) => setEditingPrompt({
                ...editingPrompt,
                description: e.target.value
              })}
              placeholder="Краткое описание промпта..."
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Текст промпта</CardTitle>
          </CardHeader>
          <CardContent>
            <textarea
              className="w-full h-96 p-4 font-mono text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={editingPrompt.prompt_text}
              onChange={(e) => setEditingPrompt({
                ...editingPrompt,
                prompt_text: e.target.value
              })}
              placeholder="Введите текст промпта..."
            />
            <div className="mt-4 text-sm text-gray-500">
              <p className="font-semibold mb-2">Доступные переменные:</p>
              <div className="grid grid-cols-2 gap-2">
                <code>{'language_level'}</code>
                <code>{'level_instruction'}</code>
                <code>{'mood_emoji'}</code>
                <code>{'learning_goal'}</code>
                <code>{'error_correction_rules'}</code>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Настройки</CardTitle>
          </CardHeader>
          <CardContent>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={editingPrompt.is_active}
                onChange={(e) => setEditingPrompt({
                  ...editingPrompt,
                  is_active: e.target.checked
                })}
                className="w-4 h-4"
              />
              <span>Промпт активен (используется ботом)</span>
            </label>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Промпты Gemini</h2>
          <p className="text-sm text-gray-500">
            Управление промптами для AI-бота
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Icon name="Search" size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <Input
                placeholder="Поиск по названию, коду или описанию..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {filteredPrompts.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                Промпты не найдены
              </div>
            ) : (
              filteredPrompts.map((prompt) => (
                <Card key={prompt.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-semibold">{prompt.name}</h3>
                          <Badge className={`${getCategoryColor(prompt.category)} text-white`}>
                            {prompt.category}
                          </Badge>
                          {!prompt.is_active && (
                            <Badge variant="outline" className="text-gray-500">
                              Неактивен
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mb-2">
                          {prompt.description || 'Нет описания'}
                        </p>
                        <p className="text-xs text-gray-400 font-mono">
                          Код: {prompt.code}
                        </p>
                        <p className="text-xs text-gray-400 mt-2">
                          {prompt.prompt_text.length} символов
                        </p>
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => togglePromptActive(prompt.id, !prompt.is_active)}
                        >
                          <Icon 
                            name={prompt.is_active ? "EyeOff" : "Eye"} 
                            size={16} 
                          />
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => setEditingPrompt(prompt)}
                        >
                          <Icon name="Edit" size={16} className="mr-1" />
                          Редактировать
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
