import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import Icon from '@/components/ui/icon';

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

interface WordDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editingWord: Word | null;
  wordForm: { 
    english_text: string; 
    russian_translation: string;
    category_id: number | null;
  };
  setWordForm: (form: { 
    english_text: string; 
    russian_translation: string;
    category_id: number | null;
  }) => void;
  categories: Category[];
  onSave: () => void;
}

export default function WordDialog({
  open,
  onOpenChange,
  editingWord,
  wordForm,
  setWordForm,
  categories,
  onSave
}: WordDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {editingWord ? 'Редактировать слово' : 'Новое слово'}
          </DialogTitle>
          <DialogDescription>
            {editingWord 
              ? 'Измените данные слова' 
              : 'Добавьте новое слово в словарь'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label htmlFor="english-text">Английское слово/фраза</Label>
            <Input
              id="english-text"
              value={wordForm.english_text}
              onChange={(e) => setWordForm({ ...wordForm, english_text: e.target.value })}
              placeholder="hello"
            />
          </div>
          <div>
            <Label htmlFor="russian-translation">Русский перевод</Label>
            <Input
              id="russian-translation"
              value={wordForm.russian_translation}
              onChange={(e) => setWordForm({ ...wordForm, russian_translation: e.target.value })}
              placeholder="привет"
            />
          </div>
          {!editingWord && (
            <div>
              <Label htmlFor="word-category">Категория (опционально)</Label>
              <Select
                value={wordForm.category_id?.toString() || 'none'}
                onValueChange={(value) => 
                  setWordForm({ 
                    ...wordForm, 
                    category_id: value === 'none' ? null : parseInt(value) 
                  })
                }
              >
                <SelectTrigger id="word-category">
                  <SelectValue placeholder="Без категории" />
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
          <Button onClick={onSave} className="w-full">
            <Icon name="Save" size={16} className="mr-2" />
            {editingWord ? 'Сохранить' : 'Добавить'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
