import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  BookOpen, 
  FolderSearch, 
  ExternalLink,
  Cpu,
  Target,
  ArrowUpRight
} from 'lucide-react';
import { api } from '../services/api';

export default function Dashboard({ setActiveTab }) {
  const [oneNoteStatus, setOneNoteStatus] = useState(null);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const status = await api.getOneNoteStatus();
      setOneNoteStatus(status);
    } catch (err) {
      console.error('Dashboard status load error:', err);
    }
  };

  const workflowSteps = [
    {
      num: '01',
      title: 'Connect OneNote',
      desc: 'Link Microsoft account to scan textile design notebooks with read-only security.',
      icon: BookOpen,
      action: () => setActiveTab('data-sources')
    },
    {
      num: '02',
      title: 'Upload Image',
      desc: 'Drag & drop any saree fabric photo, swatch, pallu, or draft sketch.',
      icon: FolderSearch,
      action: () => setActiveTab('search')
    },
    {
      num: '03',
      title: 'AI Analysis',
      desc: 'DINOv2 neural net extracts 1536-D motifs and borders, discarding fabric colors.',
      icon: Cpu,
      action: () => setActiveTab('search')
    },
    {
      num: '04',
      title: 'Find Match',
      desc: 'FAISS index instantly retrieves the exact matching historical design pattern.',
      icon: Target,
      action: () => setActiveTab('search')
    },
    {
      num: '05',
      title: 'Open in OneNote',
      desc: 'One click launches OneNote Online directly focused on that exact page.',
      icon: ExternalLink,
      action: () => setActiveTab('search')
    }
  ];

  return (
    <div className="page-container" id="dashboard-page">
      {/* 1. FIRST CARD: WELCOME & ACTION HERO */}
      <div className="hero-card" id="dashboard-hero" style={{ marginBottom: '24px' }}>
        <div style={{ maxWidth: '720px', position: 'relative', zIndex: 1 }}>
          <div className="hero-pill">
            <Sparkles size={14} /> Color-Invariant Computer Vision
          </div>
          
          <h1 className="hero-title">AI Saree Design Search</h1>
          <div className="hero-tagline">Find. Reuse. Preserve.</div>
          
          <p className="hero-desc">
            Empower your saree manufacturing, weaving, and textile design teams to discover existing designs 
            across Microsoft OneNote archives in seconds. Our deep vision model recognizes motifs, borders, 
            and layouts regardless of fabric colorways.
          </p>

          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button 
              id="btn-quick-search"
              className="btn-primary" 
              onClick={() => setActiveTab('search')}
              style={{ padding: '10px 20px', fontSize: '0.88rem', fontWeight: 600 }}
            >
              <FolderSearch size={17} /> Search a Saree Design
            </button>
            <button 
              id="btn-quick-sources"
              className="btn-secondary" 
              onClick={() => setActiveTab('data-sources')}
              style={{ padding: '10px 18px', fontSize: '0.88rem', fontWeight: 600 }}
            >
              <BookOpen size={17} style={{ color: 'var(--primary-purple)' }} /> 
              {oneNoteStatus?.is_connected ? 'Manage OneNote Sync' : 'Connect Microsoft OneNote'}
            </button>
          </div>
        </div>
      </div>

      {/* 2. CARDS SHOWING STEPS */}
      <div className="workflow-section" id="workflow-steps-section">
        <div className="section-header" style={{ marginBottom: '20px' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>
            How the Visual Retrieval Engine Works
          </h3>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
            End-to-end workflow from Microsoft OneNote ingestion to exact-object deep linking.
          </p>
        </div>

        <div className="workflow-steps-grid">
          {workflowSteps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div 
                key={idx} 
                className="workflow-step-card"
                onClick={step.action}
                style={{ cursor: 'pointer' }}
                title={`Click to go to ${step.title}`}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div className="step-num-badge">{step.num}</div>
                  <ArrowUpRight size={14} style={{ color: 'var(--text-dim)' }} />
                </div>
                <div className="step-icon-wrap">
                  <Icon size={22} />
                </div>
                <div className="step-card-title">{step.title}</div>
                <div className="step-card-desc">{step.desc}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
