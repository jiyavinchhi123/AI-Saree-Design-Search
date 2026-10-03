import React, { useState, useEffect } from 'react';
import { Cpu, BookOpen, Menu, Sparkles, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';

export default function Navbar({ activeTab, setActiveTab, mobileNavOpen, setMobileNavOpen }) {
  const [oneNoteStatus, setOneNoteStatus] = useState(null);

  useEffect(() => {
    api.getOneNoteStatus()
      .then(status => setOneNoteStatus(status))
      .catch(() => {});
  }, [activeTab]);

  const getPageTitle = () => {
    switch (activeTab) {
      case 'dashboard': return 'Dashboard Overview';
      case 'search': return 'Visual Saree Search';
      case 'data-sources': return 'OneNote Integration & Sync';
      case 'history': return 'Search History & Audits';
      default: return 'AI Saree Search';
    }
  };

  const getPageSubtitle = () => {
    switch (activeTab) {
      case 'dashboard': return 'Find. Reuse. Preserve. • Enterprise Textile Design Intelligence';
      case 'search': return 'Deep Vision Motif Matching • Color-Invariant Spatial Neural Net';
      case 'data-sources': return 'Real-Time Microsoft OneNote Notebook Synchronization';
      case 'history': return 'Audit Logs of Uploaded Saree Design Queries';
      default: return 'Enterprise Visual Intelligence';
    }
  };

  return (
    <header className="top-header" id="top-navbar">
      <div className="header-left">
        {/* Hamburger Menu Toggle on Mobile */}
        <button 
          className="mobile-menu-toggle"
          onClick={() => setMobileNavOpen(!mobileNavOpen)}
          aria-label="Toggle Navigation Menu"
        >
          <Menu size={20} />
        </button>

        <div className="header-title-block">
          <h1>{getPageTitle()}</h1>
          <p>{getPageSubtitle()}</p>
        </div>
      </div>

      <div className="header-actions">
        {/* Microsoft OneNote Account Connection Pill */}
        {oneNoteStatus?.is_connected ? (
          <div 
            className="navbar-status-pill connected"
            onClick={() => setActiveTab('data-sources')}
            title="Microsoft OneNote Connected"
          >
            <CheckCircle2 size={14} style={{ color: 'var(--accent-emerald)', flexShrink: 0 }} />
            <span className="navbar-pill-username">
              {oneNoteStatus.display_name || oneNoteStatus.user_email}
            </span>
            <span className="navbar-pill-count">
              • {oneNoteStatus.indexed_designs_count} designs
            </span>
          </div>
        ) : (
          <div 
            className="navbar-status-pill disconnected"
            onClick={() => setActiveTab('data-sources')}
            title="Connect Microsoft OneNote"
          >
            <BookOpen size={14} />
            <span>Connect OneNote</span>
          </div>
        )}

        {/* AI Engine Status Pill */}
        <div className="navbar-engine-pill">
          <Sparkles size={14} style={{ color: 'var(--gold-primary)' }} />
          <span>Color-Invariant AI</span>
        </div>
      </div>
    </header>
  );
}
