const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export const getAuthHeaders = () => {
    const headers = { 'Content-Type': 'application/json' };
    const token = typeof localStorage !== 'undefined' ? localStorage.getItem('finlytics_token') : null;
    if (token) {
        headers['Authorization'] = `Token ${token}`;
    }
    return headers;
};

export const analyzeCompany = async (ticker) => {
    const res = await fetch(`${BASE_URL}/analyze`, {
        method: 'POST',
        headers: getAuthHeaders(),
        credentials: 'include',
        body: JSON.stringify({ ticker })
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to analyze company.');
    }
    return res.json();
};

export const fetchPrinciples = async () => {
    const res = await fetch(`${BASE_URL}/principles`, {
        headers: getAuthHeaders(),
        credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to fetch principles');
    return res.json();
};

export const updatePrinciple = async (identifier, threshold) => {
    const res = await fetch(`${BASE_URL}/principles/${identifier}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        credentials: 'include',
        body: JSON.stringify({ threshold: parseFloat(threshold) })
    });
    if (!res.ok) throw new Error('Failed to update principle');
    return res.json();
};

export const askFinolitics = async (context, question) => {
    const res = await fetch(`${BASE_URL}/ask`, {
        method: 'POST',
        headers: getAuthHeaders(),
        credentials: 'include',
        body: JSON.stringify({ context, question })
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to ask question.');
    }
    return res.json();
};

export const compareCompanies = async (tickers) => {
    const res = await fetch(`${BASE_URL}/compare`, {
        method: 'POST',
        headers: getAuthHeaders(),
        credentials: 'include',
        body: JSON.stringify({ tickers })
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to compare companies.');
    }
    return res.json();
};

// -------------------------------------------------------------
// 15-Section Persistent Research Dossier APIs
// -------------------------------------------------------------

export const fetchReportsList = async (params = {}) => {
    const query = new URLSearchParams();
    if (typeof params === 'string') {
        if (params) query.append('ticker', params);
    } else if (params && typeof params === 'object') {
        if (params.ticker) query.append('ticker', params.ticker);
        if (params.status && params.status !== 'all') query.append('status', params.status);
        if (params.page) query.append('page', params.page);
    }
    const queryString = query.toString();
    const url = queryString ? `${BASE_URL}/reports?${queryString}` : `${BASE_URL}/reports`;
    const res = await fetch(url, {
        headers: getAuthHeaders(),
        credentials: 'include',
    });
    if (!res.ok) throw new Error('Failed to fetch reports list');
    const data = await res.json();
    return data;
};

export const createResearchReport = async (ticker, reportTitle = '') => {
    const payload = { ticker: ticker.trim().toUpperCase() };
    if (reportTitle) payload.report_title = reportTitle;

    const res = await fetch(`${BASE_URL}/reports/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        credentials: 'include',
        body: JSON.stringify(payload)
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to generate 15-section research report.');
    }
    return res.json();
};

export const fetchReportDetail = async (reportId) => {
    const res = await fetch(`${BASE_URL}/reports/${reportId}/`, {
        headers: getAuthHeaders(),
        credentials: 'include',
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to fetch report detail');
    }
    return res.json();
};

export const fetchReportStatus = async (reportId) => {
    const res = await fetch(`${BASE_URL}/reports/${reportId}/status/`);
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to check report status');
    }
    return res.json();
};

export const downloadReportPdf = async (reportId, ticker = 'Company') => {
    const res = await fetch(`${BASE_URL}/reports/${reportId}/download/`);
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to download report PDF');
    }
    const blob = await res.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = `${ticker}_Institutional_Report.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
    return true;
};

export const deleteReport = async (reportId) => {
    const res = await fetch(`${BASE_URL}/reports/${reportId}/`, {
        method: 'DELETE'
    });
    if (!res.ok && res.status !== 204) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to delete report');
    }
    return true;
};

export const fetchSubscriptionStatus = async () => {
    const res = await fetch(`${BASE_URL}/subscription/status/`);
    if (!res.ok) throw new Error('Failed to fetch subscription status');
    return res.json();
};

export const getReportHtmlUrl = (reportId) => `${BASE_URL}/reports/${reportId}/html`;
export const getReportMarkdownUrl = (reportId) => `${BASE_URL}/reports/${reportId}/markdown`;

// Qualitative RAG Endpoints
export const fetchCompanyDocuments = async (ticker, docType = null) => {
    const cleanTicker = ticker.trim().toUpperCase().replace(/\.(NS|BO)$/i, '');
    const query = docType ? `?doc_type=${encodeURIComponent(docType)}` : '';
    const res = await fetch(`${BASE_URL}/companies/${cleanTicker}/documents/available/${query}`, {
        headers: getAuthHeaders(),
        credentials: 'include',
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.error?.message || errorData.detail || 'Failed to fetch available company documents.');
    }
    return res.json();
};

export const ingestDocument = async (ticker, documentId, options = {}) => {
    const cleanTicker = ticker.trim().toUpperCase().replace(/\.(NS|BO)$/i, '');
    const res = await fetch(`${BASE_URL}/companies/${cleanTicker}/documents/${documentId}/ingest/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        credentials: 'include',
        body: JSON.stringify({
            ingest_all: options.ingestAll ?? true,
            max_pages: options.maxPages ?? 50
        })
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.error?.message || errorData.detail || 'Failed to ingest document pages.');
    }
    return res.json();
};

