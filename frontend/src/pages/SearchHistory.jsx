import React, { useState, useEffect } from 'react';
import { 
  History, 
  Trash2, 
  ExternalLink, 
  CheckCircle2, 
  AlertCircle, 
  Clock, 
  Eye, 
  Search, 
  Filter, 
  X,
  Target,
  BookOpen
} from 'lucide-react';
import { api, getCleanOneNoteUrl } from '../services/api';
import OneNoteBreadcrumb from '../components/OneNoteBreadcrumb';
import StructuralMapModal from '../components/StructuralMapModal';

export default function SearchHistory() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Detail Modal / Inspection State
  const [selectedItem, setSelectedItem] = useState(null);

  // Structural Tensor Inspection Modal
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
      const data = await api.getSearchHistory(100);
      setHistory(data.history || []);
    } catch (e) {
      console.error('Error loading history:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = async () => {
    if (window.confirm('Are you sure you want to clear search history? This action cannot be undone.')) {
      try {
        await api.clearSearchHistory();
        setHistory([]);
      } catch (e) {
        console.error('Error clearing history:', e);
      }
    }
  };

  const formatTime = (isoStr) => {
    if (!isoStr) return '';
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return isoStr;
    }
  };

  const filteredHistory = history.filter(item => {
    const matchesSearch = !searchQuery || 
      (item.top_match_title && item.top_match_title.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (item.notebook_name && item.notebook_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (item.section_name && item.section_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (item.id && item.id.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesStatus = statusFilter === 'all' || 
      (statusFilter === 'matched' && item.is_strong_match) ||
      (statusFilter === 'unmatched' && !item.is_strong_match);

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="page-container" id="history-page">
      {/* Page Header */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between', 
        marginBottom: '26px', 
        flexWrap: 'wrap', 
        gap: '14px' 
      }}>
        <div>
          <h2 style={{ fontSize: '1.45rem', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <History size={24} style={{ color: 'var(--primary-purple)' }} /> Visual Search History &amp; Audits
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.86rem', marginTop: '2px' }}>
            Audit log of all uploaded saree design queries, similarity scores, and mapped OneNote records.
          </p>
        </div>

        {history.length > 0 && (
          <button 
            id="btn-clear-history"
            className="btn-secondary" 
            onClick={handleClearHistory}
            style={{ color: 'var(--accent-crimson)', borderColor: '#fca5a5' }}
          >
            <Trash2 size={15} /> Clear History
          </button>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="saas-card" style={{ padding: '16px 20px', marginBottom: '24px' }}>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between', 
          flexWrap: 'wrap', 
          gap: '14px' 
        }}>
          {/* Search Box */}
          <div style={{ position: 'relative', flex: 1, minWidth: '220px', maxWidth: '420px' }}>
            <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
            <input 
              type="text"
              placeholder="Search by design title, notebook, section..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '9px 12px 9px 36px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                background: 'var(--bg-subtle)',
                fontSize: '0.86rem'
              }}
            />
          </div>

          {/* Filter Status Pills */}
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.80rem', color: 'var(--text-muted)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Filter size={14} /> Status:
            </span>
            {[
              { id: 'all', label: `All (${history.length})` },
              { id: 'matched', label: `Matched (${history.filter(h => h.is_strong_match).length})` },
              { id: 'unmatched', label: `No Match (${history.filter(h => !h.is_strong_match).length})` },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                style={{
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-full)',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  background: statusFilter === tab.id ? 'var(--primary-purple)' : 'var(--bg-subtle)',
                  color: statusFilter === tab.id ? '#ffffff' : 'var(--text-secondary)',
                  border: `1px solid ${statusFilter === tab.id ? 'var(--primary-purple)' : 'var(--border-subtle)'}`
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* History Records Container */}
      {loading ? (
        <div className="saas-card" style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
          <Clock size={32} className="spinner" style={{ margin: '0 auto 12px auto', color: 'var(--primary-purple)' }} />
          <div>Loading search audit logs...</div>
        </div>
      ) : filteredHistory.length === 0 ? (
        <div className="saas-card" style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
          <Clock size={40} style={{ color: 'var(--text-dim)', marginBottom: '12px' }} />
          <p style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
            {history.length === 0 ? 'No search queries recorded yet.' : 'No audit records match the current filter.'}
          </p>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            Upload a saree design in Visual Saree Search to begin logging motif matches.
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
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredHistory.map((item) => (
                <tr 
                  key={item.id}
                  onClick={() => setSelectedItem(item)}
                  style={{ cursor: 'pointer' }}
                  title="Click to view detailed search audit"
                >
                  <td data-label="Timestamp" style={{ fontSize: '0.80rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                    {formatTime(item.timestamp)}
                  </td>

                  <td data-label="Query Image">
                    <img 
                      src={item.query_image_url} 
                      alt="Query Saree" 
                      style={{ 
                        width: '48px', 
                        height: '48px', 
                        borderRadius: 'var(--radius-sm)', 
                        objectFit: 'cover', 
                        border: '1px solid var(--border-subtle)',
                        boxShadow: 'var(--shadow-xs)'
                      }} 
                    />
                  </td>

                  <td data-label="Top Matched OneNote Design">
                    {item.top_match_title ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        {item.top_match_image_url && (
                          <img 
                            src={item.top_match_image_url} 
                            alt={item.top_match_title} 
                            style={{ 
                              width: '48px', 
                              height: '48px', 
                              borderRadius: 'var(--radius-sm)', 
                              objectFit: 'cover', 
                              border: '1px solid var(--border-subtle)',
                              flexShrink: 0 
                            }} 
                          />
                        )}
                        <div>
                          <strong style={{ fontSize: '0.88rem', color: 'var(--text-main)' }}>
                            {item.top_match_title}
                          </strong>
                          <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                            {item.notebook_name || 'OneNote'} &gt; {item.section_name || 'Section'} &gt; {item.page_title || 'Page'}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <span style={{ color: 'var(--text-dim)', fontStyle: 'italic', fontSize: '0.82rem' }}>
                        No Match Identified
                      </span>
                    )}
                  </td>

                  <td data-label="Confidence">
                    <span style={{ 
                      fontWeight: 800, 
                      fontSize: '0.88rem',
                      color: item.similarity_percentage >= 80 ? 'var(--accent-emerald)' : item.similarity_percentage >= 60 ? 'var(--gold-primary)' : 'var(--text-muted)'
                    }}>
                      {item.similarity_percentage}%
                    </span>
                  </td>

                  <td data-label="Status">
                    {item.is_strong_match ? (
                      <span style={{ 
                        display: 'inline-flex', 
                        alignItems: 'center', 
                        gap: '5px', 
                        color: 'var(--accent-emerald)', 
                        fontSize: '0.76rem', 
                        fontWeight: 700,
                        background: 'var(--emerald-light)', 
                        border: '1px solid var(--emerald-border)',
                        padding: '3px 8px', 
                        borderRadius: 'var(--radius-sm)' 
                      }}>
                        <CheckCircle2 size={13} /> Matched
                      </span>
                    ) : (
                      <span style={{ 
                        display: 'inline-flex', 
                        alignItems: 'center', 
                        gap: '5px', 
                        color: 'var(--gold-text)', 
                        fontSize: '0.76rem', 
                        fontWeight: 700,
                        background: 'var(--gold-light)', 
                        border: '1px solid var(--gold-border)',
                        padding: '3px 8px', 
                        borderRadius: 'var(--radius-sm)' 
                      }}>
                        <AlertCircle size={13} /> No Strong Match
                      </span>
                    )}
                  </td>

                  <td data-label="Action" onClick={(e) => e.stopPropagation()}>
                    {item.top_match_id ? (
                      <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                        <a 
                          href={item.top_match_object_url || item.onenote_web_url || getCleanOneNoteUrl(item)} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="btn-onenote"
                          style={{ padding: '6px 12px', fontSize: '0.75rem' }}
                          title={`Open exact matched image in OneNote (Object: ${item.top_match_object_id || 'Page'})`}
                        >
                          <ExternalLink size={12} /> Exact Match
                        </a>
                      </div>
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

      {/* SEARCH DETAIL MODAL / DRAWER */}
      {selectedItem && (
        <div className="modal-backdrop" onClick={() => setSelectedItem(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '640px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Target size={20} style={{ color: 'var(--primary-purple)' }} />
                <h3 style={{ fontSize: '1.2rem', color: 'var(--text-main)', margin: 0 }}>Search Audit Details</h3>
              </div>
              <button 
                onClick={() => setSelectedItem(null)} 
                style={{ background: 'transparent', color: 'var(--text-muted)' }}
              >
                <X size={20} />
              </button>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
              <div>
                <div style={{ fontSize: '0.80rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '6px' }}>
                  Uploaded Saree Query
                </div>
                <div style={{ borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--border-subtle)', aspectRatio: '1' }}>
                  <img src={selectedItem.query_image_url} alt="Query Saree" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.80rem', fontWeight: 700, color: 'var(--primary-purple)', marginBottom: '6px' }}>
                  Top Matched OneNote Design
                </div>
                <div style={{ borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '2px solid var(--primary-purple)', aspectRatio: '1', background: '#f8fafc' }}>
                  {selectedItem.top_match_image_url ? (
                    <img src={selectedItem.top_match_image_url} alt={selectedItem.top_match_title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', fontSize: '0.80rem' }}>
                      No Match
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Location Breadcrumb */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: 600 }}>OneNote Verified Hierarchy:</div>
              <OneNoteBreadcrumb 
                notebook={selectedItem.notebook_name} 
                section={selectedItem.section_name} 
                page={selectedItem.page_title || selectedItem.top_match_title} 
                imageOrder={selectedItem.top_match_order}
              />
            </div>

            <div style={{ 
              background: 'var(--bg-subtle)', 
              borderRadius: 'var(--radius-md)', 
              padding: '14px', 
              fontSize: '0.82rem', 
              marginBottom: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px'
            }}>
              <div><strong>Audit ID:</strong> <code>{selectedItem.id}</code></div>
              <div><strong>Similarity Score:</strong> <strong style={{ color: 'var(--primary-purple)' }}>{selectedItem.similarity_percentage}%</strong></div>
              <div><strong>Timestamp:</strong> {formatTime(selectedItem.timestamp)}</div>
              {selectedItem.top_match_object_id && (
                <div><strong>OneNote Object ID:</strong> <code>{selectedItem.top_match_object_id}</code></div>
              )}
            </div>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', flexWrap: 'wrap' }}>
              {selectedItem.query_structural_preview_url && (
                <button 
                  className="btn-secondary"
                  onClick={() => {
                    setModalData({
                      isOpen: true,
                      originalUrl: selectedItem.query_image_url,
                      structuralUrl: selectedItem.query_structural_preview_url,
                      title: 'Query Saree Structural Map'
                    });
                  }}
                >
                  <Eye size={14} /> AI Vision Tensor
                </button>
              )}

              {selectedItem.top_match_id && (
                <a 
                  href={selectedItem.top_match_object_url || selectedItem.onenote_web_url || getCleanOneNoteUrl(selectedItem)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-primary"
                >
                  <ExternalLink size={14} /> Open Exact Match in OneNote
                </a>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Structural Tensor Inspection Modal */}
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
