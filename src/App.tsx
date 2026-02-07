
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import Dashboard from "./pages/Dashboard";
import Admin from "./pages/Admin";
import Learn from "./pages/Learn";
import AngryBirdsGame from "./pages/AngryBirdsGame";
import SystemTest from "./pages/SystemTest";
import TimezoneSetup from "./pages/TimezoneSetup";
import Pricing from "./pages/webapp/Pricing";
import Blog from "./pages/Blog";
import BlogPost from "./pages/BlogPost";
import NotFound from "./pages/NotFound";
import GoalTest from "./pages/GoalTest";
import Oferta from "./pages/Oferta";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/app" element={<Dashboard />} />
          <Route path="/learn" element={<Learn />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/blog" element={<Blog />} />
          <Route path="/blog/:id" element={<BlogPost />} />
          <Route path="/admin" element={<Admin />} />

          <Route path="/game" element={<AngryBirdsGame />} />
          <Route path="/system-test" element={<SystemTest />} />
          <Route path="/timezone-setup" element={<TimezoneSetup />} />
          <Route path="/test" element={<GoalTest />} />
          <Route path="/oferta" element={<Oferta />} />
          {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;