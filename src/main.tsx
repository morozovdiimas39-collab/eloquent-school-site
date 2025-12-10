import * as React from 'react';
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'

// Telegram WebApp cache buster and version check
async function initApp() {
  if (window.Telegram?.WebApp) {
    console.log('[WebApp] Telegram WebApp detected, version check...');
    
    try {
      // Check server version
      const response = await fetch('/version.json?t=' + Date.now());
      const serverVersion = await response.json();
      const localVersion = localStorage.getItem('app_version');
      
      console.log('[WebApp] Server version:', serverVersion.version, 'Local version:', localVersion);
      
      if (localVersion && localVersion !== serverVersion.version) {
        console.log('[WebApp] Version mismatch! Clearing cache...');
        localStorage.clear();
        sessionStorage.clear();
        localStorage.setItem('app_version', serverVersion.version);
        window.location.reload();
        return;
      } else if (!localVersion) {
        localStorage.setItem('app_version', serverVersion.version);
      }
    } catch (error) {
      console.error('[WebApp] Version check failed:', error);
    }
    
    // Force expand to full screen
    window.Telegram.WebApp.expand();
    
    // Signal ready
    window.Telegram.WebApp.ready();
    
    // Disable vertical swipes (prevents accidental closes)
    window.Telegram.WebApp.isVerticalSwipesEnabled = false;
  }
  
  createRoot(document.getElementById("root")!).render(<App />);
}

initApp();