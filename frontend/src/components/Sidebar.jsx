import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Search, 
  Database, 
  History, 
  Layers, 
  Sparkles, 
  RefreshCw,
  ExternalLink
} from 'lucide-react';
import { api } from '../services/api';

export default function Sidebar({ activeTab, setActiveTab }) {
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
      console.error(e);
    }
  };

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'search', label: 'Search Design', icon: Search },
    { id: 'data-sources', label: 'Data Sources & OneNote', icon: Database },
    { id: 'history', label: 'Search History', icon: History },
  ];

  return (
    <aside className="app-sidebar" id="main-sidebar">
      {/* Brand Header */}
      <div className="brand-section">
        <div className="brand-icon-box">
          <Layers size={24} />
        </div>
        <div>
          <div className="brand-title">AI Saree Search</div>
          <div className="brand-subtitle">OneNote Visual Intel</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="nav-menu">
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
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* OneNote Status Card */}
      <div className="sidebar-onenote-badge" id="onenote-status-badge">
        <div className="badge-header">
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Sparkles size={14} color="#d8b4fe" /> OneNote Sync
          </span>
          <span style={{ fontSize: '0.7rem', color: '#c084fc' }}>
            {oneNoteStatus?.indexed_designs_count || 0} designs
          </span>
        </div>
        <div className="badge-status">
          <div className={`status-dot ${oneNoteStatus?.is_connected ? '' : 'inactive'}`} />
          <span>
            {oneNoteStatus?.is_connected 
              ? `Connected (${oneNoteStatus.user_email || 'Active'})`
              : 'Not Connected'}
          </span>
        </div>
      </div>
    </aside>
  );
}
