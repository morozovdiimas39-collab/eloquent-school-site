import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';

interface HeroSectionProps {
  onStartDemo: () => void;
}

export default function HeroSection({ onStartDemo }: HeroSectionProps) {
  return (
    <section className="relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 bg-gradient-to-b from-blue-50 via-indigo-50 to-purple-50">
        <div className="absolute top-20 left-10 w-72 h-72 bg-blue-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
        <div className="absolute top-40 right-10 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-1/2 w-72 h-72 bg-indigo-300 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      <div className="container mx-auto px-4 py-20 md:py-32 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center max-w-7xl mx-auto">
          {/* Left: Text content */}
          <div className="space-y-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 backdrop-blur-sm text-blue-700 font-medium text-sm border border-blue-200 shadow-lg animate-fade-in">
              <Icon name="Sparkles" size={16} className="animate-pulse" />
              <span>Твой личный ИИ-репетитор английского</span>
            </div>

            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold leading-tight animate-fade-in-up">
              Учи английский
              <br />
              <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent animate-gradient">в разговорах с Аней в Telegram</span>
            </h1>

            <p className="text-xl md:text-2xl text-gray-600 animate-fade-in-up animation-delay-200">
              Аня — это ИИ-репетитор, который общается с тобой на английском, исправляет ошибки и помогает запоминать новые слова. Как настоящий учитель, но в телеграме 24/7.
            </p>

            <div className="flex flex-col sm:flex-row items-start gap-4 pt-4 animate-fade-in-up animation-delay-400">
              <Button
                onClick={onStartDemo}
                size="lg"
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 font-semibold text-lg h-14 px-8 shadow-xl hover:shadow-2xl transition-all hover:scale-105"
              >
                Попробовать демо
                <Icon name="MessageSquare" size={20} className="ml-2" />
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="font-semibold text-lg h-14 px-8 border-2 bg-white/80 backdrop-blur-sm hover:bg-white transition-all hover:scale-105"
                onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}
              >
                Как это работает
                <Icon name="Play" size={20} className="ml-2" />
              </Button>
            </div>

            <div className="flex flex-wrap items-center gap-6 pt-4 animate-fade-in-up animation-delay-600">
              <div className="flex items-center gap-2 text-gray-700">
                <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center">
                  <Icon name="Check" size={14} className="text-green-600" />
                </div>
                <span className="font-medium">Без скучных учебников</span>
              </div>
              <div className="flex items-center gap-2 text-gray-700">
                <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center">
                  <Icon name="Check" size={14} className="text-green-600" />
                </div>
                <span className="font-medium">Живые диалоги</span>
              </div>
              <div className="flex items-center gap-2 text-gray-700">
                <div className="w-6 h-6 rounded-full bg-green-100 flex items-center justify-center">
                  <Icon name="Check" size={14} className="text-green-600" />
                </div>
                <span className="font-medium">Персональный прогресс</span>
              </div>
            </div>
          </div>

          {/* Right: Screenshot/Visual */}
          <div className="relative animate-fade-in-up animation-delay-800 hidden lg:block">
            <div className="relative">
              {/* Mockup phone frame */}
              <div className="relative mx-auto w-full max-w-sm">
                <div className="relative bg-gray-900 rounded-[3rem] p-4 shadow-2xl border-8 border-gray-800">
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
                    
                    {/* Chat header */}
                    <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4 flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-white flex items-center justify-center font-bold text-blue-600">
                        A
                      </div>
                      <div className="flex-1">
                        <div className="font-semibold text-white">Anya</div>
                        <div className="text-xs text-blue-100">online</div>
                      </div>
                    </div>

                    {/* Chat messages */}
                    <div className="p-4 space-y-3 bg-gray-50 min-h-[400px]">
                      <div className="flex gap-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-500 flex-shrink-0 flex items-center justify-center text-white text-sm font-bold">
                          A
                        </div>
                        <div className="bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm max-w-[80%]">
                          <p className="text-sm text-gray-800">Hey! 👋 What did you do today?</p>
                        </div>
                      </div>

                      <div className="flex gap-2 justify-end">
                        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm max-w-[80%]">
                          <p className="text-sm text-white">I go to cinema yesterday</p>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-500 flex-shrink-0 flex items-center justify-center text-white text-sm font-bold">
                          A
                        </div>
                        <div className="bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm max-w-[80%]">
                          <div className="space-y-2">
                            <p className="text-sm text-gray-800">Sounds fun! 🎬</p>
                            <div className="bg-orange-50 border border-orange-200 rounded-lg p-2 text-xs">
                              <div className="font-semibold text-orange-700 mb-1">🔧 Fix:</div>
                              <div className="text-red-600">❌ I go to cinema yesterday</div>
                              <div className="text-green-600">✅ I went to the cinema yesterday</div>
                              <div className="text-gray-600 mt-1">🇷🇺 С 'yesterday' нужно прошедшее время</div>
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-500 flex-shrink-0 flex items-center justify-center text-white text-sm font-bold">
                          A
                        </div>
                        <div className="bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm max-w-[80%]">
                          <p className="text-sm text-gray-800">What movie did you watch? 🍿</p>
                        </div>
                      </div>
                    </div>

                    {/* Input area */}
                    <div className="bg-white border-t px-4 py-3 flex items-center gap-2">
                      <div className="flex-1 bg-gray-100 rounded-full px-4 py-2">
                        <span className="text-sm text-gray-400">Type a message...</span>
                      </div>
                      <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                        <Icon name="Send" size={16} className="text-white" />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Floating badges */}
                <div className="absolute -right-4 top-20 bg-white rounded-xl px-4 py-3 shadow-xl border border-gray-200 animate-float">
                  <div className="flex items-center gap-2">
                    <Icon name="Zap" size={20} className="text-yellow-500" />
                    <div>
                      <div className="text-xs text-gray-500">Words learned</div>
                      <div className="font-bold text-gray-900">127</div>
                    </div>
                  </div>
                </div>

                <div className="absolute -left-4 bottom-32 bg-white rounded-xl px-4 py-3 shadow-xl border border-gray-200 animate-float animation-delay-1000">
                  <div className="flex items-center gap-2">
                    <Icon name="TrendingUp" size={20} className="text-green-500" />
                    <div>
                      <div className="text-xs text-gray-500">Level</div>
                      <div className="font-bold text-gray-900">B1 → B2</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}