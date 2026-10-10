const RENDER_PROD_BASE = 'https://ai-saree-design-search.onrender.com';
const RENDER_PROD_API = `${RENDER_PROD_BASE}/api`;

const rawApiUrl = import.meta.env.VITE_API_URL;
const isProduction = typeof window !== 'undefined' && 
  window.location.hostname !== 'localhost' && 
  window.location.hostname !== '127.0.0.1';

// In production, direct connection to Render backend completely bypasses
// Vercel preview deployment protection (SSO/login walls), proxy payload size limits, and 10s timeouts.
const API_BASE = isProduction
  ? ((rawApiUrl && !rawApiUrl.includes('localhost') && !rawApiUrl.includes('127.0.0.1'))
      ? (rawApiUrl.endsWith('/api') ? rawApiUrl : `${rawApiUrl.replace(/\/$/, '')}/api`)
      : RENDER_PROD_API)
  : (rawApiUrl ? (rawApiUrl.endsWith('/api') ? rawApiUrl : `${rawApiUrl.replace(/\/$/, '')}/api`) : '/api');

export const resolveImageUrl = (url) => {
  if (!url || typeof url !== 'string') return '';
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:') || url.startsWith('blob:')) {
    return url;
  }
  const backendBase = isProduction ? RENDER_PROD_BASE : '';
  return backendBase ? `${backendBase}${url.startsWith('/') ? '' : '/'}${url}` : url;
};

export const getCurrentUserId = () => {
  try {
    if (typeof window !== 'undefined' && window.location) {
      const urlParams = new URLSearchParams(window.location.search);
      const urlUid = urlParams.get('user_id');
      if (urlUid) {
        localStorage.setItem('saree_current_user_id', urlUid);
        return urlUid;
      }
    }
    return localStorage.getItem('saree_current_user_id') || '';
  } catch (e) {
    return '';
  }
};

export const setCurrentUserId = (uid) => {
  try {
    if (uid) {
      localStorage.setItem('saree_current_user_id', uid);
    } else {
      localStorage.removeItem('saree_current_user_id');
    }
  } catch (e) {}
};

export const clearCurrentUserId = () => {
  try {
    localStorage.removeItem('saree_current_user_id');
  } catch (e) {}
};

const getHeaders = (extra = {}) => {
  const uid = getCurrentUserId();
  const headers = { ...extra };
  if (uid) {
    headers['X-User-Id'] = uid;
  }
  return headers;
};

/**
 * Robust fetch that connects directly to Render backend with automatic fallback to local /api proxy.
 * Completely immune to Vercel preview deployment login/SSO walls and proxy timeouts.
 */
const apiFetch = async (endpoint, options = {}) => {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  
  // Prioritize direct Render URL in production (with /api rewrite as fallback)
  const candidateUrls = isProduction
    ? [
        `${RENDER_PROD_API}${cleanEndpoint}`,
        `/api${cleanEndpoint}`
      ]
    : [
        `${API_BASE}${cleanEndpoint}`
      ];

  let lastError = null;
  for (const url of candidateUrls) {
    try {
      const res = await fetch(url, options);
      // If Vercel preview authentication intercepted with an HTML login page (401 with text/html)
      if (res.status === 401 && res.headers.get('content-type')?.includes('text/html')) {
        continue;
      }
      return res;
    } catch (err) {
      lastError = err;
    }
  }

  throw lastError || new Error('Backend connection failed. Please ensure the cloud server is awake.');
};

export const isPageSpecificOneNoteUrl = (url) => {
  if (!url || typeof url !== 'string' || !url.startsWith('https://')) {
    return false;
  }
  const lower = url.toLowerCase();
  return lower.includes('wd=target') || lower.includes('resid=') || lower.includes('page=') || lower.includes('pageid=');
};

