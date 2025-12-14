import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import Icon from '@/components/ui/icon';
import { useNavigate } from 'react-router-dom';

type Approach = 'methodical' | 'urgent';
type Context = 'professional' | 'travel' | 'academic' | 'conversational' | 'media' | 'hobbies';
type Intensity = 'relaxed' | 'normal' | 'intensive';
type FocusSkill = 'speaking' | 'reading' | 'writing' | 'listening' | null;

interface ContextDetails {
  [key: string]: string;
}

export default function GoalTest() {
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [goalText, setGoalText] = useState('');
  
  const [approach, setApproach] = useState<Approach>('methodical');
  const [selectedContexts, setSelectedContexts] = useState<Context[]>([]);
  const [contextDetails, setContextDetails] = useState<ContextDetails>({});
  const [deadline, setDeadline] = useState('');
  const [intensity, setIntensity] = useState<Intensity>('normal');
  const [focusSkill, setFocusSkill] = useState<FocusSkill>(null);
  
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [generatedWords, setGeneratedWords] = useState<Array<{ english: string; russian: string }>>([]);

  const approaches = [
    {
      id: 'methodical' as Approach,
      emoji: '📚',
      title: 'Методичное обучение',
      description: 'Последовательное долгосрочное изучение'
    },
    {
      id: 'urgent' as Approach,
      emoji: '⚡',
      title: 'Срочная подготовка',
      description: 'Быстрая подготовка к дедлайну'
    }
  ];

  const contexts = [
    {
      id: 'professional' as Context,
      emoji: '💼',
      title: 'Профессиональный',
      description: 'Работа, карьера, бизнес',
      subOptions: [
        { value: 'it', label: 'IT / Разработка' },
        { value: 'business', label: 'Бизнес / Менеджмент' },
        { value: 'medical', label: 'Медицина' },
        { value: 'design', label: 'Дизайн' },
        { value: 'engineering', label: 'Инженерия' },
        { value: 'education', label: 'Образование' }
      ]
    },
    {
      id: 'travel' as Context,
      emoji: '✈️',
      title: 'Путешествия',
      description: 'Туризм, поездки, общение за границей',
      subOptions: [
        { value: 'tourism', label: 'Туризм' },
        { value: 'relocation', label: 'Переезд' },
        { value: 'business_trip', label: 'Командировки' }
      ]
    },
    {
      id: 'academic' as Context,
      emoji: '🎓',
      title: 'Академический',
      description: 'Учеба, экзамены, научная работа',
      subOptions: [
        { value: 'university', label: 'Университет' },
        { value: 'ielts', label: 'IELTS' },
        { value: 'toefl', label: 'TOEFL' },
        { value: 'research', label: 'Научная работа' }
      ]
    },
    {
      id: 'conversational' as Context,
      emoji: '💬',
      title: 'Разговорный',
      description: 'Повседневное общение, друзья',
      subOptions: [
        { value: 'everyday', label: 'Повседневное' },
        { value: 'friends', label: 'С друзьями' },
        { value: 'dating', label: 'Знакомства' }
      ]
    },
    {
      id: 'media' as Context,
      emoji: '🎬',
      title: 'Медиа',
      description: 'Фильмы, сериалы, книги, новости',
      subOptions: [
        { value: 'movies', label: 'Фильмы/сериалы' },
        { value: 'books', label: 'Книги' },
        { value: 'news', label: 'Новости' },
        { value: 'podcasts', label: 'Подкасты' }
      ]
    },
    {
      id: 'hobbies' as Context,
      emoji: '🎯',
      title: 'Хобби',
      description: 'Увлечения, спорт, творчество',
      subOptions: [
        { value: 'sports', label: 'Спорт' },
        { value: 'music', label: 'Музыка' },
        { value: 'art', label: 'Искусство' },
        { value: 'gaming', label: 'Игры' }
      ]
    }
  ];

  const intensityLevels = [
    {
      id: 'relaxed' as Intensity,
      icon: 'Coffee',
      title: 'Спокойный',
      words: '+7 слов/неделю',
      time: '15 мин/день'
    },
    {
      id: 'normal' as Intensity,
      icon: 'Target',
      title: 'Обычный',
      words: '+12 слов/неделю',
      time: '30 мин/день'
    },
    {
      id: 'intensive' as Intensity,
      icon: 'Zap',
      title: 'Интенсивный',
      words: '+20 слов/неделю',
      time: '60 мин/день'
    }
  ];

  const focusSkills = [
    { id: 'speaking' as FocusSkill, emoji: '🗣️', title: 'Говорение' },
    { id: 'reading' as FocusSkill, emoji: '📖', title: 'Чтение' },
    { id: 'writing' as FocusSkill, emoji: '✍️', title: 'Письмо' },
    { id: 'listening' as FocusSkill, emoji: '👂', title: 'Аудирование' }
  ];

  const handleContextToggle = (contextId: Context) => {
    setSelectedContexts(prev => 
      prev.includes(contextId) 
        ? prev.filter(c => c !== contextId)
        : [...prev, contextId]
    );
  };

  const handleAnalyzeGoal = async () => {
    if (!goalText.trim()) return;
    setIsAnalyzing(true);
    
    setTimeout(() => {
      const text = goalText.toLowerCase();
      
      if (text.includes('срочно') || text.includes('через') || text.includes('скоро')) {
        setApproach('urgent');
        setIntensity('intensive');
      } else {
        setApproach('methodical');
        setIntensity('normal');
      }
      
      const detectedContexts: Context[] = [];
      if (text.includes('работ') || text.includes('програм') || text.includes('it')) {
        detectedContexts.push('professional');
        setContextDetails({ professional: 'it' });
      }
      if (text.includes('поездк') || text.includes('путеш') || text.includes('за границ')) {
        detectedContexts.push('travel');
      }
      if (text.includes('фильм') || text.includes('сериал') || text.includes('книг')) {
        detectedContexts.push('media');
      }
      if (text.includes('общ') || text.includes('друзь')) {
        detectedContexts.push('conversational');
      }
      
      setSelectedContexts(detectedContexts.length > 0 ? detectedContexts : ['conversational']);
      
      setIsAnalyzing(false);
      setStep(2);
    }, 1500);
  };

  const handleGenerateWords = async () => {
    setIsAnalyzing(true);
    
    setTimeout(() => {
      let words: Array<{ english: string; russian: string }> = [];
      
      if (selectedContexts.includes('professional') && contextDetails.professional === 'it') {
        words = [
          { english: 'deploy', russian: 'развертывать' },
          { english: 'debug', russian: 'отлаживать' },
          { english: 'refactor', russian: 'рефакторить' },
          { english: 'merge', russian: 'объединить' },
          { english: 'implement', russian: 'реализовать' },
          { english: 'optimize', russian: 'оптимизировать' },
          { english: 'integrate', russian: 'интегрировать' }
        ];
      } else if (selectedContexts.includes('travel')) {
        words = [
          { english: 'boarding pass', russian: 'посадочный талон' },
          { english: 'check-in', russian: 'регистрация' },
          { english: 'departure', russian: 'вылет' },
          { english: 'arrival', russian: 'прилет' },
          { english: 'customs', russian: 'таможня' },
          { english: 'accommodation', russian: 'жилье' },
          { english: 'itinerary', russian: 'маршрут' }
        ];
      } else {
        words = [
          { english: 'communicate', russian: 'общаться' },
          { english: 'understand', russian: 'понимать' },
          { english: 'express', russian: 'выражать' },
          { english: 'discuss', russian: 'обсуждать' },
          { english: 'explain', russian: 'объяснять' },
          { english: 'describe', russian: 'описывать' },
          { english: 'suggest', russian: 'предлагать' }
        ];
      }
      
      setGeneratedWords(words);
      setIsAnalyzing(false);
      setStep(3);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-6 px-4">
      <div className="max-w-2xl mx-auto">
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
              Шаг {step} из 3
            </span>
            <span className="text-sm text-gray-500">
              {step === 1 && 'Опиши цель'}
              {step === 2 && 'Комбинируй параметры'}
              {step === 3 && 'Готово!'}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-gradient-to-r from-indigo-500 to-purple-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(step / 3) * 100}%` }}
            />
          </div>
        </div>

        {step === 1 && (
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle className="text-2xl">Какая у тебя цель?</CardTitle>
              <CardDescription>
                Опиши зачем нужен английский. Можно несколько причин сразу
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="goal">Моя цель</Label>
                <Textarea
                  id="goal"
                  placeholder="Например: Работаю программистом и планирую переезд в Лондон через полгода..."
                  value={goalText}
                  onChange={(e) => setGoalText(e.target.value)}
                  className="min-h-[120px] mt-2"
                />
                <p className="text-sm text-gray-500 mt-2">
                  💡 Можешь указать работу, увлечения, планы на будущее
                </p>
              </div>

              <Button
                onClick={handleAnalyzeGoal}
                disabled={!goalText.trim() || isAnalyzing}
                className="w-full h-12 text-base"
              >
                {isAnalyzing ? (
                  <>
                    <Icon name="Loader2" size={20} className="mr-2 animate-spin" />
                    Анализирую...
                  </>
                ) : (
                  <>
                    <Icon name="Sparkles" size={20} className="mr-2" />
                    Продолжить
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        )}

        {step === 2 && (
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle className="text-2xl">Настрой параметры</CardTitle>
              <CardDescription>
                Комбинируй подход, контексты и интенсивность под себя
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              
              <div>
                <Label className="text-base font-semibold mb-3 block">1. Базовый подход</Label>
                <RadioGroup value={approach} onValueChange={(v) => setApproach(v as Approach)}>
                  <div className="grid gap-3">
                    {approaches.map((app) => (
                      <label
                        key={app.id}
                        className={`flex items-center gap-4 p-4 border-2 rounded-lg cursor-pointer transition-all ${
                          approach === app.id
                            ? 'border-indigo-500 bg-indigo-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <RadioGroupItem value={app.id} />
                        <span className="text-2xl">{app.emoji}</span>
                        <div className="flex-1">
                          <div className="font-semibold">{app.title}</div>
                          <div className="text-sm text-gray-600">{app.description}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </RadioGroup>
              </div>

              {approach === 'urgent' && (
                <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                  <Label htmlFor="deadline" className="flex items-center gap-2 mb-2">
                    <Icon name="Calendar" size={16} />
                    Дедлайн
                  </Label>
                  <Input
                    id="deadline"
                    type="date"
                    value={deadline}
                    onChange={(e) => setDeadline(e.target.value)}
                    className="bg-white"
                  />
                </div>
              )}

              <div>
                <Label className="text-base font-semibold mb-3 block">
                  2. Контексты использования
                  <span className="text-sm font-normal text-gray-500 ml-2">(можно несколько)</span>
                </Label>
                <div className="grid grid-cols-2 gap-3">
                  {contexts.map((ctx) => (
                    <div key={ctx.id}>
                      <label
                        className={`flex items-start gap-3 p-4 border-2 rounded-lg cursor-pointer transition-all ${
                          selectedContexts.includes(ctx.id)
                            ? 'border-indigo-500 bg-indigo-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <Checkbox
                          checked={selectedContexts.includes(ctx.id)}
                          onCheckedChange={() => handleContextToggle(ctx.id)}
                        />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xl">{ctx.emoji}</span>
                            <span className="font-semibold text-sm">{ctx.title}</span>
                          </div>
                          <p className="text-xs text-gray-600">{ctx.description}</p>
                        </div>
                      </label>
                      
                      {selectedContexts.includes(ctx.id) && ctx.subOptions && (
                        <div className="mt-2 ml-4">
                          <Select 
                            value={contextDetails[ctx.id] || ''} 
                            onValueChange={(v) => setContextDetails({ ...contextDetails, [ctx.id]: v })}
                          >
                            <SelectTrigger className="bg-white text-sm">
                              <SelectValue placeholder="Уточни..." />
                            </SelectTrigger>
                            <SelectContent>
                              {ctx.subOptions.map((opt) => (
                                <SelectItem key={opt.value} value={opt.value}>
                                  {opt.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <Label className="text-base font-semibold mb-3 block">3. Интенсивность</Label>
                <RadioGroup value={intensity} onValueChange={(v) => setIntensity(v as Intensity)}>
                  <div className="grid gap-3">
                    {intensityLevels.map((level) => (
                      <label
                        key={level.id}
                        className={`flex items-center gap-4 p-4 border-2 rounded-lg cursor-pointer transition-all ${
                          intensity === level.id
                            ? 'border-indigo-500 bg-indigo-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <RadioGroupItem value={level.id} />
                        <Icon name={level.icon as any} size={24} />
                        <div className="flex-1">
                          <div className="font-semibold">{level.title}</div>
                          <div className="text-sm text-gray-600">{level.words} • {level.time}</div>
                        </div>
                      </label>
                    ))}
                  </div>
                </RadioGroup>
              </div>

              <div>
                <Label className="text-base font-semibold mb-3 block">
                  4. Фокус на навыке
                  <span className="text-sm font-normal text-gray-500 ml-2">(опционально)</span>
                </Label>
                <div className="grid grid-cols-2 gap-3">
                  {focusSkills.map((skill) => (
                    <label
                      key={skill.id}
                      className={`flex items-center gap-3 p-3 border-2 rounded-lg cursor-pointer transition-all ${
                        focusSkill === skill.id
                          ? 'border-indigo-500 bg-indigo-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => setFocusSkill(focusSkill === skill.id ? null : skill.id)}
                    >
                      <span className="text-xl">{skill.emoji}</span>
                      <span className="font-medium text-sm">{skill.title}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={() => setStep(1)}
                  variant="outline"
                  className="flex-1"
                >
                  <Icon name="ChevronLeft" size={16} className="mr-2" />
                  Назад
                </Button>
                <Button
                  onClick={handleGenerateWords}
                  disabled={isAnalyzing || selectedContexts.length === 0}
                  className="flex-1"
                >
                  {isAnalyzing ? (
                    <>
                      <Icon name="Loader2" size={20} className="mr-2 animate-spin" />
                      Генерирую...
                    </>
                  ) : (
                    <>
                      <Icon name="Wand2" size={20} className="mr-2" />
                      Создать план
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <Card className="shadow-lg border-2 border-green-500">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center">
                    <Icon name="Check" size={24} className="text-white" />
                  </div>
                  <div>
                    <CardTitle className="text-2xl">Цель создана!</CardTitle>
                    <CardDescription>
                      План составлен с учетом твоих параметров
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="mb-3">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-2xl">{approaches.find(a => a.id === approach)?.emoji}</span>
                      <span className="font-semibold">{approaches.find(a => a.id === approach)?.title}</span>
                    </div>
                    <p className="text-sm text-gray-700 mb-3">{goalText}</p>
                  </div>
                  
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-gray-700">
                      <Icon name="Target" size={16} />
                      <span className="font-medium">Контексты:</span>
                      <span>
                        {selectedContexts.map((ctx) => {
                          const ctxData = contexts.find(c => c.id === ctx);
                          const detail = contextDetails[ctx];
                          const subOpt = ctxData?.subOptions?.find(s => s.value === detail);
                          return `${ctxData?.emoji} ${ctxData?.title}${subOpt ? ` (${subOpt.label})` : ''}`;
                        }).join(', ')}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-2 text-gray-700">
                      <Icon name={intensityLevels.find(i => i.id === intensity)?.icon as any} size={16} />
                      <span className="font-medium">Интенсивность:</span>
                      <span>{intensityLevels.find(i => i.id === intensity)?.title}</span>
                    </div>
                    
                    {focusSkill && (
                      <div className="flex items-center gap-2 text-gray-700">
                        <span className="text-lg">{focusSkills.find(s => s.id === focusSkill)?.emoji}</span>
                        <span className="font-medium">Фокус:</span>
                        <span>{focusSkills.find(s => s.id === focusSkill)?.title}</span>
                      </div>
                    )}
                    
                    {deadline && (
                      <div className="flex items-center gap-2 text-gray-700">
                        <Icon name="Calendar" size={16} />
                        <span className="font-medium">Дедлайн:</span>
                        <span>{new Date(deadline).toLocaleDateString('ru-RU')}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold">Первые слова ({generatedWords.length})</h3>
                    <Icon name="BookOpen" size={20} className="text-indigo-600" />
                  </div>
                  <div className="space-y-2">
                    {generatedWords.map((word, index) => (
                      <div
                        key={index}
                        className="p-3 bg-white border border-gray-200 rounded-lg flex items-center justify-between hover:border-indigo-500 transition-all"
                      >
                        <div>
                          <div className="font-semibold text-gray-900">{word.english}</div>
                          <div className="text-sm text-gray-600">{word.russian}</div>
                        </div>
                        <Icon name="Volume2" size={20} className="text-gray-400 cursor-pointer hover:text-indigo-600" />
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex gap-3">
                  <Button
                    onClick={() => {
                      setStep(1);
                      setGoalText('');
                      setSelectedContexts([]);
                      setContextDetails({});
                      setGeneratedWords([]);
                    }}
                    variant="outline"
                    className="flex-1"
                  >
                    <Icon name="Plus" size={16} className="mr-2" />
                    Новая цель
                  </Button>
                  <Button
                    onClick={() => alert('Сохранено! Теперь открой бота и начни практиковаться 🚀')}
                    className="flex-1 bg-gradient-to-r from-indigo-500 to-purple-500"
                  >
                    <Icon name="Send" size={16} className="mr-2" />
                    Начать обучение
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card className="border border-blue-200 bg-blue-50/50">
              <CardContent className="pt-4 pb-4">
                <div className="flex items-start gap-3">
                  <Icon name="Info" size={20} className="text-blue-600 mt-0.5 flex-shrink-0" />
                  <div className="text-sm text-gray-700">
                    <p className="font-semibold mb-1">Как это работает?</p>
                    <p>Я буду генерировать слова с учетом всех твоих контекстов и подстраиваться под интенсивность. Если указал фокус на навыке — буду особенно следить за его развитием.</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
