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
            onClick={() => setActiveTab('data-sources')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              background: 'var(--emerald-light)',
              border: '1px solid var(--emerald-border)',
              borderRadius: 'var(--radius-full)',
              padding: '6px 14px',
              fontSize: '0.80rem',
              color: 'var(--accent-emerald)',
              fontWeight: 600,
              cursor: 'pointer'
            }}
            title="Microsoft OneNote Connected"
          >
            <CheckCircle2 size={14} style={{ color: 'var(--accent-emerald)' }} />
            <span style={{ maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {oneNoteStatus.display_name || oneNoteStatus.user_email}
            </span>
            <span style={{ fontSize: '0.74rem', opacity: 0.8, color: '#047857' }}>
              • {oneNoteStatus.indexed_designs_count} designs
            </span>
          </div>
        ) : (
          <div 
            onClick={() => setActiveTab('data-sources')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              background: 'var(--purple-light)',
              border: '1px solid var(--purple-border)',
              borderRadius: 'var(--radius-full)',
              padding: '6px 14px',
              fontSize: '0.80rem',
              color: 'var(--primary-purple)',
              fontWeight: 600,
              cursor: 'pointer'
            }}
            title="Connect Microsoft OneNote"
          >
            <BookOpen size={14} />
            <span>Connect OneNote</span>
          </div>
        )}

        {/* AI Engine Status Pill */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '7px',
          background: 'var(--gold-light)',
          border: '1px solid var(--gold-border)',
          borderRadius: 'var(--radius-full)',
          padding: '6px 14px',
          fontSize: '0.78rem',
          color: 'var(--gold-text)',
          fontWeight: 700
        }}>
          <Sparkles size={14} style={{ color: 'var(--gold-primary)' }} />
          <span>Color-Invariant AI</span>
        </div>
      </div>
    </header>
  );
}
