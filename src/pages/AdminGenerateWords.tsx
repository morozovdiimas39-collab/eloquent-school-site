import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import Icon from '@/components/ui/icon';
import { toast } from 'sonner';
import { funcUrls } from '@/config/funcUrls';

const API_URL = funcUrls['webapp-api'];

interface Student {
  telegram_id: number;
  username: string;
  first_name: string;
  last_name: string;
  language_level: string;
  created_at: string;
}

interface GeneratedWord {
  id: number;
  english: string;
  russian: string;
}

export default function AdminGenerateWords() {
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  
  const [learningGoal, setLearningGoal] = useState('');
  const [count, setCount] = useState(10);
  const [generatedWords, setGeneratedWords] = useState<GeneratedWord[]>([]);
  const [duplicatesFound, setDuplicatesFound] = useState(0);

  useEffect(() => {
    loadStudents();
  }, []);

  const loadStudents = async () => {
    setLoading(true);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'get_all_students' })
      });
      const data = await response.json();
      setStudents(data.students || []);
    } catch (error) {
      console.error('Ошибка загрузки студентов:', error);
      toast.error('Ошибка загрузки студентов');
    } finally {
      setLoading(false);
    }
  };

  const generateWords = async () => {
    if (!selectedStudent) {
      toast.error('Выберите студента');
      return;
    }

    if (!learningGoal.trim()) {
      toast.error('Укажите цель обучения');
      return;
    }

    setGenerating(true);
    setGeneratedWords([]);
    setDuplicatesFound(0);

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'generate_unique_words',
          student_id: selectedStudent.telegram_id,
          learning_goal: learningGoal,
          language_level: selectedStudent.language_level,
          count: count
        })
      });

      const data = await response.json();

      if (data.error) {
        toast.error(`Ошибка: ${data.error}`);
        return;
      }

      if (data.success && data.words) {
        setGeneratedWords(data.words);
        setDuplicatesFound(data.duplicates_found || 0);
        toast.success(`Добавлено ${data.count} уникальных слов!`);
      } else {
        toast.error('Не удалось сгенерировать слова');
      }
    } catch (error) {
      console.error('Ошибка генерации:', error);
      toast.error('Ошибка генерации слов');
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
        <div className="max-w-6xl mx-auto">
          <Card>
            <CardContent className="py-8">
              <div className="flex flex-col items-center gap-2">
                <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <p className="text-sm text-gray-600">Загрузка...</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Генерация уникальных слов</h1>
            <p className="text-gray-600 mt-1">Создание персональных слов без дубликатов для студентов</p>
          </div>
          <Button variant="outline" onClick={() => window.location.href = '/admin'}>
            <Icon name="ArrowLeft" size={18} className="mr-2" />
            Назад
          </Button>
        </div>

        <Card className="border-2 border-blue-200 shadow-lg">
          <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
            <CardTitle className="flex items-center gap-2">
              <Icon name="Users" size={22} className="text-blue-600" />
              Выбор студента
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Студент
              </label>
              <Select
                value={selectedStudent?.telegram_id.toString()}
                onValueChange={(value) => {
                  const student = students.find(s => s.telegram_id.toString() === value);
                  setSelectedStudent(student || null);
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Выберите студента" />
                </SelectTrigger>
                <SelectContent>
                  {students.map((student) => (
                    <SelectItem key={student.telegram_id} value={student.telegram_id.toString()}>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">
                          {student.first_name} {student.last_name}
                        </span>
                        {student.username && (
                          <span className="text-gray-500">@{student.username}</span>
                        )}
                        <Badge className="ml-2 text-xs">{student.language_level}</Badge>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {selectedStudent && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <Icon name="User" size={20} className="text-blue-600 mt-0.5" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900">
                      {selectedStudent.first_name} {selectedStudent.last_name}
                    </h3>
                    {selectedStudent.username && (
                      <p className="text-sm text-gray-600">@{selectedStudent.username}</p>
                    )}
                    <div className="mt-2 flex items-center gap-2">
                      <Badge className="bg-blue-600 text-white">
                        Уровень: {selectedStudent.language_level}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {selectedStudent && (
          <Card className="border-2 border-green-200 shadow-lg">
            <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50">
              <CardTitle className="flex items-center gap-2">
                <Icon name="Sparkles" size={22} className="text-green-600" />
                Параметры генерации
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Цель обучения
                </label>
                <Input
                  type="text"
                  placeholder="Например: Путешествия, IT, Бизнес-английский..."
                  value={learningGoal}
                  onChange={(e) => setLearningGoal(e.target.value)}
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Gemini подберёт слова под эту цель и уровень студента
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Количество слов
                </label>
                <Input
                  type="number"
                  min={1}
                  max={50}
                  value={count}
                  onChange={(e) => setCount(parseInt(e.target.value) || 10)}
                  className="w-full"
                />
              </div>

              <Button
                onClick={generateWords}
                disabled={generating || !learningGoal.trim()}
                className="w-full bg-green-600 hover:bg-green-700 text-white"
                size="lg"
              >
                {generating ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                    Генерация...
                  </>
                ) : (
                  <>
                    <Icon name="Wand2" size={18} className="mr-2" />
                    Сгенерировать уникальные слова
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        )}

        {generatedWords.length > 0 && (
          <Card className="border-2 border-purple-200 shadow-lg">
            <CardHeader className="bg-gradient-to-r from-purple-50 to-pink-50">
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Icon name="CheckCircle" size={22} className="text-purple-600" />
                  Результат генерации
                </CardTitle>
                <div className="flex gap-2">
                  <Badge className="bg-purple-600 text-white">
                    {generatedWords.length} слов добавлено
                  </Badge>
                  {duplicatesFound > 0 && (
                    <Badge className="bg-yellow-600 text-white">
                      {duplicatesFound} дубликатов отфильтровано
                    </Badge>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {generatedWords.map((word) => (
                  <div
                    key={word.id}
                    className="p-3 rounded-lg bg-white border border-gray-200 hover:border-purple-300 hover:shadow-sm transition-all"
                  >
                    <h3 className="text-base font-bold text-gray-900">{word.english}</h3>
                    <p className="text-sm text-gray-600">{word.russian}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}