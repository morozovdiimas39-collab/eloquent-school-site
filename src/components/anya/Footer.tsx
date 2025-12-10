import Icon from '@/components/ui/icon';

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-white py-12">
      <div className="container mx-auto px-4">
        <div className="grid md:grid-cols-4 gap-8 mb-8">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <img 
                src="https://cdn.poehali.dev/files/загруженное (1).png" 
                alt="Anya" 
                className="w-12 h-12 rounded-full object-cover shadow-lg"
              />
              <div className="flex flex-col">
                <span className="font-bold text-xl bg-gradient-to-r from-purple-400 via-blue-400 to-indigo-400 bg-clip-text text-transparent">
                  anyaGPT
                </span>
                <span className="text-xs text-gray-500 -mt-1">
                  AI English Tutor
                </span>
              </div>
            </div>
            <p className="text-gray-400 text-sm">
              Твой личный ИИ-репетитор английского языка в Telegram
            </p>
          </div>

          <div>
            <h3 className="font-bold text-lg mb-4">Продукт</h3>
            <ul className="space-y-2 text-gray-400">
              <li><a href="#features" className="hover:text-white transition-colors">Возможности</a></li>
              <li><a href="#how-it-works" className="hover:text-white transition-colors">Как работает</a></li>
              <li><a href="#pricing" className="hover:text-white transition-colors">Тарифы</a></li>
              <li><a href="#demo" className="hover:text-white transition-colors">Попробовать демо</a></li>
            </ul>
          </div>

          <div>
            <h3 className="font-bold text-lg mb-4">Поддержка</h3>
            <ul className="space-y-2 text-gray-400">
              <li><a href="#" className="hover:text-white transition-colors">База знаний</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Часто задаваемые вопросы</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Связаться с нами</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Обратная связь</a></li>
            </ul>
          </div>

          <div>
            <h3 className="font-bold text-lg mb-4">Сообщество</h3>
            <ul className="space-y-2 text-gray-400">
              <li><a href="https://t.me/+QgiLIa1gFRY4Y2Iy" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors flex items-center gap-2">
                <Icon name="Send" size={16} />
                Telegram канал
              </a></li>
              <li><a href="#" className="hover:text-white transition-colors flex items-center gap-2">
                <Icon name="Users" size={16} />
                Сообщество учеников
              </a></li>
              <li><a href="#" className="hover:text-white transition-colors flex items-center gap-2">
                <Icon name="GraduationCap" size={16} />
                Для учителей
              </a></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-gray-400 text-sm">
              © 2025 anyaGPT. Все права защищены.
            </p>
            <div className="flex gap-6 text-sm text-gray-400">
              <a href="#" className="hover:text-white transition-colors">Политика конфиденциальности</a>
              <a href="#" className="hover:text-white transition-colors">Условия использования</a>
              <a href="#" className="hover:text-white transition-colors">Договор оферты</a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}