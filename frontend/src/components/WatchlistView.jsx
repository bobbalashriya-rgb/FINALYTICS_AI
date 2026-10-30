import React, { useState, useEffect } from 'react';
import { 
    Bookmark, Search, Plus, Trash2, ExternalLink, AlertCircle, 
    Check, Building2, TrendingUp, RefreshCw, X, ArrowRight, FileText
} from 'lucide-react';
import { fetchWatchlist, addToWatchlist, removeFromWatchlist } from '../services/api';
import { searchDirectory } from '../data/companyDirectory';

export default function WatchlistView({ onSelectTicker, onNavigate, onGenerateReport }) {
    const [watchlist, setWatchlist] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filterQuery, setFilterQuery] = useState('');
    
    // Add Company Modal / Form State
    const [showAddModal, setShowAddModal] = useState(false);
    const [newTicker, setNewTicker] = useState('');
    const [newCompanyName, setNewCompanyName] = useState('');
    const [newSector, setNewSector] = useState('');
    const [newNotes, setNewNotes] = useState('');
    const [addError, setAddError] = useState(null);
    const [adding, setAdding] = useState(false);
    const [suggestions, setSuggestions] = useState([]);

    const loadWatchlist = async (search = '') => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchWatchlist(search);
            setWatchlist(Array.isArray(data) ? data : []);
        } catch (err) {
            console.error('Failed to load watchlist:', err);
            setError(err.message || 'Unable to retrieve your saved companies.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadWatchlist(filterQuery);
    }, [filterQuery]);

    const handleTickerInput = (val) => {
        setNewTicker(val);
        if (val.trim().length >= 1) {
            const matches = searchDirectory(val).slice(0, 5);
            setSuggestions(matches);
        } else {
            setSuggestions([]);
        }
    };

    const handleSelectSuggestion = (item) => {
        setNewTicker(item.ticker);
        setNewCompanyName(item.name);
        setNewSector(item.sector || '');
        setSuggestions([]);
    };

    const handleAddCompany = async (e) => {
        e.preventDefault();
        if (!newTicker.trim()) return;

        setAdding(true);
        setAddError(null);
        try {
            await addToWatchlist(
                newTicker.trim().toUpperCase(),
                newCompanyName.trim(),
                newSector.trim(),
                newNotes.trim()
            );
            // Reset modal and reload
            setNewTicker('');
            setNewCompanyName('');
            setNewSector('');
            setNewNotes('');
            setShowAddModal(false);
            loadWatchlist();
        } catch (err) {
            setAddError(err.message || 'Failed to save company.');
        } finally {
            setAdding(false);
        }
    };

    const handleQuickAdd = async (ticker, name = '', sector = '') => {
        try {
            await addToWatchlist(ticker, name, sector, 'Added from popular suggestions');
            loadWatchlist();
        } catch (err) {
            alert(err.message || 'Could not add company');
        }
    };

    const handleRemove = async (identifier, ticker) => {
        if (!window.confirm(`Are you sure you want to remove ${ticker} from your watchlist?`)) {
            return;
        }
        try {
            await removeFromWatchlist(identifier);
            loadWatchlist();
        } catch (err) {
            alert(`Failed to remove company: ${err.message}`);
        }
    };

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-in fade-in">
            {/* HEADER */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <Bookmark className="w-6 h-6 text-amber-400" />
                        <h1 className="text-2xl font-bold text-white tracking-tight">Saved Companies Watchlist</h1>
                    </div>
                    <p className="text-slate-400 text-sm">
                        Curate and monitor your institutional investment ideas, track theses, and launch rapid quantitative deep dives.
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm px-4 py-2.5 rounded-lg shadow-md transition-colors"
                    >
                        <Plus className="w-4 h-4" /> Add Company
                    </button>
                </div>
            </div>

            {/* SEARCH AND FILTER BAR */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-[#131B2F] border border-slate-800 p-4 rounded-xl shadow-sm">
                <div className="relative w-full sm:w-96">
                    <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                    <input
                        type="text"
                        value={filterQuery}
                        onChange={(e) => setFilterQuery(e.target.value)}
                        placeholder="Filter by ticker or company name..."
                        className="w-full bg-[#0A0F1C] border border-slate-700 rounded-lg pl-10 pr-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500 placeholder-slate-500"
                    />
                </div>
                <div className="text-xs text-slate-400 font-medium">
                    {watchlist.length} {watchlist.length === 1 ? 'company' : 'companies'} saved
                </div>
            </div>

            {/* ERROR ALERT */}
            {error && (
                <div className="bg-red-950/40 border border-red-800/80 rounded-xl p-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0" />
                        <p className="text-sm text-red-200">{error}</p>
                    </div>
                    <button
                        onClick={() => loadWatchlist(filterQuery)}
                        className="text-xs text-red-300 hover:text-white font-semibold px-3 py-1 bg-red-900/40 rounded border border-red-700/60"
                    >
                        Retry
                    </button>
                </div>
            )}

            {/* WATCHLIST GRID */}
            {loading ? (
                <div className="text-center py-16">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-amber-500 border-t-transparent mb-3"></div>
                    <p className="text-slate-400 text-sm">Loading your watchlist records...</p>
                </div>
            ) : watchlist.length === 0 ? (
                <div className="text-center py-16 bg-[#131B2F] border border-slate-800 rounded-2xl p-8">
                    <Bookmark className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                    <h3 className="text-lg font-bold text-white mb-1">
                        {filterQuery ? `No companies matching "${filterQuery}"` : 'Your Watchlist is Empty'}
                    </h3>
                    <p className="text-slate-400 text-sm max-w-md mx-auto mb-6">
                        {filterQuery
                            ? 'Try clearing your filter search query or adding a new company.'
                            : 'Save companies to keep track of valuation multiples, historical performance, and institutional reports.'}
                    </p>

                    {/* POPULAR SUGGESTIONS */}
                    <div className="max-w-xl mx-auto border-t border-slate-800 pt-6">
                        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-3">
                            Quick Add Popular Equities
                        </span>
                        <div className="flex flex-wrap justify-center gap-2">
                            {[
                                { ticker: 'AAPL', name: 'Apple Inc.', sector: 'Technology' },
                                { ticker: 'MSFT', name: 'Microsoft Corp.', sector: 'Technology' },
                                { ticker: 'NVDA', name: 'NVIDIA Corp.', sector: 'Semiconductors' },
                                { ticker: 'TCS.NS', name: 'Tata Consultancy Services', sector: 'IT Services' },
                                { ticker: 'RELIANCE.NS', name: 'Reliance Industries', sector: 'Conglomerate' },
                                { ticker: 'INFY.NS', name: 'Infosys Limited', sector: 'IT Services' }
                            ].map((item) => (
                                <button
                                    key={item.ticker}
                                    onClick={() => handleQuickAdd(item.ticker, item.name, item.sector)}
                                    className="bg-[#0A0F1C] hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-colors group"
                                >
                                    <Plus className="w-3 h-3 text-blue-400 group-hover:scale-125 transition-transform" />
                                    <span className="font-semibold text-white">{item.ticker}</span>
                                    <span className="text-slate-400 hidden sm:inline">- {item.name}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {watchlist.map((item) => (
                        <div
                            key={item.id}
                            className="bg-[#131B2F] border border-slate-800 hover:border-slate-700 rounded-xl p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
                        >
                            <div>
                                <div className="flex items-start justify-between gap-3 mb-2">
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <span className="font-extrabold text-white text-lg tracking-tight">
                                                {item.ticker}
                                            </span>
                                            {item.sector && (
                                                <span className="text-[10px] bg-slate-800 text-slate-300 font-semibold px-2 py-0.5 rounded border border-slate-700">
                                                    {item.sector}
                                                </span>
                                            )}
                                        </div>
                                        <h3 className="text-xs text-slate-400 font-medium truncate max-w-[200px] mt-0.5">
                                            {item.company_name || item.ticker}
                                        </h3>
                                    </div>
                                    <button
                                        onClick={() => handleRemove(item.id, item.ticker)}
                                        className="text-slate-500 hover:text-red-400 p-1 rounded hover:bg-slate-800/80 transition-colors"
                                        title="Remove from watchlist"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>

                                {item.notes ? (
                                    <div className="bg-[#0A0F1C] rounded-lg p-3 border border-slate-800/80 my-3">
                                        <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider block mb-1">
                                            Investment Thesis & Notes
                                        </span>
                                        <p className="text-xs text-slate-300 leading-relaxed italic line-clamp-3">
                                            "{item.notes}"
                                        </p>
                                    </div>
                                ) : (
                                    <div className="my-3 text-[11px] text-slate-500 italic">
                                        No notes attached.
                                    </div>
                                )}
                            </div>

                            <div className="pt-3 border-t border-slate-800/80 space-y-2">
                                <div className="text-[11px] text-slate-500">
                                    Saved on {new Date(item.added_at).toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}
                                </div>
                                <div className="flex items-center gap-2">
                                    <button
                                        onClick={() => {
                                            if (onSelectTicker) onSelectTicker(item.ticker);
                                            if (onNavigate) onNavigate('single');
                                        }}
                                        className="flex-1 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 text-xs font-semibold py-2 px-3 rounded-lg flex items-center justify-center gap-1.5 transition-colors"
                                    >
                                        <TrendingUp className="w-3.5 h-3.5" /> Deep Dive
                                    </button>
                                    <button
                                        onClick={() => {
                                            if (onGenerateReport) onGenerateReport(item.ticker);
                                            else {
                                                if (onSelectTicker) onSelectTicker(item.ticker);
                                                if (onNavigate) onNavigate('report');
                                            }
                                        }}
                                        className="bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-400 border border-indigo-500/30 text-xs font-semibold py-2 px-3 rounded-lg flex items-center justify-center gap-1.5 transition-colors"
                                        title="Generate Institutional Report"
                                    >
                                        <FileText className="w-3.5 h-3.5" /> Report
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* ADD COMPANY MODAL */}
            {showAddModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in">
                    <div className="bg-[#131B2F] border border-slate-700 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
                        <div className="flex items-center justify-between mb-4 border-b border-slate-800 pb-3">
                            <div className="flex items-center gap-2">
                                <Bookmark className="w-5 h-5 text-amber-400" />
                                <h3 className="text-lg font-bold text-white">Save Company to Watchlist</h3>
                            </div>
                            <button
                                onClick={() => { setShowAddModal(false); setAddError(null); }}
                                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {addError && (
                            <div className="bg-red-950/40 border border-red-800/80 rounded-lg p-3 mb-4 text-xs text-red-200">
                                {addError}
                            </div>
                        )}

                        <form onSubmit={handleAddCompany} className="space-y-4">
                            <div className="relative">
                                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                                    Ticker Symbol *
                                </label>
                                <input
                                    type="text"
                                    value={newTicker}
                                    onChange={(e) => handleTickerInput(e.target.value)}
                                    placeholder="e.g. AAPL, MSFT, TCS.NS"
                                    required
                                    className="w-full bg-[#0A0F1C] border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 font-mono uppercase"
                                />

                                {/* Auto-complete suggestions */}
                                {suggestions.length > 0 && (
                                    <div className="absolute left-0 right-0 top-full mt-1 bg-[#0A0F1C] border border-slate-700 rounded-lg shadow-xl z-20 overflow-hidden divide-y divide-slate-800">
                                        {suggestions.map((s) => (
                                            <div
                                                key={s.ticker}
                                                onClick={() => handleSelectSuggestion(s)}
                                                className="p-2.5 hover:bg-slate-800 cursor-pointer text-xs flex items-center justify-between"
                                            >
                                                <div>
                                                    <span className="font-bold text-white mr-2">{s.ticker}</span>
                                                    <span className="text-slate-400">{s.name}</span>
                                                </div>
                                                <span className="text-[10px] text-slate-500">{s.sector}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            <div>
                                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                                    Company Full Name
                                </label>
                                <input
                                    type="text"
                                    value={newCompanyName}
                                    onChange={(e) => setNewCompanyName(e.target.value)}
                                    placeholder="e.g. Apple Inc."
                                    className="w-full bg-[#0A0F1C] border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                                    Sector / Industry
                                </label>
                                <input
                                    type="text"
                                    value={newSector}
                                    onChange={(e) => setNewSector(e.target.value)}
                                    placeholder="e.g. Consumer Electronics or Technology"
                                    className="w-full bg-[#0A0F1C] border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                                    Investment Thesis / Personal Notes
                                </label>
                                <textarea
                                    value={newNotes}
                                    onChange={(e) => setNewNotes(e.target.value)}
                                    rows="3"
                                    placeholder="e.g. Monitoring for entry below \$175; high ROIC and free cash flow generation."
                                    className="w-full bg-[#0A0F1C] border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500 resize-none"
                                />
                            </div>

                            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                                <button
                                    type="button"
                                    onClick={() => { setShowAddModal(false); setAddError(null); }}
                                    className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white rounded-lg transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={adding || !newTicker.trim()}
                                    className="px-5 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-bold rounded-lg transition-colors shadow-md"
                                >
                                    {adding ? 'Saving...' : 'Save to Watchlist'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}