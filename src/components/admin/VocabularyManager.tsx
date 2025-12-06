import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import Icon from '@/components/ui/icon';
import { toast } from 'sonner';

const API_URL = 'https://functions.poehali.dev/42c13bf2-f4d5-4710-9170-596c38d438a4';

interface Category {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

interface Word {
  id: number;
  category_id: number;
  english_text: string;
  russian_translation: string;
  created_at: string;
}

export default function VocabularyManager() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [words, setWords] = useState<Word[]>([]);
  const [loading, setLoading] = useState(false);
  const [categoryDialogOpen, setCategoryDialogOpen] = useState(false);
  const [wordDialogOpen, setWordDialogOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [editingWord, setEditingWord] = useState<Word | null>(null);

  const [categoryForm, setCategoryForm] = useState({ name: '', description: '' });
  const [wordForm, setWordForm] = useState({ english_text: '', russian_translation: '' });

  useEffect(() => {
    loadCategories();
  }, []);

  useEffect(() => {
    if (selectedCategory) {
      loadWords(selectedCategory);
    }
  }, [selectedCategory]);

  const loadCategories = async () => {
    setLoading(true);
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
    } finally {
      setLoading(false);
    }
  };

  const loadWords = async (categoryId: number) => {
    setLoading(true);
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'get_words', category_id: categoryId })
      });
      const data = await response.json();
      setWords(data.words || []);
    } catch (error) {
      toast.error('Ошибка загрузки слов');
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
      }
    } catch (error) {
      toast.error('Ошибка создания категории');
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
      }
    } catch (error) {
      toast.error('Ошибка обновления категории');
    }
  };

  const handleCreateWord = async () => {
    if (!selectedCategory || !wordForm.english_text.trim() || !wordForm.russian_translation.trim()) {
      toast.error('Заполните все поля');
      return;
    }

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'create_word',
          category_id: selectedCategory,
          english_text: wordForm.english_text,
          russian_translation: wordForm.russian_translation
        })
      });
      const data = await response.json();
      if (data.word) {
        toast.success('Слово добавлено');
        loadWords(selectedCategory);
        setWordDialogOpen(false);
        setWordForm({ english_text: '', russian_translation: '' });
      }
    } catch (error) {
      toast.error('Ошибка добавления слова');
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
        loadWords(selectedCategory!);
        setWordDialogOpen(false);
        setEditingWord(null);
        setWordForm({ english_text: '', russian_translation: '' });
      }
    } catch (error) {
      toast.error('Ошибка обновления слова');
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
      setWordForm({ english_text: word.english_text, russian_translation: word.russian_translation });
    } else {
      setEditingWord(null);
      setWordForm({ english_text: '', russian_translation: '' });
    }
    setWordDialogOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Управление словарем</h2>
        <Dialog open={categoryDialogOpen} onOpenChange={setCategoryDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => openCategoryDialog()}>
              <Icon name="Plus" className="mr-2 h-4 w-4" />
              Добавить категорию
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editingCategory ? 'Редактировать категорию' : 'Новая категория'}</DialogTitle>
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
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Категории</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {loading && categories.length === 0 ? (
              <p className="text-sm text-muted-foreground">Загрузка...</p>
            ) : categories.length === 0 ? (
              <p className="text-sm text-muted-foreground">Нет категорий</p>
            ) : (
              categories.map((category) => (
                <div
                  key={category.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedCategory === category.id
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-accent'
                  }`}
                  onClick={() => setSelectedCategory(category.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="font-medium">{category.name}</p>
                      {category.description && (
                        <p className="text-xs opacity-80 mt-1">{category.description}</p>
                      )}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        openCategoryDialog(category);
                      }}
                    >
                      <Icon name="Edit" className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card className="md:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>
                {selectedCategory ? `Слова в категории` : 'Выберите категорию'}
              </CardTitle>
              {selectedCategory && (
                <Dialog open={wordDialogOpen} onOpenChange={setWordDialogOpen}>
                  <DialogTrigger asChild>
                    <Button size="sm" onClick={() => openWordDialog()}>
                      <Icon name="Plus" className="mr-2 h-4 w-4" />
                      Добавить слово
                    </Button>
                  </DialogTrigger>
                  <DialogContent>
                    <DialogHeader>
                      <DialogTitle>{editingWord ? 'Редактировать слово' : 'Новое слово'}</DialogTitle>
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
                      <Button onClick={editingWord ? handleUpdateWord : handleCreateWord} className="w-full">
                        {editingWord ? 'Сохранить' : 'Добавить'}
                      </Button>
                    </div>
                  </DialogContent>
                </Dialog>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {!selectedCategory ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                Выберите категорию слева, чтобы увидеть слова
              </p>
            ) : loading ? (
              <p className="text-sm text-muted-foreground">Загрузка...</p>
            ) : words.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                В этой категории пока нет слов
              </p>
            ) : (
              <div className="grid gap-3">
                {words.map((word) => (
                  <div
                    key={word.id}
                    className="flex items-center justify-between p-4 rounded-lg border bg-card hover:bg-accent transition-colors"
                  >
                    <div className="flex-1">
                      <p className="font-medium text-lg">{word.english_text}</p>
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
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
