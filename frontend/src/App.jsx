import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import SearchDesign from './pages/SearchDesign';
import DataSources from './pages/DataSources';
import SearchHistory from './pages/SearchHistory';

export default function App() {
  // Initialize activeTab from pathname or query
  const getInitialTab = () => {
    try {
      const path = window.location.pathname.toLowerCase();
      const params = new URLSearchParams(window.location.search);
      const userId = params.get('user_id');
      if (userId) {
        localStorage.setItem('saree_current_user_id', userId);
      }
      if (path.includes('search')) return 'search';
      if (path.includes('data-sources') || path.includes('sources') || path.includes('onenote')) return 'data-sources';
      if (path.includes('history')) return 'history';
      return 'dashboard';
    } catch {
      return 'dashboard';
    }
  };

  const [activeTab, setActiveTab] = useState(getInitialTab);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  // Sync browser URL with tab changes
  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
    setMobileNavOpen(false); // Close mobile drawer on selection

    try {
      const pathMap = {
        'dashboard': '/',
        'search': '/search',
        'data-sources': '/data-sources',
        'history': '/history'
      };
      const newPath = pathMap[tabId] || '/';
      if (window.location.pathname !== newPath) {
        window.history.pushState({ tab: tabId }, '', newPath);
      }
    } catch (e) {
      console.warn('URL pushState notice:', e);
    }
  };

  // Listen for browser back/forward navigation
  React.useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname.toLowerCase();
      if (path.includes('search')) setActiveTab('search');
      else if (path.includes('data-sources') || path.includes('sources')) setActiveTab('data-sources');
      else if (path.includes('history')) setActiveTab('history');
      else setActiveTab('dashboard');
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const renderActivePage = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard setActiveTab={handleTabChange} />;
      case 'search':
        return <SearchDesign />;
      case 'data-sources':
        return <DataSources />;
      case 'history':
        return <SearchHistory />;
      default:
        return <Dashboard setActiveTab={handleTabChange} />;
    }
  };

  return (
    <div className="app-container" id="app-root">
      {/* Mobile Drawer Overlay */}
      <div 
        className={`mobile-sidebar-overlay ${mobileNavOpen ? 'active' : ''}`}
        onClick={() => setMobileNavOpen(false)}
        aria-hidden="true"
      />

      {/* Sidebar Navigation */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={handleTabChange} 
        mobileNavOpen={mobileNavOpen}
        setMobileNavOpen={setMobileNavOpen}
      />

      {/* Main Content Area */}
      <div className="main-wrapper">
        <Navbar 
          activeTab={activeTab} 
          setActiveTab={handleTabChange} 
          mobileNavOpen={mobileNavOpen}
          setMobileNavOpen={setMobileNavOpen}
        />
        <main>{renderActivePage()}</main>
      </div>
    </div>
  );
}
