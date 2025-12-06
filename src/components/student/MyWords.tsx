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
}

interface MyWordsProps {
  studentId: number;
}

export default function MyWords({ studentId }: MyWordsProps) {
  const [words, setWords] = useState<AssignedWord[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadWords();
  }, []);

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
                        {word.status === 'completed' && (
                          <Badge className="bg-green-500 text-white text-xs px-1.5 py-0">
                            <Icon name="Check" className="h-3 w-3 mr-0.5" />
                            Выучено
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-700">
                        {word.russian_translation}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        {new Date(word.assigned_at).toLocaleDateString('ru-RU')}
                      </p>
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