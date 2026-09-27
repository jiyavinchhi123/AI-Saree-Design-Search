import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Layers, 
  BookOpen, 
  FolderSearch, 
  CheckCircle2, 
  ArrowRight,
  ExternalLink
} from 'lucide-react';
import { api, getCleanOneNoteUrl } from '../services/api';
import OneNoteBreadcrumb from '../components/OneNoteBreadcrumb';

export default function Dashboard({ setActiveTab }) {
  const [stats, setStats] = useState({
    totalDesigns: 0,
    notebooks: 0,
    categories: 0,
    status: 'Ready'
  });
  const [recentDesigns, setRecentDesigns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const data = await api.getDesigns();
      const designs = data.designs || [];
      const notebooks = data.filters?.notebooks || [];
      const categories = data.filters?.categories || [];

      setStats({
        totalDesigns: designs.length,
        notebooks: notebooks.length,
        categories: categories.length,
        status: designs.length > 0 ? 'Active & Indexed' : 'Awaiting OneNote Ingestion'
      });
      setRecentDesigns(designs.slice(0, 6));
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-container" id="dashboard-page">
      {/* Welcome Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(212, 175, 55, 0.12), rgba(134, 50, 168, 0.15))',
        border: '1px solid var(--border-active)',
        borderRadius: 'var(--radius-xl)',
        padding: '32px',
        marginBottom: '32px',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: 'var(--shadow-lg)'
      }}>
        <div style={{ maxWidth: '680px' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', background: 'rgba(212, 175, 55, 0.15)', border: '1px solid var(--gold-primary)', borderRadius: '20px', padding: '4px 12px', fontSize: '0.78rem', color: 'var(--gold-light)', fontWeight: 600, marginBottom: '14px' }}>
            <Sparkles size={14} /> Color-Invariant Computer Vision
          </div>
          <h2 style={{ fontSize: '1.9rem', color: '#fff', marginBottom: '10px' }}>
            Intelligent Saree Design Search &amp; Retrieval
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.92rem', lineHeight: '1.6', marginBottom: '22px' }}>
            Empower your saree manufacturing and design team to discover existing designs across Microsoft OneNote archives. Our deep vision model recognizes motifs, borders, and layouts regardless of fabric colorways.
          </p>
          <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
            <button 
              id="btn-quick-search"
              className="btn-primary" 
              onClick={() => setActiveTab('search')}
            >
              <FolderSearch size={16} /> Search a Saree Design
            </button>
            <button 
              id="btn-quick-sources"
              className="btn-secondary" 
              onClick={() => setActiveTab('data-sources')}
            >
              <BookOpen size={16} /> Manage OneNote Sources
            </button>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card" id="kpi-total-designs">
          <div className="kpi-icon-box" style={{ background: 'rgba(212, 175, 55, 0.12)', color: 'var(--gold-primary)' }}>
            <Layers size={26} />
          </div>
          <div>
            <div className="kpi-val">{stats.totalDesigns}</div>
            <div className="kpi-label">Indexed Saree Designs</div>
          </div>
        </div>

        <div className="kpi-card" id="kpi-notebooks">
          <div className="kpi-icon-box" style={{ background: 'rgba(134, 50, 168, 0.15)', color: '#d8b4fe' }}>
            <BookOpen size={26} />
          </div>
          <div>
            <div className="kpi-val">{stats.notebooks}</div>
            <div className="kpi-label">Connected OneNote Notebooks</div>
          </div>
        </div>

        <div className="kpi-card" id="kpi-engine">
          <div className="kpi-icon-box" style={{ background: 'rgba(16, 185, 129, 0.12)', color: 'var(--accent-emerald)' }}>
            <CheckCircle2 size={26} />
          </div>
          <div>
            <div className="kpi-val">FAISS Cosine</div>
            <div className="kpi-label">Vector Search Engine</div>
          </div>
        </div>

        <div className="kpi-card" id="kpi-invariance">
          <div className="kpi-icon-box" style={{ background: 'rgba(6, 182, 212, 0.12)', color: 'var(--accent-cyan)' }}>
            <Sparkles size={26} />
          </div>
          <div>
            <div className="kpi-val">100% Color-Free</div>
            <div className="kpi-label">Motif &amp; Border Matching</div>
          </div>
        </div>
      </div>

      {/* Recent Indexed Catalog Section */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <h3 style={{ fontSize: '1.25rem', color: '#fff' }}>Historical Designs in OneNote</h3>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-dim)', marginTop: '2px' }}>
            Archived saree designs currently indexed with Notebook, Section, and Page metadata.
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
        <div style={{ textAlign: 'center', padding: '60px', background: 'var(--surface-card)', borderRadius: 'var(--radius-lg)' }}>
          <p style={{ color: 'var(--text-muted)', marginBottom: '8px' }}>No OneNote designs indexed yet.</p>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: '16px' }}>
            Connect your Microsoft OneNote account or upload an exported notebook archive (.zip) in Data Sources to start visual retrieval.
          </p>
          <button 
            className="btn-primary" 
            onClick={() => setActiveTab('data-sources')}
          >
            Go to Data Sources &amp; OneNote
          </button>
        </div>
      ) : (
        <div className="matches-grid">
          {recentDesigns.map((design) => (
            <div key={design.id} className="match-card" id={`catalog-card-${design.id}`}>
              <div className="match-img-box">
                <img src={design.image_url} alt={design.title} />
                <span className="match-score-badge score-mid" style={{ background: 'rgba(0,0,0,0.75)' }}>
                  {design.category}
                </span>
              </div>
              <div className="match-card-body">
                <div className="match-title">{design.title}</div>
                <OneNoteBreadcrumb 
                  notebook={design.notebook_name} 
                  section={design.section_name} 
                  page={design.page_title} 
                />
                
                {design.colorway && (
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                    <strong style={{ color: 'var(--text-dim)' }}>Colorway:</strong> {design.colorway}
                  </div>
                )}

                <div className="tags-row">
                  {design.motifs && design.motifs.map((motif, i) => (
                    <span key={i} className="motif-tag">{motif}</span>
                  ))}
                </div>

                <div className="match-card-footer">
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                    ID: {design.design_id}
                  </span>
                  <a 
                    href={getCleanOneNoteUrl(design)} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="btn-onenote"
                    title="Open in Microsoft OneNote"
                  >
                    <ExternalLink size={13} /> Open in OneNote
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
