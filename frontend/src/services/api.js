const API_BASE = '/api';

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

export const getCleanOneNoteUrl = (itemOrUrl, designId = null) => {
  const id = (typeof itemOrUrl === 'object' && itemOrUrl) 
    ? (itemOrUrl.id || itemOrUrl.design_id || itemOrUrl.top_match_id) 
    : designId;

  if (id) {
    return `/api/designs/${id}/open-onenote?mode=desktop`;
  }
  if (typeof itemOrUrl === 'object' && itemOrUrl && itemOrUrl.onenote_client_url) {
    return itemOrUrl.onenote_client_url;
  }
  return 'onenote:';
};

export const getCleanOneNoteWebUrl = (itemOrUrl, designId = null) => {
  if (typeof itemOrUrl === 'object' && itemOrUrl && itemOrUrl.onenote_web_url) {
    return itemOrUrl.onenote_web_url;
  }
  const id = (typeof itemOrUrl === 'object' && itemOrUrl) 
    ? (itemOrUrl.id || itemOrUrl.design_id || itemOrUrl.top_match_id) 
    : designId;

  if (id) {
    return `/api/designs/${id}/open-onenote?mode=web`;
  }
  return 'https://www.onenote.com';
};

export const getCleanOneNoteClientUrl = (itemOrUrl, designId = null) => {
  if (typeof itemOrUrl === 'object' && itemOrUrl) {
    if (itemOrUrl.onenote_client_url && itemOrUrl.onenote_client_url.startsWith('onenote:')) {
      return itemOrUrl.onenote_client_url;
    }
    const id = itemOrUrl.id || itemOrUrl.design_id || itemOrUrl.top_match_id || designId;
    if (id) {
      return `/api/designs/${id}/open-onenote?mode=desktop`;
    }
  }
  if (typeof itemOrUrl === 'string' && itemOrUrl.startsWith('onenote:')) {
    return itemOrUrl;
  }
  if (designId) {
    return `/api/designs/${designId}/open-onenote?mode=desktop`;
  }
  return 'onenote:';
};

export const api = {
  // Search with real uploaded saree image
  searchByImage: async (file, threshold = 0.82, topK = 6) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('threshold', threshold.toString());
    formData.append('top_k', topK.toString());
    const res = await fetch(`${API_BASE}/search/upload`, {
      method: 'POST',
      headers: getHeaders(),
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Search request failed');
    }
    return res.json();
  },

  // OneNote & Data Sources Status
  getOneNoteStatus: async () => {
    const res = await fetch(`${API_BASE}/data-sources/onenote/status`, {
      headers: getHeaders(),
    });
    const data = await res.json();
    if (data && data.user_id && !getCurrentUserId()) {
      setCurrentUserId(data.user_id);
    }
    return data;
  },

  getOneNoteAuthUrl: async () => {
    const res = await fetch(`${API_BASE}/data-sources/onenote/auth/url`, {
      headers: getHeaders(),
    });
    return res.json();
  },

  getOneNoteNotebooks: async () => {
    const res = await fetch(`${API_BASE}/data-sources/onenote/notebooks`, {
      headers: getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch OneNote notebooks');
    }
    return res.json();
  },

  syncOneNote: async (notebookIds = null) => {
    const res = await fetch(`${API_BASE}/data-sources/onenote/sync`, {
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

  disconnectOneNote: async () => {
    const res = await fetch(`${API_BASE}/data-sources/onenote/disconnect`, {
      method: 'POST',
      headers: getHeaders(),
    });
    clearCurrentUserId();
    return res.json();
  },

  // 1-Click Device Login
  startDeviceLogin: async () => {
    const res = await fetch(`${API_BASE}/data-sources/onenote/device-flow/start`, {
      headers: getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to initiate device login');
    }
    return res.json();
  },

  completeDeviceLogin: async (sessionId = 'default') => {
    const res = await fetch(`${API_BASE}/data-sources/onenote/device-flow/complete?session_id=${encodeURIComponent(sessionId)}`, {
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

  // Designs Catalog
  getDesigns: async (params = {}) => {
    const query = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/designs?${query}`, {
      headers: getHeaders(),
    });
    return res.json();
  },

  clearAllDesigns: async () => {
    const res = await fetch(`${API_BASE}/designs`, { 
      method: 'DELETE',
      headers: getHeaders(),
    });
    return res.json();
  },

  // Search History
  getSearchHistory: async () => {
    const res = await fetch(`${API_BASE}/history`, {
      headers: getHeaders(),
    });
    return res.json();
  },

  clearSearchHistory: async () => {
    const res = await fetch(`${API_BASE}/history`, {
      method: 'DELETE',
      headers: getHeaders(),
    });
    return res.json();
  },

  // OneNote & Local File Actions
  openInOneNote: async (designId, mode = 'desktop') => {
    const res = await fetch(`${API_BASE}/designs/${designId}/open-onenote?mode=${mode}`, {
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
    const res = await fetch(`${API_BASE}/designs/${designId}/open-local`, {
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
    const res = await fetch(`${API_BASE}/designs/${designId}/location`, {
      headers: getHeaders(),
    });
    return res.json();
  },
};
