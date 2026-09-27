import React, { useState, useEffect } from 'react';
import { History, Trash2, ExternalLink, CheckCircle2, AlertCircle, Clock, Eye } from 'lucide-react';
import { api, getCleanOneNoteUrl } from '../services/api';
import OneNoteBreadcrumb from '../components/OneNoteBreadcrumb';
import StructuralMapModal from '../components/StructuralMapModal';

export default function SearchHistory() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalData, setModalData] = useState({
    isOpen: false,
    originalUrl: '',
    structuralUrl: '',
    title: ''
  });

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const data = await api.getSearchHistory();
      setHistory(data.history || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = async () => {
    if (window.confirm('Are you sure you want to clear search history?')) {
      try {
        await api.clearSearchHistory();
        setHistory([]);
      } catch (e) {
        console.error(e);
      }
    }
  };

  const formatTime = (isoStr) => {
    if (!isoStr) return '';
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', month: 'short', day: 'numeric' });
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="page-container" id="history-page">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h2 style={{ fontSize: '1.65rem', color: '#fff', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <History size={26} style={{ color: 'var(--gold-primary)' }} /> Visual Search History &amp; Audits
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginTop: '4px' }}>
            Audit log of all uploaded saree design queries, similarity scores, and mapped OneNote records.
          </p>
        </div>

        {history.length > 0 && (
          <button 
            id="btn-clear-history"
            className="btn-secondary" 
            onClick={handleClearHistory}
            style={{ color: '#fca5a5' }}
          >
            <Trash2 size={15} /> Clear History
          </button>
        )}
      </div>

      {history.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '60px', background: 'var(--surface-card)', borderRadius: 'var(--radius-lg)' }}>
          <Clock size={40} style={{ color: 'var(--text-dim)', marginBottom: '12px' }} />
          <p style={{ color: 'var(--text-muted)' }}>No search queries recorded yet.</p>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginTop: '4px' }}>
            Upload a saree design in the Search Design tab to begin auditing matches.
          </p>
        </div>
      ) : (
        <div className="data-table-container">
          <table className="data-table" id="search-history-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Query Image</th>
                <th>Top Matched OneNote Design</th>
                <th>Confidence</th>
                <th>Status</th>
                <th>OneNote Link</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item) => (
                <tr key={item.id} id={`history-row-${item.id}`}>
                  <td>
                    <span style={{ fontSize: '0.82rem', color: 'var(--text-dim)' }}>
                      {formatTime(item.timestamp)}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <img src={item.query_image_url} alt="Query" className="table-thumb" />
                      {item.query_structural_preview_url && (
                        <button
                          className="btn-secondary"
                          style={{ padding: '4px 8px', fontSize: '0.7rem' }}
                          onClick={() => setModalData({
                            isOpen: true,
                            originalUrl: item.query_image_url,
                            structuralUrl: item.query_structural_preview_url,
                            title: 'Historical Query AI Tensor Map'
                          })}
                        >
                          <Eye size={11} /> AI Map
                        </button>
                      )}
                    </div>
                  </td>
                  <td>
                    {item.top_match_title ? (
                      <div>
                        <div style={{ fontWeight: 600, color: '#fff', marginBottom: '4px' }}>
                          {item.top_match_title}
                        </div>
                        <OneNoteBreadcrumb 
                          notebook={item.notebook_name}
                          section={item.section_name}
                          page={item.page_title}
                        />
                      </div>
                    ) : (
                      <span style={{ color: 'var(--text-dim)', fontStyle: 'italic' }}>None</span>
                    )}
                  </td>
                  <td>
                    <span style={{ 
                      fontWeight: 700, 
                      color: item.similarity_percentage >= 80 ? 'var(--accent-emerald)' : item.similarity_percentage >= 60 ? 'var(--accent-amber)' : 'var(--text-dim)' 
                    }}>
                      {item.similarity_percentage}%
                    </span>
                  </td>
                  <td>
                    {item.is_strong_match ? (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#a7f3d0', fontSize: '0.8rem', background: 'rgba(16, 185, 129, 0.15)', padding: '3px 8px', borderRadius: '4px' }}>
                        <CheckCircle2 size={13} /> Matched
                      </span>
                    ) : (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#fca5a5', fontSize: '0.8rem', background: 'rgba(239, 68, 68, 0.15)', padding: '3px 8px', borderRadius: '4px' }}>
                        <AlertCircle size={13} /> No Strong Match
                      </span>
                    )}
                  </td>
                  <td>
                    {item.onenote_web_url ? (
                      <a 
                        href={getCleanOneNoteUrl(item)} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="btn-onenote"
                        style={{ padding: '6px 10px', fontSize: '0.75rem' }}
                        title="Open in Microsoft OneNote"
                      >
                        <ExternalLink size={12} /> View Page
                      </a>
                    ) : (
                      <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Structural Preview Modal */}
      <StructuralMapModal 
        isOpen={modalData.isOpen}
        onClose={() => setModalData({ ...modalData, isOpen: false })}
        originalUrl={modalData.originalUrl}
        structuralUrl={modalData.structuralUrl}
        title={modalData.title}
      />
    </div>
  );
}
