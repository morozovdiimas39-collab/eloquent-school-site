import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import Icon from '@/components/ui/icon';
import { useNavigate } from 'react-router-dom';

type Approach = 'methodical' | 'urgent';

interface Topic {
  id: string;
  emoji: string;
  title: string;
}

interface SuggestedSubtopic {
  id: string;
  title: string;
  description: string;
}

export default function GoalTest() {
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  
  const [approach, setApproach] = useState<Approach>('methodical');
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [urgentGoal, setUrgentGoal] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [suggestedSubtopics, setSuggestedSubtopics] = useState<SuggestedSubtopic[]>([]);
  const [selectedSubtopics, setSelectedSubtopics] = useState<string[]>([]);

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
    { id: 'cars', emoji: '🚗', title: 'Авто' }
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

  const handleSubtopicToggle = (subtopicId: string) => {
    setSelectedSubtopics(prev => 
      prev.includes(subtopicId) 
        ? prev.filter(t => t !== subtopicId)
        : [...prev, subtopicId]
    );
  };

  const analyzeUrgentGoal = async () => {
    if (!urgentGoal.trim()) return;
    
    setIsAnalyzing(true);

    try {
      const response = await fetch('https://functions.poehali.dev/42c13bf2-f4d5-4710-9170-596c38d438a4', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'analyze_urgent_goal',
          goal: urgentGoal
        })
      });

      const data = await response.json();
      console.log('🔍 Gemini response:', data);

      if (data.subtopics && data.subtopics.length > 0) {
        console.log('✅ Got subtopics from Gemini:', data.subtopics);
        setSuggestedSubtopics(data.subtopics);
        setSelectedSubtopics(data.subtopics.map((s: SuggestedSubtopic) => s.id));
      } else {
        console.log('⚠️ No subtopics, using fallback. Response:', data);
        setSuggestedSubtopics([
          { id: 'general', title: 'Общая подготовка', description: 'Базовые фразы и выражения' }
        ]);
        setSelectedSubtopics(['general']);
      }
    } catch (error) {
      console.error('Failed to analyze goal:', error);
      setSuggestedSubtopics([
        { id: 'general', title: 'Общая подготовка', description: 'Базовые фразы и выражения' }
      ]);
      setSelectedSubtopics(['general']);
    }

    setIsAnalyzing(false);
  };

  const handleNext = () => {
    if (step === 1) {
      setStep(2);
    } else if (step === 2) {
      if (approach === 'methodical' && selectedTopics.length >= 2) {
        setStep(3);
      } else if (approach === 'urgent' && selectedSubtopics.length >= 1) {
        setStep(3);
      }
    }
  };

  const canProceed = () => {
    if (step === 2) {
      if (approach === 'methodical') {
        return selectedTopics.length >= 2;
      } else {
        return selectedSubtopics.length >= 1 && suggestedSubtopics.length > 0;
      }
    }
    return true;
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

        {step === 2 && approach === 'methodical' && (
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

              <div className="grid grid-cols-4 gap-2">
                {topics.map((topic) => (
                  <button
                    key={topic.id}
                    onClick={() => handleTopicToggle(topic.id)}
                    className={`flex flex-col items-center justify-center p-3 border-2 rounded-lg cursor-pointer transition-all ${
                      selectedTopics.includes(topic.id)
                        ? 'border-[#3390ec] bg-[#e8f4fd]'
                        : 'border-gray-200 bg-white hover:border-gray-300'
                    }`}
                  >
                    <span className="text-2xl mb-1">{topic.emoji}</span>
                    <span className="text-xs font-medium text-gray-900 text-center leading-tight">{topic.title}</span>
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

        {step === 2 && approach === 'urgent' && (
          <Card className="shadow-sm border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-xl">Что тебе нужно?</CardTitle>
              <CardDescription className="text-gray-600">
                Опиши свою срочную задачу, и я подберу нужные темы
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Textarea
                  placeholder="Например: Я еду в Лондон через 2 недели..."
                  value={urgentGoal}
                  onChange={(e) => setUrgentGoal(e.target.value)}
                  className="min-h-[100px] resize-none"
                />
              </div>

              {suggestedSubtopics.length === 0 && (
                <Button
                  onClick={analyzeUrgentGoal}
                  disabled={!urgentGoal.trim() || isAnalyzing}
                  className="w-full bg-[#3390ec] hover:bg-[#2a7dd4]"
                >
                  {isAnalyzing ? (
                    <>
                      <Icon name="Loader2" size={20} className="mr-2 animate-spin" />
                      Анализирую...
                    </>
                  ) : (
                    <>
                      <Icon name="Sparkles" size={20} className="mr-2" />
                      Подобрать темы
                    </>
                  )}
                </Button>
              )}

              {suggestedSubtopics.length > 0 && (
                <>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">
                        Рекомендованные темы:
                      </span>
                      <span className="text-xs text-gray-500">
                        {selectedSubtopics.length} выбрано
                      </span>
                    </div>
                    <div className="space-y-2">
                      {suggestedSubtopics.map((subtopic) => (
                        <label
                          key={subtopic.id}
                          className={`flex items-start gap-3 p-3 border-2 rounded-lg cursor-pointer transition-all ${
                            selectedSubtopics.includes(subtopic.id)
                              ? 'border-[#3390ec] bg-[#e8f4fd]'
                              : 'border-gray-200 bg-white hover:border-gray-300'
                          }`}
                        >
                          <Checkbox
                            checked={selectedSubtopics.includes(subtopic.id)}
                            onCheckedChange={() => handleSubtopicToggle(subtopic.id)}
                            className="mt-0.5"
                          />
                          <div className="flex-1">
                            <div className="font-medium text-gray-900 text-sm">{subtopic.title}</div>
                            <div className="text-xs text-gray-600 mt-0.5">{subtopic.description}</div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-3 pt-2">
                    <Button
                      onClick={() => {
                        setStep(1);
                        setSuggestedSubtopics([]);
                        setSelectedSubtopics([]);
                        setUrgentGoal('');
                      }}
                      variant="outline"
                      className="flex-1"
                    >
                      <Icon name="ChevronLeft" size={16} className="mr-2" />
                      Назад
                    </Button>
                    <Button
                      onClick={handleNext}
                      disabled={!canProceed()}
                      className="flex-1 bg-[#3390ec] hover:bg-[#2a7dd4]"
                    >
                      Готово
                      <Icon name="Check" size={20} className="ml-2" />
                    </Button>
                  </div>
                </>
              )}

              {suggestedSubtopics.length === 0 && (
                <Button
                  onClick={() => setStep(1)}
                  variant="outline"
                  className="w-full"
                >
                  <Icon name="ChevronLeft" size={16} className="mr-2" />
                  Назад
                </Button>
              )}
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
                  {approach === 'urgent' && urgentGoal && (
                    <p className="text-sm text-gray-600 italic ml-9">"{urgentGoal}"</p>
                  )}
                </div>
                
                <div className="pt-2 border-t border-gray-200">
                  <div className="text-sm font-medium text-gray-700 mb-2">
                    {approach === 'methodical' ? 'Твои темы:' : 'Выбранные темы для подготовки:'}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {approach === 'methodical' && selectedTopics.map((topicId) => {
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
                    {approach === 'urgent' && selectedSubtopics.map((subtopicId) => {
                      const subtopic = suggestedSubtopics.find(s => s.id === subtopicId);
                      return (
                        <div
                          key={subtopicId}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 rounded-full text-sm"
                        >
                          <span className="font-medium text-gray-900">{subtopic?.title}</span>
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
                    <p>
                      {approach === 'methodical' 
                        ? 'Аня начнет общаться с тобой на эти темы и органически узнает твои более детальные интересы прямо в диалогах 😊'
                        : 'Аня сфокусируется на этих темах и поможет тебе быстро подготовиться к твоей поездке! 🚀'
                      }
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={() => {
                    setStep(1);
                    setSelectedTopics([]);
                    setSuggestedSubtopics([]);
                    setSelectedSubtopics([]);
                    setUrgentGoal('');
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