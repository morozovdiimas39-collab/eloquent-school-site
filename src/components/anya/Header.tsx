import { Button } from '@/components/ui/button';
import Icon from '@/components/ui/icon';
import { useNavigate } from 'react-router-dom';

export default function Header() {
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-white/80 backdrop-blur-md">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <button 
          onClick={() => navigate('/')}
          className="group flex items-center gap-2 hover:scale-105 transition-transform"
        >
          <img 
            src="https://cdn.poehali.dev/projects/b7f7b2d5-b36c-4ecd-924a-51eec76a70ee/files/18725014-599d-4e0d-9f9c-fda9c37e1b86.jpg" 
            alt="anyaGPT" 
            className="h-10 w-auto object-contain"
          />
        </button>

        <nav className="hidden md:flex items-center gap-6">
          <a href="#features" className="text-gray-700 hover:text-blue-600 transition-colors font-medium">
            Возможности
          </a>
          <a href="#how-it-works" className="text-gray-700 hover:text-blue-600 transition-colors font-medium">
            Как работает
          </a>
          <a href="#pricing" className="text-gray-700 hover:text-blue-600 transition-colors font-medium">
            Тарифы
          </a>
        </nav>

        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            onClick={() => navigate('/app')}
            className="font-medium"
          >
            Войти
          </Button>
          <Button
            onClick={() => navigate('/app')}
            className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 font-semibold shadow-lg"
          >
            Начать учиться
            <Icon name="ArrowRight" size={16} className="ml-2" />
          </Button>
        </div>
      </div>
    </header>
  );
}