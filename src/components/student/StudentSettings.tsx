import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import { toast } from 'sonner';
import funcUrls from '../../../backend/func2url.json';

const API_URL = funcUrls['webapp-api'];

interface Topic {
  emoji: string;
  topic: string;
}

interface StudentSettingsProps {
  studentId: number;
  currentLevel: string;
  currentTopics: Topic[];
  currentTimezone: string;
}

const LANGUAGE_LEVELS = [
  { value: 'A1', label: 'A1 - Beginner', description: 'Начинающий' },
  { value: 'A2', label: 'A2 - Elementary', description: 'Элементарный' },
  { value: 'B1', label: 'B1 - Intermediate', description: 'Средний' },
  { value: 'B2', label: 'B2 - Upper Intermediate', description: 'Выше среднего' },
  { value: 'C1', label: 'C1 - Advanced', description: 'Продвинутый' },
  { value: 'C2', label: 'C2 - Proficiency', description: 'Владение в совершенстве' }
];

const POPULAR_TOPICS = [
  { emoji: '💼', topic: 'Work' },
  { emoji: '✈️', topic: 'Travel' },
  { emoji: '🍕', topic: 'Food' },
  { emoji: '⚽', topic: 'Sports' },
  { emoji: '🎮', topic: 'Gaming' },
  { emoji: '🎬', topic: 'Movies' },
  { emoji: '📚', topic: 'Books' },
  { emoji: '🎵', topic: 'Music' },
  { emoji: '💻', topic: 'Technology' },
  { emoji: '🏠', topic: 'Home' },
  { emoji: '👨‍👩‍👧', topic: 'Family' },
  { emoji: '🐶', topic: 'Pets' },
  { emoji: '🌍', topic: 'Nature' },
  { emoji: '🎨', topic: 'Art' },
  { emoji: '🧘', topic: 'Health' },
  { emoji: '🛍️', topic: 'Shopping' }
];

export default function StudentSettings({ 
  studentId, 
  currentLevel, 
  currentTopics, 
  currentTimezone 
}: StudentSettingsProps) {
  const [languageLevel, setLanguageLevel] = useState(currentLevel);
  const [topics, setTopics] = useState<Topic[]>(currentTopics);
  const [newTopicEmoji, setNewTopicEmoji] = useState('');
  const [newTopicName, setNewTopicName] = useState('');
  const [timezone, setTimezone] = useState(currentTimezone);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setLanguageLevel(currentLevel);
    setTopics(currentTopics);
    setTimezone(currentTimezone);
  }, [currentLevel, currentTopics, currentTimezone]);

  const addTopic = () => {
    if (!newTopicEmoji || !newTopicName.trim()) {
      toast.error('Укажите эмодзи и название темы');
      return;
    }

    if (topics.some(t => t.topic.toLowerCase() === newTopicName.trim().toLowerCase())) {
      toast.error('Эта тема уже добавлена');
      return;
    }

    setTopics([...topics, { emoji: newTopicEmoji, topic: newTopicName.trim() }]);
    setNewTopicEmoji('');
    setNewTopicName('');
  };

  const addPopularTopic = (topic: Topic) => {
    if (topics.some(t => t.topic === topic.topic)) {
      toast.error('Эта тема уже добавлена');
      return;
    }
    setTopics([...topics, topic]);
  };

  const removeTopic = (index: number) => {
    setTopics(topics.filter((_, i) => i !== index));
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'update_student_settings',
          telegram_id: studentId,
          language_level: languageLevel,
          preferred_topics: topics,
          timezone: timezone
        })
      });

      const data = await response.json();

      if (data.success) {
        toast.success('Настройки сохранены!');
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

  const levelInfo = LANGUAGE_LEVELS.find(l => l.value === languageLevel);

  return (
    <Card className="border border-gray-200 shadow-sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg font-bold">
          <Icon name="Settings" size={20} />
          Настройки обучения
        </CardTitle>
        <CardDescription className="text-sm">
          Настрой уровень языка и темы для разговоров с Аней
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        
        <div>
          <label className="text-sm font-semibold mb-2 block text-gray-700">
            Уровень владения английским
          </label>
          <Select value={languageLevel} onValueChange={setLanguageLevel}>
            <SelectTrigger className="h-11">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {LANGUAGE_LEVELS.map((level) => (
                <SelectItem key={level.value} value={level.value}>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{level.label}</span>
                    <span className="text-xs text-gray-500">— {level.description}</span>
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {levelInfo && (
            <p className="text-xs text-gray-500 mt-1.5">
              Аня адаптирует сложность диалогов под твой уровень
            </p>
          )}
        </div>

        <div>
          <label className="text-sm font-semibold mb-2 block text-gray-700">
            Темы для разговоров
          </label>
          
          {topics.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {topics.map((topic, index) => (
                <Badge
                  key={index}
                  className="bg-blue-50 text-blue-700 border border-blue-200 px-3 py-1.5 text-sm font-medium"
                >
                  <span className="mr-1.5">{topic.emoji}</span>
                  {topic.topic}
                  <button
                    onClick={() => removeTopic(index)}
                    className="ml-2 hover:text-red-600 transition-colors"
                  >
                    ×
                  </button>
                </Badge>
              ))}
            </div>
          )}

          <div className="space-y-3">
            <div>
              <p className="text-xs text-gray-600 mb-2 font-medium">Популярные темы:</p>
              <div className="flex flex-wrap gap-1.5">
                {POPULAR_TOPICS.map((topic, index) => (
                  <button
                    key={index}
                    onClick={() => addPopularTopic(topic)}
                    className="px-2.5 py-1.5 text-sm bg-gray-50 hover:bg-blue-50 border border-gray-200 hover:border-blue-300 rounded-md transition-all"
                  >
                    {topic.emoji} {topic.topic}
                  </button>
                ))}
              </div>
            </div>

            <div className="border-t pt-3">
              <p className="text-xs text-gray-600 mb-2 font-medium">Или добавь свою тему:</p>
              <div className="flex gap-2">
                <Input
                  type="text"
                  placeholder="🎯"
                  value={newTopicEmoji}
                  onChange={(e) => setNewTopicEmoji(e.target.value)}
                  className="w-16 h-10 text-center text-lg"
                  maxLength={2}
                />
                <Input
                  type="text"
                  placeholder="Название темы"
                  value={newTopicName}
                  onChange={(e) => setNewTopicName(e.target.value)}
                  className="flex-1 h-10"
                  maxLength={30}
                />
                <Button
                  onClick={addTopic}
                  variant="outline"
                  className="h-10 px-4"
                >
                  <Icon name="Plus" size={16} />
                </Button>
              </div>
            </div>
          </div>

          <p className="text-xs text-gray-500 mt-2">
            Аня будет использовать эти темы для инициации диалогов
          </p>
        </div>

        <Button
          onClick={saveSettings}
          disabled={saving}
          className="w-full h-11 text-base font-semibold bg-blue-600 hover:bg-blue-700"
        >
          {saving ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
              Сохранение...
            </>
          ) : (
            <>
              <Icon name="Save" size={18} className="mr-2" />
              Сохранить настройки
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
