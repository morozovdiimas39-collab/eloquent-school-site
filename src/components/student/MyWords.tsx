import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import funcUrls from '../../../backend/func2url.json';

const API_URL = funcUrls['webapp-api'];

interface AssignedWord {
  id: number;
  word_id: number;
  english_text: string;
  russian_translation: string;
  category_id: number | null;
  assigned_at: string;
  status: string;
  mastery_score: number;
  attempts: number;
  correct_uses: number;
  progress_status: 'new' | 'learning' | 'learned' | 'mastered';
}

interface ProgressStats {
  total_words: number;
  new: number;
  learning: number;
  learned: number;
  mastered: number;
  average_mastery: number;
}

interface MyWordsProps {
  studentId: number;
  teacherId?: number | null;
  languageLevel?: string;
}

export default function MyWords({ studentId, teacherId, languageLevel = 'A1' }: MyWordsProps) {
  const [words, setWords] = useState<AssignedWord[]>([]);
  const [stats, setStats] = useState<ProgressStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [autoAssigning, setAutoAssigning] = useState(false);

  useEffect(() => {
    loadWords();
    loadStats();
  }, [studentId]);

  const loadWords = async () => {
    setLoading(true);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'get_student_words',
          student_id: studentId
        })
      });
      const data = await response.json();
      setWords(data.words || []);
    } catch (error) {
      console.error('Ошибка загрузки слов:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'get_student_progress_stats',
          student_id: studentId
        })
      });
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Ошибка загрузки статистики:', error);
    }
  };

  const deleteWord = async (studentWordId: number) => {
    if (!confirm('Удалить это слово из изучения?')) return;
    
    try {
      await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'delete_student_word',
          student_word_id: studentWordId
        })
      });
      await loadWords();
      await loadStats();
    } catch (error) {
      console.error('Ошибка удаления слова:', error);
      alert('Не удалось удалить слово');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'new': return 'bg-blue-100 text-blue-700';
      case 'learning': return 'bg-yellow-100 text-yellow-700';
      case 'learned': return 'bg-green-100 text-green-700';
      case 'mastered': return 'bg-purple-100 text-purple-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'new': return 'Новое';
      case 'learning': return 'Изучаю';
      case 'learned': return 'Выучено';
      case 'mastered': return 'Освоено';
      default: return status;
    }
  };

  const filteredWords = words.filter(word => {
    const query = searchQuery.toLowerCase();
    return (
      word.english_text.toLowerCase().includes(query) ||
      word.russian_translation.toLowerCase().includes(query)
    );
  });

  if (loading) {
    return (
      <Card className="border border-gray-200 shadow-sm">
        <CardContent className="py-8">
          <div className="flex flex-col items-center gap-2">
            <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-sm text-muted-foreground">Загрузка слов...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border border-gray-200 shadow-sm">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg font-bold">
            <Icon name="BookOpen" size={20} />
            Мои слова для изучения
          </CardTitle>
          <Badge variant="secondary" className="text-sm px-2.5 py-0.5 font-semibold">
            {words.length}
          </Badge>
        </div>
        
        {stats && (
          <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2">
            <div className="bg-blue-50 rounded-lg p-2 border border-blue-200">
              <div className="text-xs text-blue-600 font-medium">Новые</div>
              <div className="text-lg font-bold text-blue-700">{stats.new}</div>
            </div>
            <div className="bg-yellow-50 rounded-lg p-2 border border-yellow-200">
              <div className="text-xs text-yellow-600 font-medium">Изучаю</div>
              <div className="text-lg font-bold text-yellow-700">{stats.learning}</div>
            </div>
            <div className="bg-green-50 rounded-lg p-2 border border-green-200">
              <div className="text-xs text-green-600 font-medium">Выучено</div>
              <div className="text-lg font-bold text-green-700">{stats.learned}</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-2 border border-purple-200">
              <div className="text-xs text-purple-600 font-medium">Освоено</div>
              <div className="text-lg font-bold text-purple-700">{stats.mastered}</div>
            </div>
          </div>
        )}
      </CardHeader>
      <CardContent>
        {words.length === 0 ? (
          <div className="text-center py-8">
            <Icon name="BookOpen" size={48} className="mx-auto mb-3 text-muted-foreground opacity-30" />
            <p className="text-sm font-medium text-muted-foreground">
              Пока нет слов для изучения
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Ваш преподаватель добавит слова позже
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            <Input
              type="text"
              placeholder="Поиск по словам..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full h-10 text-sm"
            />

            <div className="space-y-2">
              {filteredWords.map((word) => (
                <div
                  key={word.id}
                  className="p-3 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50/30 transition-all"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <h3 className="text-base font-bold text-blue-600 truncate">
                          {word.english_text}
                        </h3>
                        <Badge className={`text-xs px-1.5 py-0 ${getStatusColor(word.progress_status)}`}>
                          {getStatusText(word.progress_status)}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-700">
                        {word.russian_translation}
                      </p>
                      
                      {word.attempts > 0 && (
                        <div className="mt-2">
                          <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                            <span>Прогресс: {Math.round(word.mastery_score)}%</span>
                            <span>{word.correct_uses}/{word.attempts} правильно</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-1.5">
                            <div 
                              className="bg-gradient-to-r from-blue-500 to-green-500 h-1.5 rounded-full transition-all"
                              style={{ width: `${word.mastery_score}%` }}
                            />
                          </div>
                        </div>
                      )}
                      
                      <p className="text-xs text-gray-400 mt-1">
                        Назначено: {new Date(word.assigned_at).toLocaleDateString('ru-RU')}
                      </p>
                    </div>
                    
                    <button
                      onClick={() => deleteWord(word.id)}
                      className="text-red-500 hover:text-red-700 hover:bg-red-50 p-1.5 rounded-lg transition-colors"
                      title="Удалить слово"
                    >
                      <Icon name="Trash2" size={18} />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {filteredWords.length === 0 && searchQuery && (
              <div className="text-center py-6">
                <Icon name="Search" size={40} className="mx-auto mb-2 text-muted-foreground opacity-30" />
                <p className="text-sm text-muted-foreground">Ничего не найдено</p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}