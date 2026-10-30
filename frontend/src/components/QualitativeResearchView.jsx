import React, { useState, useEffect } from 'react';
import { 
    FileSearch, Search, FileText, Database, CheckCircle, AlertCircle, 
    Loader2, ArrowRight, BookOpen, Quote, ShieldAlert, Cpu, Sparkles, 
    RefreshCw, Layers, ExternalLink, ChevronRight, Check, Info, FileCheck
} from 'lucide-react';
import { 
    fetchCompanyDocuments, 
    ingestDocument, 
    indexDocument, 
    runQualitativeAnalysis,
    retrieveEvidence
} from '../services/api';

const SUGGESTED_PROMPTS = [
    {
        title: "Competitive Moats & Tech",
        query: "What are the company's proprietary technology platforms, intellectual property, and core competitive advantages that protect its pricing power?"
    },
    {
        title: "Client Concentration",
        query: "What does the report disclose regarding client concentration, top-5 and top-10 client revenue contributions, and multi-year client retention rates?"
    },
    {
        title: "Risks & Contingencies",
        query: "What key operational, legal, environmental, and regulatory risks are disclosed in the MD&A and notes to accounts?"
    },
    {
        title: "Management Outlook",
        query: "Summarize management commentary regarding order book execution, deal pipeline, margin expansion, and capital expenditure priorities."
    }
];