export const getExactPageWebUrl = (item) => {
  if (!item) return '';
  let url = '';

  if (typeof item === 'string') {
    url = item.trim();
  } else if (typeof item === 'object') {
    if (item.page_web_url && typeof item.page_web_url === 'string') {
      url = item.page_web_url.trim();
    } else if (item.oneNoteWebUrl && typeof item.oneNoteWebUrl === 'string') {
      url = item.oneNoteWebUrl.trim();
    } else if (item.onenote_web_url && typeof item.onenote_web_url === 'string') {
      url = item.onenote_web_url.trim();
    } else if (item.top_match_page_web_url && typeof item.top_match_page_web_url === 'string') {
      url = item.top_match_page_web_url.trim();
    } else if (item.web_url && typeof item.web_url === 'string') {
      url = item.web_url.trim();
    }
  }

  if (!url || !url.startsWith('https://')) {
    return '';
  }

  if (url.toLowerCase().startsWith('onenote:')) {
    return '';
  }

  const lower = url.toLowerCase();
  if (
    lower === 'https://onenote.com' ||
    lower === 'https://onenote.com/' ||
    lower === 'https://www.onenote.com' ||
    lower === 'https://www.onenote.com/' ||
    lower.startsWith('https://www.onenote.com/notebooks') ||
    lower === 'https://onedrive.live.com' ||
    lower === 'https://onedrive.live.com/'
  ) {
    return '';
  }

  return url;
};

export const getExactObjectWebUrl = (item) => getExactPageWebUrl(item);
export const getCleanOneNoteUrl = (itemOrUrl) => getExactPageWebUrl(itemOrUrl);
export const getCleanOneNoteWebUrl = (itemOrUrl) => getExactPageWebUrl(itemOrUrl);

export const isValidOneNoteDeepLink = (url) => {
  if (!url || typeof url !== 'string' || !url.startsWith('onenote:')) return false;
  return url.includes('section-id=') && url.includes('page-id=') && url.includes('object-id=');
};

export const getCleanOneNoteClientUrl = (itemOrUrl, designId = null) => {
  if (typeof itemOrUrl === 'object' && itemOrUrl) {
    if (isValidOneNoteDeepLink(itemOrUrl.object_client_url)) {
      return itemOrUrl.object_client_url;
    }
    if (isValidOneNoteDeepLink(itemOrUrl.onenote_client_url)) {
      return itemOrUrl.onenote_client_url;
    }
    const id = itemOrUrl.id || itemOrUrl.design_id || itemOrUrl.top_match_id || designId;
    if (id) {
      return `/api/designs/${id}/open-onenote?mode=desktop`;
    }
  }
  if (typeof itemOrUrl === 'string' && isValidOneNoteDeepLink(itemOrUrl)) {
    return itemOrUrl;
  }
  if (designId) {
    return `/api/designs/${designId}/open-onenote?mode=desktop`;
  }
  return null;
};

