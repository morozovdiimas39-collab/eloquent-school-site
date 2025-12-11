import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '@/components/anya/Header';
import HeroSection from '@/components/anya/HeroSection';
import DemoChat from '@/components/anya/DemoChat';
import FeaturesSection from '@/components/anya/FeaturesSection';
import ComparisonSection from '@/components/anya/ComparisonSection';
import HowItWorks from '@/components/anya/HowItWorks';
import StatsSection from '@/components/anya/StatsSection';
import TestimonialsSection from '@/components/anya/TestimonialsSection';
import LevelSection from '@/components/anya/LevelSection';
import TeacherSection from '@/components/anya/TeacherSection';
import PricingSection from '@/components/anya/PricingSection';
import BlogSection from '@/components/anya/BlogSection';
import FAQSection from '@/components/anya/FAQSection';
import CTASection from '@/components/anya/CTASection';
import Footer from '@/components/anya/Footer';

export default function Index() {
  const navigate = useNavigate();

  useEffect(() => {
    // Если открыто через Telegram WebApp - редиректим на Dashboard
    if (window.Telegram?.WebApp?.initDataUnsafe?.user) {
      console.log('🔄 Telegram WebApp detected, redirecting to /app');
      navigate('/app');
    }
  }, [navigate]);

  const handleStartDemo = () => {
    document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Header />
      <HeroSection onStartDemo={handleStartDemo} />
      <DemoChat />
      <StatsSection />
      <FeaturesSection />
      <ComparisonSection />
      <HowItWorks />
      <LevelSection />
      <TeacherSection />
      <TestimonialsSection />
      <PricingSection />
      <BlogSection />
      <FAQSection />
      <CTASection />
      <Footer />
    </div>
  );
}