export default function QualitativeResearchView({ initialTicker = 'LT', onSelectTicker, onNavigateReport, onNavigate }) {
    const [ticker, setTicker] = useState(initialTicker);
    const [searchTicker, setSearchTicker] = useState(initialTicker);
    const [activeTab, setActiveTab] = useState('assistant'); // 'assistant' or 'documents'

    // Documents State
    const [documents, setDocuments] = useState([]);
    const [companyMeta, setCompanyMeta] = useState(null);
    const [docsLoading, setDocsLoading] = useState(false);
    const [docsError, setDocsError] = useState(null);
    const [docsWarning, setDocsWarning] = useState(null);

    // Ingestion & Indexing Action State
    const [processingDocId, setProcessingDocId] = useState(null);
    const [actionMessage, setActionMessage] = useState(null);

    // Analysis / Q&A State
    const [question, setQuestion] = useState(SUGGESTED_PROMPTS[0].query);
    const [analyzing, setAnalyzing] = useState(false);
    const [analysisResult, setAnalysisResult] = useState(null);
    const [analysisError, setAnalysisError] = useState(null);
    const [claimFilter, setClaimFilter] = useState('all'); // 'all', 'reported_fact', 'management_statement', 'analytical_interpretation'

    // Load available filings whenever ticker changes
    const loadCompanyDocs = async (targetTicker) => {
        if (!targetTicker) return;
        const clean = targetTicker.trim().toUpperCase().replace(/\.(NS|BO)$/i, '');
        setDocsLoading(true);
        setDocsError(null);
        setDocsWarning(null);
        try {
            const data = await fetchCompanyDocuments(clean);
            setCompanyMeta(data.company || null);
            setDocuments(Array.isArray(data.results) ? data.results : []);
            if (data.warning || data.limit_reached) {
                setDocsWarning(data.warning || "MarketPing's daily free MCP limit is reached (resets at midnight IST). Quantitative analysis remains fully operational.");
            }
        } catch (err) {
            console.error('Error fetching documents:', err);
            const msg = err.message || '';
            if (msg.includes('daily') || msg.includes('limit') || msg.includes('429')) {
                setDocsWarning("MarketPing daily free MCP limit is reached (resets at midnight IST). Quantitative analysis remains fully operational.");
                setDocsError(null);
            } else {
                setDocsError(err.message || 'Unable to retrieve company filings.');
            }
            setDocuments([]);
        } finally {
            setDocsLoading(false);
        }
    };

    useEffect(() => {
        loadCompanyDocs(ticker);
    }, [ticker]);

    const handleSearchSubmit = (e) => {
        e.preventDefault();
        if (searchTicker.trim()) {
            const clean = searchTicker.trim().toUpperCase().replace(/\.(NS|BO)$/i, '');
            setSearchTicker(clean);
            setTicker(clean);
            setAnalysisResult(null);
            setAnalysisError(null);
        }
    };

    const handleSelectPill = (sym) => {
        const clean = sym.trim().toUpperCase().replace(/\.(NS|BO)$/i, '');
        setSearchTicker(clean);
        setTicker(clean);
        setAnalysisResult(null);
        setAnalysisError(null);
    };

    // 1-Click Ingest & Index Handler
    const handleIngestAndIndex = async (doc) => {
        const docId = doc.external_id || doc.id;
        setProcessingDocId(docId);
        setActionMessage({ type: 'info', text: `Ingesting pages for "${doc.title}"...` });

        try {
            // Step 1: Ingest Pages
            await ingestDocument(ticker, docId, { ingestAll: true, maxPages: 50 });
            setActionMessage({ type: 'info', text: `Pages ingested! Chunking and computing vector embeddings...` });

            // Step 2: Index Chunks
            await indexDocument(ticker, docId, { forceReindex: true });
            setActionMessage({ type: 'success', text: `Successfully indexed "${doc.title}" for RAG research!` });

            // Refresh document list
            await loadCompanyDocs(ticker);
        } catch (err) {
            console.error('Failed to ingest/index document:', err);
            const msg = err.message || '';
            if (msg.includes('daily') || msg.includes('limit') || msg.includes('600') || msg.includes('429')) {
                setActionMessage({
                    type: 'error',
                    text: "MarketPing daily free quota reached (600 pages/day). Resets at midnight IST, or switch to mobile hotspot/VPN to get a fresh daily quota immediately."
                });
            } else {
                setActionMessage({ type: 'error', text: err.message || 'Ingestion or indexing failed.' });
            }
        } finally {
            setProcessingDocId(null);
            setTimeout(() => setActionMessage(null), 8000);
        }
    };

    // Execute Qualitative Analysis
    const handleRunAnalysis = async (customQ) => {
        const queryText = (customQ || question).trim();
        if (!queryText) return;
        setAnalyzing(true);
        setAnalysisError(null);

        try {
            const result = await runQualitativeAnalysis(ticker, queryText);
            setAnalysisResult(result);
        } catch (err) {
            console.error('Qualitative analysis failed:', err);
            const msg = err.message || '';
            if (msg.includes('daily') || msg.includes('limit') || msg.includes('429')) {
                setAnalysisError("MarketPing's daily free MCP limit is reached (resets at midnight IST). Local quantitative deep dive analysis remains fully functional.");
            } else {
                setAnalysisError(err.message || 'Qualitative analysis failed. Ensure reports are indexed.');
            }
        } finally {
            setAnalyzing(false);
        }
    };

    const countIndexedDocs = documents.filter(d => (d.indexed_chunks_count > 0 || d.ingestion_status === 'INDEXED')).length;

    // Filter claims
    const filteredClaims = analysisResult?.key_findings?.filter(finding => {
        if (claimFilter === 'all') return true;
        return finding.category === claimFilter;
    }) || [];

    return (
        <div className="space-y-6">
            {/* TOP HEADER & SEARCH BAR */}
            <div className="bg-[#131B2F] border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />
                
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
                    <div>
                        <div className="flex items-center gap-2.5 text-blue-400 font-semibold text-xs tracking-wider uppercase mb-1.5">
                            <BookOpen className="w-4 h-4" />
                            <span>Qualitative Fundamental Research & Filings RAG</span>
                        </div>
                        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
                            <span>{companyMeta?.name || ticker}</span>
                            <span className="text-sm font-mono font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2.5 py-0.5 rounded-md">
                                {companyMeta?.ticker || ticker}
                            </span>
                        </h1>
                        <p className="text-sm text-slate-400 mt-1 max-w-2xl">
                            Analyze corporate disclosures, Annual Reports, 10-Ks, and earnings calls using dense vector retrieval, epistemic claims verification, and traceable citations.
                        </p>
                    </div>

                    {/* Search Input */}
                    <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 max-w-md w-full">
                        <div className="relative flex-1">
                            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                            <input
                                type="text"
                                value={searchTicker}
                                onChange={(e) => setSearchTicker(e.target.value)}
                                placeholder="Enter ticker (e.g. LT, INFY, TCS)"
                                className="w-full bg-[#0A0F1C] border border-slate-700/80 rounded-xl pl-9 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500 placeholder-slate-500 transition-colors"
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={docsLoading || !searchTicker.trim()}
                            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold px-4 py-2 rounded-xl text-sm transition-colors whitespace-nowrap shadow-md cursor-pointer"
                        >
                            Search
                        </button>
                    </form>
                </div>

                {/* Quick Ticker Chips */}
                <div className="flex flex-wrap items-center gap-2 mt-4 pt-4 border-t border-slate-800/60 text-xs">
                    <span className="text-slate-500 font-medium">Quick Companies:</span>
                    {['LT', 'INFY', 'TCS', 'RELIANCE', 'HDFCBANK', 'AAPL'].map((sym) => (
                        <button
                            key={sym}
                            onClick={() => handleSelectPill(sym)}
                            className={`px-2.5 py-1 rounded-md font-mono font-semibold transition-colors cursor-pointer ${
                                ticker === sym
                                    ? 'bg-blue-500 text-white'
                                    : 'bg-slate-800/80 text-slate-300 hover:bg-slate-700 border border-slate-700/50'
                            }`}
                        >
                            {sym}
                        </button>
                    ))}
                    {countIndexedDocs > 0 && (
                        <span className="ml-auto inline-flex items-center gap-1.5 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-md font-medium">
                            <CheckCircle className="w-3.5 h-3.5" />
                            {countIndexedDocs} Indexed Filing{countIndexedDocs > 1 ? 's' : ''} Ready for RAG
                        </span>
                    )}
                </div>
            </div>

            {/* ACTION / NOTIFICATION TOAST */}
            {actionMessage && (
                <div className={`p-4 rounded-xl border flex items-center gap-3 transition-all animate-in fade-in ${
                    actionMessage.type === 'success' 
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                        : actionMessage.type === 'error'
                        ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                        : 'bg-blue-500/10 border-blue-500/30 text-blue-300'
                }`}>
                    {actionMessage.type === 'info' ? (
                        <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" />
                    ) : actionMessage.type === 'success' ? (
                        <CheckCircle className="w-4 h-4 flex-shrink-0 text-emerald-400" />
                    ) : (
                        <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-400" />
                    )}
                    <span className="text-sm font-medium">{actionMessage.text}</span>
                </div>
            )}

            {/* NAVIGATION TABS */}
            <div className="flex border-b border-slate-800 space-x-6">
                <button
                    onClick={() => setActiveTab('assistant')}
                    className={`pb-3 text-sm font-semibold border-b-2 flex items-center gap-2 transition-colors cursor-pointer ${
                        activeTab === 'assistant'
                            ? 'border-blue-500 text-blue-400'
                            : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                >
                    <Sparkles className="w-4 h-4" />
                    <span>Qualitative Research Assistant (RAG Q&A)</span>
                </button>
                <button
                    onClick={() => setActiveTab('documents')}
                    className={`pb-3 text-sm font-semibold border-b-2 flex items-center gap-2 transition-colors cursor-pointer ${
                        activeTab === 'documents'
                            ? 'border-blue-500 text-blue-400'
                            : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                >
                    <Database className="w-4 h-4" />
                    <span>Filings & Document Ingestion ({documents.length})</span>
                </button>
            </div>

            {/* TAB 1: QUALITATIVE RESEARCH ASSISTANT */}
            {activeTab === 'assistant' && (
                <div className="space-y-6">
                    {/* Zero-Index Warning Callout if needed */}
                    {countIndexedDocs === 0 && !docsLoading && (
                        <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                            <div className="flex items-start gap-3">
                                <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                                <div>
                                    <h4 className="text-sm font-bold text-amber-300">No Annual Reports or Filings Indexed Yet for {ticker}</h4>
                                    <p className="text-xs text-slate-300 mt-0.5">
                                        To answer questions on pricing power, competitive moats, or client concentration, ingest and index the company's annual report into the vector database.
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={() => setActiveTab('documents')}
                                className="bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold px-4 py-2 rounded-xl text-xs flex items-center gap-1.5 transition-colors whitespace-nowrap cursor-pointer shadow"
                            >
                                Ingest Filings Now →
                            </button>
                        </div>
                    )}

                    {/* Question Input & Prompt Chips */}
                    <div className="bg-[#131B2F] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                        <div className="flex items-center justify-between">
                            <label className="text-sm font-bold text-white flex items-center gap-2">
                                <FileSearch className="w-4 h-4 text-blue-400" />
                                Research Question
                            </label>
                            <span className="text-xs text-slate-400">Grounded strictly in verified filings</span>
                        </div>

                        <form onSubmit={(e) => { e.preventDefault(); handleRunAnalysis(); }} className="space-y-3">
                            <div className="relative">
                                <textarea
                                    rows={3}
                                    value={question}
                                    onChange={(e) => setQuestion(e.target.value)}
                                    placeholder="Ask anything about the company's moats, customer concentration, pricing power, legal risks, or management outlook..."
                                    className="w-full bg-[#0A0F1C] border border-slate-700/80 rounded-xl p-3.5 text-sm text-white focus:outline-none focus:border-blue-500 placeholder-slate-500 resize-none font-medium leading-relaxed"
                                    disabled={analyzing}
                                />
                            </div>

                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                                <div className="flex flex-wrap items-center gap-1.5">
                                    <span className="text-xs text-slate-500 mr-1">Suggested:</span>
                                    {SUGGESTED_PROMPTS.map((p, idx) => (
                                        <button
                                            key={idx}
                                            type="button"
                                            onClick={() => { setQuestion(p.query); handleRunAnalysis(p.query); }}
                                            className="text-xs bg-[#0A0F1C] hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/60 px-2.5 py-1 rounded-lg transition-colors cursor-pointer"
                                        >
                                            {p.title}
                                        </button>
                                    ))}
                                </div>

                                <button
                                    type="submit"
                                    disabled={analyzing || !question.trim()}
                                    className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-bold px-6 py-2.5 rounded-xl text-sm flex items-center justify-center gap-2 transition-all shadow-md shadow-blue-500/10 cursor-pointer self-end"
                                >
                                    {analyzing ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin" />
                                            <span>Analyzing Filings...</span>
                                        </>
                                    ) : (
                                        <>
                                            <Sparkles className="w-4 h-4" />
                                            <span>Analyze Qualitative Filings</span>
                                        </>
                                    )}
                                </button>
                            </div>
                        </form>
                    </div>

                    {/* Analysis Error Message */}
                    {analysisError && (
                        <div className="bg-rose-500/10 border border-rose-500/30 rounded-2xl p-5 text-rose-300 text-sm flex items-start gap-3">
                            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-400" />
                            <div>
                                <h4 className="font-bold text-rose-200">Analysis Error</h4>
                                <p className="mt-0.5">{analysisError}</p>
                            </div>
                        </div>
                    )}

                    {/* Analysis Results Display */}
                    {analysisResult && !analyzing && (
                        <div className="space-y-6 animate-in fade-in duration-300">
                            {/* Executive Summary Card */}
                            <div className="bg-[#131B2F] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                                    <h3 className="text-base font-bold text-white flex items-center gap-2">
                                        <BookOpen className="w-4 h-4 text-blue-400" />
                                        Executive Qualitative Synthesis
                                    </h3>
                                    {analysisResult.metrics && (
                                        <span className="text-xs font-mono text-slate-400">
                                            Retrieval: {analysisResult.metrics.retrieval_time_ms}ms • Total: {analysisResult.metrics.total_time_ms}ms
                                        </span>
                                    )}
                                </div>
                                <div className="text-slate-200 text-sm leading-relaxed whitespace-pre-wrap bg-[#0A0F1C]/60 p-4 rounded-xl border border-slate-800/60">
                                    {analysisResult.executive_summary}
                                </div>
                            </div>

                            {/* Categorized Epistemic Claims */}
                            {analysisResult.key_findings && analysisResult.key_findings.length > 0 && (
                                <div className="bg-[#131B2F] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
                                        <h3 className="text-base font-bold text-white flex items-center gap-2">
                                            <CheckCircle className="w-4 h-4 text-emerald-400" />
                                            <span>Key Findings & Epistemic Claims ({analysisResult.key_findings.length})</span>
                                        </h3>
                                        {/* Filter pills */}
                                        <div className="flex items-center gap-1.5 text-xs">
                                            {[
                                                { id: 'all', label: 'All' },
                                                { id: 'reported_fact', label: 'Reported Facts' },
                                                { id: 'management_statement', label: 'Management Statements' },
                                                { id: 'analytical_interpretation', label: 'Interpretations' }
                                            ].map((f) => (
                                                <button
                                                    key={f.id}
                                                    onClick={() => setClaimFilter(f.id)}
                                                    className={`px-2.5 py-1 rounded-md transition-colors cursor-pointer font-medium ${
                                                        claimFilter === f.id
                                                            ? 'bg-blue-600 text-white'
                                                            : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                                                    }`}
                                                >
                                                    {f.label}
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="space-y-3">
                                        {filteredClaims.map((item, idx) => (
                                            <div key={idx} className="bg-[#0A0F1C] border border-slate-800 p-4 rounded-xl space-y-2">
                                                <div className="flex items-start justify-between gap-3">
                                                    <p className="text-sm font-semibold text-slate-100 flex-1 leading-snug">
                                                        {item.claim}
                                                    </p>
                                                    <span className={`text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border flex-shrink-0 ${
                                                        item.category === 'reported_fact'
                                                            ? 'bg-blue-500/10 text-blue-400 border-blue-500/30'
                                                            : item.category === 'management_statement'
                                                            ? 'bg-purple-500/10 text-purple-400 border-purple-500/30'
                                                            : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                                                    }`}>
                                                        {item.category.replace('_', ' ')}
                                                    </span>
                                                </div>
                                                {item.quote && (
                                                    <div className="text-xs text-slate-400 italic bg-slate-900/50 border-l-2 border-slate-700 pl-3 py-1 mt-1 flex items-start gap-1.5">
                                                        <Quote className="w-3.5 h-3.5 text-slate-500 flex-shrink-0 mt-0.5" />
                                                        <span>"{item.quote}"</span>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Traceable Citations Section */}
                            {analysisResult.citations && analysisResult.citations.length > 0 && (
                                <div className="bg-[#131B2F] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                                    <h3 className="text-base font-bold text-white flex items-center gap-2 border-b border-slate-800/80 pb-3">
                                        <Layers className="w-4 h-4 text-amber-400" />
                                        Traceable Citations & Page References ({analysisResult.citations.length})
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                        {analysisResult.citations.map((cite, idx) => (
                                            <div key={idx} className="bg-[#0A0F1C] border border-slate-800/80 p-3.5 rounded-xl space-y-1.5">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-xs font-bold text-slate-200 truncate pr-2">
                                                        {cite.document_title}
                                                    </span>
                                                    <span className="text-[11px] font-mono font-bold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded">
                                                        p. {cite.page_start}{cite.page_end !== cite.page_start ? `-${cite.page_end}` : ''}
                                                    </span>
                                                </div>
                                                {cite.section_heading && (
                                                    <div className="text-[11px] text-slate-400 font-medium">
                                                        Section: {cite.section_heading}
                                                    </div>
                                                )}
                                                <div className="text-[10px] text-slate-500 font-mono">
                                                    Chunk ID #{cite.chunk_id} • {cite.fiscal_period || 'Annual Report'}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Risks & Limitations Disclosures */}
                            {((analysisResult.risks_and_uncertainties && analysisResult.risks_and_uncertainties.length > 0) ||
                              (analysisResult.missing_information_and_limitations && analysisResult.missing_information_and_limitations.length > 0)) && (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {analysisResult.risks_and_uncertainties?.length > 0 && (
                                        <div className="bg-[#131B2F] border border-slate-800 rounded-2xl p-5 space-y-2.5">
                                            <h4 className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center gap-1.5">
                                                <ShieldAlert className="w-4 h-4" />
                                                Disclosed Risks & Uncertainties
                                            </h4>
                                            <ul className="text-xs text-slate-300 space-y-1.5 list-disc pl-4">
                                                {analysisResult.risks_and_uncertainties.map((r, i) => (
                                                    <li key={i}>{r}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                    {analysisResult.missing_information_and_limitations?.length > 0 && (
                                        <div className="bg-[#131B2F] border border-slate-800 rounded-2xl p-5 space-y-2.5">
                                            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                                                <Info className="w-4 h-4 text-blue-400" />
                                                Omitted / Missing Information
                                            </h4>
                                            <ul className="text-xs text-slate-400 space-y-1.5 list-disc pl-4">
                                                {analysisResult.missing_information_and_limitations.map((m, i) => (
                                                    <li key={i}>{m}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* TAB 2: FILINGS & DOCUMENT INGESTION */}
            {activeTab === 'documents' && (
                <div className="space-y-6">
                    <div className="bg-[#131B2F] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-4">
                            <div>
                                <h3 className="text-base font-bold text-white flex items-center gap-2">
                                    <Database className="w-4 h-4 text-blue-400" />
                                    Available Company Filings ({documents.length})
                                </h3>
                                <p className="text-xs text-slate-400 mt-0.5">
                                    Ingest annual reports and earnings transcripts to feed the semantic vector database.
                                </p>
                            </div>
                            <button
                                onClick={() => loadCompanyDocs(ticker)}
                                disabled={docsLoading}
                                className="inline-flex items-center gap-1.5 text-xs text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 px-3 py-1.5 rounded-lg font-semibold transition-colors cursor-pointer self-start sm:self-auto"
                            >
                                <RefreshCw className={`w-3.5 h-3.5 ${docsLoading ? 'animate-spin' : ''}`} />
                                Refresh Filings
                            </button>
                        </div>

                        {docsWarning && (
                            <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-200 text-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
                                <div className="flex items-start gap-3">
                                    <Info className="w-5 h-5 flex-shrink-0 text-amber-400 mt-0.5 sm:mt-0" />
                                    <div>
                                        <p className="font-semibold text-amber-300">MarketPing Daily Free Quota</p>
                                        <p className="text-xs text-amber-200/80 mt-0.5">{docsWarning}</p>
                                    </div>
                                </div>
                                {onNavigate && (
                                    <button
                                        type="button"
                                        onClick={() => onNavigate('dashboard')}
                                        className="px-3 py-1.5 bg-amber-600/80 hover:bg-amber-600 text-white rounded-lg text-xs font-semibold whitespace-nowrap transition cursor-pointer self-stretch sm:self-auto text-center"
                                    >
                                        Open Quantitative Analysis
                                    </button>
                                )}
                            </div>
                        )}

                        {docsLoading ? (
                            <div className="py-12 flex flex-col items-center justify-center gap-3 text-slate-400">
                                <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                                <span className="text-sm">Discovering corporate filings from MarketPing MCP...</span>
                            </div>
                        ) : docsError ? (
                            <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-sm flex items-center gap-3">
                                <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-400" />
                                <span>{docsError}</span>
                            </div>
                        ) : documents.length === 0 ? (
                            <div className="py-12 text-center text-slate-400 space-y-2">
                                <FileText className="w-8 h-8 mx-auto text-slate-600" />
                                <p className="text-sm font-semibold text-slate-300">No filings discovered yet for {ticker}</p>
                                <p className="text-xs text-slate-500">Ensure ticker is listed or check connection with MarketPing MCP.</p>
                            </div>
                        ) : (
                            <div className="divide-y divide-slate-800/60">
                                {documents.map((doc) => {
                                    const docId = doc.external_id || doc.id;
                                    const isIndexed = doc.indexed_chunks_count > 0 || doc.ingestion_status === 'INDEXED';
                                    const isIngested = doc.ingested_pages_count > 0;
                                    const isProcessing = processingDocId === docId;

                                    return (
                                        <div key={docId} className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-4 group">
                                            <div className="space-y-1 max-w-2xl">
                                                <div className="flex flex-wrap items-center gap-2">
                                                    <span className="text-sm font-bold text-white group-hover:text-blue-400 transition-colors">
                                                        {doc.title}
                                                    </span>
                                                    <span className="text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                                                        {doc.doc_type?.replace('_', ' ') || 'Report'}
                                                    </span>
                                                    {doc.fiscal_period && (
                                                        <span className="text-[11px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                                                            {doc.fiscal_period}
                                                        </span>
                                                    )}
                                                </div>

                                                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                                                    <span>Pages: {doc.ingested_pages_count || 0} / {doc.total_pages || 'N/A'}</span>
                                                    <span>•</span>
                                                    <span>Indexed Chunks: <strong className="text-slate-200">{doc.indexed_chunks_count || 0}</strong></span>
                                                    {doc.filing_date && (
                                                        <>
                                                            <span>•</span>
                                                            <span>Filing Date: {doc.filing_date}</span>
                                                        </>
                                                    )}
                                                </div>
                                            </div>

                                            {/* Status & Action */}
                                            <div className="flex items-center gap-3 flex-shrink-0">
                                                {isIndexed ? (
                                                    <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg">
                                                        <CheckCircle className="w-4 h-4 text-emerald-400" />
                                                        Indexed for RAG
                                                    </span>
                                                ) : isIngested ? (
                                                    <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-400 bg-blue-500/10 border border-blue-500/20 px-3 py-1.5 rounded-lg">
                                                        <FileCheck className="w-4 h-4 text-blue-400" />
                                                        Ingested (Needs Indexing)
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-slate-400 bg-slate-800/80 px-2.5 py-1 rounded-lg">
                                                        Discovered
                                                    </span>
                                                )}

                                                <button
                                                    onClick={() => handleIngestAndIndex(doc)}
                                                    disabled={isProcessing}
                                                    className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
                                                        isIndexed
                                                            ? 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700'
                                                            : 'bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-500/20'
                                                    } disabled:opacity-50`}
                                                >
                                                    {isProcessing ? (
                                                        <>
                                                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                                            <span>Processing...</span>
                                                        </>
                                                    ) : isIndexed ? (
                                                        <>
                                                            <RefreshCw className="w-3.5 h-3.5" />
                                                            <span>Re-Index Chunks</span>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <Database className="w-3.5 h-3.5" />
                                                            <span>1-Click Ingest & Index</span>
                                                        </>
                                                    )}
                                                </button>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* BOTTOM BRIDGE TO FULL 15-SECTION INSTITUTIONAL REPORT */}
            <div className="bg-gradient-to-r from-blue-900/30 via-slate-900/40 to-slate-900/30 border border-blue-500/20 rounded-2xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-xl">
                <div>
                    <h4 className="text-base font-bold text-white flex items-center gap-2">
                        <FileText className="w-4 h-4 text-blue-400" />
                        Compile Full 15-Section Research Dossier
                    </h4>
                    <p className="text-xs text-slate-300 mt-0.5">
                        Combine quantitative financial metrics (ROE, DCF, Multiples) with these indexed qualitative disclosures into a publication-ready PDF.
                    </p>
                </div>
                <button
                    onClick={() => onNavigateReport && onNavigateReport(ticker)}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-bold px-5 py-2.5 rounded-xl text-xs flex items-center gap-2 transition-colors whitespace-nowrap shadow-lg shadow-blue-500/20 cursor-pointer"
                >
                    <span>Generate Institutional Report</span>
                    <ArrowRight className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
}
