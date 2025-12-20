import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import Icon from '@/components/ui/icon';
import { funcUrls } from '@/config/funcUrls';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'anya';
  role: 'user' | 'model';
}

const TELEGRAM_BOT_LINK = 'https://t.me/eloquent_school_bot';
const API_URL = funcUrls['webapp-api'];

export default function DemoChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: "Hi! I'm Anya 👋 Try chatting with me in English! I'll help you improve.",
      sender: 'anya',
      role: 'model'
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [messageCount, setMessageCount] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    // Не прокручиваем автоматически, пользователь сам управляет
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: input,
      sender: 'user',
      role: 'user'
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    const newCount = messageCount + 1;
    setMessageCount(newCount);

    // Прокручиваем вниз при отправке сообщения
    setTimeout(() => scrollToBottom(), 100);

    // Проверяем, если это 7-е сообщение - предлагаем перейти в Telegram
    if (newCount >= 7) {
      setTimeout(() => {
        const finalMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: "Great practice! 🎉\n\nTo continue learning with unlimited messages, exercises, and voice practice, let's move to Telegram where it's more convenient!\n\nClick the button below to start! 👇",
          sender: 'anya',
          role: 'model'
        };
        setMessages(prev => [...prev, finalMessage]);
        setIsTyping(false);
      }, 1500);
      return;
    }

    try {
      // Формируем историю для API
      const history = messages.map(msg => ({
        role: msg.role,
        content: msg.text
      }));

      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'demo_chat',
          message: input,
          history: history
        })
      });

      const data = await response.json();

      if (data.success && data.response) {
        const anyaMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: data.response,
          sender: 'anya',
          role: 'model'
        };
        setMessages(prev => [...prev, anyaMessage]);
        // Прокручиваем к ответу Ани
        setTimeout(() => scrollToBottom(), 100);
      } else {
        throw new Error(data.error || 'Failed to get response');
      }
    } catch (error) {
      console.error('Demo chat error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: "Sorry, I'm having trouble connecting right now. Try again in a moment! 😊",
        sender: 'anya',
        role: 'model'
      };
      setMessages(prev => [...prev, errorMessage]);
      setTimeout(() => scrollToBottom(), 100);
    } finally {
      setIsTyping(false);
    }
  };

  const handleQuickPhrase = (phrase: string) => {
    setInput(phrase);
  };

  const quickPhrases = [
    "Hi! How are you?",
    "I like learning English",
    "Tell me about yourself"
  ];

  const showTelegramButton = messageCount >= 7;

  return (
    <section id="demo" className="relative py-20 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-purple-50 via-white to-blue-50"></div>
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
              Напиши Ане на английском — она отвечает с помощью настоящего AI!
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
                                Online • Powered by Gemini 2.0
                              </p>
                            </div>
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
                                <p className="text-base leading-relaxed whitespace-pre-line">{message.text}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                        
                        {isTyping && (
                          <div className="flex justify-start animate-fade-in">
                            <div className="max-w-[75%] space-y-2">
                              <div className="flex items-center gap-2 mb-1">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-white text-sm font-bold shadow-md">
                                  A
                                </div>
                                <span className="text-xs text-gray-500 font-medium">Anya is typing...</span>
                              </div>
                              <div className="bg-white border-2 border-purple-100 rounded-2xl rounded-tl-sm px-5 py-4">
                                <div className="flex gap-1.5">
                                  <div className="w-2.5 h-2.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                  <div className="w-2.5 h-2.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                  <div className="w-2.5 h-2.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                        
                        <div ref={messagesEndRef} />
                      </div>

                      {showTelegramButton ? (
                        <div className="p-6 bg-gradient-to-r from-blue-50 to-purple-50 border-t-2 border-purple-100">
                          <Button
                            onClick={() => window.open(TELEGRAM_BOT_LINK, '_blank')}
                            className="w-full h-14 text-lg font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-lg hover:shadow-xl transition-all"
                          >
                            <Icon name="Send" size={20} className="mr-2" />
                            Продолжить в Telegram
                          </Button>
                        </div>
                      ) : (
                        <div className="p-6 bg-gradient-to-r from-gray-50 to-blue-50 border-t-2 border-gray-100 space-y-4">
                          {/* Quick phrases */}
                          <div className="flex flex-wrap gap-2">
                            {quickPhrases.map((phrase, index) => (
                              <button
                                key={index}
                                onClick={() => handleQuickPhrase(phrase)}
                                className="px-4 py-2 bg-white hover:bg-purple-50 text-gray-700 hover:text-purple-700 rounded-full text-sm font-medium border border-gray-200 hover:border-purple-300 transition-all hover:shadow-md"
                              >
                                {phrase}
                              </button>
                            ))}
                          </div>

                          {/* Input */}
                          <div className="flex gap-3">
                            <input
                              type="text"
                              value={input}
                              onChange={(e) => setInput(e.target.value)}
                              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                              placeholder="Type your message in English..."
                              disabled={isTyping}
                              className="flex-1 px-5 py-3.5 rounded-2xl border-2 border-gray-200 focus:border-purple-400 focus:ring-4 focus:ring-purple-100 outline-none text-base transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            />
                            <Button
                              onClick={handleSend}
                              disabled={!input.trim() || isTyping}
                              size="lg"
                              className="px-6 py-3.5 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              <Icon name="Send" size={20} />
                            </Button>
                          </div>

                          {/* Message counter */}
                          <div className="text-center text-sm text-gray-500">
                            {messageCount}/7 demo messages • {7 - messageCount} left
                          </div>
                        </div>
                      )}
                    </Card>
                  </div>
                </div>

                {/* Laptop base */}
                <div className="h-6 bg-gray-800 rounded-b-3xl border-8 border-gray-800 border-t-0"></div>
                <div className="h-2 bg-gray-700 rounded-b-lg mx-auto" style={{ width: '60%' }}></div>
              </div>
            </div>

            {/* Mobile: Full-width chat without phone frame */}
            <div className="lg:hidden px-4">
              <div className="relative mx-auto w-full max-w-2xl">
                <Card className="overflow-hidden border-0 shadow-2xl rounded-2xl">
                  {/* Chat header */}
                  <div className="bg-gradient-to-r from-purple-600 to-indigo-600 px-6 py-4 flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center relative">
                      <span className="text-2xl">👩‍🏫</span>
                      <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-green-400 rounded-full border-2 border-white"></div>
                    </div>
                    <div className="flex-1">
                      <div className="font-bold text-white text-lg">Anya AI</div>
                      <div className="text-sm text-white/90 flex items-center gap-1.5">
                        <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                        Gemini 2.0
                      </div>
                    </div>
                  </div>

                  {/* Chat messages */}
                  <div className="h-[400px] overflow-y-auto p-4 space-y-3 bg-gray-50">
                    {messages.map((message) => (
                      <div
                        key={message.id}
                        className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-up`}
                      >
                        <div className="max-w-[80%]">
                          {message.sender === 'anya' && (
                            <div className="flex items-center gap-2 mb-1.5">
                              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center text-white text-sm font-bold">
                                A
                              </div>
                            </div>
                          )}
                          <div
                            className={`rounded-2xl px-5 py-3 shadow-sm text-base ${
                              message.sender === 'user'
                                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-tr-sm'
                                : 'bg-white border-2 border-purple-100 text-gray-900 rounded-tl-sm'
                            }`}
                          >
                            <p className="leading-relaxed whitespace-pre-line">{message.text}</p>
                          </div>
                        </div>
                      </div>
                    ))}

                    {isTyping && (
                      <div className="flex justify-start animate-fade-in">
                        <div className="max-w-[80%]">
                          <div className="flex items-center gap-2 mb-1.5">
                            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-purple-500 to-indigo-500 flex items-center justify-center text-white text-sm font-bold">
                              A
                            </div>
                            <span className="text-sm text-gray-500">typing...</span>
                          </div>
                          <div className="bg-white border-2 border-purple-100 rounded-2xl rounded-tl-sm px-5 py-4">
                            <div className="flex gap-1.5">
                              <div className="w-2.5 h-2.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                              <div className="w-2.5 h-2.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                              <div className="w-2.5 h-2.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    <div ref={messagesEndRef} />
                  </div>

                  {showTelegramButton ? (
                    <div className="p-5 bg-gradient-to-r from-blue-50 to-purple-50 border-t-2 border-purple-100">
                      <Button
                        onClick={() => window.open(TELEGRAM_BOT_LINK, '_blank')}
                        className="w-full h-14 text-lg font-semibold bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
                      >
                        <Icon name="Send" size={20} className="mr-2" />
                        Продолжить в Telegram
                      </Button>
                    </div>
                  ) : (
                    <div className="p-5 bg-white border-t-2 border-gray-100 space-y-4">
                      {/* Quick phrases */}
                      <div className="flex flex-wrap gap-2">
                        {quickPhrases.slice(0, 2).map((phrase, index) => (
                          <button
                            key={index}
                            onClick={() => handleQuickPhrase(phrase)}
                            className="px-4 py-2 bg-gray-50 hover:bg-purple-50 text-gray-700 hover:text-purple-700 rounded-full text-sm font-medium border border-gray-200 hover:border-purple-300 transition-all"
                          >
                            {phrase}
                          </button>
                        ))}
                      </div>

                      {/* Input */}
                      <div className="flex gap-3">
                        <input
                          type="text"
                          value={input}
                          onChange={(e) => setInput(e.target.value)}
                          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                          placeholder="Type in English..."
                          disabled={isTyping}
                          className="flex-1 px-5 py-3 rounded-full border-2 border-gray-200 focus:border-purple-400 focus:ring-4 focus:ring-purple-100 outline-none text-base disabled:opacity-50"
                        />
                        <Button
                          onClick={handleSend}
                          disabled={!input.trim() || isTyping}
                          size="lg"
                          className="px-6 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:opacity-50"
                        >
                          <Icon name="Send" size={18} />
                        </Button>
                      </div>

                      {/* Message counter */}
                      <div className="text-center text-sm text-gray-500 font-medium">
                        {messageCount}/7 demo messages • {7 - messageCount} left
                      </div>
                    </div>
                  )}
                </Card>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}