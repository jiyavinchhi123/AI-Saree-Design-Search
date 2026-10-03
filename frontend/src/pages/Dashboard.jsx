import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Layers, 
  BookOpen, 
  FolderSearch, 
  CheckCircle2, 
  ArrowRight,
  ExternalLink,
  History,
  CloudSync,
  Cpu,
  Target,
  ArrowUpRight,
  ShieldCheck
} from 'lucide-react';
import { api, getExactPageWebUrl, getCleanOneNoteUrl } from '../services/api';
import OneNoteBreadcrumb from '../components/OneNoteBreadcrumb';

export default function Dashboard({ setActiveTab }) {
  const [stats, setStats] = useState({
    totalDesigns: 0,
    notebooks: 0,
    categories: 0,
    totalSearches: 0
  });
  const [oneNoteStatus, setOneNoteStatus] = useState(null);
  const [recentDesigns, setRecentDesigns] = useState([]);
  const [recentSearches, setRecentSearches] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [catalogData, statusData, historyData] = await Promise.allSettled([
        api.getDesigns(),
        api.getOneNoteStatus(),
        api.getSearchHistory(6)
      ]);

      const designs = catalogData.status === 'fulfilled' ? (catalogData.value.designs || []) : [];
      const notebooks = catalogData.status === 'fulfilled' ? (catalogData.value.filters?.notebooks || []) : [];
      const categories = catalogData.status === 'fulfilled' ? (catalogData.value.filters?.categories || []) : [];
      const status = statusData.status === 'fulfilled' ? statusData.value : null;
      const historyList = historyData.status === 'fulfilled' ? (historyData.value.history || []) : [];

      setOneNoteStatus(status);
      setStats({
        totalDesigns: designs.length,
        notebooks: notebooks.length,
        categories: categories.length,
        totalSearches: historyList.length
      });
      setRecentDesigns(designs.slice(0, 6));
      setRecentSearches(historyList.slice(0, 4));
    } catch (err) {
      console.error('Dashboard load error:', err);
    } finally {
      setLoading(false);
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
      desc: 'One click launches OneNote Desktop or Online directly focused on that exact image.',
      icon: ExternalLink,
      action: () => setActiveTab('search')
    }
  ];

  return (
    <div className="page-container" id="dashboard-page">
      {/* 1. WELCOME HERO SECTION */}
      <div className="hero-card" id="dashboard-hero">
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

          <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
            <button 
              id="btn-quick-search"
              className="btn-primary" 
              onClick={() => setActiveTab('search')}
              style={{ padding: '12px 24px', fontSize: '0.94rem' }}
            >
              <FolderSearch size={18} /> Search a Saree Design
            </button>
            <button 
              id="btn-quick-sources"
              className="btn-secondary" 
              onClick={() => setActiveTab('data-sources')}
              style={{ padding: '12px 22px', fontSize: '0.94rem' }}
            >
              <BookOpen size={18} style={{ color: 'var(--primary-purple)' }} /> 
              {oneNoteStatus?.is_connected ? 'Manage OneNote Sync' : 'Connect Microsoft OneNote'}
            </button>
          </div>
        </div>
      </div>

      {/* 2. QUICK STATISTICS KPI GRID */}
      <div className="kpi-grid">
        <div className="kpi-card" id="kpi-total-designs">
          <div className="kpi-icon-box" style={{ background: 'var(--purple-light)', color: 'var(--primary-purple)' }}>
            <Layers size={26} />
          </div>
          <div>
            <div className="kpi-val">{oneNoteStatus?.indexed_designs_count ?? stats.totalDesigns ?? 0}</div>
            <div className="kpi-label">Cloud Designs Indexed</div>
          </div>
        </div>

        <div className="kpi-card" id="kpi-notebooks">
          <div className="kpi-icon-box" style={{ background: 'var(--gold-light)', color: 'var(--gold-primary)' }}>
            <BookOpen size={26} />
          </div>
          <div>
            <div className="kpi-val">{oneNoteStatus?.notebooks_count ?? stats.notebooks ?? 0}</div>
            <div className="kpi-label">Connected Notebooks</div>
          </div>
        </div>

        <div className="kpi-card" id="kpi-searches">
          <div className="kpi-icon-box" style={{ background: 'var(--blue-light)', color: 'var(--accent-blue)' }}>
            <History size={26} />
          </div>
          <div>
            <div className="kpi-val">{stats.totalSearches}</div>
            <div className="kpi-label">Recent Searches</div>
          </div>
        </div>

        <div className="kpi-card" id="kpi-engine">
          <div className="kpi-icon-box" style={{ background: 'var(--emerald-light)', color: 'var(--accent-emerald)' }}>
            <ShieldCheck size={26} />
          </div>
          <div>
            <div className="kpi-val" style={{ fontSize: '1.25rem', fontWeight: 800 }}>Read-Only</div>
            <div className="kpi-label">Microsoft OneNote Safe</div>
          </div>
        </div>
      </div>

      {/* 3. VISUAL WORKFLOW EXPLAINER */}
      <div className="workflow-section">
        <div className="section-header">
          <h3>How the Visual Retrieval Engine Works</h3>
          <p>End-to-end workflow from Microsoft OneNote ingestion to exact-object deep linking.</p>
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

      {/* 4. ONENOTE CONNECTION CARD & RECENT SEARCHES DUAL COLUMN */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', 
        gap: '24px', 
        marginBottom: '36px' 
      }}>
        {/* OneNote Connection Card */}
        <div className="saas-card" id="onenote-connection-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{ 
                width: '38px', 
                height: '38px', 
                borderRadius: 'var(--radius-md)', 
                background: 'var(--purple-light)', 
                color: 'var(--primary-purple)',
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center' 
              }}>
                <BookOpen size={20} />
              </div>
              <div>
                <h4 style={{ fontSize: '1.05rem', color: 'var(--text-main)' }}>Microsoft OneNote Status</h4>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Cloud Synchronization Health</p>
              </div>
            </div>

            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px 10px',
              borderRadius: 'var(--radius-full)',
              fontSize: '0.74rem',
              fontWeight: 700,
              background: oneNoteStatus?.is_connected ? 'var(--emerald-light)' : 'var(--gold-light)',
              color: oneNoteStatus?.is_connected ? 'var(--accent-emerald)' : 'var(--gold-text)',
              border: `1px solid ${oneNoteStatus?.is_connected ? 'var(--emerald-border)' : 'var(--gold-border)'}`
            }}>
              <span className={`status-dot ${oneNoteStatus?.is_connected ? '' : 'inactive'}`} />
              {oneNoteStatus?.is_connected ? 'Connected' : 'Not Connected'}
            </span>
          </div>

          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '18px' }}>
            {oneNoteStatus?.is_connected ? (
              <>Authenticated as <strong>{oneNoteStatus.display_name || oneNoteStatus.user_email}</strong>. Saree design catalog is synchronized with your cloud notebooks.</>
            ) : (
              <>Connect your Microsoft account to automatically index saree photos, motifs, and notes directly from your OneNote notebooks.</>
            )}
          </p>

          <div style={{ 
            background: 'var(--bg-subtle)', 
            borderRadius: 'var(--radius-md)', 
            padding: '12px 14px', 
            marginBottom: '18px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.80rem'
          }}>
            <span style={{ color: 'var(--text-muted)' }}>Indexed Saree Images:</span>
            <strong style={{ color: 'var(--primary-purple)', fontSize: '0.90rem' }}>
              {oneNoteStatus?.indexed_designs_count || stats.totalDesigns} designs
            </strong>
          </div>

          <button 
            className="btn-primary"
            onClick={() => setActiveTab('data-sources')}
            style={{ width: '100%', justifyContent: 'center' }}
          >
            {oneNoteStatus?.is_connected ? 'Open OneNote Sync Manager' : 'Connect Microsoft OneNote'}
          </button>
        </div>

        {/* Recent Searches Card */}
        <div className="saas-card" id="recent-searches-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div>
              <h4 style={{ fontSize: '1.05rem', color: 'var(--text-main)' }}>Recent Design Searches</h4>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Latest visual query audit logs</p>
            </div>
            <button 
              className="btn-secondary" 
              onClick={() => setActiveTab('history')}
              style={{ padding: '6px 12px', fontSize: '0.76rem', minHeight: 'auto' }}
            >
              View All <ArrowRight size={12} />
            </button>
          </div>

          {recentSearches.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '36px 16px', color: 'var(--text-muted)', fontSize: '0.86rem' }}>
              No visual searches recorded yet. Upload a saree photo to start searching.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {recentSearches.map((item) => (
                <div 
                  key={item.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                    background: '#ffffff',
                    gap: '12px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: 0 }}>
                    <img 
                      src={item.query_image_url} 
                      alt="Query" 
                      style={{ width: '42px', height: '42px', borderRadius: '6px', objectFit: 'cover', border: '1px solid #e2e8f0', flexShrink: 0 }} 
                    />
                    <div style={{ minWidth: 0 }}>
                      <div style={{ fontSize: '0.84rem', fontWeight: 700, color: 'var(--text-main)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {item.top_match_title || 'Saree Query'}
                      </div>
                      <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>
                        {item.similarity_percentage}% match &bull; {item.notebook_name || 'OneNote'}
                      </div>
                    </div>
                  </div>

                  <a 
                    href={getExactPageWebUrl(item) || 'https://www.onenote.com/notebooks'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-onenote"
                    style={{ padding: '5px 9px', fontSize: '0.72rem', flexShrink: 0 }}
                    title="Open Exact Match in OneNote"
                  >
                    <ExternalLink size={12} /> Open Exact Match in OneNote
                  </a>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 5. HISTORICAL INDEXED DESIGNS PREVIEW */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h3 style={{ fontSize: '1.25rem', color: 'var(--text-main)' }}>Indexed OneNote Saree Catalog</h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Historical saree designs indexed with notebook, section, page, and exact image coordinates.
            </p>
          </div>
          <button 
            id="btn-view-all-designs"
            className="btn-secondary" 
            onClick={() => setActiveTab('data-sources')}
          >
            View Full Catalog ({stats.totalDesigns}) <ArrowRight size={14} />
          </button>
        </div>

        {recentDesigns.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '50px', background: '#ffffff', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border-card)' }}>
            <p style={{ color: 'var(--text-muted)', marginBottom: '8px', fontWeight: 600 }}>No OneNote designs indexed yet.</p>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-dim)', marginBottom: '16px' }}>
              Connect your Microsoft OneNote account in OneNote Integration to start visual retrieval.
            </p>
            <button 
              className="btn-primary" 
              onClick={() => setActiveTab('data-sources')}
            >
              Go to OneNote Integration
            </button>
          </div>
        ) : (
          <div className="matches-grid">
            {recentDesigns.map((design) => (
              <div key={design.id} className="match-card" id={`catalog-card-${design.id}`}>
                <div className="match-img-box">
                  <img src={design.image_url} alt={design.title} />
                  <span className="match-score-badge score-mid" style={{ background: 'rgba(15, 23, 42, 0.82)' }}>
                    {design.category || 'Traditional'}
                  </span>
                </div>
                <div className="match-card-body">
                  <div className="match-title">{design.title}</div>
                  <OneNoteBreadcrumb 
                    notebook={design.notebook_name} 
                    section={design.section_name} 
                    page={design.page_title} 
                    imageOrder={design.image_order}
                    item={design}
                    copyUrl={getExactPageWebUrl(design)}
                  />
                  
                  {design.colorway && (
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                      <strong style={{ color: 'var(--text-secondary)' }}>Colorway:</strong> {design.colorway}
                    </div>
                  )}

                  <div className="tags-row">
                    {design.motifs && design.motifs.map((motif, i) => (
                      <span key={i} className="motif-tag">{motif}</span>
                    ))}
                  </div>

                  <div className="match-card-footer">
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontFamily: 'monospace' }}>
                      ID: {design.design_id}
                    </span>
                    <a 
                      href={getExactPageWebUrl(design) || 'https://www.onenote.com/notebooks'} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="btn-onenote"
                      title="Open Exact Match in OneNote"
                    >
                      <ExternalLink size={13} /> Open Exact Match in OneNote
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
