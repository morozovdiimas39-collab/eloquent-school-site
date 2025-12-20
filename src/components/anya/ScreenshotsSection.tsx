import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import { useState } from 'react';

export default function ScreenshotsSection() {
  const [activeTab, setActiveTab] = useState<'screenshots' | 'video'>('screenshots');

  const screenshots = [
    {
      title: 'Диалог с Аней',
      description: 'Общайся на английском и получай мгновенные исправления',
      image: 'https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=800&h=600&fit=crop',
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

  return (
    <section className="relative py-20 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-indigo-50 via-white to-purple-50"></div>
      <div className="absolute top-20 right-10 w-96 h-96 bg-indigo-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
      <div className="absolute bottom-20 left-10 w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="inline-block mb-4">
              <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 backdrop-blur-sm text-indigo-700 font-medium text-sm border border-indigo-200 shadow-lg">
                <Icon name="Monitor" size={16} />
                Посмотри как это работает
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-gray-900 to-indigo-600 bg-clip-text text-transparent">
              Увидь Аню в действии
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Реальные скриншоты и видео работы AI-репетитора
            </p>
          </div>

          {/* Tabs */}
          <div className="flex justify-center mb-8">
            <div className="inline-flex items-center gap-2 p-1.5 bg-white rounded-2xl shadow-lg border border-gray-200">
              <button
                onClick={() => setActiveTab('screenshots')}
                className={`px-6 py-3 rounded-xl font-semibold transition-all ${
                  activeTab === 'screenshots'
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Icon name="Image" size={18} className="inline mr-2" />
                Скриншоты
              </button>
              <button
                onClick={() => setActiveTab('video')}
                className={`px-6 py-3 rounded-xl font-semibold transition-all ${
                  activeTab === 'video'
                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <Icon name="Video" size={18} className="inline mr-2" />
                Видео
              </button>
            </div>
          </div>

          {/* Screenshots Grid */}
          {activeTab === 'screenshots' && (
            <div className="grid md:grid-cols-2 gap-8 animate-fade-in">
              {screenshots.map((screenshot, index) => (
                <Card 
                  key={index}
                  className="overflow-hidden hover:shadow-2xl transition-all duration-300 group border-2 border-gray-100"
                >
                  <div className="relative overflow-hidden">
                    {/* Category badge */}
                    <div className="absolute top-4 left-4 z-10">
                      <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold bg-white/90 backdrop-blur-sm text-indigo-700 border border-indigo-200 shadow-lg">
                        {screenshot.category}
                      </span>
                    </div>

                    {/* Image */}
                    <div className="relative h-64 bg-gradient-to-br from-gray-100 to-gray-200 overflow-hidden">
                      <img
                        src={screenshot.image}
                        alt={screenshot.title}
                        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                    </div>

                    {/* Content */}
                    <div className="p-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-2 group-hover:text-indigo-600 transition-colors">
                        {screenshot.title}
                      </h3>
                      <p className="text-gray-600 leading-relaxed">
                        {screenshot.description}
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* Video Section */}
          {activeTab === 'video' && (
            <div className="animate-fade-in">
              <div className="max-w-5xl mx-auto">
                <Card className="overflow-hidden border-2 border-indigo-200 shadow-2xl">
                  {/* Video Player Placeholder */}
                  <div className="relative bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 aspect-video flex items-center justify-center group cursor-pointer">
                    {/* Play button */}
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="w-20 h-20 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center group-hover:bg-white/30 transition-all group-hover:scale-110 duration-300">
                        <div className="w-16 h-16 rounded-full bg-white flex items-center justify-center shadow-2xl">
                          <Icon name="Play" size={32} className="text-indigo-600 ml-1" />
                        </div>
                      </div>
                    </div>

                    {/* Video thumbnail overlay */}
                    <div className="absolute inset-0 bg-black/40"></div>
                    
                    {/* Duration badge */}
                    <div className="absolute bottom-4 right-4">
                      <span className="px-3 py-1.5 rounded-lg text-sm font-semibold bg-black/60 backdrop-blur-sm text-white">
                        2:45
                      </span>
                    </div>

                    {/* Title overlay */}
                    <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-black/80 to-transparent">
                      <h3 className="text-2xl font-bold text-white mb-2">
                        Как работает Аня: полный обзор
                      </h3>
                      <p className="text-white/80">
                        Посмотри демонстрацию всех возможностей AI-репетитора
                      </p>
                    </div>
                  </div>

                  {/* Video info */}
                  <div className="p-6 bg-gradient-to-br from-indigo-50 to-purple-50">
                    <div className="flex flex-wrap items-center gap-6 text-sm text-gray-600">
                      <div className="flex items-center gap-2">
                        <Icon name="Eye" size={18} className="text-indigo-600" />
                        <span>12,345 просмотров</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Icon name="ThumbsUp" size={18} className="text-indigo-600" />
                        <span>1,234 лайка</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Icon name="Clock" size={18} className="text-indigo-600" />
                        <span>2 минуты 45 секунд</span>
                      </div>
                    </div>
                  </div>
                </Card>

                {/* Additional videos */}
                <div className="grid md:grid-cols-3 gap-6 mt-8">
                  {[
                    { title: 'Первый диалог с Аней', duration: '1:20', views: '5.2K' },
                    { title: 'Упражнения на практике', duration: '2:10', views: '3.8K' },
                    { title: 'Прогресс за неделю', duration: '1:45', views: '4.1K' }
                  ].map((video, index) => (
                    <Card key={index} className="overflow-hidden hover:shadow-xl transition-all group cursor-pointer border border-gray-200">
                      <div className="relative h-40 bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center">
                        <div className="absolute inset-0 bg-black/20"></div>
                        <div className="w-12 h-12 rounded-full bg-white/90 backdrop-blur-sm flex items-center justify-center group-hover:scale-110 transition-transform">
                          <Icon name="Play" size={20} className="text-indigo-600 ml-0.5" />
                        </div>
                        <div className="absolute bottom-2 right-2">
                          <span className="px-2 py-1 rounded text-xs font-semibold bg-black/60 backdrop-blur-sm text-white">
                            {video.duration}
                          </span>
                        </div>
                      </div>
                      <div className="p-4">
                        <h4 className="font-semibold text-gray-900 mb-1 group-hover:text-indigo-600 transition-colors line-clamp-2">
                          {video.title}
                        </h4>
                        <p className="text-sm text-gray-500">{video.views} просмотров</p>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            </div>
          )}

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