export const api = {
  // Search with real uploaded saree image
  searchByImage: async (file, threshold = 0.82, topK = 6) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('threshold', threshold.toString());
    formData.append('top_k', topK.toString());
    const res = await apiFetch('/search/upload', {
      method: 'POST',
      headers: getHeaders(),
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Search request failed');
    }
    const data = await res.json();
    if (data.query_image_url) data.query_image_url = resolveImageUrl(data.query_image_url);
    if (data.query_structural_preview_url) data.query_structural_preview_url = resolveImageUrl(data.query_structural_preview_url);
    if (Array.isArray(data.matches)) {
      data.matches = data.matches.map(m => ({
        ...m,
        image_url: resolveImageUrl(m.image_url),
        structural_preview_url: resolveImageUrl(m.structural_preview_url)
      }));
    }
    return data;
  },

  // OneNote & Data Sources Status
  getOneNoteStatus: async () => {
    try {
      const res = await apiFetch('/data-sources/onenote/status', {
        headers: getHeaders(),
      });
      if (!res.ok) {
        return null;
      }
      const data = await res.json();
      if (data && data.user_id && !getCurrentUserId()) {
        setCurrentUserId(data.user_id);
      }
      return data;
    } catch (e) {
      console.warn('OneNote status fetch warning:', e);
      return null;
    }
  },

  getOneNoteAuthUrl: async () => {
    const res = await apiFetch('/data-sources/onenote/auth/url', {
      headers: getHeaders(),
    });
    return res.json();
  },

  getOneNoteAuthConfig: async () => {
    const res = await apiFetch('/data-sources/onenote/auth/config', {
      headers: getHeaders(),
    });
    return res.json();
  },

  saveOneNoteAuthConfig: async (config) => {
    const res = await apiFetch('/data-sources/onenote/auth/config', {
      method: 'POST',
      headers: getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(config),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to save configuration');
    }
    return res.json();
  },

  getOneNoteNotebooks: async () => {
    const res = await apiFetch('/data-sources/onenote/notebooks', {
      headers: getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch OneNote notebooks');
    }
    return res.json();
  },

  syncOneNote: async (notebookIds = null) => {
    const res = await apiFetch('/data-sources/onenote/sync', {
      method: 'POST',
      headers: getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ notebook_ids: notebookIds }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'OneNote sync failed');
    }
    return res.json();
  },

  syncOneNoteNotebooks: async (notebookIds = null) => {
    return api.syncOneNote(notebookIds);
  },

  disconnectOneNote: async () => {
    const res = await apiFetch('/data-sources/onenote/disconnect', {
      method: 'POST',
      headers: getHeaders(),
    });
    clearCurrentUserId();
    return res.json();
  },

  // 1-Click Device Login
  startDeviceLogin: async () => {
    const res = await apiFetch('/data-sources/onenote/device-flow/start', {
      headers: getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to initiate device login');
    }
    return res.json();
  },

  completeDeviceLogin: async (sessionId = 'default') => {
    const res = await apiFetch(`/data-sources/onenote/device-flow/complete?session_id=${encodeURIComponent(sessionId)}`, {
      method: 'POST',
      headers: getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Device login verification failed');
    }
    const data = await res.json();
    if (data.status === 'success' && data.user && data.user.id) {
      setCurrentUserId(data.user.id);
    }
    return data;
  },

  // Exchange Auth Code or Redirect URL directly
  exchangeAuthCode: async (codeOrUrl) => {
    const res = await apiFetch('/data-sources/onenote/auth/exchange-code', {
      method: 'POST',
      headers: getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ code: codeOrUrl }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Code exchange failed or code has expired');
    }
    const data = await res.json();
    if (data.status === 'success' && data.user && data.user.id) {
      setCurrentUserId(data.user.id);
    }
    return data;
  },

  // Designs Catalog
  getDesigns: async (params = {}) => {
    const query = new URLSearchParams(params).toString();
    const res = await apiFetch(`/designs?${query}`, {
      headers: getHeaders(),
    });
    const data = await res.json();
    if (data && Array.isArray(data.designs)) {
      data.designs = data.designs.map(d => ({
        ...d,
        image_url: resolveImageUrl(d.image_url)
      }));
    }
    return data;
  },

  clearAllDesigns: async () => {
    const res = await apiFetch('/designs', { 
      method: 'DELETE',
      headers: getHeaders(),
    });
    return res.json();
  },

  // Search History
  getSearchHistory: async () => {
    const res = await apiFetch('/history', {
      headers: getHeaders(),
    });
    const data = await res.json();
    if (data && Array.isArray(data.history)) {
      data.history = data.history.map(h => ({
        ...h,
        query_image_url: resolveImageUrl(h.query_image_url),
        top_match_image_url: resolveImageUrl(h.top_match_image_url),
        query_structural_preview_url: resolveImageUrl(h.query_structural_preview_url)
      }));
    }
    return data;
  },

  clearSearchHistory: async () => {
    const res = await apiFetch('/history', {
      method: 'DELETE',
      headers: getHeaders(),
    });
    return res.json();
  },

  // OneNote & Local File Actions
  openInOneNote: async (designId, mode = 'desktop') => {
    const res = await apiFetch(`/designs/${designId}/open-onenote?mode=${mode}`, {
      method: 'POST',
      headers: getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to open OneNote');
    }
    return res.json();
  },

  openLocalFolder: async (designId) => {
    const res = await apiFetch(`/designs/${designId}/open-local`, {
      method: 'POST',
      headers: getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to open local folder');
    }
    return res.json();
  },

  getDesignLocation: async (designId) => {
    const res = await apiFetch(`/designs/${designId}/location`, {
      headers: getHeaders(),
    });
    return res.json();
  },
};
