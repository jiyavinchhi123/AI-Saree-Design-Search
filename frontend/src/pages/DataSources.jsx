import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  BookOpen, 
  RefreshCw, 
  ExternalLink, 
  CheckCircle2, 
  AlertCircle, 
  Trash2, 
  Sparkles, 
  Copy, 
  Check, 
  LogOut, 
  Layers, 
  ShieldCheck, 
  ChevronRight,
  Folder,
  FileText,
  Clock,
  Search,
  KeyRound,
  X
} from 'lucide-react';
import { api, getExactPageWebUrl, getCleanOneNoteUrl } from '../services/api';
import OneNoteBreadcrumb from '../components/OneNoteBreadcrumb';

export default function DataSources() {
  const [oneNoteStatus, setOneNoteStatus] = useState(null);
  const [notebooks, setNotebooks] = useState([]);
  const [selectedNotebookIds, setSelectedNotebookIds] = useState([]);
  const [isLoadingNotebooks, setIsLoadingNotebooks] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [notification, setNotification] = useState(null);

  // 1-Click Device Login State
  const [deviceLogin, setDeviceLogin] = useState({
    isOpen: false,
    sessionId: '',
    userCode: '',
    verificationUri: 'https://microsoft.com/devicelogin',
    isPolling: false,
    message: '',
    copied: false
  });
  const pollingRef = useRef(null);
  const [manualCode, setManualCode] = useState('');
  const [isSubmittingCode, setIsSubmittingCode] = useState(false);
  const [showManualInput, setShowManualInput] = useState(false);

  // Catalog Table State
  const [designs, setDesigns] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  const loadNotebooks = useCallback(async () => {
    setIsLoadingNotebooks(true);
    try {
      const res = await api.getOneNoteNotebooks();
      const nbs = res.notebooks || [];
      setNotebooks(nbs);
      setSelectedNotebookIds(nbs.map(n => n.id));
    } catch (err) {
      console.error('Failed to load user notebooks:', err);
    } finally {
      setIsLoadingNotebooks(false);
    }
  }, []);

  const loadData = useCallback(async () => {
    try {
      const status = await api.getOneNoteStatus();
      setOneNoteStatus(status);

      if (status?.is_connected) {
        loadNotebooks();
      }

      const catalogData = await api.getDesigns();
      setDesigns(catalogData.designs || []);
    } catch (e) {
      console.error('Error loading data sources:', e);
    }
  }, [loadNotebooks]);

  useEffect(() => {
    loadData();
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [loadData]);

  const handleDirectOAuthLogin = async () => {
    try {
      setNotification({ type: 'info', message: 'Opening Microsoft Sign-In window...' });
      const res = await api.getOneNoteAuthUrl();
      if (res && res.auth_url) {
        window.location.href = res.auth_url;
      } else {
        throw new Error('Failed to generate Microsoft login URL');
      }
    } catch (err) {
      setNotification({ type: 'error', message: err.message || 'Login initiation failed' });
    }
  };

  const closeDeviceLoginModal = () => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    setDeviceLogin(prev => ({ ...prev, isOpen: false, isPolling: false }));
  };

  const handleStartDeviceLogin = async () => {
    try {
      setNotification({ type: 'info', message: 'Requesting Microsoft Device Code...' });
      const flow = await api.startDeviceLogin();
      setDeviceLogin({
        isOpen: true,
        sessionId: flow.session_id,
        userCode: flow.user_code,
        verificationUri: flow.verification_uri || 'https://microsoft.com/devicelogin',
        isPolling: true,
        message: flow.message || 'Enter code on Microsoft device login page',
        copied: false
      });

      // Poll for authorization completion
      pollingRef.current = setInterval(async () => {
        try {
          const res = await api.completeDeviceLogin(flow.session_id);
          if (res.status === 'success') {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
            setDeviceLogin(prev => ({ ...prev, isOpen: false, isPolling: false }));
            setNotification({ type: 'success', message: 'Connected successfully to Microsoft OneNote!' });
            loadData();
          }
        } catch {
          // Keep polling until user completes on browser
        }
      }, 4000);
    } catch (err) {
      setNotification({ type: 'error', message: err.message || 'Device login failed' });
    }
  };

  const handleExchangeManualCode = async (e) => {
    if (e) e.preventDefault();
    if (!manualCode.trim()) return;
    setIsSubmittingCode(true);
    try {
      setNotification({ type: 'info', message: 'Verifying Microsoft authorization code...' });
      const res = await api.exchangeAuthCode(manualCode.trim());
      if (res.status === 'success') {
        closeDeviceLoginModal();
        setManualCode('');
        setShowManualInput(false);
        setNotification({ type: 'success', message: 'Connected successfully to Microsoft OneNote!' });
        loadData();
      }
    } catch (err) {
      setNotification({ type: 'error', message: err.message || 'Authorization code invalid or expired' });
    } finally {
      setIsSubmittingCode(false);
    }
  };

  const handleDisconnect = async () => {
    if (window.confirm('Disconnect your Microsoft OneNote account from this workspace?')) {
      try {
        await api.disconnectOneNote();
        setOneNoteStatus(null);
        setNotebooks([]);
        setNotification({ type: 'info', message: 'Microsoft account disconnected' });
        loadData();
      } catch (err) {
        setNotification({ type: 'error', message: 'Failed to disconnect account' });
      }
    }
  };

  const handleSyncNotebooks = async () => {
    setIsSyncing(true);
    setNotification({ type: 'info', message: 'Scanning OneNote pages & extracting saree design embeddings...' });
    try {
      const res = await api.syncOneNoteNotebooks(selectedNotebookIds);
      setNotification({ 
        type: 'success', 
        message: res.message || `Successfully synced ${res.indexed_count || 0} designs from OneNote!` 
      });
      loadData();
    } catch (err) {
      setNotification({ type: 'error', message: err.message || 'Synchronization failed' });
    } finally {
      setIsSyncing(false);
    }
  };

  const handleToggleNotebook = (nbId) => {
    setSelectedNotebookIds(prev => 
      prev.includes(nbId) ? prev.filter(id => id !== nbId) : [...prev, nbId]
    );
  };

  // Filter catalog items
  const filteredDesigns = designs.filter(d => {
    const matchesSearch = !searchQuery || 
      (d.title && d.title.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (d.notebook_name && d.notebook_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (d.section_name && d.section_name.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesCat = selectedCategory === 'all' || d.category === selectedCategory;
    return matchesSearch && matchesCat;
  });

  const uniqueCategories = ['all', ...new Set(designs.map(d => d.category).filter(Boolean))];

  return (
    <div className="page-container" id="data-sources-page">
      {/* Notifications */}
      {notification && (
        <div style={{
          padding: '14px 18px',
          borderRadius: 'var(--radius-md)',
          marginBottom: '24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: notification.type === 'error' ? 'var(--crimson-light)' : notification.type === 'success' ? 'var(--emerald-light)' : 'var(--purple-light)',
          border: `1px solid ${notification.type === 'error' ? 'var(--crimson-border)' : notification.type === 'success' ? 'var(--emerald-border)' : 'var(--purple-border)'}`,
          color: notification.type === 'error' ? 'var(--accent-crimson)' : notification.type === 'success' ? 'var(--accent-emerald)' : 'var(--primary-purple)',
          fontSize: '0.88rem',
          fontWeight: 600
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {notification.type === 'error' ? <AlertCircle size={18} /> : <CheckCircle2 size={18} />}
            <span>{notification.message}</span>
          </div>
          <button 
            onClick={() => setNotification(null)}
            style={{ background: 'transparent', color: 'inherit', padding: '4px' }}
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* 1. READ-ONLY SECURITY EXPLANATION CARD */}
      <div style={{
        background: 'linear-gradient(135deg, #ffffff 0%, #faf8ff 100%)',
        border: '1px solid var(--purple-border)',
        borderRadius: 'var(--radius-xl)',
        padding: '22px 26px',
        marginBottom: '28px',
        display: 'flex',
        alignItems: 'center',
        gap: '18px',
        boxShadow: 'var(--shadow-sm)'
      }}>
        <div style={{
          width: '46px',
          height: '46px',
          borderRadius: 'var(--radius-md)',
          background: 'var(--purple-light)',
          color: 'var(--primary-purple)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0
        }}>
          <ShieldCheck size={26} />
        </div>
        <div style={{ flex: 1 }}>
          <h4 style={{ fontSize: '1.05rem', color: 'var(--text-main)', marginBottom: '4px' }}>
            Read-Only Access
          </h4>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
            Your OneNote notebooks, sections, and pages are <strong>never modified or deleted</strong>. The app only reads image designs.
          </p>
        </div>
      </div>

      {/* 2. MICROSOFT ONENOTE CONNECTION & STATUS */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', 
        gap: '24px', 
        marginBottom: '32px' 
      }}>
        {/* Account Status Card */}
        <div className="saas-card" id="card-onenote-account">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                width: '42px',
                height: '42px',
                borderRadius: 'var(--radius-md)',
                background: 'linear-gradient(135deg, #7c3aed 0%, #581c87 100%)',
                color: '#ffffff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 10px rgba(124, 58, 237, 0.25)'
              }}>
                <BookOpen size={22} />
              </div>
              <div>
                <h3 style={{ fontSize: '1.15rem', color: 'var(--text-main)' }}>Microsoft OneNote</h3>
                <p style={{ fontSize: '0.80rem', color: 'var(--text-muted)' }}>Account Status</p>
              </div>
            </div>

            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '5px 12px',
              borderRadius: 'var(--radius-full)',
              fontSize: '0.78rem',
              fontWeight: 700,
              background: oneNoteStatus?.is_connected ? 'var(--emerald-light)' : 'var(--gold-light)',
              color: oneNoteStatus?.is_connected ? 'var(--accent-emerald)' : 'var(--gold-text)',
              border: `1px solid ${oneNoteStatus?.is_connected ? 'var(--emerald-border)' : 'var(--gold-border)'}`
            }}>
              <span className={`status-dot ${oneNoteStatus?.is_connected ? '' : 'inactive'}`} />
              {oneNoteStatus?.is_connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>

          {oneNoteStatus?.is_connected ? (
            <div>
              <div style={{ 
                background: 'var(--bg-subtle)', 
                borderRadius: 'var(--radius-md)', 
                padding: '16px', 
                marginBottom: '20px' 
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Account Name:</span>
                  <strong style={{ fontSize: '0.84rem', color: 'var(--text-main)' }}>
                    {oneNoteStatus.display_name || 'Microsoft User'}
                  </strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Account Email:</span>
                  <strong style={{ fontSize: '0.84rem', color: 'var(--primary-purple)' }}>
                    {oneNoteStatus.user_email}
                  </strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Indexed Designs:</span>
                  <strong style={{ fontSize: '0.84rem', color: 'var(--accent-emerald)' }}>
                    {oneNoteStatus.indexed_designs_count} designs
                  </strong>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <button 
                  id="btn-sync-onenote"
                  className="btn-primary" 
                  onClick={handleSyncNotebooks}
                  disabled={isSyncing}
                  style={{ flex: 1, minWidth: '160px' }}
                >
                  <RefreshCw size={16} className={isSyncing ? 'spinner' : ''} />
                  <span>{isSyncing ? 'Syncing...' : 'Sync Notebooks'}</span>
                </button>
                <button 
                  id="btn-disconnect-onenote"
                  className="btn-secondary" 
                  onClick={handleDisconnect}
                  style={{ color: 'var(--accent-crimson)', borderColor: '#fca5a5' }}
                >
                  <LogOut size={15} /> Disconnect
                </button>
              </div>
            </div>
          ) : (
            <div>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: '1.6', marginBottom: '22px' }}>
                Sign in to automatically index saree designs from your OneNote notebooks.
              </p>

              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <button 
                  id="btn-connect-onenote"
                  className="btn-primary" 
                  onClick={oneNoteStatus?.is_configured ? handleDirectOAuthLogin : handleStartDeviceLogin}
                  style={{ flex: 1, minWidth: '180px' }}
                >
                  <BookOpen size={16} /> Connect OneNote
                </button>
                {oneNoteStatus?.is_configured && (
                  <button 
                    id="btn-device-login"
                    className="btn-secondary" 
                    onClick={handleStartDeviceLogin}
                  >
                    <KeyRound size={15} /> Device Code
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Sync Summary & Health Card */}
        <div className="saas-card" id="card-sync-summary">
          <h3 style={{ fontSize: '1.15rem', color: 'var(--text-main)', marginBottom: '8px' }}>
            Sync Summary
          </h3>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '20px' }}>
            Overview of indexed notebooks and designs.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '14px', marginBottom: '20px' }}>
            <div style={{ background: 'var(--bg-subtle)', padding: '14px', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600 }}>DESIGNS</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--primary-purple)', marginTop: '4px' }}>
                {oneNoteStatus?.indexed_designs_count ?? 0}
              </div>
            </div>
            <div style={{ background: 'var(--bg-subtle)', padding: '14px', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600 }}>NOTEBOOKS</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--gold-primary)', marginTop: '4px' }}>
                {oneNoteStatus?.notebooks_count ?? notebooks.length ?? 0}
              </div>
            </div>
            <div style={{ background: 'var(--bg-subtle)', padding: '14px', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', fontWeight: 600 }}>SECTIONS</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--accent-emerald)', marginTop: '4px' }}>
                {notebooks.reduce((acc, nb) => acc + (nb.sectionsCount || (nb.sections ? nb.sections.length : 0)), 0)}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.80rem', color: 'var(--text-muted)' }}>
            <Clock size={16} style={{ color: 'var(--text-dim)' }} />
            <span>
              Last synced: <strong>{oneNoteStatus?.last_synced ? new Date(oneNoteStatus.last_synced).toLocaleString() : 'Not synced yet'}</strong>
            </span>
          </div>
        </div>
      </div>

      {/* 3. CONNECTED NOTEBOOKS SELECTOR (When Connected) */}
      {oneNoteStatus?.is_connected && (
        <div className="saas-card" style={{ marginBottom: '32px' }} id="connected-notebooks-section">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h3 style={{ fontSize: '1.15rem', color: 'var(--text-main)' }}>Connected OneNote Notebooks</h3>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                Select which notebooks to include during automated image extraction and FAISS indexing.
              </p>
            </div>
            <button 
              className="btn-secondary"
              onClick={loadNotebooks}
              disabled={isLoadingNotebooks}
              style={{ padding: '6px 12px', fontSize: '0.78rem', minHeight: 'auto' }}
            >
              <RefreshCw size={13} className={isLoadingNotebooks ? 'spinner' : ''} /> Refresh List
            </button>
          </div>

          {isLoadingNotebooks ? (
            <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
              <RefreshCw size={24} className="spinner" style={{ margin: '0 auto 10px auto', color: 'var(--primary-purple)' }} />
              <div>Fetching notebooks and sections from Microsoft Graph API...</div>
            </div>
          ) : notebooks.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)', background: 'var(--bg-subtle)', borderRadius: 'var(--radius-md)' }}>
              No notebooks discovered yet. Ensure your Microsoft OneNote account contains at least one notebook with sections.
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
              {notebooks.map((nb) => {
                const isSelected = selectedNotebookIds.includes(nb.id);
                return (
                  <div 
                    key={nb.id}
                    onClick={() => handleToggleNotebook(nb.id)}
                    style={{
                      border: `1.5px solid ${isSelected ? 'var(--primary-purple)' : 'var(--border-subtle)'}`,
                      background: isSelected ? 'var(--purple-light)' : '#ffffff',
                      borderRadius: 'var(--radius-lg)',
                      padding: '16px',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      boxShadow: isSelected ? 'var(--shadow-purple)' : 'var(--shadow-xs)'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <BookOpen size={18} style={{ color: isSelected ? 'var(--primary-purple)' : 'var(--text-muted)' }} />
                        <strong style={{ fontSize: '0.92rem', color: 'var(--text-main)' }}>{nb.displayName}</strong>
                      </div>
                      <input 
                        type="checkbox" 
                        checked={isSelected} 
                        onChange={() => {}} 
                        style={{ accentColor: 'var(--primary-purple)', width: '16px', height: '16px', cursor: 'pointer' }} 
                      />
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                      {nb.sectionsCount || (nb.sections ? nb.sections.length : 0)} sections available
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* 4. INDEXED SAREE DESIGNS CATALOG TABLE */}
      <div className="saas-card" id="indexed-catalog-section">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '14px' }}>
          <div>
            <h3 style={{ fontSize: '1.25rem', color: 'var(--text-main)' }}>
              Indexed Saree Designs Catalog ({filteredDesigns.length})
            </h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '2px' }}>
              Full library of saree patterns extracted and vectorized from your OneNote archive.
            </p>
          </div>

          {/* Search & Filter Controls */}
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ position: 'relative' }}>
              <Search size={15} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
              <input 
                type="text"
                placeholder="Search catalog..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  padding: '8px 12px 8px 34px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-subtle)',
                  fontSize: '0.84rem',
                  width: '180px'
                }}
              />
            </div>

            {uniqueCategories.length > 2 && (
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                style={{
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  background: 'var(--bg-subtle)',
                  fontSize: '0.84rem'
                }}
              >
                {uniqueCategories.map(c => (
                  <option key={c} value={c}>
                    {c === 'all' ? 'All Categories' : c}
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>

        {filteredDesigns.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
            No saree designs match the selected search filter.
          </div>
        ) : (
          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Preview</th>
                  <th>Design Title</th>
                  <th>OneNote Location</th>
                  <th>Category</th>
                  <th>Position</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredDesigns.slice(0, 50).map((item) => (
                  <tr key={item.id}>
                    <td data-label="Preview">
                      <img 
                        src={item.image_url} 
                        alt={item.title} 
                        style={{ width: '48px', height: '48px', borderRadius: '6px', objectFit: 'cover', border: '1px solid #e2e8f0' }} 
                      />
                    </td>
                    <td data-label="Design Title">
                      <strong style={{ color: 'var(--text-main)', fontSize: '0.88rem' }}>{item.title}</strong>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontFamily: 'monospace' }}>
                        ID: {item.design_id || item.id}
                      </div>
                    </td>
                    <td data-label="OneNote Location">
                      <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                        <strong>{item.notebook_name}</strong> &gt; {item.section_name} &gt; {item.page_title}
                      </div>
                    </td>
                    <td data-label="Category">
                      <span style={{ 
                        background: 'var(--purple-light)', 
                        color: 'var(--primary-purple)', 
                        padding: '3px 8px', 
                        borderRadius: '4px',
                        fontSize: '0.74rem',
                        fontWeight: 600
                      }}>
                        {item.category || 'Traditional'}
                      </span>
                    </td>
                    <td data-label="Position">
                      <span className="exact-image-badge">
                        Image #{item.image_order || 1} on page
                      </span>
                    </td>
                    <td data-label="Action">
                      <a 
                        href={getExactPageWebUrl(item) || 'https://www.onenote.com/notebooks'}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-onenote"
                        style={{ padding: '6px 12px', fontSize: '0.76rem' }}
                        title="Open in OneNote"
                      >
                        <ExternalLink size={12} /> Open in OneNote
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 5. MICROSOFT DEVICE LOGIN MODAL (Fallback Flow) */}
      {deviceLogin.isOpen && (
        <div className="modal-backdrop" onClick={closeDeviceLoginModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '500px', textAlign: 'center' }}>
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={closeDeviceLoginModal} style={{ background: 'transparent', color: 'var(--text-muted)' }}>
                <X size={20} />
              </button>
            </div>
            
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: 'var(--radius-full)',
              background: 'var(--purple-light)',
              color: 'var(--primary-purple)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px auto'
            }}>
              <KeyRound size={28} />
            </div>

            <h3 style={{ fontSize: '1.35rem', color: 'var(--text-main)', marginBottom: '8px' }}>
              Connect Microsoft OneNote
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '18px', lineHeight: '1.5' }}>
              Enter this 9-character code on the Microsoft Device Login page to link your OneNote account:
            </p>

            <div style={{
              background: 'var(--bg-subtle)',
              border: '2px dashed var(--purple-border)',
              borderRadius: 'var(--radius-lg)',
              padding: '18px',
              marginBottom: '16px'
            }}>
              <div style={{ fontSize: '1.9rem', fontWeight: 800, letterSpacing: '0.15em', color: 'var(--primary-purple)', fontFamily: 'monospace' }}>
                {deviceLogin.userCode}
              </div>
              <button 
                onClick={() => {
                  navigator.clipboard.writeText(deviceLogin.userCode);
                  setDeviceLogin(prev => ({ ...prev, copied: true }));
                  setTimeout(() => setDeviceLogin(prev => ({ ...prev, copied: false })), 2000);
                }}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: '#ffffff',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '4px 10px',
                  fontSize: '0.78rem',
                  marginTop: '10px',
                  cursor: 'pointer'
                }}
              >
                {deviceLogin.copied ? <Check size={13} style={{ color: 'var(--accent-emerald)' }} /> : <Copy size={13} />}
                <span>{deviceLogin.copied ? 'Copied Code!' : 'Copy Code'}</span>
              </button>
            </div>

            <div style={{
              background: 'var(--purple-light)',
              borderRadius: 'var(--radius-md)',
              padding: '12px 16px',
              textAlign: 'left',
              fontSize: '0.80rem',
              color: 'var(--text-secondary)',
              marginBottom: '18px',
              lineHeight: '1.5'
            }}>
              <strong style={{ color: 'var(--primary-purple)' }}>Quick 3-step setup:</strong>
              <ol style={{ paddingLeft: '18px', marginTop: '4px' }}>
                <li>Copy the 9-letter code above</li>
                <li>Click <strong>Open Microsoft Login Page</strong> below</li>
                <li>Paste code & sign in — this window connects automatically!</li>
              </ol>
            </div>

            <a 
              href={deviceLogin.verificationUri} 
              target="_blank" 
              rel="noopener noreferrer"
              className="btn-primary"
              style={{ width: '100%', justifyContent: 'center', marginBottom: '14px' }}
            >
              <ExternalLink size={16} /> Open Microsoft Login Page
            </a>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', fontSize: '0.80rem', color: 'var(--text-muted)' }}>
              <RefreshCw size={14} className="spinner" />
              <span>Waiting for approval on Microsoft...</span>
            </div>

            {/* Localhost redirect fallback */}
            <div style={{ marginTop: '20px', borderTop: '1px solid var(--border-subtle)', paddingTop: '14px', textAlign: 'left' }}>
              <button 
                type="button"
                onClick={() => setShowManualInput(!showManualInput)}
                style={{ 
                  background: 'none', 
                  border: 'none', 
                  color: 'var(--primary-purple)', 
                  fontSize: '0.76rem', 
                  cursor: 'pointer',
                  fontWeight: 600,
                  padding: 0,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <span>{showManualInput ? '▼ Hide manual code input' : '▶ Redirected to localhost with a code? Paste here'}</span>
              </button>

              {showManualInput && (
                <form onSubmit={handleExchangeManualCode} style={{ marginTop: '10px', display: 'flex', gap: '8px' }}>
                  <input
                    type="text"
                    value={manualCode}
                    onChange={(e) => setManualCode(e.target.value)}
                    placeholder="Paste http://localhost/?code=... or authorization code"
                    style={{
                      flex: 1,
                      padding: '7px 10px',
                      borderRadius: 'var(--radius-sm)',
                      border: '1px solid var(--border-subtle)',
                      fontSize: '0.78rem'
                    }}
                  />
                  <button
                    type="submit"
                    className="btn-primary"
                    disabled={isSubmittingCode || !manualCode.trim()}
                    style={{ padding: '7px 12px', fontSize: '0.76rem' }}
                  >
                    {isSubmittingCode ? 'Connecting...' : 'Connect'}
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
