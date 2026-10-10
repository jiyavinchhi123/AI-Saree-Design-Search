import React, { useState, useRef, useMemo } from 'react';
import {
  UploadCloud,
  Search,
  RotateCcw,
  ExternalLink,
  Eye,
  Sliders,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Target,
  Globe,
  Cpu,
  Image as ImageIcon,
  X,
  Layers,
  ShieldCheck
} from 'lucide-react';
import { api, getExactPageWebUrl, getCleanOneNoteUrl, getCleanOneNoteClientUrl, getCleanOneNoteWebUrl } from '../services/api';
import OneNoteBreadcrumb from '../components/OneNoteBreadcrumb';
import StructuralMapModal from '../components/StructuralMapModal';

export default function SearchDesign() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [threshold, setThreshold] = useState(0.82);
  const [isSearching, setIsSearching] = useState(false);
  const [searchResult, setSearchResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [isDragging, setIsDragging] = useState(false);

  // Modal State for AI Tensor / Structural Edge map
  const [modalData, setModalData] = useState({
    isOpen: false,
    originalUrl: '',
    structuralUrl: '',
    title: ''
  });

  const fileInputRef = useRef(null);

  const handleFileSelect = (file) => {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setErrorMsg('Please select a valid image file (JPEG, PNG, WebP).');
      return;
    }
    setErrorMsg(null);
    setSelectedFile(file);
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const resetSearch = () => {
    setSelectedFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setSearchResult(null);
    setErrorMsg(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Fast client-side image downscaler to ensure uploads are lightweight (<250KB)
  // and eliminate Vercel proxy payload limits and Render cloud container memory spikes
  const optimizeImageForUpload = (file, maxDimension = 800, quality = 0.85) => {
    return new Promise((resolve) => {
      if (!file || !file.type.startsWith('image/') || file.size < 200 * 1024) {
        resolve(file);
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          let width = img.width;
          let height = img.height;

          if (width > maxDimension || height > maxDimension) {
            if (width > height) {
              height = Math.round((height * maxDimension) / width);
              width = maxDimension;
            } else {
              width = Math.round((width * maxDimension) / height);
              height = maxDimension;
            }
          }

          const canvas = document.createElement('canvas');
          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, width, height);

          canvas.toBlob(
            (blob) => {
              if (blob && blob.size < file.size) {
                const optimizedFile = new File([blob], file.name.replace(/\.[^/.]+$/, "") + ".jpg", {
                  type: 'image/jpeg',
                  lastModified: Date.now()
                });
                resolve(optimizedFile);
              } else {
                resolve(file);
              }
            },
            'image/jpeg',
            quality
          );
        };
        img.onerror = () => resolve(file);
        img.src = e.target.result;
      };
      reader.onerror = () => resolve(file);
      reader.readAsDataURL(file);
    });
  };

  const executeSearch = async () => {
    if (!selectedFile) {
      setErrorMsg('Please upload a saree photo to begin searching.');
      return;
    }
    setIsSearching(true);
    setErrorMsg(null);
    try {
      // Optimize image on client side (max 800px, under 250KB) to ensure fast upload
      // and eliminate any cloud memory spikes on Render
      const uploadFile = await optimizeImageForUpload(selectedFile);
      const res = await api.searchByImage(uploadFile, 0.0, 50);
      setSearchResult(res);
    } catch (err) {
      console.error('Search error:', err);
      setErrorMsg(err.message || 'Error occurred during vector retrieval. Please verify backend connection.');
    } finally {
      setIsSearching(false);
    }
  };

  // Convert threshold (e.g. 0.82) to integer percentage (82)
  const thresholdPct = Math.round(threshold <= 1 ? threshold * 100 : threshold);

  // Apply minimum similarity filter immediately to existing search results without re-searching
  // Results below the threshold are hidden; results >= threshold (including exact equality) are shown
  const filteredMatches = useMemo(() => {
    if (!searchResult?.matches) return [];
    return searchResult.matches.filter((m) => {
      const scorePct = typeof m.similarity_percentage === 'number'
        ? m.similarity_percentage
        : (typeof m.similarity_score === 'number' ? m.similarity_score * 100 : 0);
      return (scorePct + 0.0001) >= thresholdPct;
    });
  }, [searchResult, thresholdPct]);

  // Split matches into top match and other similar designs
  const isMatchFound = filteredMatches.length > 0;
  const topMatch = isMatchFound ? filteredMatches[0] : null;
  const otherMatches = filteredMatches.length > 1 ? filteredMatches.slice(1) : [];

  const handleOpenExactMatch = (item) => {
    if (!item) return;
    const targetUrl = item.page_web_url || item.oneNoteWebUrl || getExactPageWebUrl(item);
    console.log('[OneNote Navigation] Open Exact Match in OneNote:', {
      page_id: item.page_id,
      page_title: item.page_title || item.title,
      stored_page_web_url: item.page_web_url,
      window_open_url: targetUrl
    });

    if (targetUrl && targetUrl.startsWith('https://') && !targetUrl.toLowerCase().startsWith('onenote:')) {
      window.open(targetUrl, '_blank', 'noopener,noreferrer');
      return;
    }

    console.error('[OneNote Navigation] ERROR: No valid page-specific OneNote HTTPS URL found on record:', item);
    alert('Specific OneNote page web URL not found for this design.');
  };

  return (
    <div className="page-container" id="search-design-page">
      {/* 1. UPLOAD & QUERY SPECIFICATION CARD */}
      <div className="saas-card" style={{ marginBottom: '32px' }}>
        <div style={{ marginBottom: '22px' }}>
          <h2 style={{ fontSize: '1.55rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Search size={24} style={{ color: 'var(--primary-purple)' }} />
            Visual Saree Design Search
          </h2>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
            Upload a saree photo, pallu, border, fabric sample, or design sketch. Our AI identifies the key design patterns and finds matching saree designs&mdash;even when the colors are different.
          </p>
        </div>

        {/* Drag and Drop Zone */}
        <div
          className={`upload-dropzone ${isDragging ? 'drag-active' : ''}`}
          id="dropzone-area"
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => !previewUrl && fileInputRef.current && fileInputRef.current.click()}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => e.target.files && handleFileSelect(e.target.files[0])}
            accept="image/*"
            style={{ display: 'none' }}
            id="query-file-input"
          />

          {!previewUrl ? (
            <div>
              <div className="upload-icon-circle">
                <UploadCloud size={34} style={{ color: 'var(--primary-purple)' }} />
              </div>
              <div className="upload-main-text">
                Drag &amp; drop your saree image here
              </div>
              <div className="upload-sub-text">
                Supports JPG, PNG, WEBP fabric swatches up to 25MB. Touch to capture from camera on mobile.
              </div>
              <button
                type="button"
                className="btn-secondary"
                id="btn-browse-computer"
                onClick={(e) => {
                  e.stopPropagation();
                  fileInputRef.current?.click();
                }}
                style={{
                  border: '1.5px solid var(--purple-border)',
                  color: 'var(--primary-purple)',
                  background: '#ffffff',
                  fontWeight: 700,
                  fontSize: '0.86rem',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '9px 20px',
                  borderRadius: 'var(--radius-md)',
                  boxShadow: 'var(--shadow-xs)'
                }}
              >
                <ImageIcon size={16} /> Browse from Computer
              </button>
            </div>
          ) : (
            <div className="query-preview-container" onClick={(e) => e.stopPropagation()}>
              <img
                src={previewUrl}
                alt="Selected Saree Preview"
                className="query-preview-thumb"
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '0.74rem', color: 'var(--primary-purple)', fontWeight: 700, textTransform: 'uppercase' }}>
                  Query Image Selected
                </div>
                <div style={{ fontSize: '0.94rem', fontWeight: 700, color: 'var(--text-main)', margin: '3px 0 6px 0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {selectedFile?.name || 'Saree Query'}
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  Size: {(selectedFile?.size ? (selectedFile.size / 1024).toFixed(1) : 0)} KB &bull; Ready for AI feature extraction
                </div>
              </div>
              <button
                onClick={resetSearch}
                aria-label="Remove Image"
                style={{
                  background: 'var(--bg-subtle)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-full)',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--text-muted)',
                  cursor: 'pointer'
                }}
              >
                <X size={16} />
              </button>
            </div>
          )}
        </div>

        {/* AI Engine Clarification Notice */}
        <div className="ai-notice-banner">
          <div style={{
            width: '34px',
            height: '34px',
            borderRadius: 'var(--radius-full)',
            background: '#ffffff',
            border: '1px solid var(--purple-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--primary-purple)',
            flexShrink: 0
          }}>
            <Sparkles size={16} />
          </div>
          <p>
            <strong>Smart Color-Independent Matching:</strong> The search focuses on motifs, borders, pallu, patterns, and overall design rather than color, helping you find the same design across different color variations.
          </p>
        </div>

        {/* Action Controls & Threshold Slider */}
        <div className="search-controls-bar" style={{
          marginTop: '24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
          paddingTop: '20px',
          borderTop: '1px solid var(--border-subtle)'
        }}>
          {/* Threshold Slider */}
          <div className="threshold-slider-group" style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <Sliders size={18} style={{ color: 'var(--primary-purple)', flexShrink: 0 }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '0.84rem', color: 'var(--text-secondary)', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                <span>Match Confidence Threshold:</span>
                <span style={{
                  background: 'var(--purple-light)',
                  color: 'var(--primary-purple)',
                  border: '1px solid var(--purple-border)',
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-sm)',
                  fontWeight: 800,
                  fontSize: '0.84rem'
                }}>
                  {Math.round(threshold * 100)}%
                </span>
              </div>
              <input
                id="threshold-slider"
                type="range"
                min="0.50"
                max="1.00"
                step="0.01"
                value={threshold}
                onChange={(e) => setThreshold(parseFloat(e.target.value))}
                className="threshold-slider-input"
                style={{ width: '200px', accentColor: 'var(--primary-purple)', cursor: 'pointer', marginTop: '6px' }}
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="search-action-btns" style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
            {previewUrl && (
              <button
                className="btn-secondary"
                onClick={resetSearch}
                id="btn-reset-search"
                style={{ padding: '11px 18px', fontSize: '0.88rem', fontWeight: 600 }}
              >
                <RotateCcw size={15} /> Reset
              </button>
            )}
            <button
              id="btn-find-matching-designs"
              className="btn-primary"
              onClick={executeSearch}
              disabled={isSearching || !selectedFile}
              style={{
                opacity: isSearching || !selectedFile ? 0.65 : 1,
                padding: '11px 24px',
                fontSize: '0.92rem',
                fontWeight: 700,
                boxShadow: !selectedFile ? 'none' : '0 4px 16px rgba(109, 40, 217, 0.28)'
              }}
            >
              {isSearching ? (
                <>
                  <Sparkles size={18} className="spinner" />
                  <span>Extracting AI Motifs...</span>
                </>
              ) : (
                <>
                  <Search size={18} />
                  <span>Find Matching Designs</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Error Message */}
        {errorMsg && (
          <div style={{
            marginTop: '18px',
            padding: '12px 16px',
            background: 'var(--crimson-light)',
            border: '1px solid var(--crimson-border)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--accent-crimson)',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <AlertCircle size={16} /> {errorMsg}
          </div>
        )}
      </div>

      {/* 2. SEARCH RESULTS SECTION */}
      {searchResult && (
        <div id="search-results-section">
          {/* Status Banner */}
          <div
            id="search-status-banner"
            className={`results-header-banner ${isMatchFound ? 'banner-match-strong' : 'banner-no-match'}`}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              {isMatchFound ? (
                <CheckCircle2 size={26} style={{ color: 'var(--accent-emerald)', flexShrink: 0 }} />
              ) : (
                <AlertCircle size={26} style={{ color: 'var(--gold-primary)', flexShrink: 0 }} />
              )}
              <div>
                <div style={{ fontWeight: 800, fontSize: '1.15rem' }}>
                  {isMatchFound ? 'Design Match Confirmed in OneNote Archive!' : 'No matching designs found above the selected threshold.'}
                </div>
                <div style={{ fontSize: '0.84rem', opacity: 0.95, marginTop: '2px' }}>
                  {isMatchFound ? (
                    `Found ${filteredMatches.length} design${filteredMatches.length > 1 ? 's' : ''} matching at or above ${thresholdPct}% confidence (Top match: ${topMatch?.similarity_percentage}%).`
                  ) : (
                    searchResult.matches && searchResult.matches.length > 0
                      ? `Top candidate match in archive is ${searchResult.matches[0].similarity_percentage}%. Lower the threshold slider to view closer matches.`
                      : 'No indexed designs in catalog.'
                  )}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
              {isMatchFound && topMatch && (
                <button
                  id="btn-banner-open-exact"
                  className="btn-primary"
                  style={{
                    background: 'var(--accent-emerald)',
                    borderColor: 'var(--accent-emerald)',
                    color: '#ffffff',
                    fontSize: '0.84rem',
                    padding: '8px 16px',
                    fontWeight: 700
                  }}
                  title={`Open exact image in OneNote: ${topMatch.notebook_name} > ${topMatch.section_name} > ${topMatch.page_title || topMatch.title}`}
                  onClick={() => handleOpenExactMatch(topMatch)}
                >
                  <ExternalLink size={14} /> Open Exact Match in OneNote
                </button>
              )}
              <span style={{ fontSize: '0.80rem', color: 'var(--text-muted)' }}>
                Indexed Catalog: <strong>{searchResult.total_indexed || searchResult.matches?.length || 0}</strong> designs
              </span>
            </div>
          </div>

          {/* Dual Comparison Layout */}
          <div className="comparison-container">
            {/* Left: Query Card */}
            <div className="query-card" id="query-preview-card">
              <div style={{ fontSize: '0.90rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span>Uploaded Saree Image</span>
                <span style={{ fontSize: '0.72rem', color: 'var(--primary-purple)', background: 'var(--purple-light)', border: '1px solid var(--purple-border)', padding: '2px 8px', borderRadius: '4px', fontWeight: 700 }}>
                  Query Input
                </span>
              </div>

              <div className="query-img-wrapper">
                <img src={searchResult.query_image_url} alt="Uploaded Saree Query" />
              </div>

              <button
                id="btn-inspect-query-tensor"
                className="btn-secondary"
                style={{ width: '100%', justifyContent: 'center', fontSize: '0.80rem', marginBottom: '14px' }}
                onClick={() => setModalData({
                  isOpen: true,
                  originalUrl: searchResult.query_image_url,
                  structuralUrl: searchResult.query_structural_preview_url,
                  title: 'Query Saree Structural & Motif Edge Tensor'
                })}
              >
                <Cpu size={14} style={{ color: 'var(--primary-purple)' }} /> Inspect AI Vision Tensor
              </button>

              <div style={{ background: 'var(--bg-subtle)', padding: '12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 700, letterSpacing: '0.04em' }}>
                  NEURAL VERIFICATION
                </div>
                <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: '1.45', marginTop: '4px' }}>
                  Extracted 1536-D DINOv2 color-invariant motif embedding (4-zone spatial pooling: Top Border, Field Jaal, Bottom Border &amp; Pallu).
                </div>
              </div>
            </div>

            {/* Right: Results Cards */}
            <div>
              {searchResult.matches.length === 0 ? (
                <div className="saas-card" style={{ textAlign: 'center', padding: '50px', color: 'var(--text-muted)' }}>
                  No indexed designs found. Please connect your OneNote account in OneNote Integration to populate the catalog.
                </div>
              ) : filteredMatches.length === 0 ? (
                <div
                  id="no-threshold-matches"
                  className="saas-card"
                  style={{
                    textAlign: 'center',
                    padding: '50px 30px',
                    color: 'var(--text-secondary)',
                    borderRadius: 'var(--radius-lg)',
                    border: '1px solid var(--border-subtle)',
                    background: 'var(--bg-card)'
                  }}
                >
                  <div style={{
                    width: '54px',
                    height: '54px',
                    borderRadius: '50%',
                    background: 'var(--gold-light)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: '16px'
                  }}>
                    <AlertCircle size={28} style={{ color: 'var(--gold-primary)' }} />
                  </div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '8px' }}>
                    No matching designs found above the selected threshold.
                  </div>
                  <div style={{ fontSize: '0.88rem', color: 'var(--text-muted)', maxWidth: '440px', margin: '0 auto', lineHeight: 1.5 }}>
                    The confidence threshold is currently set to <strong>{thresholdPct}%</strong>. Adjust the slider above to a lower threshold to view candidate designs.
                  </div>
                </div>
              ) : (
                <div>
                  {/* Highlighted Top Match */}
                  {topMatch && (
                    <div style={{ marginBottom: '28px' }}>
                      <div style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Target size={18} style={{ color: 'var(--primary-purple)' }} />
                        <span>Strongest Identified Match</span>
                      </div>

                      <div className="match-card is-top-match" id={`match-card-${topMatch.id}`}>
                        <div className="match-img-box" style={{ aspectRatio: '1.4' }}>
                          <img src={topMatch.image_url} alt={topMatch.title} />
                          <div className={`match-score-badge ${topMatch.similarity_percentage >= 80 ? 'score-high' : topMatch.similarity_percentage >= 60 ? 'score-mid' : 'score-low'}`}>
                            {topMatch.similarity_percentage}% Match
                          </div>
                        </div>

                        <div className="match-card-body">
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px', flexWrap: 'wrap', gap: '6px' }}>
                            <span className="exact-image-badge" title={`Exact matched image: Position #${topMatch.image_order || 1} on OneNote page`}>
                              <Target size={12} style={{ color: 'var(--gold-primary)' }} />
                              Exact Match: Image #{topMatch.image_order || 1} on page
                            </span>
                            {topMatch.resource_id && (
                              <span style={{ fontSize: '0.70rem', color: 'var(--text-dim)', fontFamily: 'monospace' }}>
                                ID: {topMatch.resource_id.length > 16 ? topMatch.resource_id.substring(0, 16) + '...' : topMatch.resource_id}
                              </span>
                            )}
                          </div>

                          <div className="match-title" style={{ fontSize: '1.1rem' }}>{topMatch.title}</div>

                          <OneNoteBreadcrumb
                            notebook={topMatch.notebook_name}
                            section={topMatch.section_name}
                            page={topMatch.page_title}
                            imageOrder={topMatch.image_order}
                            item={topMatch}
                            copyUrl={getExactPageWebUrl(topMatch)}
                          />

                          {topMatch.motifs && topMatch.motifs.length > 0 && (
                            <div className="tags-row">
                              {topMatch.motifs.map((motif, i) => (
                                <span key={i} className="motif-tag">{motif}</span>
                              ))}
                            </div>
                          )}

                          <div className="match-card-footer">
                            <button
                              className="btn-secondary"
                              style={{ padding: '6px 12px', fontSize: '0.78rem' }}
                              onClick={() => setModalData({
                                isOpen: true,
                                originalUrl: topMatch.image_url,
                                structuralUrl: topMatch.structural_preview_url || topMatch.image_url,
                                title: `${topMatch.title} - Structural Map`
                              })}
                              id={`btn-inspect-match-${topMatch.id}`}
                            >
                              <Eye size={13} /> AI Map
                            </button>

                            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                              <button
                                className="btn-primary"
                                id={`btn-open-onenote-${topMatch.id}`}
                                title={`Open exact matched page in OneNote: ${topMatch.notebook_name} > ${topMatch.section_name} > ${topMatch.page_title || topMatch.title}`}
                                onClick={(e) => {
                                  e.preventDefault();
                                  handleOpenExactMatch(topMatch);
                                }}
                              >
                                <ExternalLink size={14} /> Open Exact Match in OneNote
                              </button>

                              <button
                                className="btn-secondary"
                                style={{ padding: '8px 12px', fontSize: '0.78rem' }}
                                title="Open exact page in OneNote Online"
                                id={`btn-open-web-${topMatch.id}`}
                                onClick={(e) => {
                                  e.preventDefault();
                                  handleOpenExactMatch(topMatch);
                                }}
                              >
                                <Globe size={14} />
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Other Similar Designs */}
                  {otherMatches.length > 0 && (
                    <div>
                      <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '14px' }}>
                        Other Similar Designs in Archive ({otherMatches.length})
                      </div>

                      <div className="matches-grid">
                        {otherMatches.map((match) => {
                          const scoreClass = match.similarity_percentage >= 80
                            ? 'score-high'
                            : match.similarity_percentage >= 60
                              ? 'score-mid'
                              : 'score-low';

                          return (
                            <div
                              key={match.id}
                              className="match-card"
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

                                <OneNoteBreadcrumb
                                  notebook={match.notebook_name}
                                  section={match.section_name}
                                  page={match.page_title}
                                  imageOrder={match.image_order}
                                  item={match}
                                  copyUrl={getExactPageWebUrl(match)}
                                />

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
                                      title="Open Exact Match in OneNote"
                                      onClick={(e) => {
                                        e.preventDefault();
                                        handleOpenExactMatch(match);
                                      }}
                                    >
                                      <ExternalLink size={12} /> Open Exact Match in OneNote
                                    </button>

                                    <button
                                      className="btn-secondary"
                                      style={{ padding: '6px 9px', fontSize: '0.75rem' }}
                                      title="Open exact page in OneNote Online"
                                      onClick={(e) => {
                                        e.preventDefault();
                                        handleOpenExactMatch(match);
                                      }}
                                    >
                                      <Globe size={12} />
                                    </button>
                                  </div>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 3. STRUCTURAL MAP INSPECTION MODAL */}
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
