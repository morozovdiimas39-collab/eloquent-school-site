import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
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

interface AssignWordsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  teacherId: number;
}

export default function AssignWordsDialog({ open, onOpenChange, teacherId }: AssignWordsDialogProps) {
  const [step, setStep] = useState<1 | 2>(1);
  const [categories, setCategories] = useState<Category[]>([]);
  const [words, setWords] = useState<Word[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [selectedStudent, setSelectedStudent] = useState<number | null>(null);
  const [selectedWords, setSelectedWords] = useState<Set<number>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      loadCategories();
      loadStudents();
      setStep(1);
      setSelectedStudent(null);
      setSelectedWords(new Set());
      setSearchQuery('');
      setCategoryFilter(null);
    }
  }, [open]);

  useEffect(() => {
    if (step === 2) {
      loadWords();
    }
  }, [step, searchQuery, categoryFilter]);

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
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'get_students',
          telegram_id: teacherId
        })
      });
      const data = await response.json();
      setStudents(data.students || []);
    } catch (error) {
      console.error(error);
    }
  };

  const getStudentName = (student: Student) => {
    return student.first_name || student.username || `ID: ${student.telegram_id}`;
  };

  const getCategoryName = (categoryId: number | null) => {
    if (!categoryId) return 'Без категории';
    const category = categories.find(c => c.id === categoryId);
    return category?.name || 'Неизвестно';
  };

  const toggleWord = (wordId: number) => {
    setSelectedWords(prev => {
      const newSet = new Set(prev);
      if (newSet.has(wordId)) {
        newSet.delete(wordId);
      } else {
        newSet.add(wordId);
      }
      return newSet;
    });
  };

  const selectAllWords = () => {
    if (selectedWords.size === words.length) {
      setSelectedWords(new Set());
    } else {
      setSelectedWords(new Set(words.map(w => w.id)));
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
        toast.success('Категория назначена ученику');
        onOpenChange(false);
      } else {
        toast.error(data.error || 'Ошибка назначения');
      }
    } catch (error) {
      console.error(error);
      toast.error('Ошибка сети');
    }
  };

  const assignWords = async () => {
    if (!selectedStudent || selectedWords.size === 0) return;

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
        toast.success(`Назначено ${selectedWords.size} слов`);
        onOpenChange(false);
      } else {
        toast.error(data.error || 'Ошибка назначения');
      }
    } catch (error) {
      console.error(error);
      toast.error('Ошибка сети');
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Icon name="BookPlus" size={20} />
            {step === 1 ? 'Выбери ученика' : 'Выбери слова'}
          </DialogTitle>
        </DialogHeader>

        {step === 1 && (
          <div className="space-y-4 py-2">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Выбери ученика
              </label>
              {students.length > 0 ? (
                <Select
                  value={selectedStudent?.toString() || ''}
                  onValueChange={(value) => {
                    setSelectedStudent(parseInt(value));
                  }}
                >
                  <SelectTrigger className="h-11">
                    <SelectValue placeholder="Выбери ученика" />
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
                <div className="text-center py-3 text-sm text-muted-foreground border rounded-lg bg-gray-50">
                  У вас пока нет учеников
                </div>
              )}
            </div>

            <Button
              onClick={() => setStep(2)}
              disabled={!selectedStudent}
              className="w-full h-11 text-base font-semibold"
            >
              Далее
              <Icon name="ChevronRight" size={16} className="ml-2" />
            </Button>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-3 py-2">
            <Button
              variant="outline"
              onClick={() => setStep(1)}
              className="w-full h-10 text-sm"
            >
              <Icon name="ChevronLeft" size={16} className="mr-2" />
              Назад к выбору ученика
            </Button>

            <div>
              <label className="text-sm font-medium mb-2 block">
                Выбери слова
              </label>
              
              <div className="flex flex-col sm:flex-row gap-2 mb-3">
                <Input
                  type="text"
                  placeholder="Поиск слов..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1 h-10 text-sm"
                />
                <Select
                  value={categoryFilter === null ? 'all' : categoryFilter.toString()}
                  onValueChange={(value) => {
                    setCategoryFilter(value === 'all' ? null : parseInt(value));
                  }}
                >
                  <SelectTrigger className="w-full sm:w-[180px] h-10 text-sm">
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

              <div className="flex items-center justify-between mb-2">
                <Button variant="outline" size="sm" onClick={selectAllWords} className="h-8 text-xs">
                  {selectedWords.size === words.length ? 'Снять' : 'Выбрать все'}
                </Button>
                <Badge variant="secondary" className="text-xs font-semibold">
                  Выбрано: {selectedWords.size}
                </Badge>
              </div>

              {loading ? (
                <div className="text-center py-6">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : words.length === 0 ? (
                <div className="text-center py-6 text-sm text-muted-foreground">
                  Слова не найдены
                </div>
              ) : (
                <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
                  {words.map((word) => (
                    <div
                      key={word.id}
                      className="flex items-center gap-2.5 p-2.5 rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50/30 transition-all cursor-pointer"
                      onClick={(e) => {
                        e.preventDefault();
                        toggleWord(word.id);
                      }}
                    >
                      <Checkbox
                        checked={selectedWords.has(word.id)}
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setSelectedWords(prev => new Set([...prev, word.id]));
                          } else {
                            setSelectedWords(prev => {
                              const newSet = new Set(prev);
                              newSet.delete(word.id);
                              return newSet;
                            });
                          }
                        }}
                        className="shrink-0"
                        onClick={(e) => e.stopPropagation()}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5 mb-0.5">
                          <span className="font-medium text-sm truncate">{word.english_text}</span>
                          <span className="text-xs px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-600 shrink-0">
                            {getCategoryName(word.category_id)}
                          </span>
                        </div>
                        <span className="text-xs text-muted-foreground block truncate">
                          {word.russian_translation}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <Button
                onClick={assignWords}
                disabled={selectedWords.size === 0}
                className="w-full h-11 text-base font-semibold mt-3"
              >
                <Icon name="Send" size={16} className="mr-2" />
                Назначить ({selectedWords.size})
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}