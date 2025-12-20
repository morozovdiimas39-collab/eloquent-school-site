import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import Icon from '@/components/ui/icon';

interface Category {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

interface CategoryDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editingCategory: Category | null;
  categoryForm: { name: string; description: string };
  setCategoryForm: (form: { name: string; description: string }) => void;
  onSave: () => void;
}

export default function CategoryDialog({
  open,
  onOpenChange,
  editingCategory,
  categoryForm,
  setCategoryForm,
  onSave
}: CategoryDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {editingCategory ? 'Редактировать категорию' : 'Новая категория'}
          </DialogTitle>
          <DialogDescription>
            {editingCategory 
              ? 'Измените данные категории' 
              : 'Создайте новую категорию для организации слов'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <Label htmlFor="category-name">Название категории</Label>
            <Input
              id="category-name"
              value={categoryForm.name}
              onChange={(e) => setCategoryForm({ ...categoryForm, name: e.target.value })}
              placeholder="Например: Еда, Путешествия"
            />
          </div>
          <div>
            <Label htmlFor="category-description">Описание (опционально)</Label>
            <Textarea
              id="category-description"
              value={categoryForm.description}
              onChange={(e) => setCategoryForm({ ...categoryForm, description: e.target.value })}
              placeholder="Краткое описание категории"
            />
          </div>
          <Button onClick={onSave} className="w-full">
            <Icon name="Save" size={16} className="mr-2" />
            {editingCategory ? 'Сохранить' : 'Создать'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
