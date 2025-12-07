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
    <section id="demo" className="container mx-auto px-4 py-12">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Попробуй поговорить с Аней
          </h2>
          <p className="text-gray-600 text-lg">
            Это демо-версия. Напиши что-нибудь на английском и посмотри, как Аня отвечает
          </p>
        </div>

        <Card className="overflow-hidden shadow-2xl border-2 border-blue-100">
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-4 text-white">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
                <span className="text-2xl">👩‍🏫</span>
              </div>
              <div>
                <h3 className="font-bold text-lg">Anya</h3>
                <p className="text-sm text-white/80">Твой ИИ-репетитор • Онлайн</p>
              </div>
            </div>
          </div>

          <div className="h-96 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[80%] space-y-2`}>
                  <div
                    className={`rounded-2xl px-4 py-3 ${
                      message.sender === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-white border-2 border-blue-100 text-gray-900'
                    }`}
                  >
                    <p className="text-sm md:text-base">{message.text}</p>
                  </div>
                  {message.translation && (
                    <div className="text-xs text-gray-500 italic px-2">
                      💭 {message.translation}
                    </div>
                  )}
                  {message.correction && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-3 py-2 text-xs text-yellow-800">
                      <Icon name="Lightbulb" size={14} className="inline mr-1" />
                      {message.correction}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isTyping && (
              <div className="flex justify-start">
                <div className="bg-white border-2 border-blue-100 rounded-2xl px-4 py-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
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
                  className="text-xs"
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
                placeholder="Type your message in English..."
                className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-400 focus:outline-none"
              />
              <Button
                onClick={handleSend}
                disabled={!input.trim() || isTyping}
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 px-6"
              >
                <Icon name="Send" size={20} />
              </Button>
            </div>
          </div>
        </Card>

        <div className="text-center mt-6 text-sm text-gray-600">
          💡 Это демо с ограниченными ответами. Полная версия в Telegram намного умнее!
        </div>
      </div>
    </section>
  );
}