export const indexDocument = async (ticker, documentId, options = {}) => {
    const cleanTicker = ticker.trim().toUpperCase().replace(/\.(NS|BO)$/i, '');
    const res = await fetch(`${BASE_URL}/companies/${cleanTicker}/documents/${documentId}/index/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        credentials: 'include',
        body: JSON.stringify({
            force_reindex: options.forceReindex ?? false,
            target_chunk_chars: 1000,
            overlap_chars: 150
        })
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.error?.message || errorData.detail || 'Failed to index document.');
    }
    return res.json();
};

export const runQualitativeAnalysis = async (ticker, question, options = {}) => {
    const cleanTicker = ticker.trim().toUpperCase().replace(/\.(NS|BO)$/i, '');
    const res = await fetch(`${BASE_URL}/research/analyze/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        credentials: 'include',
        body: JSON.stringify({
            ticker: cleanTicker,
            question: question.trim(),
            top_k: options.topK || 8,
            min_score: options.minScore || 0.15,
            document_types: options.documentTypes || [],
            fiscal_periods: options.fiscalPeriods || []
        })
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.error?.message || errorData.detail || 'Failed to run qualitative analysis.');
    }
    return res.json();
};

export const retrieveEvidence = async (ticker, question, options = {}) => {
    const cleanTicker = ticker.trim().toUpperCase().replace(/\.(NS|BO)$/i, '');
    const res = await fetch(`${BASE_URL}/research/retrieve/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        credentials: 'include',
        body: JSON.stringify({
            ticker: cleanTicker,
            question: question.trim(),
            top_k: options.topK || 5,
            min_score: options.minScore || 0.10
        })
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.error?.message || errorData.detail || 'Failed to retrieve evidence.');
    }
    return res.json();
};

// -------------------------------------------------------------
// Prompt 6: Dashboard, Watchlist, Research History, and Auth APIs
// -------------------------------------------------------------



export const fetchUserDashboard = async () => {
    const res = await fetch(`${BASE_URL}/dashboard/`, {
        headers: getAuthHeaders(),
        credentials: 'include',
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to fetch dashboard data.');
    }
    return res.json();
};

export const fetchWatchlist = async (query = '') => {
    const q = query ? `?query=${encodeURIComponent(query)}` : '';
    const res = await fetch(`${BASE_URL}/watchlist/${q}`, {
        headers: getAuthHeaders(),
        credentials: 'include',
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to fetch watchlist.');
    }
    return res.json();
};

export const addToWatchlist = async (ticker, companyName = '', sector = '', notes = '') => {
    const res = await fetch(`${BASE_URL}/watchlist/`, {
        method: 'POST',
        headers: getAuthHeaders(),
        credentials: 'include',
        body: JSON.stringify({
            ticker: ticker.trim().toUpperCase(),
            company_name: companyName,
            sector: sector,
            notes: notes,
        })
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to add company to watchlist.');
    }
    return res.json();
};

export const removeFromWatchlist = async (identifier) => {
    const res = await fetch(`${BASE_URL}/watchlist/${identifier}/`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
        credentials: 'include',
    });
    if (!res.ok && res.status !== 204) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to remove company from watchlist.');
    }
    return true;
};

export const checkWatchlist = async (ticker) => {
    const res = await fetch(`${BASE_URL}/watchlist/check/?ticker=${encodeURIComponent(ticker)}`, {
        headers: getAuthHeaders(),
        credentials: 'include',
    });
    if (!res.ok) return { ticker, is_saved: false };
    return res.json();
};

export const fetchResearchHistory = async (params = {}) => {
    const query = new URLSearchParams();
    if (params.ticker) query.append('ticker', params.ticker);
    if (params.research_type) query.append('research_type', params.research_type);
    if (params.page) query.append('page', params.page);

    const qs = query.toString() ? `?${query.toString()}` : '';
    const res = await fetch(`${BASE_URL}/history/${qs}`, {
        headers: getAuthHeaders(),
        credentials: 'include',
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to fetch research history.');
    }
    return res.json();
};

export const deleteResearchActivity = async (id) => {
    const res = await fetch(`${BASE_URL}/history/${id}/`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
        credentials: 'include',
    });
    if (!res.ok && res.status !== 204) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to delete research activity.');
    }
    return true;
};

export const registerUser = async (username, password, confirmPassword) => {
    const res = await fetch(`${BASE_URL}/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
            username: username.trim(),
            password: password,
            confirm_password: confirmPassword,
        })
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        let message = 'Registration failed. Please check your information.';
        if (errorData.username) {
            message = Array.isArray(errorData.username) ? errorData.username[0] : errorData.username;
        } else if (errorData.confirm_password) {
            message = Array.isArray(errorData.confirm_password) ? errorData.confirm_password[0] : errorData.confirm_password;
        } else if (errorData.password) {
            message = Array.isArray(errorData.password) ? errorData.password[0] : errorData.password;
        } else if (errorData.detail) {
            message = errorData.detail;
        }
        throw new Error(message);
    }
    return res.json();
};

export const loginUser = async (username, password) => {
    const res = await fetch(`${BASE_URL}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username, password })
    });
    if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Login failed. Please check your credentials.');
    }
    const data = await res.json();
    if (data.token) {
        localStorage.setItem('finlytics_token', data.token);
    }
    return data;
};

export const logoutUser = async () => {
    try {
        await fetch(`${BASE_URL}/auth/logout/`, {
            method: 'POST',
            headers: getAuthHeaders(),
            credentials: 'include',
        });
    } finally {
        localStorage.removeItem('finlytics_token');
    }
    return true;
};

export const fetchCurrentUser = async () => {
    const res = await fetch(`${BASE_URL}/auth/user/`, {
        headers: getAuthHeaders(),
        credentials: 'include',
    });
    if (!res.ok) return { is_authenticated: false, user: null };
    return res.json();
};
