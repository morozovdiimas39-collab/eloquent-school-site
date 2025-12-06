import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import Icon from '@/components/ui/icon';
import { toast } from 'sonner';
import funcUrls from '../../../backend/func2url.json';

const API_URL = funcUrls['webapp-api'];

interface Category {
  id: number;
  name: string;
  description: string | null;
}

interface Word {
  id: number;
  category_id: number | null;
  english_text: string;
  russian_translation: string;
}

interface Student {
  telegram_id: number;
  username?: string;
  first_name?: string;
  last_name?: string;
}

interface AssignWordsProps {
  teacherId: number;
}

export default function AssignWords({ teacherId }: AssignWordsProps) {
  const [categories, setCategories] = useState<Category[]>([]);
  const [words, setWords] = useState<Word[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedStudent, setSelectedStudent] = useState<number | null>(null);
  const [selectedWords, setSelectedWords] = useState<Set<number>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadCategories();
    loadStudents();
  }, []);

  useEffect(() => {
    loadWords();
  }, [searchQuery, categoryFilter]);

  const loadCategories = async () => {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'get_categories' })
      });
      const data = await response.json();
      setCategories(data.categories || []);
    } catch (error) {
      console.error(error);
    }
  };

  const loadWords = async () => {
    setLoading(true);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'search_words',
          search_query: searchQuery || null,
          category_id: categoryFilter,
          limit: 1000,
          offset: 0
        })
      });
      const data = await response.json();
      setWords(data.words || []);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const loadStudents = async () => {
    try {
      console.log('Loading students for teacher:', teacherId);
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'get_students',
          telegram_id: teacherId
        })
      });
      const data = await response.json();
      console.log('Students response:', data);
      setStudents(data.students || []);
    } catch (error) {
      console.error('Error loading students:', error);
    }
  };

  const toggleWord = (wordId: number) => {
    const newSelected = new Set(selectedWords);
    if (newSelected.has(wordId)) {
      newSelected.delete(wordId);
    } else {
      newSelected.add(wordId);
    }
    setSelectedWords(newSelected);
  };

  const selectAllWords = () => {
    if (selectedWords.size === words.length) {
      setSelectedWords(new Set());
    } else {
      setSelectedWords(new Set(words.map(w => w.id)));
    }
  };

  const assignWords = async () => {
    if (!selectedStudent || selectedWords.size === 0) {
      toast.error('Выберите ученика и хотя бы одно слово');
      return;
    }

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'assign_words',
          teacher_id: teacherId,
          student_id: selectedStudent,
          word_ids: Array.from(selectedWords)
        })
      });
      const data = await response.json();
      
      if (data.success) {
        toast.success(`Назначено слов: ${data.assigned_count}`);
        setSelectedWords(new Set());
      } else {
        toast.error('Ошибка назначения');
      }
    } catch (error) {
      toast.error('Ошибка назначения слов');
      console.error(error);
    }
  };

  const assignCategory = async (categoryId: number) => {
    if (!selectedStudent) {
      toast.error('Выберите ученика');
      return;
    }

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'assign_category',
          teacher_id: teacherId,
          student_id: selectedStudent,
          category_id: categoryId
        })
      });
      const data = await response.json();
      
      if (data.success) {
        toast.success(`Назначена категория: ${data.assigned_count} слов`);
      } else {
        toast.error('Ошибка назначения категории');
      }
    } catch (error) {
      toast.error('Ошибка назначения категории');
      console.error(error);
    }
  };

  const getCategoryName = (categoryId: number | null) => {
    if (!categoryId) return 'Без категории';
    const category = categories.find(c => c.id === categoryId);
    return category ? category.name : 'Без категории';
  };

  const getStudentName = (student: Student) => {
    return student.first_name || student.username || `ID: ${student.telegram_id}`;
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Назначить слова ученику</CardTitle>
          <CardDescription>
            Выберите ученика, затем выберите слова или целую категорию
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Выберите ученика (найдено: {students.length})
              </label>
              {students.length > 0 ? (
                <Select
                  value={selectedStudent?.toString() || ''}
                  onValueChange={(value) => {
                    console.log('Student selected:', value);
                    setSelectedStudent(parseInt(value));
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Выберите ученика" />
                  </SelectTrigger>
                  <SelectContent>
                    {students.map((student) => (
                      <SelectItem key={student.telegram_id} value={student.telegram_id.toString()}>
                        {getStudentName(student)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <div className="text-center py-4 text-muted-foreground border rounded-lg">
                  У вас пока нет учеников. Поделитесь промокодом со студентами.
                </div>
              )}
          </div>
        </CardContent>
      </Card>

      {categories.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Назначить категорию целиком</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {categories.map((category) => (
                <Button
                  key={category.id}
                  variant="outline"
                  size="sm"
                  onClick={() => assignCategory(category.id)}
                  disabled={!selectedStudent}
                >
                  <Icon name="FolderPlus" className="mr-2 h-4 w-4" />
                  {category.name}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Выбрать отдельные слова</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <Input
              type="text"
              placeholder="Поиск слов..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1"
            />
            <Select
              value={categoryFilter === null ? 'all' : categoryFilter.toString()}
              onValueChange={(value) => {
                setCategoryFilter(value === 'all' ? null : parseInt(value));
              }}
            >
              <SelectTrigger className="w-full sm:w-[200px]">
                <SelectValue placeholder="Все категории" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Все категории</SelectItem>
                {categories.map((cat) => (
                  <SelectItem key={cat.id} value={cat.id.toString()}>
                    {cat.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center justify-between">
            <Button variant="outline" size="sm" onClick={selectAllWords}>
              {selectedWords.size === words.length ? 'Снять выделение' : 'Выбрать все'}
            </Button>
            <Badge variant="secondary">
              Выбрано: {selectedWords.size} из {words.length}
            </Badge>
          </div>

          {loading ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : words.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              Слова не найдены
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {words.map((word) => (
                <div
                  key={word.id}
                  className="flex items-center gap-3 p-3 rounded-lg border hover:bg-accent transition-colors cursor-pointer"
                  onClick={() => toggleWord(word.id)}
                >
                  <Checkbox
                    checked={selectedWords.has(word.id)}
                    onCheckedChange={() => toggleWord(word.id)}
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{word.english_text}</span>
                      <span className="text-xs px-2 py-1 rounded-full bg-secondary">
                        {getCategoryName(word.category_id)}
                      </span>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {word.russian_translation}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          <Button
            onClick={assignWords}
            disabled={!selectedStudent || selectedWords.size === 0}
            className="w-full"
          >
            <Icon name="Send" className="mr-2 h-4 w-4" />
            Назначить выбранные слова ({selectedWords.size})
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}