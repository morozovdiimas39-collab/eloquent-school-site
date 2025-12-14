import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import Icon from '@/components/ui/icon';
import { useNavigate } from 'react-router-dom';

type Approach = 'methodical' | 'urgent';

interface Topic {
  id: string;
  emoji: string;
  title: string;
}

export default function GoalTest() {
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  
  const [approach, setApproach] = useState<Approach>('methodical');
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);

  const approaches = [
    {
      id: 'methodical' as Approach,
      emoji: '📚',
      title: 'Методичное обучение',
      description: 'Последовательно повышаю уровень языка'
    },
    {
      id: 'urgent' as Approach,
      emoji: '⚡',
      title: 'Срочная подготовка',
      description: 'Нужно быстро подготовиться к событию'
    }
  ];

  const topics: Topic[] = [
    { id: 'movies', emoji: '🎬', title: 'Кино' },
    { id: 'technology', emoji: '💻', title: 'Технологии' },
    { id: 'travel', emoji: '✈️', title: 'Путешествия' },
    { id: 'sports', emoji: '⚽', title: 'Спорт' },
    { id: 'music', emoji: '🎵', title: 'Музыка' },
    { id: 'food', emoji: '🍕', title: 'Еда' },
    { id: 'books', emoji: '📚', title: 'Книги' },
    { id: 'business', emoji: '💼', title: 'Бизнес' },
    { id: 'art', emoji: '🎨', title: 'Искусство' },
    { id: 'science', emoji: '🔬', title: 'Наука' },
    { id: 'games', emoji: '🎮', title: 'Игры' },
    { id: 'fashion', emoji: '👗', title: 'Мода' },
    { id: 'health', emoji: '💪', title: 'Здоровье' },
    { id: 'nature', emoji: '🌿', title: 'Природа' },
    { id: 'pets', emoji: '🐶', title: 'Питомцы' },
    { id: 'cars', emoji: '🚗', title: 'Автомобили' }
  ];

  const handleTopicToggle = (topicId: string) => {
    setSelectedTopics(prev => 
      prev.includes(topicId) 
        ? prev.filter(t => t !== topicId)
        : prev.length < 5 
          ? [...prev, topicId]
          : prev
    );
  };

  const handleNext = () => {
    if (step === 1) {
      setStep(2);
    } else if (step === 2 && selectedTopics.length >= 2) {
      setStep(3);
    }
  };

  return (
    <div className="min-h-screen bg-[#f5f5f5] py-6 px-4">
      <div className="max-w-xl mx-auto">
        <Button
          onClick={() => navigate('/')}
          variant="ghost"
          size="sm"
          className="mb-4"
        >
          <Icon name="ArrowLeft" size={16} className="mr-2" />
          Назад
        </Button>

        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Шаг {step} из 2
            </span>
            <span className="text-sm text-gray-500">
              {step === 1 && 'Подход'}
              {step === 2 && 'Темы'}
              {step === 3 && 'Готово'}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-1.5">
            <div 
              className="bg-[#3390ec] h-1.5 rounded-full transition-all duration-300"
              style={{ width: `${(step / 2) * 100}%` }}
            />
          </div>
        </div>

        {step === 1 && (
          <Card className="shadow-sm border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl">Как хочешь заниматься?</CardTitle>
              <CardDescription className="text-gray-600">
                Выбери подход который тебе подходит
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <RadioGroup value={approach} onValueChange={(v) => setApproach(v as Approach)}>
                <div className="space-y-3">
                  {approaches.map((app) => (
                    <label
                      key={app.id}
                      className={`flex items-start gap-3 p-4 border-2 rounded-xl cursor-pointer transition-all ${
                        approach === app.id
                          ? 'border-[#3390ec] bg-[#e8f4fd]'
                          : 'border-gray-200 bg-white hover:border-gray-300'
                      }`}
                    >
                      <RadioGroupItem value={app.id} className="mt-1" />
                      <span className="text-3xl">{app.emoji}</span>
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900">{app.title}</div>
                        <div className="text-sm text-gray-600 mt-0.5">{app.description}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </RadioGroup>

              <Button
                onClick={handleNext}
                className="w-full h-12 text-base bg-[#3390ec] hover:bg-[#2a7dd4] mt-4"
              >
                Продолжить
                <Icon name="ArrowRight" size={20} className="ml-2" />
              </Button>
            </CardContent>
          </Card>
        )}

        {step === 2 && (
          <Card className="shadow-sm border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl">Какие темы тебе интересны?</CardTitle>
              <CardDescription className="text-gray-600">
                Выбери 2-5 тем, на которых хочешь практиковаться
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Выбрано: {selectedTopics.length} из 5</span>
                {selectedTopics.length >= 2 && selectedTopics.length <= 5 && (
                  <span className="text-green-600 font-medium flex items-center gap-1">
                    <Icon name="Check" size={16} />
                    Готово
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                {topics.map((topic) => (
                  <button
                    key={topic.id}
                    onClick={() => handleTopicToggle(topic.id)}
                    className={`flex flex-col items-center justify-center p-4 border-2 rounded-xl cursor-pointer transition-all ${
                      selectedTopics.includes(topic.id)
                        ? 'border-[#3390ec] bg-[#e8f4fd]'
                        : 'border-gray-200 bg-white hover:border-gray-300'
                    }`}
                  >
                    <span className="text-3xl mb-2">{topic.emoji}</span>
                    <span className="text-sm font-medium text-gray-900">{topic.title}</span>
                  </button>
                ))}
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  onClick={() => setStep(1)}
                  variant="outline"
                  className="flex-1"
                >
                  <Icon name="ChevronLeft" size={16} className="mr-2" />
                  Назад
                </Button>
                <Button
                  onClick={handleNext}
                  disabled={selectedTopics.length < 2}
                  className="flex-1 bg-[#3390ec] hover:bg-[#2a7dd4]"
                >
                  Готово
                  <Icon name="Check" size={20} className="ml-2" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {step === 3 && (
          <Card className="shadow-sm border-0 border-t-4 border-t-green-500">
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center">
                  <Icon name="Check" size={24} className="text-white" />
                </div>
                <div>
                  <CardTitle className="text-xl">Отлично!</CardTitle>
                  <CardDescription className="text-gray-600">
                    Настройка завершена
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 bg-gray-50 rounded-xl space-y-3">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">{approaches.find(a => a.id === approach)?.emoji}</span>
                    <span className="font-semibold text-gray-900">
                      {approaches.find(a => a.id === approach)?.title}
                    </span>
                  </div>
                </div>
                
                <div className="pt-2 border-t border-gray-200">
                  <div className="text-sm font-medium text-gray-700 mb-2">Твои темы:</div>
                  <div className="flex flex-wrap gap-2">
                    {selectedTopics.map((topicId) => {
                      const topic = topics.find(t => t.id === topicId);
                      return (
                        <div
                          key={topicId}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 rounded-full text-sm"
                        >
                          <span>{topic?.emoji}</span>
                          <span className="font-medium text-gray-900">{topic?.title}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl">
                <div className="flex gap-3">
                  <Icon name="Info" size={20} className="text-blue-600 mt-0.5 flex-shrink-0" />
                  <div className="text-sm text-gray-700">
                    <p className="font-semibold mb-1">Что дальше?</p>
                    <p>Аня начнет общаться с тобой на эти темы и органически узнает твои более детальные интересы прямо в диалогах 😊</p>
                  </div>
                </div>
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={() => {
                    setStep(1);
                    setSelectedTopics([]);
                  }}
                  variant="outline"
                  className="flex-1"
                >
                  <Icon name="RotateCcw" size={16} className="mr-2" />
                  Заново
                </Button>
                <Button
                  onClick={() => alert('В реальном приложении здесь будет сохранение в БД и переход к боту 🚀')}
                  className="flex-1 bg-green-600 hover:bg-green-700"
                >
                  <Icon name="Send" size={16} className="mr-2" />
                  Начать обучение
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
