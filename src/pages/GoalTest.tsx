import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import Icon from '@/components/ui/icon';
import { useNavigate } from 'react-router-dom';

type GoalType = 'sequential' | 'urgent' | 'professional';
type Intensity = 'relaxed' | 'normal' | 'intensive';

export default function GoalTest() {
  const navigate = useNavigate();
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [goalText, setGoalText] = useState('');
  const [goalType, setGoalType] = useState<GoalType>('sequential');
  const [intensity, setIntensity] = useState<Intensity>('normal');
  const [deadline, setDeadline] = useState('');
  const [domain, setDomain] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [generatedWords, setGeneratedWords] = useState<Array<{ english: string; russian: string }>>([]);

  const goalTypes = [
    {
      id: 'sequential' as GoalType,
      icon: 'BookOpen',
      title: 'Методичное изучение',
      description: 'Последовательное освоение языка с нуля или продолжение обучения',
      emoji: '📚',
      color: 'from-blue-500 to-cyan-500'
    },
    {
      id: 'urgent' as GoalType,
      icon: 'Clock',
      title: 'Срочная цель',
      description: 'Подготовка к поездке, собеседованию или важному событию',
      emoji: '⚡',
      color: 'from-orange-500 to-red-500'
    },
    {
      id: 'professional' as GoalType,
      icon: 'Briefcase',
      title: 'Профессиональный',
      description: 'Изучение терминологии и языка для работы в конкретной сфере',
      emoji: '💼',
      color: 'from-purple-500 to-pink-500'
    }
  ];

  const domains = [
    { value: 'it', label: 'IT / Программирование', icon: '💻' },
    { value: 'business', label: 'Бизнес / Менеджмент', icon: '📊' },
    { value: 'travel', label: 'Путешествия / Туризм', icon: '✈️' },
    { value: 'medical', label: 'Медицина / Здоровье', icon: '🏥' },
    { value: 'design', label: 'Дизайн / Творчество', icon: '🎨' },
    { value: 'education', label: 'Образование / Наука', icon: '🎓' },
    { value: 'sales', label: 'Продажи / Маркетинг', icon: '📈' },
    { value: 'other', label: 'Другое', icon: '🎯' }
  ];

  const intensityLevels = [
    {
      id: 'relaxed' as Intensity,
      icon: 'Coffee',
      title: 'Спокойный',
      words: '+7 слов/неделю',
      time: '15 мин/день',
      color: 'border-green-300 bg-green-50'
    },
    {
      id: 'normal' as Intensity,
      icon: 'Target',
      title: 'Обычный',
      words: '+12 слов/неделю',
      time: '30 мин/день',
      color: 'border-blue-300 bg-blue-50'
    },
    {
      id: 'intensive' as Intensity,
      icon: 'Zap',
      title: 'Интенсивный',
      words: '+20 слов/неделю',
      time: '60 мин/день',
      color: 'border-orange-300 bg-orange-50'
    }
  ];

  const handleAnalyzeGoal = async () => {
    if (!goalText.trim()) return;
    
    setIsAnalyzing(true);
    
    // Имитация анализа через AI
    setTimeout(() => {
      // Автоопределение типа цели
      const text = goalText.toLowerCase();
      if (text.includes('поездка') || text.includes('путешеств') || text.includes('через')) {
        setGoalType('urgent');
        setIntensity('intensive');
      } else if (text.includes('работа') || text.includes('документаци') || text.includes('терминолог')) {
        setGoalType('professional');
        setIntensity('normal');
      } else {
        setGoalType('sequential');
        setIntensity('normal');
      }
      
      setIsAnalyzing(false);
      setStep(2);
    }, 1500);
  };

  const handleGenerateWords = async () => {
    setIsAnalyzing(true);
    
    // Имитация генерации слов
    setTimeout(() => {
      // Примеры слов в зависимости от типа
      let words: Array<{ english: string; russian: string }> = [];
      
      if (goalType === 'urgent' && domain === 'travel') {
        words = [
          { english: 'boarding pass', russian: 'посадочный талон' },
          { english: 'delayed flight', russian: 'задержка рейса' },
          { english: 'baggage claim', russian: 'выдача багажа' },
          { english: 'customs', russian: 'таможня' },
          { english: 'check-in', russian: 'регистрация на рейс' },
          { english: 'gate', russian: 'выход на посадку' },
          { english: 'connecting flight', russian: 'стыковочный рейс' }
        ];
      } else if (goalType === 'professional' && domain === 'it') {
        words = [
          { english: 'deploy', russian: 'развертывать' },
          { english: 'debug', russian: 'отлаживать' },
          { english: 'refactor', russian: 'рефакторить' },
          { english: 'legacy code', russian: 'устаревший код' },
          { english: 'deprecated', russian: 'устаревший (метод)' },
          { english: 'rollback', russian: 'откатить изменения' },
          { english: 'backward compatible', russian: 'обратно совместимый' }
        ];
      } else {
        words = [
          { english: 'think', russian: 'думать' },
          { english: 'feel', russian: 'чувствовать' },
          { english: 'understand', russian: 'понимать' },
          { english: 'explain', russian: 'объяснять' },
          { english: 'decide', russian: 'решать' },
          { english: 'believe', russian: 'верить' },
          { english: 'remember', russian: 'помнить' }
        ];
      }
      
      setGeneratedWords(words);
      setIsAnalyzing(false);
      setStep(3);
    }, 2000);
  };

  const selectedGoalType = goalTypes.find(g => g.id === goalType);
  const selectedIntensity = intensityLevels.find(i => i.id === intensity);

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

        {/* Прогресс-бар */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              Шаг {step} из 3
            </span>
            <span className="text-sm text-gray-500">
              {step === 1 && 'Опиши цель'}
              {step === 2 && 'Настрой параметры'}
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

        {/* Шаг 1: Описание цели */}
        {step === 1 && (
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle className="text-2xl">Какая у тебя цель?</CardTitle>
              <CardDescription>
                Опиши что хочешь выучить или для чего нужен английский
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="goal">Моя цель</Label>
                <Textarea
                  id="goal"
                  placeholder="Например: Хочу поехать в Лондон через 2 месяца..."
                  value={goalText}
                  onChange={(e) => setGoalText(e.target.value)}
                  className="min-h-[120px] mt-2"
                />
                <p className="text-sm text-gray-500 mt-2">
                  💡 Чем подробнее опишешь, тем лучше я подберу программу
                </p>
              </div>

              <div className="grid grid-cols-3 gap-3">
                {goalTypes.map((type) => (
                  <button
                    key={type.id}
                    onClick={() => setGoalText(
                      type.id === 'sequential' ? 'Хочу систематически изучать английский с нуля' :
                      type.id === 'urgent' ? 'Мне нужен английский для поездки через 2 месяца' :
                      'Хочу читать техническую документацию на английском для работы'
                    )}
                    className="p-3 border-2 border-gray-200 rounded-lg hover:border-indigo-500 transition-all text-center"
                  >
                    <div className="text-2xl mb-1">{type.emoji}</div>
                    <div className="text-xs text-gray-700 font-medium">{type.title.split(' ')[0]}</div>
                  </button>
                ))}
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

        {/* Шаг 2: Настройка параметров */}
        {step === 2 && (
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle className="text-2xl">Настрой программу</CardTitle>
              <CardDescription>
                Я подобрал параметры под твою цель, можешь изменить
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Тип цели */}
              <div>
                <Label className="text-base font-semibold mb-3 block">Тип обучения</Label>
                <RadioGroup value={goalType} onValueChange={(v) => setGoalType(v as GoalType)}>
                  <div className="space-y-3">
                    {goalTypes.map((type) => (
                      <label
                        key={type.id}
                        className={`flex items-start gap-4 p-4 border-2 rounded-lg cursor-pointer transition-all ${
                          goalType === type.id
                            ? 'border-indigo-500 bg-indigo-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <RadioGroupItem value={type.id} className="mt-1" />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xl">{type.emoji}</span>
                            <span className="font-semibold">{type.title}</span>
                          </div>
                          <p className="text-sm text-gray-600">{type.description}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                </RadioGroup>
              </div>

              {/* Дополнительные поля для urgent */}
              {goalType === 'urgent' && (
                <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
                  <Label htmlFor="deadline" className="flex items-center gap-2 mb-2">
                    <Icon name="Calendar" size={16} />
                    Когда нужно быть готовым?
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

              {/* Дополнительные поля для professional */}
              {goalType === 'professional' && (
                <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
                  <Label htmlFor="domain" className="flex items-center gap-2 mb-2">
                    <Icon name="Briefcase" size={16} />
                    Сфера деятельности
                  </Label>
                  <Select value={domain} onValueChange={setDomain}>
                    <SelectTrigger className="bg-white">
                      <SelectValue placeholder="Выбери сферу" />
                    </SelectTrigger>
                    <SelectContent>
                      {domains.map((d) => (
                        <SelectItem key={d.value} value={d.value}>
                          <span className="flex items-center gap-2">
                            <span>{d.icon}</span>
                            <span>{d.label}</span>
                          </span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* Интенсивность */}
              <div>
                <Label className="text-base font-semibold mb-3 block">Интенсивность обучения</Label>
                <RadioGroup value={intensity} onValueChange={(v) => setIntensity(v as Intensity)}>
                  <div className="grid gap-3">
                    {intensityLevels.map((level) => (
                      <label
                        key={level.id}
                        className={`flex items-center gap-4 p-4 border-2 rounded-lg cursor-pointer transition-all ${
                          intensity === level.id
                            ? level.color.replace('bg-', 'bg-') + ' border-current'
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
                  disabled={isAnalyzing || (goalType === 'professional' && !domain)}
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

        {/* Шаг 3: Результат */}
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
                      Я подобрал первые слова для тебя
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-2xl">{selectedGoalType?.emoji}</span>
                    <span className="font-semibold">{selectedGoalType?.title}</span>
                  </div>
                  <p className="text-sm text-gray-700 mb-3">{goalText}</p>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <div className="flex items-center gap-1">
                      <Icon name={selectedIntensity?.icon as any} size={16} />
                      <span>{selectedIntensity?.title}</span>
                    </div>
                    {goalType === 'urgent' && deadline && (
                      <div className="flex items-center gap-1">
                        <Icon name="Calendar" size={16} />
                        <span>{new Date(deadline).toLocaleDateString('ru-RU')}</span>
                      </div>
                    )}
                    {goalType === 'professional' && domain && (
                      <div className="flex items-center gap-1">
                        <Icon name="Briefcase" size={16} />
                        <span>{domains.find(d => d.value === domain)?.label}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold">Твои первые слова ({generatedWords.length})</h3>
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
                      setGeneratedWords([]);
                    }}
                    variant="outline"
                    className="flex-1"
                  >
                    <Icon name="Plus" size={16} className="mr-2" />
                    Новая цель
                  </Button>
                  <Button
                    onClick={() => alert('Сохранено! Теперь открой бота в Telegram и начни практиковаться 🚀')}
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
                    <p className="font-semibold mb-1">Что дальше?</p>
                    <p>Открой бота в Telegram и начни практиковаться! Я буду автоматически добавлять новые слова по твоей цели каждую неделю.</p>
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
