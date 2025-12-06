import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import Icon from '@/components/ui/icon';
import { toast } from 'sonner';

const API_URL = 'https://functions.poehali.dev/42c13bf2-f4d5-4710-9170-596c38d438a4';
const ITEMS_PER_PAGE = 50;

interface Category {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

interface Word {
  id: number;
  category_id: number | null;
  english_text: string;
  russian_translation: string;
  created_at: string;
}

interface SearchResult {
  words: Word[];
  total: number;
  limit: number;
  offset: number;
}

export default function VocabularyManager() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [words, setWords] = useState<Word[]>([]);
  const [totalWords, setTotalWords] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<number | null>(null);
  
  const [categoryDialogOpen, setCategoryDialogOpen] = useState(false);
  const [wordDialogOpen, setWordDialogOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [editingWord, setEditingWord] = useState<Word | null>(null);

  const [categoryForm, setCategoryForm] = useState({ name: '', description: '' });
  const [wordForm, setWordForm] = useState({ 
    english_text: '', 
    russian_translation: '',
    category_id: null as number | null 
  });

  useEffect(() => {
    loadCategories();
    loadWords();
  }, []);

  useEffect(() => {
    setCurrentPage(1);
    loadWords();
  }, [searchQuery, selectedCategoryFilter]);

  useEffect(() => {
    loadWords();
  }, [currentPage]);

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
      toast.error('Ошибка загрузки категорий');
      console.error(error);
    }
  };

  const loadWords = async () => {
    setLoading(true);
    try {
      const offset = (currentPage - 1) * ITEMS_PER_PAGE;
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'search_words',
          search_query: searchQuery || null,
          category_id: selectedCategoryFilter,
          limit: ITEMS_PER_PAGE,
          offset: offset
        })
      });
      const data: SearchResult = await response.json();
      setWords(data.words || []);
      setTotalWords(data.total || 0);
    } catch (error) {
      toast.error('Ошибка загрузки слов');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCategory = async () => {
    if (!categoryForm.name.trim()) {
      toast.error('Введите название категории');
      return;
    }

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'create_category',
          name: categoryForm.name,
          description: categoryForm.description || null
        })
      });
      const data = await response.json();
      if (data.category) {
        toast.success('Категория создана');
        loadCategories();
        setCategoryDialogOpen(false);
        setCategoryForm({ name: '', description: '' });
      } else if (data.error) {
        toast.error(data.error);
      }
    } catch (error) {
      toast.error('Ошибка создания категории');
      console.error(error);
    }
  };

  const handleUpdateCategory = async () => {
    if (!editingCategory || !categoryForm.name.trim()) return;

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'update_category',
          category_id: editingCategory.id,
          name: categoryForm.name,
          description: categoryForm.description || null
        })
      });
      const data = await response.json();
      if (data.category) {
        toast.success('Категория обновлена');
        loadCategories();
        setCategoryDialogOpen(false);
        setEditingCategory(null);
        setCategoryForm({ name: '', description: '' });
      } else if (data.error) {
        toast.error(data.error);
      }
    } catch (error) {
      toast.error('Ошибка обновления категории');
      console.error(error);
    }
  };

  const handleCreateWord = async () => {
    if (!wordForm.english_text.trim() || !wordForm.russian_translation.trim()) {
      toast.error('Заполните оба поля');
      return;
    }

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'create_word',
          english_text: wordForm.english_text,
          russian_translation: wordForm.russian_translation,
          category_id: wordForm.category_id || null
        })
      });
      const data = await response.json();
      if (data.word) {
        toast.success('Слово добавлено');
        loadWords();
        setWordDialogOpen(false);
        setWordForm({ english_text: '', russian_translation: '', category_id: null });
      } else if (data.error) {
        toast.error(data.error);
      }
    } catch (error) {
      toast.error('Ошибка добавления слова');
      console.error(error);
    }
  };

  const handleUpdateWord = async () => {
    if (!editingWord || !wordForm.english_text.trim() || !wordForm.russian_translation.trim()) return;

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'update_word',
          word_id: editingWord.id,
          english_text: wordForm.english_text,
          russian_translation: wordForm.russian_translation
        })
      });
      const data = await response.json();
      if (data.word) {
        toast.success('Слово обновлено');
        loadWords();
        setWordDialogOpen(false);
        setEditingWord(null);
        setWordForm({ english_text: '', russian_translation: '', category_id: null });
      } else if (data.error) {
        toast.error(data.error);
      }
    } catch (error) {
      toast.error('Ошибка обновления слова');
      console.error(error);
    }
  };

  const openCategoryDialog = (category?: Category) => {
    if (category) {
      setEditingCategory(category);
      setCategoryForm({ name: category.name, description: category.description || '' });
    } else {
      setEditingCategory(null);
      setCategoryForm({ name: '', description: '' });
    }
    setCategoryDialogOpen(true);
  };

  const openWordDialog = (word?: Word) => {
    if (word) {
      setEditingWord(word);
      setWordForm({ 
        english_text: word.english_text, 
        russian_translation: word.russian_translation,
        category_id: word.category_id 
      });
    } else {
      setEditingWord(null);
      setWordForm({ english_text: '', russian_translation: '', category_id: null });
    }
    setWordDialogOpen(true);
  };

  const totalPages = Math.ceil(totalWords / ITEMS_PER_PAGE);

  const getCategoryName = (categoryId: number | null) => {
    if (!categoryId) return 'Без категории';
    const category = categories.find(c => c.id === categoryId);
    return category ? category.name : 'Без категории';
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">Управление словарем</h2>
          <p className="text-muted-foreground">Всего слов: {totalWords}</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={categoryDialogOpen} onOpenChange={setCategoryDialogOpen}>
            <DialogTrigger asChild>
              <Button onClick={() => openCategoryDialog()} variant="outline">
                <Icon name="FolderPlus" className="mr-2 h-4 w-4" />
                Категория
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{editingCategory ? 'Редактировать категорию' : 'Новая категория'}</DialogTitle>
                <DialogDescription>
                  {editingCategory ? 'Измените название или описание категории' : 'Создайте категорию для группировки слов'}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="category-name">Название</Label>
                  <Input
                    id="category-name"
                    value={categoryForm.name}
                    onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
                    placeholder="Например: Животные"
                  />
                </div>
                <div>
                  <Label htmlFor="category-desc">Описание (опционально)</Label>
                  <Textarea
                    id="category-desc"
                    value={categoryForm.description}
                    onChange={(e) => setCategoryForm({ ...categoryForm, description: e.target.value })}
                    placeholder="Краткое описание категории"
                  />
                </div>
                <Button onClick={editingCategory ? handleUpdateCategory : handleCreateCategory} className="w-full">
                  {editingCategory ? 'Сохранить' : 'Создать'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>

          <Dialog open={wordDialogOpen} onOpenChange={setWordDialogOpen}>
            <DialogTrigger asChild>
              <Button onClick={() => openWordDialog()}>
                <Icon name="Plus" className="mr-2 h-4 w-4" />
                Добавить слово
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{editingWord ? 'Редактировать слово' : 'Новое слово'}</DialogTitle>
                <DialogDescription>
                  {editingWord ? 'Измените перевод или текст слова' : 'Добавьте английское слово и его перевод'}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="english">Английский</Label>
                  <Input
                    id="english"
                    value={wordForm.english_text}
                    onChange={(e) => setWordForm({ ...wordForm, english_text: e.target.value })}
                    placeholder="cat"
                  />
                </div>
                <div>
                  <Label htmlFor="russian">Русский перевод</Label>
                  <Input
                    id="russian"
                    value={wordForm.russian_translation}
                    onChange={(e) => setWordForm({ ...wordForm, russian_translation: e.target.value })}
                    placeholder="кошка"
                  />
                </div>
                {!editingWord && (
                  <div>
                    <Label htmlFor="category">Категория (опционально)</Label>
                    <Select 
                      value={wordForm.category_id?.toString() || 'none'} 
                      onValueChange={(value) => setWordForm({ 
                        ...wordForm, 
                        category_id: value === 'none' ? null : parseInt(value) 
                      })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Выберите категорию" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Без категории</SelectItem>
                        {categories.map((cat) => (
                          <SelectItem key={cat.id} value={cat.id.toString()}>
                            {cat.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}
                <Button onClick={editingWord ? handleUpdateWord : handleCreateWord} className="w-full">
                  {editingWord ? 'Сохранить' : 'Добавить'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <Input
            type="text"
            placeholder="Поиск по английскому или русскому..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full"
          />
        </div>
        <Select 
          value={selectedCategoryFilter === null ? 'all' : selectedCategoryFilter === 0 ? 'uncategorized' : selectedCategoryFilter.toString()} 
          onValueChange={(value) => {
            if (value === 'all') setSelectedCategoryFilter(null);
            else if (value === 'uncategorized') setSelectedCategoryFilter(0);
            else setSelectedCategoryFilter(parseInt(value));
          }}
        >
          <SelectTrigger className="w-full sm:w-[200px]">
            <SelectValue placeholder="Все категории" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Все категории</SelectItem>
            <SelectItem value="uncategorized">Без категории</SelectItem>
            {categories.map((cat) => (
              <SelectItem key={cat.id} value={cat.id.toString()}>
                {cat.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {categories.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Категории</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {categories.map((category) => (
                <div
                  key={category.id}
                  className="flex items-center gap-2 px-3 py-1 rounded-full border bg-secondary/50 hover:bg-secondary transition-colors"
                >
                  <span className="text-sm font-medium">{category.name}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-5 w-5 p-0"
                    onClick={() => openCategoryDialog(category)}
                  >
                    <Icon name="Edit" className="h-3 w-3" />
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>
            {searchQuery ? `Результаты поиска` : selectedCategoryFilter !== null ? `Слова в категории` : 'Все слова'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <p className="text-sm text-muted-foreground mt-2">Загрузка...</p>
            </div>
          ) : words.length === 0 ? (
            <div className="text-center py-8">
              <Icon name="Search" size={48} className="mx-auto mb-4 text-muted-foreground" />
              <p className="text-muted-foreground">
                {searchQuery ? 'Ничего не найдено' : 'Нет слов. Добавьте первое слово!'}
              </p>
            </div>
          ) : (
            <>
              <div className="grid gap-3">
                {words.map((word) => (
                  <div
                    key={word.id}
                    className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-lg">{word.english_text}</p>
                        <span className="text-xs px-2 py-1 rounded-full bg-secondary">
                          {getCategoryName(word.category_id)}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground">{word.russian_translation}</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => openWordDialog(word)}
                    >
                      <Icon name="Edit" className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>

              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-6 pt-6 border-t">
                  <p className="text-sm text-muted-foreground">
                    Страница {currentPage} из {totalPages}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                    >
                      <Icon name="ChevronLeft" className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                    >
                      <Icon name="ChevronRight" className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
