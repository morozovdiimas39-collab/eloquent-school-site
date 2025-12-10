import Header from '@/components/anya/Header';
import Footer from '@/components/anya/Footer';
import BlogSection from '@/components/anya/BlogSection';

export default function Blog() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Header />
      <div className="pt-20">
        <BlogSection showAll={true} />
      </div>
      <Footer />
    </div>
  );
}
