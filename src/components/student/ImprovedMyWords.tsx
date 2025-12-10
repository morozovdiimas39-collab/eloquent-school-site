import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import { toast } from 'sonner';
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

interface ImprovedMyWordsProps {
  studentId: number;
  languageLevel?: string;
  learningGoal?: string;
}

export default function ImprovedMyWords({ studentId, languageLevel = 'A1', learningGoal = '' }: ImprovedMyWordsProps) {
  const [words, setWords] = useState<AssignedWord[]>([]);
  const [stats, setStats] = useState<ProgressStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [autoAssigning, setAutoAssigning] = useState(false);
  const [generatingWords, setGeneratingWords] = useState(false);

  useEffect(() => {
    loadData();
  }, [studentId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [wordsRes, statsRes] = await Promise.all([
        fetch(API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            action: 'get_student_words',
            student_id: studentId
          })
        }),
        fetch(API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            action: 'get_student_progress_stats',
            student_id: studentId
          })
        })
      ]);

      const wordsData = await wordsRes.json();
      const statsData = await statsRes.json();

      setWords(wordsData.words || []);
      setStats(statsData);
    } catch (error) {
      console.error('Ошибка загрузки слов:', error);
    } finally {
      setLoading(false);
    }
  };

  const generatePersonalizedWords = async () => {
    if (!learningGoal) {
      toast.error('Укажите цель обучения в настройках');
      return;
    }

    setGeneratingWords(true);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'generate_personalized_words',
          student_id: studentId,
          learning_goal: learningGoal,
          language_level: languageLevel,
          count: 7
        })
      });

      const data = await response.json();
      
      if (data.success && data.words) {
        toast.success(`Добавлено ${data.count} персональных слов для вашей цели!`);
        await loadData();
      } else {
        toast.error(data.error || 'Ошибка генерации слов');
      }
    } catch (error) {
      console.error('Error generating words:', error);
      toast.error('Ошибка генерации слов');
    } finally {
      setGeneratingWords(false);
    }
  };

  const autoAssignWords = async () => {
    setAutoAssigning(true);
    try {
      const defaultWords = getDefaultWordsForLevel(languageLevel);
      
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'assign_words',
          teacher_id: studentId,
          student_id: studentId,
          word_ids: defaultWords.map(w => w.id)
        })
      });

      const data = await response.json();
      if (data.success) {
        toast.success('Слова добавлены для изучения!');
        loadData();
      }
    } catch (error) {
      console.error('Ошибка автоназначения:', error);
      toast.error('Не удалось добавить слова');
    } finally {
      setAutoAssigning(false);
    }
  };

  const getDefaultWordsForLevel = (level: string) => {
    return [];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'new': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'learning': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'learned': return 'bg-green-100 text-green-700 border-green-200';
      case 'mastered': return 'bg-purple-100 text-purple-700 border-purple-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
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
      <Card className="border border-blue-200 shadow-sm bg-gradient-to-br from-blue-50 to-indigo-50">
        <CardContent className="py-8">
          <div className="flex flex-col items-center gap-2">
            <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-sm text-gray-600">Загрузка слов...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const avgMastery = stats?.average_mastery || 0;

  return (
    <Card className="border border-blue-200 shadow-sm bg-gradient-to-br from-blue-50 to-indigo-50">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg font-bold">
            <Icon name="BookOpen" size={22} className="text-blue-600" />
            Мои слова
          </CardTitle>
          <Badge className="bg-blue-600 text-white text-sm px-3 py-1 font-bold">
            {words.length}
          </Badge>
        </div>
        
        {stats && words.length > 0 && (
          <div className="mt-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-gray-600">Средний прогресс</span>
              <span className="text-xs font-bold text-blue-600">{avgMastery.toFixed(0)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
              <div 
                className="bg-gradient-to-r from-blue-500 to-indigo-600 h-full rounded-full transition-all duration-500"
                style={{ width: `${avgMastery}%` }}
              ></div>
            </div>
            
            <div className="mt-3 grid grid-cols-4 gap-2">
              <div className="bg-white rounded-lg p-2 text-center border border-blue-200">
                <div className="text-lg font-bold text-blue-600">{stats.new}</div>
                <div className="text-xs text-gray-600">Новые</div>
              </div>
              <div className="bg-white rounded-lg p-2 text-center border border-yellow-200">
                <div className="text-lg font-bold text-yellow-600">{stats.learning}</div>
                <div className="text-xs text-gray-600">Изучаю</div>
              </div>
              <div className="bg-white rounded-lg p-2 text-center border border-green-200">
                <div className="text-lg font-bold text-green-600">{stats.learned}</div>
                <div className="text-xs text-gray-600">Выучено</div>
              </div>
              <div className="bg-white rounded-lg p-2 text-center border border-purple-200">
                <div className="text-lg font-bold text-purple-600">{stats.mastered}</div>
                <div className="text-xs text-gray-600">Освоено</div>
              </div>
            </div>
          </div>
        )}
      </CardHeader>
      
      <CardContent>
        {words.length === 0 ? (
          <div className="text-center py-8 bg-white rounded-lg border-2 border-dashed border-blue-200">
            <Icon name="BookOpen" size={56} className="mx-auto mb-3 text-blue-300" />
            <p className="text-base font-semibold text-gray-700 mb-1">
              {!teacherId ? 'Начни самостоятельное обучение' : 'Пока нет слов'}
            </p>
            <p className="text-sm text-gray-500 mb-4">
              {!teacherId 
                ? 'Бот автоматически подберет слова под твой уровень'
                : 'Преподаватель скоро назначит слова для изучения'}
            </p>
            {!teacherId && (
              <div className="flex flex-col gap-2">
                <Button
                  onClick={generatePersonalizedWords}
                  disabled={generatingWords || !learningGoal}
                  className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 h-10 text-white"
                >
                  {generatingWords ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                      Генерация слов...
                    </>
                  ) : (
                    <>
                      <Icon name="Sparkles" className="mr-2 h-4 w-4" />
                      Персональные слова для моей цели
                    </>
                  )}
                </Button>
                {!learningGoal && (
                  <p className="text-xs text-gray-500 text-center">
                    Укажите цель обучения в настройках
                  </p>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex gap-2">
              <Input
                type="text"
                placeholder="Поиск по словам..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="flex-1 h-10 text-sm bg-white"
              />
              {!teacherId && learningGoal && stats && stats.mastered === stats.total_words && stats.total_words > 0 && (
                <Button
                  onClick={generatePersonalizedWords}
                  disabled={generatingWords}
                  size="sm"
                  className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white whitespace-nowrap"
                >
                  {generatingWords ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <>
                      <Icon name="Plus" size={16} className="mr-1" />
                      Новые слова
                    </>
                  )}
                </Button>
              )}
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto">
              {filteredWords.map((word) => (
                <div
                  key={word.id}
                  className="p-3 rounded-lg bg-white border border-gray-200 hover:border-blue-300 hover:shadow-sm transition-all"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="text-base font-bold text-gray-900 truncate">
                          {word.english_text}
                        </h3>
                        <Badge className={`text-xs px-2 py-0.5 border ${getStatusColor(word.progress_status)}`}>
                          {getStatusText(word.progress_status)}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600">
                        {word.russian_translation}
                      </p>
                      
                      {word.mastery_score > 0 && (
                        <div className="mt-2">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-gray-500">Прогресс</span>
                            <span className="text-xs font-semibold text-gray-700">{word.mastery_score.toFixed(0)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-1.5 overflow-hidden">
                            <div 
                              className={`h-full rounded-full transition-all ${
                                word.mastery_score >= 75 ? 'bg-green-500' :
                                word.mastery_score >= 50 ? 'bg-yellow-500' :
                                'bg-blue-500'
                              }`}
                              style={{ width: `${word.mastery_score}%` }}
                            ></div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {filteredWords.length === 0 && (
              <div className="text-center py-6 text-sm text-gray-500">
                <Icon name="Search" size={32} className="mx-auto mb-2 opacity-30" />
                Ничего не найдено
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}