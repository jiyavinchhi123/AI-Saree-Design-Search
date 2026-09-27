import React, { useState, useRef, useEffect } from 'react';
import { 
  UploadCloud, 
  Search, 
  AlertCircle, 
  CheckCircle2, 
  Sliders, 
  ExternalLink, 
  Eye, 
  Image as ImageIcon, 
  RotateCcw, 
  Cpu, 
  Laptop,
  Globe
} from 'lucide-react';
import { api, getCleanOneNoteUrl, getCleanOneNoteClientUrl, getCleanOneNoteWebUrl } from '../services/api';
import OneNoteBreadcrumb from '../components/OneNoteBreadcrumb';
import StructuralMapModal from '../components/StructuralMapModal';

export default function SearchDesign() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [oneNoteStatus, setOneNoteStatus] = useState(null);
  
  const [threshold, setThreshold] = useState(0.80);
  const [isSearching, setIsSearching] = useState(false);
  const [searchResult, setSearchResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  useEffect(() => {
    api.getOneNoteStatus().then(status => {
      setOneNoteStatus(status);
    }).catch(() => {});
  }, []);

  // Modal inspection state
  const [modalData, setModalData] = useState({
    isOpen: false,
    originalUrl: '',
    structuralUrl: '',
    title: ''
  });

  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setSearchResult(null);
      setErrorMsg(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setSearchResult(null);
      setErrorMsg(null);
    }
  };

  const executeSearch = async () => {
    if (!selectedFile) {
      setErrorMsg('Please select or upload a saree design image first.');
      return;
    }

    setIsSearching(true);
    setErrorMsg(null);

    try {
      const res = await api.searchByImage(selectedFile, threshold, 6);
      setSearchResult(res);
    } catch (err) {
      setErrorMsg(err.message || 'Search execution failed');
    } finally {
      setIsSearching(false);
    }
  };

  const resetSearch = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setSearchResult(null);
    setErrorMsg(null);
  };

  return (
    <div className="page-container" id="search-design-page">
      {/* Top Banner */}
      <div style={{ marginBottom: '28px' }}>
        <h2 style={{ fontSize: '1.65rem', color: '#fff', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Search size={26} style={{ color: 'var(--gold-primary)' }} /> Visual Saree Design Search
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginTop: '4px' }}>
          Upload any saree photograph, loom artwork, or fabric sample. Our model extracts motif vectors, border geometry, and layout patterns while disregarding color variations.
        </p>
      </div>

      {oneNoteStatus && !oneNoteStatus.is_connected && (
        <div style={{
          background: 'rgba(212, 175, 55, 0.08)',
          border: '1px solid rgba(212, 175, 55, 0.3)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 18px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <AlertCircle size={18} style={{ color: 'var(--gold-primary)', flexShrink: 0 }} />
          <span style={{ fontSize: '0.86rem', color: '#fff' }}>
            <strong>Microsoft OneNote Not Connected:</strong> Connect your OneNote in Data Sources to index and search saree designs from your account.
          </span>
        </div>
      )}

      {/* Upload Zone & Settings Card */}
      <div className="upload-card">
        <div 
          className="dropzone" 
          id="search-dropzone"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            accept="image/*" 
            style={{ display: 'none' }} 
            id="file-input-saree"
          />

          {previewUrl ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '140px', height: '140px', borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '2px solid var(--gold-primary)', boxShadow: 'var(--shadow-gold)' }}>
                <img src={previewUrl} alt="Preview" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              </div>
              <div style={{ color: 'var(--gold-light)', fontWeight: 600, fontSize: '0.95rem' }}>
                {selectedFile?.name}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>
                Click or drag another image to replace
              </div>
            </div>
          ) : (
            <>
              <div className="dropzone-icon">
                <UploadCloud size={32} />
              </div>
              <div className="dropzone-title">Drag & drop your saree image here</div>
              <div className="dropzone-desc">
                Supports JPG, PNG, WEBP. Focuses on motifs, borders, and jaal patterns — invariant to color variations.
              </div>
              <button 
                type="button" 
                className="btn-secondary" 
                onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}
                id="btn-browse-file"
              >
                <ImageIcon size={15} /> Browse from Computer
              </button>
            </>
          )}
        </div>

        {/* Action Controls & Threshold Slider */}
        <div style={{ 
          marginTop: '24px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between', 
          flexWrap: 'wrap',
          gap: '16px',
          paddingTop: '20px',
          borderTop: '1px solid var(--border-subtle)'
        }}>
          {/* Threshold slider */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <Sliders size={18} style={{ color: 'var(--gold-primary)' }} />
            <div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Match Confidence Threshold: <strong style={{ color: '#fff' }}>{Math.round(threshold * 100)}%</strong>
              </div>
              <input 
                id="threshold-slider"
                type="range" 
                min="0.50" 
                max="0.95" 
                step="0.01" 
                value={threshold} 
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                style={{ width: '180px', accentColor: 'var(--gold-primary)', cursor: 'pointer' }}
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '12px' }}>
            {previewUrl && (
              <button className="btn-secondary" onClick={resetSearch} id="btn-reset-search">
                <RotateCcw size={15} /> Reset
              </button>
            )}
            <button 
              id="btn-find-matching-designs"
              className="btn-primary" 
              onClick={executeSearch}
              disabled={isSearching || !selectedFile}
              style={{ opacity: isSearching || !selectedFile ? 0.6 : 1 }}
            >
              {isSearching ? (
                <>Searching Vector Index...</>
              ) : (
                <><Search size={16} /> Find Matching Designs</>
              )}
            </button>
          </div>
        </div>

        {errorMsg && (
          <div style={{ marginTop: '16px', padding: '12px 16px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid var(--accent-crimson)', borderRadius: 'var(--radius-md)', color: '#fca5a5', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={16} /> {errorMsg}
          </div>
        )}
      </div>

      {/* SEARCH RESULTS SECTION */}
      {searchResult && (
        <div id="search-results-section">
          {/* Status Banner */}
          <div 
            id="search-status-banner"
            className={`results-header-banner ${searchResult.is_strong_match ? 'banner-match-strong' : 'banner-no-match'}`}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              {searchResult.is_strong_match ? (
                <CheckCircle2 size={24} style={{ color: 'var(--accent-emerald)', flexShrink: 0 }} />
              ) : (
                <AlertCircle size={24} style={{ color: 'var(--accent-crimson)', flexShrink: 0 }} />
              )}
              <div>
                <div style={{ fontWeight: 700, fontSize: '1.1rem' }}>
                  {searchResult.is_strong_match ? 'Design Match Confirmed in OneNote Archive!' : 'No strong design match found.'}
                </div>
                <div style={{ fontSize: '0.82rem', opacity: 0.9, marginTop: '2px' }}>
                  {searchResult.status_message} (Top result: {searchResult.top_percentage}%, Required threshold: {Math.round(searchResult.threshold * 100)}%)
                </div>
              </div>
            </div>
            <div style={{ textAlign: 'right', display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Indexed Catalog: {searchResult.total_indexed} designs
              </span>
            </div>
          </div>

          {/* Side by Side Comparison Layout */}
          <div className="comparison-container">
            {/* Left: Uploaded Query Image */}
            <div className="query-card" id="query-preview-card">
              <div style={{ fontSize: '0.9rem', fontWeight: 700, color: '#fff', marginBottom: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span>Uploaded Saree Image</span>
                <span style={{ fontSize: '0.72rem', color: 'var(--gold-primary)', background: 'rgba(212, 175, 55, 0.1)', padding: '2px 8px', borderRadius: '4px' }}>
                  Query Input
                </span>
              </div>

              <div className="query-img-wrapper">
                <img src={searchResult.query_image_url} alt="Uploaded Saree Query" />
              </div>

              <button 
                id="btn-inspect-query-tensor"
                className="btn-secondary" 
                style={{ width: '100%', justifyContent: 'center', fontSize: '0.8rem' }}
                onClick={() => setModalData({
                  isOpen: true,
                  originalUrl: searchResult.query_image_url,
                  structuralUrl: searchResult.query_structural_preview_url,
                  title: 'Query Saree Structural & Motif Edge Tensor'
                })}
              >
                <Cpu size={14} style={{ color: 'var(--gold-primary)' }} /> Inspect AI Vision Tensor
              </button>

              <div style={{ marginTop: '16px', background: 'rgba(255, 255, 255, 0.02)', padding: '12px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '4px' }}>ENGINE VERIFICATION:</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.4' }}>
                  Extracted 1536-dimensional DINOv2 color-invariant motif embedding (4-Zone Spatial Pooling). Matching against historical designs via FAISS.
                </div>
              </div>
            </div>

            {/* Right: Matches Grid */}
            <div>
              <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff', marginBottom: '16px' }}>
                Historical OneNote Matches ({searchResult.matches.length})
              </div>

              {searchResult.matches.length === 0 ? (
                <div style={{ padding: '40px', background: 'var(--surface-card)', borderRadius: 'var(--radius-lg)', textAlign: 'center', color: 'var(--text-muted)' }}>
                  No indexed designs found. Please connect OneNote or upload an archive to populate the catalog.
                </div>
              ) : (
                <div className="matches-grid">
                  {searchResult.matches.map((match, idx) => {
                    const isTop = idx === 0 && searchResult.is_strong_match;
                    const scoreClass = match.similarity_percentage >= 80 
                      ? 'score-high' 
                      : match.similarity_percentage >= 60 
                        ? 'score-mid' 
                        : 'score-low';

                    return (
                      <div 
                        key={match.id} 
                        className={`match-card ${isTop ? 'is-top-match' : ''}`}
                        id={`match-card-${match.id}`}
                      >
                        <div className="match-img-box">
                          <img src={match.image_url} alt={match.title} />
                          <div className={`match-score-badge ${scoreClass}`}>
                            {match.similarity_percentage}% Match
                          </div>
                        </div>

                        <div className="match-card-body">
                          <div className="match-title">{match.title}</div>
                          
                          {/* OneNote Hierarchy: Notebook -> Section -> Page */}
                          <OneNoteBreadcrumb 
                            notebook={match.notebook_name} 
                            section={match.section_name} 
                            page={match.page_title} 
                          />

                          {match.colorway && (
                            <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
                              <strong style={{ color: 'var(--text-dim)' }}>Archived Color:</strong> {match.colorway}
                            </div>
                          )}

                          {/* Motifs Tags */}
                          <div className="tags-row">
                            {match.motifs && match.motifs.map((motif, i) => (
                              <span key={i} className="motif-tag">{motif}</span>
                            ))}
                          </div>

                          {/* Card Footer Actions */}
                          <div className="match-card-footer">
                            <button 
                              className="btn-secondary" 
                              style={{ padding: '6px 10px', fontSize: '0.75rem' }}
                              onClick={() => setModalData({
                                isOpen: true,
                                originalUrl: match.image_url,
                                structuralUrl: match.structural_preview_url || match.image_url,
                                title: `${match.title} - Structural Map`
                              })}
                              id={`btn-inspect-match-${match.id}`}
                            >
                              <Eye size={12} /> AI Map
                            </button>

                            <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                              <button 
                                className="btn-onenote"
                                id={`btn-open-onenote-${match.id}`}
                                title={`Open exact location in Desktop OneNote: ${match.notebook_name} > ${match.section_name} > ${match.page_title || match.title}`}
                                onClick={async (e) => {
                                  e.preventDefault();
                                  try {
                                    const res = await api.openInOneNote(match.id, 'desktop');
                                    if (res && res.client_url) {
                                      window.location.href = res.client_url;
                                    }
                                  } catch (err) {
                                    console.error('OneNote desktop launch error:', err);
                                  }
                                }}
                                style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}
                              >
                                <ExternalLink size={13} /> Open in OneNote
                              </button>

                              <a
                                href={getCleanOneNoteWebUrl(match)}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="btn-secondary"
                                style={{ padding: '6px 9px', fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', textDecoration: 'none' }}
                                title="Open in OneNote Online (Browser)"
                                id={`btn-open-web-${match.id}`}
                              >
                                <Globe size={13} />
                              </a>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Structural Map Inspection Modal */}
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
