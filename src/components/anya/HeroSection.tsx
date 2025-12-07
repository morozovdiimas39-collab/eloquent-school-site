import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';

interface HeroSectionProps {
  onStartDemo: () => void;
}

export default function HeroSection({ onStartDemo }: HeroSectionProps) {
  return (
    <section className="container mx-auto px-4 py-20 md:py-32">
      <div className="max-w-5xl mx-auto text-center space-y-8">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-100 text-blue-700 font-medium text-sm border border-blue-200">
          <Icon name="Sparkles" size={16} />
          <span>Твой личный ИИ-репетитор английского</span>
        </div>

        <h1 className="text-5xl md:text-7xl font-bold leading-tight">
          Учи английский
          <br />
          <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
            в разговорах с Аней
          </span>
        </h1>

        <p className="text-xl md:text-2xl text-gray-600 max-w-3xl mx-auto">
          Аня — это ИИ-репетитор, который общается с тобой на английском, исправляет ошибки и помогает запоминать новые слова. Как настоящий учитель, но в телеграме 24/7.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
          <Button
            onClick={onStartDemo}
            size="lg"
            className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 font-semibold text-lg h-14 px-8 shadow-xl"
          >
            Попробовать демо
            <Icon name="MessageSquare" size={20} className="ml-2" />
          </Button>
          <Button
            variant="outline"
            size="lg"
            className="font-semibold text-lg h-14 px-8 border-2"
            onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}
          >
            Как это работает
            <Icon name="Play" size={20} className="ml-2" />
          </Button>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-8 pt-8 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <Icon name="Check" size={18} className="text-green-600" />
            <span>Без скучных учебников</span>
          </div>
          <div className="flex items-center gap-2">
            <Icon name="Check" size={18} className="text-green-600" />
            <span>Живые диалоги</span>
          </div>
          <div className="flex items-center gap-2">
            <Icon name="Check" size={18} className="text-green-600" />
            <span>Персональный прогресс</span>
          </div>
        </div>
      </div>
    </section>
  );
}