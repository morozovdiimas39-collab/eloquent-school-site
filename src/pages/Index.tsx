import { useState } from 'react';
import Header from '@/components/anya/Header';
import HeroSection from '@/components/anya/HeroSection';
import DemoChat from '@/components/anya/DemoChat';
import FeaturesSection from '@/components/anya/FeaturesSection';
import HowItWorks from '@/components/anya/HowItWorks';
import PricingSection from '@/components/anya/PricingSection';
import Footer from '@/components/anya/Footer';

export default function Index() {
  const [showDemo, setShowDemo] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-50 via-white to-purple-50">
      <Header />
      <HeroSection onStartDemo={() => setShowDemo(true)} />
      {showDemo && <DemoChat />}
      <FeaturesSection />
      <HowItWorks />
      <PricingSection />
      <Footer />
    </div>
  );
}
