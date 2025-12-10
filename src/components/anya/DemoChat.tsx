import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'anya';
  correction?: string;
  translation?: string;
}

const demoScenarios = [
  {
    trigger: /hi|hello|привет|hey/i,
    response: "Hi! 👋 I'm Anya, your English tutor. What would you like to talk about today?",
    translation: "Привет! Я Аня, твой репетитор английского. О чём хотел бы поговорить сегодня?"
  },
  {
    trigger: /how are you|как дела/i,
    response: "I'm doing great, thanks for asking! How about you?",
    translation: "У меня всё отлично, спасибо что спросил! Как у тебя дела?"
  },
  {
    trigger: /weather|погода/i,
    response: "The weather is nice today! Do you like sunny days? ☀️",
    translation: "Сегодня хорошая погода! Ты любишь солнечные дни?"
  },
  {
    trigger: /i like|я люблю/i,
    response: "That's wonderful! Tell me more about what you enjoy doing.",
    translation: "Это прекрасно! Расскажи мне больше о том, что тебе нравится делать.",
    correction: "Great sentence! Just remember: 'I like' + verb+ing (I like reading)"
  },
];

export default function DemoChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: "Hi there! I'm Anya 🌟 Try chatting with me in English! I'll help you improve.",
      sender: 'anya',
      translation: "Привет! Я Аня 🌟 Попробуй пообщаться со мной на английском! Я помогу тебе улучшиться."
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: input,
      sender: 'user'
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    setTimeout(() => {
      const matchedScenario = demoScenarios.find(scenario => 
        scenario.trigger.test(input)
      );

      const anyaMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: matchedScenario?.response || "That's interesting! Can you tell me more? 😊",
        sender: 'anya',
        translation: matchedScenario?.translation || "Интересно! Можешь рассказать больше?",
        correction: matchedScenario?.correction
      };

      setMessages(prev => [...prev, anyaMessage]);
      setIsTyping(false);
    }, 1500);
  };

  const quickPhrases = [
    "Hi! How are you?",
    "I like learning English",
    "Tell me about the weather"
  ];

  return (
    <section id="demo" className="relative py-20 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-50 via-white to-blue-50"></div>
      <div className="absolute top-20 left-10 w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <div className="inline-block mb-4">
              <span className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 backdrop-blur-sm text-purple-700 font-medium text-sm border border-purple-200 shadow-lg">
                <Icon name="MessageSquare" size={16} />
                Живая демонстрация
              </span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-gray-900 to-purple-600 bg-clip-text text-transparent">
              Попробуй прямо сейчас
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Напиши Ане на английском и посмотри, как она исправляет ошибки и помогает учиться
            </p>
          </div>

          {/* Desktop: Laptop mockup, Mobile: Phone mockup */}
          <div className="relative">
            {/* Desktop Laptop Frame */}
            <div className="hidden lg:block">
              <div className="relative mx-auto max-w-5xl">
                {/* Laptop screen */}
                <div className="bg-gray-900 rounded-t-3xl p-6 shadow-2xl border-8 border-gray-800">
                  <div className="bg-white rounded-2xl overflow-hidden shadow-inner">
                    <Card className="overflow-hidden border-0">
                      <div className="bg-gradient-to-r from-purple-600 via-blue-600 to-indigo-600 p-6 text-white">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-4">
                            <div className="w-14 h-14 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center relative">
                              <span className="text-3xl">👩‍🏫</span>
                              <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-white"></div>
                            </div>
                            <div>
                              <h3 className="font-bold text-xl">Anya AI Tutor</h3>
                              <p className="text-sm text-white/90 flex items-center gap-2">
                                <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                                Online • Отвечает мгновенно
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-3">
                            <Button variant="ghost" size="sm" className="text-white hover:bg-white/10">
                              <Icon name="Phone" size={20} />
                            </Button>
                            <Button variant="ghost" size="sm" className="text-white hover:bg-white/10">
                              <Icon name="Video" size={20} />
                            </Button>
                            <Button variant="ghost" size="sm" className="text-white hover:bg-white/10">
                              <Icon name="MoreVertical" size={20} />
                            </Button>
                          </div>
                        </div>
                      </div>

                      <div className="h-[500px] overflow-y-auto p-6 space-y-4 bg-gradient-to-b from-gray-50 to-white">
                        {messages.map((message) => (
                          <div
                            key={message.id}
                            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-up`}
                          >
                            <div className={`max-w-[75%] space-y-2`}>
                              {message.sender === 'anya' && (
                                <div className="flex items-center gap-2 mb-1">
                                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-white text-sm font-bold shadow-md">
                                    A
                                  </div>
                                  <span className="text-xs text-gray-500 font-medium">Anya</span>
                                </div>
                              )}
                              <div
                                className={`rounded-2xl px-5 py-3.5 shadow-md transition-all hover:shadow-lg ${
                                  message.sender === 'user'
                                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-tr-sm'
                                    : 'bg-white border-2 border-purple-100 text-gray-900 rounded-tl-sm'
                                }`}
                              >
                                <p className="text-base leading-relaxed">{message.text}</p>
                              </div>
                              {message.translation && (
                                <div className="text-xs text-gray-500 italic px-3 flex items-start gap-1">
                                  <Icon name="Languages" size={12} className="mt-0.5 flex-shrink-0" />
                                  {message.translation}
                                </div>
                              )}
                              {message.correction && (
                                <div className="bg-orange-50 border-2 border-orange-200 rounded-xl px-4 py-3 text-sm text-orange-900 shadow-sm">
                                  <div className="flex items-start gap-2">
                                    <Icon name="Lightbulb" size={16} className="text-orange-500 mt-0.5 flex-shrink-0" />
                                    <div>
                                      <div className="font-semibold mb-1">💡 Подсказка</div>
                                      <div>{message.correction}</div>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                        {isTyping && (
                          <div className="flex justify-start animate-fade-in">
                            <div className="flex items-center gap-2">
                              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-white text-sm font-bold shadow-md">
                                A
                              </div>
                              <div className="bg-white border-2 border-purple-100 rounded-2xl rounded-tl-sm px-5 py-3.5 shadow-md">
                                <div className="flex gap-1.5">
                                  <div className="w-2.5 h-2.5 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                  <div className="w-2.5 h-2.5 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                  <div className="w-2.5 h-2.5 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                        <div ref={messagesEndRef} />
                      </div>

                      <div className="p-6 bg-white border-t-2 border-gray-100">
                        <div className="flex flex-wrap gap-2 mb-4">
                          {quickPhrases.map((phrase, idx) => (
                            <Button
                              key={idx}
                              variant="outline"
                              size="sm"
                              onClick={() => setInput(phrase)}
                              className="text-sm hover:bg-purple-50 hover:border-purple-300 transition-all"
                            >
                              <Icon name="Zap" size={14} className="mr-1.5" />
                              {phrase}
                            </Button>
                          ))}
                        </div>
                        <div className="flex gap-3">
                          <Button variant="ghost" size="sm" className="px-3">
                            <Icon name="Paperclip" size={20} className="text-gray-500" />
                          </Button>
                          <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                            placeholder="Type your message in English..."
                            className="flex-1 px-5 py-3.5 text-base border-2 border-gray-200 rounded-xl focus:border-purple-400 focus:outline-none transition-all"
                          />
                          <Button variant="ghost" size="sm" className="px-3">
                            <Icon name="Smile" size={20} className="text-gray-500" />
                          </Button>
                          <Button
                            onClick={handleSend}
                            disabled={!input.trim() || isTyping}
                            className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 px-6 py-3.5 shadow-lg hover:shadow-xl transition-all"
                          >
                            <Icon name="Send" size={20} />
                          </Button>
                        </div>
                      </div>
                    </Card>
                  </div>
                </div>
                {/* Laptop base */}
                <div className="relative">
                  <div className="h-6 bg-gradient-to-b from-gray-700 to-gray-800 rounded-b-3xl"></div>
                  <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-48 h-2 bg-gray-900 rounded-t-lg"></div>
                </div>

                {/* Floating stats */}
                <div className="absolute -right-8 top-32 bg-white rounded-2xl px-6 py-4 shadow-2xl border-2 border-purple-100 animate-float">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center">
                      <Icon name="CheckCircle2" size={24} className="text-white" />
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Ошибок исправлено</div>
                      <div className="text-2xl font-bold text-gray-900">247</div>
                    </div>
                  </div>
                </div>

                <div className="absolute -left-8 bottom-48 bg-white rounded-2xl px-6 py-4 shadow-2xl border-2 border-blue-100 animate-float animation-delay-1000">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center">
                      <Icon name="BookOpen" size={24} className="text-white" />
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Слов изучено</div>
                      <div className="text-2xl font-bold text-gray-900">1,432</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Mobile: Phone mockup */}
            <div className="lg:hidden">
              <div className="relative mx-auto max-w-sm">
                <div className="bg-gray-900 rounded-[3rem] p-4 shadow-2xl border-8 border-gray-800">
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

                    <Card className="overflow-hidden border-0 rounded-none">
                      <div className="bg-gradient-to-r from-purple-600 via-blue-600 to-indigo-600 p-4 text-white">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center relative">
                            <span className="text-xl">👩‍🏫</span>
                            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-400 rounded-full border-2 border-white"></div>
                          </div>
                          <div className="flex-1">
                            <h3 className="font-bold">Anya</h3>
                            <p className="text-xs text-white/90 flex items-center gap-1.5">
                              <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></span>
                              online
                            </p>
                          </div>
                          <Button variant="ghost" size="sm" className="text-white hover:bg-white/10 h-8 w-8 p-0">
                            <Icon name="MoreVertical" size={18} />
                          </Button>
                        </div>
                      </div>

                      <div className="h-[450px] overflow-y-auto p-4 space-y-3 bg-gradient-to-b from-gray-50 to-white">
                        {messages.map((message) => (
                          <div
                            key={message.id}
                            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-up`}
                          >
                            <div className={`max-w-[85%] space-y-2`}>
                              {message.sender === 'anya' && (
                                <div className="flex items-center gap-2 mb-1">
                                  <div className="w-6 h-6 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-white text-xs font-bold shadow">
                                    A
                                  </div>
                                  <span className="text-xs text-gray-500 font-medium">Anya</span>
                                </div>
                              )}
                              <div
                                className={`rounded-2xl px-4 py-3 shadow-md ${
                                  message.sender === 'user'
                                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-tr-sm'
                                    : 'bg-white border-2 border-purple-100 text-gray-900 rounded-tl-sm'
                                }`}
                              >
                                <p className="text-sm leading-relaxed">{message.text}</p>
                              </div>
                              {message.translation && (
                                <div className="text-xs text-gray-500 italic px-2 flex items-start gap-1">
                                  <Icon name="Languages" size={11} className="mt-0.5 flex-shrink-0" />
                                  {message.translation}
                                </div>
                              )}
                              {message.correction && (
                                <div className="bg-orange-50 border-2 border-orange-200 rounded-xl px-3 py-2.5 text-xs text-orange-900 shadow-sm">
                                  <div className="flex items-start gap-2">
                                    <Icon name="Lightbulb" size={14} className="text-orange-500 mt-0.5 flex-shrink-0" />
                                    <div>
                                      <div className="font-semibold mb-1">💡 Подсказка</div>
                                      <div>{message.correction}</div>
                                    </div>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                        {isTyping && (
                          <div className="flex justify-start animate-fade-in">
                            <div className="flex items-center gap-2">
                              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-white text-xs font-bold shadow">
                                A
                              </div>
                              <div className="bg-white border-2 border-purple-100 rounded-2xl rounded-tl-sm px-4 py-3 shadow-md">
                                <div className="flex gap-1">
                                  <div className="w-2 h-2 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                  <div className="w-2 h-2 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                  <div className="w-2 h-2 bg-gradient-to-r from-purple-400 to-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                        <div ref={messagesEndRef} />
                      </div>

                      <div className="p-4 bg-white border-t">
                        <div className="flex flex-wrap gap-2 mb-3">
                          {quickPhrases.map((phrase, idx) => (
                            <Button
                              key={idx}
                              variant="outline"
                              size="sm"
                              onClick={() => setInput(phrase)}
                              className="text-xs hover:bg-purple-50 hover:border-purple-300"
                            >
                              {phrase}
                            </Button>
                          ))}
                        </div>
                        <div className="flex gap-2">
                          <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                            placeholder="Type in English..."
                            className="flex-1 px-4 py-3 text-sm border-2 border-gray-200 rounded-xl focus:border-purple-400 focus:outline-none"
                          />
                          <Button
                            onClick={handleSend}
                            disabled={!input.trim() || isTyping}
                            className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 px-4 shadow-lg"
                          >
                            <Icon name="Send" size={18} />
                          </Button>
                        </div>
                      </div>
                    </Card>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="text-center mt-12">
            <div className="inline-flex items-center gap-2 px-6 py-3 bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border-2 border-purple-100">
              <Icon name="Sparkles" size={18} className="text-purple-600" />
              <span className="text-gray-700 font-medium">Это демо с ограниченными ответами. Полная версия в Telegram намного умнее!</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
