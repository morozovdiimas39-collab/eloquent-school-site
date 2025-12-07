import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import Icon from '@/components/ui/icon';

const faqs = [
  {
    question: 'Как начать пользоваться anyaGPT?',
    answer: 'Просто нажми "Начать учиться" и открой бота в Telegram. При первом запуске Аня задаст несколько вопросов, чтобы определить твой уровень, и можно будет сразу начать практику. Регистрация не требуется!'
  },
  {
    question: 'Бесплатная версия будет всегда?',
    answer: 'Да! Бесплатный план с 20 сообщениями в день останется навсегда. Этого достаточно для регулярной практики. Premium нужен, если хочешь безлимитное общение и дополнительные функции.'
  },
  {
    question: 'Можно ли отменить подписку?',
    answer: 'Конечно! Подписка оформляется через Telegram Stars и отменяется в любой момент в настройках Telegram. Никаких скрытых платежей. Первые 3 дня — пробный период с возвратом средств.'
  },
  {
    question: 'Аня исправляет ошибки?',
    answer: 'Да, Аня видит твои ошибки и тактично исправляет их прямо в диалоге. Она объясняет правило и даёт примеры. При этом не перебивает беседу — главное, чтобы ты практиковался свободно.'
  },
  {
    question: 'Можно ли заниматься без интернета?',
    answer: 'К сожалению, нет. anyaGPT работает через Telegram и требует подключения к интернету. Но зато ты можешь заниматься где угодно — в метро, кафе, на прогулке.'
  },
  {
    question: 'Подойдёт ли для подготовки к экзаменам?',
    answer: 'Да! anyaGPT помогает подготовиться к IELTS, TOEFL, ЕГЭ и другим экзаменам. Практикуй speaking, расширяй словарный запас, разбирай сложные темы. Но для полной подготовки лучше совмещать с репетитором.'
  },
  {
    question: 'Как Аня определяет мой уровень?',
    answer: 'При первом запуске Аня задаст тебе несколько вопросов на английском разной сложности. По твоим ответам она определит уровень (A1-C2) и будет подстраивать сложность диалогов.'
  },
  {
    question: 'Что делать, если я ничего не понимаю?',
    answer: 'Аня всегда даёт переводы своих сообщений (можно включить/выключить). Если что-то непонятно, просто спроси "What does this mean?" — она объяснит по-русски или проще на английском.'
  },
  {
    question: 'Могу ли я учить другие языки?',
    answer: 'Пока anyaGPT работает только с английским языком. Но мы планируем добавить другие языки в будущем. Следи за обновлениями в нашем Telegram-канале!'
  },
  {
    question: 'Как работает система для учителей?',
    answer: 'Учителя создают промокод и делятся им с учениками. Ученики привязываются к учителю и получают персональные слова для изучения. Учитель видит прогресс и получает 30% от подписок.'
  }
];

export default function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section className="container mx-auto px-4 py-20 bg-gradient-to-br from-blue-50 to-indigo-50">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Частые вопросы
          </h2>
          <p className="text-xl text-gray-600">
            Здесь ответы на самые популярные вопросы о anyaGPT
          </p>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, idx) => (
            <Card
              key={idx}
              className={`border-2 transition-all cursor-pointer ${
                openIndex === idx
                  ? 'border-blue-500 shadow-xl'
                  : 'border-blue-200 hover:border-blue-300'
              }`}
              onClick={() => setOpenIndex(openIndex === idx ? null : idx)}
            >
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-all ${
                    openIndex === idx
                      ? 'bg-blue-600'
                      : 'bg-blue-100'
                  }`}>
                    <Icon
                      name={openIndex === idx ? 'ChevronDown' : 'ChevronRight'}
                      size={20}
                      className={openIndex === idx ? 'text-white' : 'text-blue-600'}
                    />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-bold mb-2">{faq.question}</h3>
                    {openIndex === idx && (
                      <p className="text-gray-600 leading-relaxed animate-fade-in">
                        {faq.answer}
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mt-12 text-center">
          <Card className="inline-block border-2 border-blue-200 bg-white">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <Icon name="HelpCircle" size={32} className="text-blue-600 flex-shrink-0" />
                <div className="text-left">
                  <h4 className="font-bold text-lg mb-1">Не нашёл ответ?</h4>
                  <p className="text-gray-600 text-sm">
                    Напиши нам в Telegram: <a href="https://t.me/+QgiLIa1gFRY4Y2Iy" className="text-blue-600 hover:underline font-medium">@anyaGPT_support</a>
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>
  );
}
