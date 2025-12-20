import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import { useState, useEffect } from 'react';

export default function ScreenshotsSection() {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);

  const screenshots = [
    {
      title: 'Диалог с Аней',
      description: 'Общайся на английском и получай мгновенные исправления',
      image: 'https://cdn.poehali.dev/files/Снимок экрана 2025-12-21 в 00.35.46.png',
      category: 'Практика'
    },
    {
      title: 'Упражнения',
      description: 'Интерактивные задания для закрепления слов',
      image: 'https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=800&h=600&fit=crop',
      category: 'Обучение'
    },
    {
      title: 'Прогресс',
      description: 'Отслеживай свои успехи и достижения',
      image: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=600&fit=crop',
      category: 'Статистика'
    },
    {
      title: 'Голосовые сообщения',
      description: 'Практикуй произношение с голосовым AI',
      image: 'https://images.unsplash.com/photo-1589903308904-1010c2294adc?w=800&h=600&fit=crop',
      category: 'Произношение'
    }
  ];

  const nextSlide = () => {
    if (!isAnimating) {
      setIsAnimating(true);
      setCurrentIndex((prev) => (prev + 1) % screenshots.length);
      setTimeout(() => setIsAnimating(false), 500);
    }
  };

  const prevSlide = () => {
    if (!isAnimating) {
      setIsAnimating(true);
      setCurrentIndex((prev) => (prev - 1 + screenshots.length) % screenshots.length);
      setTimeout(() => setIsAnimating(false), 500);
    }
  };

  const goToSlide = (index: number) => {
    if (!isAnimating && index !== currentIndex) {
      setIsAnimating(true);
      setCurrentIndex(index);
      setTimeout(() => setIsAnimating(false), 500);
    }
  };

  // Auto-rotate slides
  useEffect(() => {
    const interval = setInterval(() => {
      nextSlide();
    }, 5000);
    return () => clearInterval(interval);
  }, [currentIndex]);

  const currentScreenshot = screenshots[currentIndex];

  return (
    <section className="relative py-20 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-50 via-white to-purple-50"></div>
      <div className="absolute top-20 right-10 w-96 h-96 bg-indigo-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
      <div className="absolute bottom-20 left-10 w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-16">
            <div className="inline-block mb-4">
              <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 backdrop-blur-sm text-indigo-700 font-medium text-sm border border-indigo-200 shadow-lg">
                <Icon name="Smartphone" size={16} />
                Посмотри как это работает
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-gray-900 to-indigo-600 bg-clip-text text-transparent">
              Увидь Аню в действии
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Реальные скриншоты работы AI-репетитора в Telegram
            </p>
          </div>

          {/* 3D Phone Mockup with Carousel */}
          <div className="relative max-w-md mx-auto mb-16">
            {/* Phone Frame */}
            <div className="relative bg-gray-900 rounded-[3rem] p-4 shadow-2xl border-8 border-gray-800 transform hover:scale-105 transition-transform duration-500" style={{ perspective: '1000px' }}>
              <div className="bg-white rounded-[2.5rem] overflow-hidden">
                {/* Status bar */}
                <div className="bg-gray-50 px-6 py-3 flex items-center justify-between text-xs">
                  <span className="font-semibold">9:41</span>
                  <div className="flex items-center gap-1">
                    <Icon name="Signal" size={12} />
                    <Icon name="Wifi" size={12} />
                    <Icon name="Battery" size={12} />
                  </div>
                </div>

                {/* Screenshot Display */}
                <div className="relative bg-gray-900" style={{ aspectRatio: '9/16' }}>
                  {/* Current Screenshot */}
                  <div className="absolute inset-0">
                    <img
                      src={currentScreenshot.image}
                      alt={currentScreenshot.title}
                      className={`w-full h-full object-cover transition-all duration-500 ${
                        isAnimating ? 'opacity-0 scale-95' : 'opacity-100 scale-100'
                      }`}
                    />
                  </div>

                  {/* Category Badge */}
                  <div className="absolute top-4 left-4 z-10">
                    <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold bg-white/90 backdrop-blur-sm text-indigo-700 border border-indigo-200 shadow-lg">
                      {currentScreenshot.category}
                    </span>
                  </div>

                  {/* Navigation Arrows */}
                  <button
                    onClick={prevSlide}
                    disabled={isAnimating}
                    className="absolute left-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/20 backdrop-blur-md hover:bg-white/30 flex items-center justify-center transition-all disabled:opacity-50 disabled:cursor-not-allowed z-10"
                  >
                    <Icon name="ChevronLeft" size={24} className="text-white" />
                  </button>
                  <button
                    onClick={nextSlide}
                    disabled={isAnimating}
                    className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full bg-white/20 backdrop-blur-md hover:bg-white/30 flex items-center justify-center transition-all disabled:opacity-50 disabled:cursor-not-allowed z-10"
                  >
                    <Icon name="ChevronRight" size={24} className="text-white" />
                  </button>

                  {/* Slide Indicators */}
                  <div className="absolute bottom-4 left-0 right-0 flex justify-center gap-2 z-10">
                    {screenshots.map((_, index) => (
                      <button
                        key={index}
                        onClick={() => goToSlide(index)}
                        disabled={isAnimating}
                        className={`h-1.5 rounded-full transition-all duration-300 disabled:cursor-not-allowed ${
                          index === currentIndex
                            ? 'w-8 bg-white'
                            : 'w-1.5 bg-white/50 hover:bg-white/75'
                        }`}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Floating 3D elements */}
            <div className="absolute -left-8 top-1/4 animate-float">
              <div className="bg-white rounded-2xl px-4 py-3 shadow-2xl border border-indigo-200">
                <div className="flex items-center gap-2">
                  <Icon name="MessageSquare" size={20} className="text-indigo-600" />
                  <div>
                    <div className="text-xs text-gray-500">Сообщений</div>
                    <div className="font-bold text-gray-900">1,284</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="absolute -right-8 top-2/3 animate-float animation-delay-1000">
              <div className="bg-white rounded-2xl px-4 py-3 shadow-2xl border border-purple-200">
                <div className="flex items-center gap-2">
                  <Icon name="Zap" size={20} className="text-yellow-500" />
                  <div>
                    <div className="text-xs text-gray-500">Слов выучено</div>
                    <div className="font-bold text-gray-900">342</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Info Card Below Phone */}
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-3xl p-8 shadow-xl border-2 border-indigo-100">
              <div className="text-center mb-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  {currentScreenshot.title}
                </h3>
                <p className="text-gray-600 text-lg">
                  {currentScreenshot.description}
                </p>
              </div>

              {/* Quick Navigation */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {screenshots.map((screenshot, index) => (
                  <button
                    key={index}
                    onClick={() => goToSlide(index)}
                    disabled={isAnimating}
                    className={`p-4 rounded-2xl border-2 transition-all disabled:cursor-not-allowed ${
                      index === currentIndex
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-gray-200 hover:border-indigo-300 bg-white'
                    }`}
                  >
                    <div className={`text-sm font-semibold mb-1 ${
                      index === currentIndex ? 'text-indigo-600' : 'text-gray-700'
                    }`}>
                      {screenshot.category}
                    </div>
                    <div className="text-xs text-gray-500">
                      Слайд {index + 1}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* CTA */}
          <div className="text-center mt-12">
            <Button
              size="lg"
              className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 font-semibold text-lg h-14 px-8 shadow-xl hover:shadow-2xl transition-all hover:scale-105"
            >
              Попробовать Аню бесплатно
              <Icon name="ArrowRight" size={20} className="ml-2" />
            </Button>
          </div>
        </div>
      </div>
    </section>
  );
}