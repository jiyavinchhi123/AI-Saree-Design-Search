import React, { useState, useEffect } from 'react';
import { Cpu, BookOpen } from 'lucide-react';
import { api } from '../services/api';

export default function Navbar({ activeTab, setActiveTab }) {
  const [oneNoteStatus, setOneNoteStatus] = useState(null);

  useEffect(() => {
    api.getOneNoteStatus().then(status => {
      setOneNoteStatus(status);
    }).catch(() => {});
  }, [activeTab]);

  const getPageTitle = () => {
    switch (activeTab) {
      case 'dashboard': return 'Executive Overview';
      case 'search': return 'Visual Saree Search';
      case 'data-sources': return 'OneNote Integration & Sync';
      case 'history': return 'Search Audits & History';
      default: return 'Enterprise Visual Retrieval';
    }
  };

  return (
    <header className="top-header" id="top-navbar">
      <div className="header-title-block">
        <h1>{getPageTitle()}</h1>
        <p>AI Saree Design Search &bull; Real-Time Microsoft OneNote Visual Engine</p>
      </div>

      <div className="header-actions" style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {oneNoteStatus?.is_connected ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(16, 185, 129, 0.12)',
            border: '1px solid rgba(16, 185, 129, 0.35)',
            borderRadius: '20px',
            padding: '5px 14px',
            fontSize: '0.78rem',
            color: '#10b981'
          }}>
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#10b981', boxShadow: '0 0 6px #10b981' }} />
            <span>{oneNoteStatus.display_name || oneNoteStatus.user_email}</span>
            <span style={{ opacity: 0.6, fontSize: '0.7rem' }}>• {oneNoteStatus.indexed_designs_count} designs</span>
          </div>
        ) : (
          <div 
            onClick={() => setActiveTab && setActiveTab('data-sources')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(212, 175, 55, 0.1)',
              border: '1px solid rgba(212, 175, 55, 0.3)',
              borderRadius: '20px',
              padding: '5px 14px',
              fontSize: '0.78rem',
              color: 'var(--gold-light)',
              cursor: 'pointer'
            }}
            title="Click to connect Microsoft OneNote"
          >
            <BookOpen size={13} style={{ color: 'var(--gold-primary)' }} />
            <span>Connect Microsoft OneNote</span>
          </div>
        )}

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'rgba(212, 175, 55, 0.08)',
          border: '1px solid var(--border-active)',
          borderRadius: '20px',
          padding: '6px 14px',
          fontSize: '0.78rem',
          color: 'var(--gold-light)'
        }}>
          <Cpu size={14} style={{ color: 'var(--gold-primary)' }} />
          <span>Color-Invariant AI Active</span>
        </div>
      </div>
    </header>
  );
}
