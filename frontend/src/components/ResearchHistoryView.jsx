import React, { useState, useEffect } from 'react';
import { 
    History, Search, Filter, Trash2, ArrowRight, ExternalLink, 
    AlertCircle, Clock, CheckCircle, Database, FileText, Brain, RefreshCw
} from 'lucide-react';
import { fetchResearchHistory, deleteResearchActivity } from '../services/api';

export default function ResearchHistoryView({ onSelectTicker, onNavigate }) {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filterTicker, setFilterTicker] = useState('');
    const [filterType, setFilterType] = useState('all');

    const loadHistory = async () => {
        setLoading(true);
        setError(null);
        try {
            const params = {};
            if (filterTicker.trim()) params.ticker = filterTicker.trim();
            if (filterType !== 'all') params.research_type = filterType;

            const res = await fetchResearchHistory(params);
            // Paginated response or list
            const items = res?.results ? res.results : (Array.isArray(res) ? res : []);
            setHistory(items);
        } catch (err) {
            console.error('Failed to load research history:', err);
            setError(err.message || 'Unable to retrieve research history.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadHistory();
    }, [filterType]);

    const handleSearchSubmit = (e) => {
        e.preventDefault();
        loadHistory();
    };

    const handleDelete = async (id, ticker) => {
        if (!window.confirm(`Delete research record for ${ticker}?`)) return;
        try {
            await deleteResearchActivity(id);
            setHistory((prev) => prev.filter((item) => item.id !== id));
        } catch (err) {
            alert(`Failed to delete history record: ${err.message}`);
        }
    };

    const getTypeBadge = (type) => {
        switch (type) {
            case 'quantitative':
                return {
                    label: 'Quantitative Valuation',
                    icon: Database,
                    cls: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                };
            case 'qualitative':
                return {
                    label: 'Qualitative SEC Evidence',
                    icon: Brain,
                    cls: 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                };
            case 'report':
                return {
                    label: 'Institutional Report',
                    icon: FileText,
                    cls: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30'
                };
            default:
                return {
                    label: type,
                    icon: History,
                    cls: 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                };
        }
    };

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-in fade-in">
            {/* HEADER */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <History className="w-6 h-6 text-emerald-400" />
                        <h1 className="text-2xl font-bold text-white tracking-tight">Research History & Audit Trail</h1>
                    </div>
                    <p className="text-slate-400 text-sm">
                        Comprehensive ledger of all valuation computations, qualitative SEC filings inquiries, and institutional reports.
                    </p>
                </div>
                <button
                    onClick={loadHistory}
                    className="inline-flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-[#131B2F] border border-slate-700 px-3 py-2 rounded-lg font-semibold transition-colors"
                >
                    <RefreshCw className="w-3.5 h-3.5" /> Refresh
                </button>
            </div>

            {/* CONTROLS BAR */}
            <div className="flex flex-col md:flex-row items-center justify-between gap-4 bg-[#131B2F] border border-slate-800 p-4 rounded-xl shadow-sm">
                <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
                    <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                    <input
                        type="text"
                        value={filterTicker}
                        onChange={(e) => setFilterTicker(e.target.value)}
                        placeholder="Search ticker (e.g. AAPL)..."
                        className="w-full bg-[#0A0F1C] border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500 placeholder-slate-500 uppercase font-mono"
                    />
                </form>

                <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto">
                    <span className="text-xs text-slate-400 font-semibold flex items-center gap-1 mr-1 flex-shrink-0">
                        <Filter className="w-3.5 h-3.5" /> Type:
                    </span>
                    {[
                        { key: 'all', label: 'All Activities' },
                        { key: 'quantitative', label: 'Quantitative' },
                        { key: 'qualitative', label: 'Qualitative RAG' },
                        { key: 'report', label: 'Reports' }
                    ].map((tab) => (
                        <button
                            key={tab.key}
                            onClick={() => setFilterType(tab.key)}
                            className={`text-xs px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition-colors ${
                                filterType === tab.key
                                    ? 'bg-blue-600 text-white shadow-sm'
                                    : 'bg-[#0A0F1C] text-slate-400 hover:text-white border border-slate-800'
                            }`}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* ERROR */}
            {error && (
                <div className="bg-red-950/40 border border-red-800/80 rounded-xl p-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                        <p className="text-sm text-red-200">{error}</p>
                    </div>
                    <button
                        onClick={loadHistory}
                        className="text-xs text-red-300 hover:text-white font-semibold px-3 py-1 bg-red-900/40 rounded border border-red-700/60"
                    >
                        Retry
                    </button>
                </div>
            )}

            {/* TABLE / LIST */}
            {loading ? (
                <div className="text-center py-16">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-emerald-500 border-t-transparent mb-3"></div>
                    <p className="text-slate-400 text-sm">Loading research history records...</p>
                </div>
            ) : history.length === 0 ? (
                <div className="text-center py-16 bg-[#131B2F] border border-slate-800 rounded-2xl p-8">
                    <History className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                    <h3 className="text-lg font-bold text-white mb-1">No Research Activity Found</h3>
                    <p className="text-slate-400 text-sm max-w-md mx-auto mb-5">
                        {filterTicker || filterType !== 'all'
                            ? 'No activities matched your current filters. Try resetting your search filters.'
                            : 'Every time you analyze a company, perform qualitative evidence retrieval, or generate an institutional report, it will be automatically logged here.'}
                    </p>
                    <button
                        onClick={() => {
                            setFilterTicker('');
                            setFilterType('all');
                        }}
                        className="text-xs text-blue-400 hover:text-blue-300 font-semibold underline"
                    >
                        Reset filters
                    </button>
                </div>
            ) : (
                <div className="bg-[#131B2F] border border-slate-800 rounded-xl overflow-hidden shadow-sm">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr className="border-b border-slate-800 bg-[#0A0F1C]/60 text-slate-400 text-xs font-semibold uppercase tracking-wider">
                                    <th className="py-3.5 px-4">Company</th>
                                    <th className="py-3.5 px-4">Research Type</th>
                                    <th className="py-3.5 px-4">Key Findings / Summary</th>
                                    <th className="py-3.5 px-4">Timestamp</th>
                                    <th className="py-3.5 px-4">Status</th>
                                    <th className="py-3.5 px-4 text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/80 text-sm">
                                {history.map((item) => {
                                    const badge = getTypeBadge(item.research_type);
                                    const IconComp = badge.icon;
                                    return (
                                        <tr key={item.id} className="hover:bg-slate-850/50 transition-colors">
                                            <td className="py-4 px-4">
                                                <div className="flex items-center gap-2">
                                                    <span className="font-bold text-white tracking-wide">
                                                        {item.ticker}
                                                    </span>
                                                    <span className="text-xs text-slate-400 truncate max-w-[140px]">
                                                        {item.company_name}
                                                    </span>
                                                </div>
                                            </td>

                                            <td className="py-4 px-4">
                                                <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border ${badge.cls}`}>
                                                    <IconComp className="w-3 h-3" />
                                                    {badge.label}
                                                </span>
                                            </td>

                                            <td className="py-4 px-4 text-xs text-slate-300 max-w-xs">
                                                {item.summary_data && Object.keys(item.summary_data).length > 0 ? (
                                                    <div className="space-y-0.5">
                                                        {item.summary_data.passed_count !== undefined && (
                                                            <div>Principles: <span className="font-semibold text-emerald-400">{item.summary_data.passed_count} Passed</span> / {item.summary_data.failed_count} Flagged</div>
                                                        )}
                                                        {item.summary_data.dcf_fair_value && (
                                                            <div>DCF Fair Value: <span className="font-mono font-semibold text-blue-400">\${item.summary_data.dcf_fair_value}</span></div>
                                                        )}
                                                        {item.summary_data.page_count && (
                                                            <div>Report Size: <span className="font-semibold text-indigo-400">{item.summary_data.page_count} Pages</span></div>
                                                        )}
                                                        {item.summary_data.notes && (
                                                            <div className="text-slate-400 italic">{item.summary_data.notes}</div>
                                                        )}
                                                    </div>
                                                ) : (
                                                    <span className="text-slate-500 italic">Completed pipeline analysis</span>
                                                )}
                                            </td>

                                            <td className="py-4 px-4 text-xs text-slate-400 font-medium whitespace-nowrap">
                                                <div className="flex items-center gap-1.5">
                                                    <Clock className="w-3.5 h-3.5 text-slate-500" />
                                                    {new Date(item.created_at).toLocaleDateString([], {
                                                        month: 'short',
                                                        day: 'numeric',
                                                        year: 'numeric',
                                                        hour: '2-digit',
                                                        minute: '2-digit'
                                                    })}
                                                </div>
                                            </td>

                                            <td className="py-4 px-4">
                                                <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-400">
                                                    <CheckCircle className="w-3.5 h-3.5" /> Completed
                                                </span>
                                            </td>

                                            <td className="py-4 px-4 text-right whitespace-nowrap">
                                                <div className="flex items-center justify-end gap-2">
                                                    <button
                                                        onClick={() => {
                                                            if (onSelectTicker) onSelectTicker(item.ticker);
                                                            if (onNavigate) {
                                                                if (item.research_type === 'report') onNavigate('my-reports');
                                                                else onNavigate('single');
                                                            }
                                                        }}
                                                        className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 font-semibold px-2.5 py-1 bg-blue-500/10 hover:bg-blue-500/20 rounded border border-blue-500/20 transition-colors"
                                                    >
                                                        Revisit <ArrowRight className="w-3 h-3" />
                                                    </button>
                                                    <button
                                                        onClick={() => handleDelete(item.id, item.ticker)}
                                                        className="text-slate-500 hover:text-red-400 p-1.5 rounded hover:bg-slate-800 transition-colors"
                                                        title="Delete activity record"
                                                    >
                                                        <Trash2 className="w-3.5 h-3.5" />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}