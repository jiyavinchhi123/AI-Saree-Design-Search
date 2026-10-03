import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Search, 
  History, 
  Layers, 
  Sparkles, 
  X,
  BookOpen
} from 'lucide-react';
import { api } from '../services/api';

export default function Sidebar({ activeTab, setActiveTab, mobileNavOpen, setMobileNavOpen }) {
  const [oneNoteStatus, setOneNoteStatus] = useState(null);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 15000);
    return () => clearInterval(interval);
  }, []);

  const loadStatus = async () => {
    try {
      const data = await api.getOneNoteStatus();
      setOneNoteStatus(data);
    } catch (e) {
      console.error('Sidebar status load error:', e);
    }
  };

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'data-sources', label: 'OneNote Integration', icon: BookOpen },
    { id: 'search', label: 'Search Design', icon: Search },
    { id: 'history', label: 'Search History', icon: History },
  ];

  return (
    <aside 
      className={`app-sidebar ${mobileNavOpen ? 'mobile-open' : ''}`} 
      id="main-sidebar"
    >
      {/* Brand Header */}
      <div className="brand-section">
        <div className="brand-icon-box" title="AI Saree Design Search">
          <Layers size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <div className="brand-title">AI Saree Search</div>
          <div className="brand-subtitle">OneNote Visual Intel</div>
        </div>

        {/* Close Button on Mobile Drawer */}
        {setMobileNavOpen && (
          <button 
            className="mobile-close-btn"
            onClick={() => setMobileNavOpen(false)}
            aria-label="Close Navigation"
            style={{
              display: 'none',
              background: 'transparent',
              color: 'var(--text-muted)',
              padding: '6px'
            }}
          >
            <X size={20} />
          </button>
        )}
      </div>

      {/* Navigation Items */}
      <nav className="nav-menu" aria-label="Main Navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              id={`nav-${item.id}`}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <Icon size={19} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* OneNote Status Card */}
      <div 
        className="sidebar-onenote-badge" 
        id="onenote-status-badge"
        onClick={() => setActiveTab('data-sources')}
        style={{ cursor: 'pointer' }}
        title="View Microsoft OneNote Integration & Sync Details"
      >
        <div className="badge-header">
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Sparkles size={14} style={{ color: 'var(--primary-purple)' }} /> OneNote Sync
          </span>
          <span style={{ fontSize: '0.74rem', color: 'var(--primary-purple)', fontWeight: 800 }}>
            {oneNoteStatus?.indexed_designs_count || 0} designs
          </span>
        </div>
        <div className="badge-status">
          <div className={`status-dot ${oneNoteStatus?.is_connected ? '' : 'inactive'}`} />
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {oneNoteStatus?.is_connected 
              ? (oneNoteStatus.display_name || oneNoteStatus.user_email || 'Connected')
              : 'Not Connected'}
          </span>
        </div>
      </div>
    </aside>
  );
}
