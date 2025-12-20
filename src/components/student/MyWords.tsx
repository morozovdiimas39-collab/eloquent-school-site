import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import { funcUrls } from '@/config/funcUrls';

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
  dialog_uses: number;
  needs_check: boolean;
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
      // API возвращает массив напрямую, НЕ {words: [...]}
      setWords(Array.isArray(data) ? data : []);
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

  const autoAssignWords = async () => {
    setAutoAssigning(true);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'auto_assign_basic_words',
          student_id: studentId,
          count: 15
        })
      });
      const data = await response.json();
      if (data.success) {
        await loadWords();
        await loadStats();
        alert(`Добавлено ${data.count} новых слов!`);
      }
    } catch (error) {
      console.error('Ошибка добавления слов:', error);
      alert('Не удалось добавить слова');
    } finally {
      setAutoAssigning(false);
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
              Добавьте базовые слова для начала
            </p>
            <button
              onClick={autoAssignWords}
              disabled={autoAssigning}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {autoAssigning ? 'Добавление...' : '+ Добавить базовые слова'}
            </button>
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
                  <div>
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
                    
                    {/* ПРОГРЕСС ИСПОЛЬЗОВАНИЯ АНЕ */}
                    <div className="mt-4 bg-blue-600 p-4 rounded-xl shadow-2xl border-4 border-blue-700">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-lg font-black text-white">🗣️ Аня использовала:</span>
                        <span className="text-4xl font-black text-yellow-300">{word.dialog_uses}/5</span>
                      </div>
                      <div className="w-full bg-blue-900 rounded-full h-10 shadow-inner border-2 border-blue-800">
                        <div 
                          className={`h-10 rounded-full transition-all duration-500 flex items-center justify-center ${
                            word.needs_check 
                              ? 'bg-gradient-to-r from-yellow-400 via-orange-500 to-red-600 animate-pulse shadow-2xl' 
                              : 'bg-gradient-to-r from-green-400 via-emerald-500 to-teal-600 shadow-xl'
                          }`}
                          style={{ width: `${Math.max(15, (word.dialog_uses / 5 * 100))}%` }}
                        >
                          <span className="text-base font-black text-white drop-shadow-lg">
                            {(word.dialog_uses / 5 * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      {word.needs_check && (
                        <div className="mt-3 bg-yellow-400 border-4 border-yellow-500 rounded-xl p-3 shadow-lg">
                          <p className="text-base text-yellow-900 font-black text-center">
                            🎯 ГОТОВО К ПРОВЕРКЕ! Аня спросит на следующем сообщении
                          </p>
                        </div>
                      )}
                      {word.progress_status === 'mastered' && (
                        <div className="mt-3 bg-green-400 border-4 border-green-500 rounded-xl p-3 shadow-lg">
                          <p className="text-base text-green-900 font-black text-center">
                            ✅ СЛОВО ПОЛНОСТЬЮ ОСВОЕНО!
                          </p>
                        </div>
                      )}
                    </div>
                    
                    {word.attempts > 0 && (
                      <div className="mt-2">
                        <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
                          <span>Упражнения: {word.correct_uses}/{word.attempts}</span>
                        </div>
                      </div>
                    )}
                    
                    <div className="flex items-center justify-between mt-2">
                      <p className="text-xs text-gray-400">
                        Назначено: {new Date(word.assigned_at).toLocaleDateString('ru-RU')}
                      </p>
                      <button
                        onClick={() => deleteWord(word.id)}
                        className="flex items-center gap-1 text-xs text-red-500 hover:text-red-700 hover:bg-red-50 px-2 py-1 rounded-lg transition-colors"
                        title="Удалить слово"
                      >
                        <Icon name="Trash2" size={14} />
                        <span>Удалить</span>
                      </button>
                    </div>
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