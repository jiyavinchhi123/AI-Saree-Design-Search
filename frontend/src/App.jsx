import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import SearchDesign from './pages/SearchDesign';
import DataSources from './pages/DataSources';
import SearchHistory from './pages/SearchHistory';

export default function App() {
  const [activeTab, setActiveTab] = useState('search');

  const renderActivePage = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard setActiveTab={setActiveTab} />;
      case 'search':
        return <SearchDesign />;
      case 'data-sources':
        return <DataSources />;
      case 'history':
        return <SearchHistory />;
      default:
        return <SearchDesign />;
    }
  };

  return (
    <div className="app-container" id="app-root">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="main-wrapper">
        <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
        <main>{renderActivePage()}</main>
      </div>
    </div>
  );
}
