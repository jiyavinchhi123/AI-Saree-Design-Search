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
  ChevronRight 
} from 'lucide-react';
import { api, getCleanOneNoteUrl } from '../services/api';
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

  // Catalog Table State
  const [designs, setDesigns] = useState([]);

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
      console.error(e);
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
      setNotification(null);
      const res = await api.startDeviceLogin();
      setDeviceLogin({
        isOpen: true,
        sessionId: res.session_id || 'default',
        userCode: res.user_code,
        verificationUri: res.verification_uri || 'https://microsoft.com/devicelogin',
        isPolling: true,
        message: res.message,
        copied: false
      });

      if (pollingRef.current) clearInterval(pollingRef.current);
      pollingRef.current = setInterval(async () => {
        try {
          const comp = await api.completeDeviceLogin(res.session_id);
          if (comp.status === 'success') {
            if (pollingRef.current) clearInterval(pollingRef.current);
            pollingRef.current = null;
            setDeviceLogin(prev => ({ ...prev, isOpen: false, isPolling: false }));
            setNotification({ 
              type: 'success', 
              message: `Connected successfully as ${comp.user?.displayName || 'User'}!` 
            });
            await loadData();
          }
        } catch (pollErr) {
          // Keep polling until user authorizes on microsoft.com/devicelogin
        }
      }, 5000);
    } catch (err) {
      setNotification({ type: 'error', message: err.message || 'Failed to start device login' });
    }
  };

  const handleCheckDeviceLoginStatus = async () => {
    try {
      const comp = await api.completeDeviceLogin(deviceLogin.sessionId);
      if (comp.status === 'success') {
        if (pollingRef.current) clearInterval(pollingRef.current);
        pollingRef.current = null;
        setDeviceLogin(prev => ({ ...prev, isOpen: false, isPolling: false }));
        setNotification({ 
          type: 'success', 
          message: `Connected successfully as ${comp.user?.displayName || 'User'}!` 
        });
        await loadData();
      } else {
        setNotification({ type: 'info', message: 'Waiting for sign-in approval on microsoft.com/devicelogin...' });
      }
    } catch (err) {
      setNotification({ type: 'error', message: err.message || 'Sign-in still pending' });
    }
  };

  const handleCopyCode = () => {
    if (deviceLogin.userCode) {
      navigator.clipboard.writeText(deviceLogin.userCode);
      setDeviceLogin(prev => ({ ...prev, copied: true }));
      setTimeout(() => setDeviceLogin(prev => ({ ...prev, copied: false })), 2000);
    }
  };

  const handleDisconnect = async () => {
    if (!window.confirm('Disconnect your Microsoft OneNote account?')) return;
    try {
      await api.disconnectOneNote();
      setOneNoteStatus(null);
      setNotebooks([]);
      setDesigns([]);
      setNotification({ type: 'info', message: 'OneNote account disconnected.' });
      loadData();
    } catch (e) {
      setNotification({ type: 'error', message: 'Failed to disconnect' });
    }
  };

  const toggleNotebookSelection = (id) => {
    setSelectedNotebookIds(prev => 
      prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]
    );
  };

  const handleSyncNow = async () => {
    setIsSyncing(true);
    setNotification(null);
    try {
      const res = await api.syncOneNote(selectedNotebookIds.length > 0 ? selectedNotebookIds : null);
      setNotification({
        type: 'success',
        message: res.message || `Indexed ${res.indexed_count || 0} saree images across ${res.pages_scanned || 0} pages.`
      });
      await loadData();
    } catch (err) {
      setNotification({ type: 'error', message: err.message || 'OneNote sync failed' });
    } finally {
      setIsSyncing(false);
    }
  };

  const handleClearCatalog = async () => {
    if (!window.confirm('Clear all indexed saree designs from your local catalog?')) return;
    try {
      await api.clearAllDesigns();
      setNotification({ type: 'info', message: 'Catalog cleared.' });
      loadData();
    } catch (err) {
      setNotification({ type: 'error', message: 'Failed to clear catalog' });
    }
  };

  return (
    <div className="page-container" id="data-sources-page">
      <div style={{ marginBottom: '28px' }}>
        <h2 style={{ fontSize: '1.65rem', color: '#fff', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <BookOpen size={26} style={{ color: 'var(--gold-primary)' }} /> Real-Time Microsoft OneNote Integration
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginTop: '4px' }}>
          Connect your personal or enterprise Microsoft account. Select your notebooks to ingest saree designs and search them with Color-Invariant AI.
        </p>
      </div>

      {notification && (
        <div style={{
          padding: '14px 20px',
          borderRadius: 'var(--radius-md)',
          marginBottom: '24px',
          background: notification.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
          border: `1px solid ${notification.type === 'success' ? 'var(--accent-emerald)' : 'var(--accent-crimson)'}`,
          color: notification.type === 'success' ? '#a7f3d0' : '#fca5a5',
          fontSize: '0.88rem',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          {notification.type === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
          <span>{notification.message}</span>
        </div>
      )}

      {/* Main Connection & Profile Section */}
      <div style={{ display: 'grid', gridTemplateColumns: oneNoteStatus?.is_connected ? '1.1fr 1fr' : '1fr', gap: '24px', marginBottom: '32px' }}>
        
        {/* Account Status Card */}
        <div className="upload-card" style={{ margin: 0, padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ 
                width: '44px', 
                height: '44px', 
                borderRadius: '8px', 
                background: 'linear-gradient(135deg, #7719aa, #9b30ff)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                color: '#fff',
                fontWeight: 800,
                fontSize: '22px'
              }}>
                N
              </div>
              <div>
                <h3 style={{ fontSize: '1.2rem', color: '#fff' }}>Microsoft OneNote Account</h3>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <ShieldCheck size={13} style={{ color: '#10b981' }} /> Strictly Read-Only (Notes.Read)
                </span>
              </div>
            </div>
            <div className={`status-dot ${oneNoteStatus?.is_connected ? '' : 'inactive'}`} title={oneNoteStatus?.is_connected ? 'Connected' : 'Not Connected'} />
          </div>

          {!oneNoteStatus?.is_connected ? (
            <div>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: '1.6', marginBottom: '20px' }}>
                Sign in with your Microsoft account (e.g. <strong>@outlook.com, @hotmail.com, @gmail.com</strong> or enterprise Office 365) to let AI access your saree design pages.
              </p>

              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <button 
                  id="btn-device-login-onenote"
                  className="btn-primary" 
                  onClick={handleStartDeviceLogin}
                  style={{ padding: '12px 20px', fontSize: '0.9rem', flex: 1, justifyContent: 'center' }}
                >
                  <Sparkles size={16} /> Connect Microsoft OneNote (1-Click)
                </button>
                <button 
                  id="btn-oauth-login-onenote"
                  className="btn-secondary" 
                  onClick={handleDirectOAuthLogin}
                  style={{ padding: '12px 18px', fontSize: '0.85rem' }}
                >
                  <ExternalLink size={14} /> Direct Web Login
                </button>
              </div>
            </div>
          ) : (
            <div>
              <div style={{ 
                background: 'rgba(255, 255, 255, 0.03)', 
                border: '1px solid var(--border-subtle)', 
                borderRadius: '8px', 
                padding: '16px', 
                marginBottom: '18px' 
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-dim)' }}>Signed In As:</span>
                  <strong style={{ color: '#fff' }}>{oneNoteStatus.display_name || 'Microsoft User'}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-dim)' }}>Account Email:</span>
                  <strong style={{ color: 'var(--gold-light)' }}>{oneNoteStatus.user_email}</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-dim)' }}>Indexed Saree Designs:</span>
                  <strong style={{ color: '#10b981' }}>{oneNoteStatus.indexed_designs_count || 0} designs</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-dim)' }}>Last Synced:</span>
                  <span style={{ color: 'var(--text-muted)' }}>
                    {oneNoteStatus.last_synced ? new Date(oneNoteStatus.last_synced).toLocaleString() : 'Never synced'}
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', gap: '10px' }}>
                <button 
                  id="btn-sync-onenote-top"
                  className="btn-primary" 
                  onClick={handleSyncNow}
                  disabled={isSyncing}
                  style={{ flex: 1, justifyContent: 'center' }}
                >
                  <RefreshCw size={15} className={isSyncing ? 'spin' : ''} /> {isSyncing ? 'Scanning & Ingesting...' : 'Sync Notebooks Now'}
                </button>
                <button 
                  id="btn-disconnect-onenote"
                  className="btn-secondary" 
                  onClick={handleDisconnect}
                  title="Switch or Disconnect Microsoft account"
                  style={{ color: '#fca5a5' }}
                >
                  <LogOut size={14} /> Disconnect
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Notebooks Selector (When Connected) */}
        {oneNoteStatus?.is_connected && (
          <div className="upload-card" style={{ margin: 0, padding: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <div>
                <h3 style={{ fontSize: '1.15rem', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Layers size={18} style={{ color: 'var(--gold-primary)' }} /> Your OneNote Notebooks
                </h3>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
                  Fetched live via Microsoft Graph API
                </span>
              </div>
              <button 
                className="btn-secondary" 
                onClick={loadNotebooks} 
                disabled={isLoadingNotebooks}
                style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                title="Refresh Notebooks List"
              >
                <RefreshCw size={12} className={isLoadingNotebooks ? 'spin' : ''} /> Refresh
              </button>
            </div>

            {isLoadingNotebooks ? (
              <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                <RefreshCw size={20} className="spin" style={{ color: 'var(--gold-primary)', marginBottom: '8px' }} />
                <p style={{ fontSize: '0.85rem' }}>Loading notebooks from Microsoft Cloud...</p>
              </div>
            ) : notebooks.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '24px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No notebooks found in this Microsoft account.</p>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '4px' }}>Create a notebook in OneNote with saree photos, then click Refresh.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '220px', overflowY: 'auto' }}>
                {notebooks.map(nb => {
                  const isChecked = selectedNotebookIds.includes(nb.id);
                  return (
                    <div 
                      key={nb.id}
                      onClick={() => toggleNotebookSelection(nb.id)}
                      style={{
                        padding: '12px',
                        borderRadius: '6px',
                        background: isChecked ? 'rgba(155, 48, 255, 0.12)' : 'rgba(255,255,255,0.02)',
                        border: `1px solid ${isChecked ? 'rgba(155, 48, 255, 0.4)' : 'var(--border-subtle)'}`,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <input 
                          type="checkbox" 
                          checked={isChecked} 
                          onChange={() => {}} 
                          style={{ accentColor: '#a855f7', cursor: 'pointer' }}
                        />
                        <div>
                          <div style={{ fontWeight: 600, color: '#fff', fontSize: '0.9rem' }}>{nb.displayName}</div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                            {nb.sectionsCount} {nb.sectionsCount === 1 ? 'section' : 'sections'}: {nb.sections?.map(s => s.displayName).join(', ') || 'No sections'}
                          </div>
                        </div>
                      </div>
                      <ChevronRight size={14} style={{ color: 'var(--text-dim)' }} />
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Catalog Table */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 style={{ fontSize: '1.25rem', color: '#fff' }}>Your Indexed OneNote Designs</h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {designs.length} designs available for AI similarity search in your account.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          {designs.length > 0 && (
            <button 
              className="btn-secondary" 
              onClick={handleClearCatalog}
              style={{ color: '#fca5a5', fontSize: '0.8rem' }}
            >
              <Trash2 size={13} /> Clear Catalog
            </button>
          )}
        </div>
      </div>

      {/* Table Display */}
      <div className="table-responsive">
        <table className="catalog-table">
          <thead>
            <tr>
              <th>Preview</th>
              <th>Design / Page Title</th>
              <th>Category / Section</th>
              <th>OneNote Location</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {designs.length === 0 ? (
              <tr>
                <td colSpan="5" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  {oneNoteStatus?.is_connected 
                    ? "No saree designs indexed yet. Click 'Sync Notebooks Now' above to ingest images from your OneNote."
                    : "Connect your Microsoft OneNote account above to view and search your designs."}
                </td>
              </tr>
            ) : (
              designs.slice(0, 100).map((d) => (
                <tr key={d.id}>
                  <td style={{ width: '60px' }}>
                    <div style={{ width: '48px', height: '48px', borderRadius: '4px', overflow: 'hidden', background: '#000', border: '1px solid var(--border-subtle)' }}>
                      <img src={d.image_url} alt={d.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                    </div>
                  </td>
                  <td>
                    <div style={{ fontWeight: 600, color: '#fff' }}>{d.title}</div>
                    <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>ID: {d.design_id}</div>
                  </td>
                  <td>
                    <span className="badge-tag">{d.category || d.section_name || 'OneNote'}</span>
                  </td>
                  <td>
                    <OneNoteBreadcrumb 
                      notebook={d.notebook_name} 
                      section={d.section_name} 
                      page={d.page_title}
                    />
                  </td>
                  <td>
                    {d.onenote_web_url || d.onenote_client_url ? (
                      <button 
                        onClick={async (e) => {
                          e.preventDefault();
                          try {
                            const res = await api.openInOneNote(d.id, 'desktop');
                            if (res && res.client_url) {
                              window.location.href = res.client_url;
                            }
                          } catch (err) {}
                        }}
                        className="btn-onenote"
                        style={{ padding: '6px 12px', fontSize: '0.78rem', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                        title={`Open exact location in Desktop OneNote: ${d.notebook_name} > ${d.section_name} > ${d.page_title}`}
                      >
                        <ExternalLink size={12} /> Open in OneNote
                      </button>
                    ) : (
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 1-Click Microsoft Device Login Modal */}
      {deviceLogin.isOpen && (
        <div className="modal-overlay" onClick={closeDeviceLoginModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '480px', textAlign: 'center' }}>
            <div className="modal-header" style={{ justifyContent: 'center', position: 'relative' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'rgba(212, 175, 55, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--gold-primary)' }}>
                  <Sparkles size={20} />
                </div>
                <h3 style={{ fontSize: '1.2rem', color: '#fff' }}>Sign In to Microsoft OneNote</h3>
              </div>
              <button 
                className="close-btn" 
                onClick={closeDeviceLoginModal}
                style={{ position: 'absolute', right: '16px', top: '16px' }}
              >
                ×
              </button>
            </div>

            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: '14px 0 16px', lineHeight: '1.5' }}>
              Works with personal accounts (<strong>@outlook.com, @hotmail.com, @gmail.com</strong>) or work/school accounts.
            </p>

            <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px dashed var(--gold-primary)', borderRadius: 'var(--radius-md)', padding: '18px', marginBottom: '18px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '6px' }}>
                Step 1: Your OneNote Login Code:
              </div>
              <div style={{ fontSize: '2.2rem', fontWeight: 800, color: 'var(--gold-light)', letterSpacing: '4px', fontFamily: 'monospace' }}>
                {deviceLogin.userCode || 'LOADING...'}
              </div>
              <button 
                onClick={handleCopyCode}
                style={{ marginTop: '10px', fontSize: '0.8rem', padding: '6px 14px', borderRadius: '4px', background: 'rgba(212, 175, 55, 0.2)', color: 'var(--gold-light)', border: '1px solid var(--border-active)', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}
              >
                {deviceLogin.copied ? <Check size={14} /> : <Copy size={14} />}
                {deviceLogin.copied ? 'Copied to Clipboard!' : 'Copy Code'}
              </button>
            </div>

            <div style={{ marginBottom: '14px' }}>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-dim)', marginBottom: '8px' }}>
                Step 2: Enter code on Microsoft's authorization page:
              </div>
              <a 
                href={deviceLogin.verificationUri} 
                target="_blank" 
                rel="noreferrer"
                className="btn-primary"
                style={{ width: '100%', justifyContent: 'center', padding: '12px', fontSize: '0.92rem' }}
              >
                <ExternalLink size={16} /> Open {deviceLogin.verificationUri}
              </a>
            </div>

            <div style={{ marginBottom: '18px' }}>
              <button
                type="button"
                className="btn-secondary"
                onClick={handleCheckDeviceLoginStatus}
                style={{ width: '100%', justifyContent: 'center', padding: '10px', fontSize: '0.84rem' }}
              >
                <CheckCircle2 size={15} style={{ color: 'var(--accent-emerald)' }} /> I've Approved the Code - Connect Now
              </button>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              <RefreshCw size={13} className="spin" style={{ color: 'var(--gold-primary)' }} />
              <span>Auto-detecting your approval in the background...</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
