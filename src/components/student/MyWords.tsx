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
      <Card>
        <CardContent className="py-12">
          <div className="flex flex-col items-center gap-3">
            <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-muted-foreground">Загрузка слов...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Icon name="BookOpen" size={24} />
              Мои слова для изучения
            </CardTitle>
            <Badge variant="secondary" className="text-lg px-4 py-1">
              {words.length}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          {words.length === 0 ? (
            <div className="text-center py-12">
              <Icon name="BookOpen" size={64} className="mx-auto mb-4 text-muted-foreground opacity-50" />
              <p className="text-lg text-muted-foreground">
                Пока нет слов для изучения
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                Ваш преподаватель добавит слова позже
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <Input
                type="text"
                placeholder="Поиск по словам..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full"
              />

              <div className="space-y-3">
                {filteredWords.map((word) => (
                  <Card key={word.id} className="border-2 hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="text-xl font-bold text-primary">
                              {word.english_text}
                            </h3>
                            {word.status === 'completed' && (
                              <Badge variant="default" className="bg-green-500">
                                <Icon name="Check" className="h-3 w-3 mr-1" />
                                Выучено
                              </Badge>
                            )}
                          </div>
                          <p className="text-lg text-muted-foreground">
                            {word.russian_translation}
                          </p>
                          <p className="text-xs text-muted-foreground mt-2">
                            Добавлено: {new Date(word.assigned_at).toLocaleDateString('ru-RU')}
                          </p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {filteredWords.length === 0 && searchQuery && (
                <div className="text-center py-8">
                  <Icon name="Search" size={48} className="mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">Ничего не найдено</p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
