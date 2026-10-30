import React, { useState, useEffect } from 'react';
import { 
    LayoutDashboard, Bookmark, History, FileText, Search, Crown, 
    ArrowRight, CheckCircle, Clock, AlertCircle, RefreshCw, Plus, 
    Trash2, ExternalLink, ShieldCheck, TrendingUp, Building2, ChevronRight
} from 'lucide-react';
import { fetchUserDashboard, removeFromWatchlist, downloadReportPdf } from '../services/api';

export default function UserDashboard({ onNavigate, onSelectTicker, onOpenReport }) {
    const [dashboardData, setDashboardData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTicker, setSearchTicker] = useState('');
    const [downloadingId, setDownloadingId] = useState(null);

    const loadDashboard = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchUserDashboard();
            setDashboardData(data);
        } catch (err) {
            console.error('Failed to load user dashboard:', err);
            setError(err.message || 'Unable to load personalized dashboard.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadDashboard();
    }, []);

    const handleQuickSearch = (e) => {
        e.preventDefault();
        if (searchTicker.trim()) {
            if (onSelectTicker) onSelectTicker(searchTicker.trim().toUpperCase());
            if (onNavigate) onNavigate('single');
        }
    };

    const handleRemoveWatchlist = async (ticker, e) => {
        e.stopPropagation();
        try {
            await removeFromWatchlist(ticker);
            // Refresh dashboard
            loadDashboard();
        } catch (err) {
            alert(`Failed to remove ${ticker}: ${err.message}`);
        }
    };

    const handleDownloadReport = async (reportId, ticker, e) => {
        e.stopPropagation();
        setDownloadingId(reportId);
        try {
            await downloadReportPdf(reportId, ticker);
        } catch (err) {
            alert(`Download failed: ${err.message}`);
        } finally {
            setDownloadingId(null);
        }
    };

    if (loading) {
        return (
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center animate-in fade-in">
                <div className="inline-block animate-spin rounded-full h-10 w-10 border-4 border-blue-500 border-t-transparent mb-4"></div>
                <h3 className="text-xl font-bold text-white">Loading Your Research Dashboard...</h3>
                <p className="text-slate-400 text-sm mt-1">Aggregating saved companies, recent activities, and research reports.</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="max-w-4xl mx-auto px-4 py-8">
                <div className="bg-red-950/40 border border-red-800/80 rounded-xl p-6 text-center">
                    <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
                    <h3 className="text-lg font-bold text-red-200 mb-2">Failed to Load Dashboard</h3>
                    <p className="text-slate-300 text-sm mb-4">{error}</p>
                    <button
                        onClick={loadDashboard}
                        className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-sm px-4 py-2 rounded-lg transition-colors"
                    >
                        <RefreshCw className="w-4 h-4" /> Try Again
                    </button>
                </div>
            </div>
        );
    }

    const { user, welcome_message, stats, saved_companies, recent_activities, recent_reports, subscription } = dashboardData || {};

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-in fade-in">
            {/* WELCOME BANNER */}
            <div className="bg-gradient-to-r from-blue-900/40 via-[#131B2F] to-[#131B2F] border border-blue-500/20 rounded-2xl p-6 sm:p-8 relative overflow-hidden shadow-xl">
                <div className="absolute right-0 top-0 bottom-0 w-96 bg-gradient-to-l from-blue-500/5 to-transparent pointer-events-none" />
                <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div>
                        <div className="flex items-center gap-2 mb-2">
                            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30">
                                Institutional Research Console
                            </span>
                            <span className="text-xs text-slate-400">
                                {user?.email ? user.email : user?.username}
                            </span>
                        </div>
                        <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                            {welcome_message || `Welcome to Finlytics AI, ${user?.username || 'Analyst'}`}
                        </h1>
                        <p className="text-slate-300 text-sm sm:text-base mt-1.5 max-w-2xl leading-relaxed">
                            Analyze listed equities, track watchlist ideas, examine qualitative SEC disclosures, and generate 15-section institutional research reports.
                        </p>
                    </div>

                    {/* QUICK SEARCH INPUT */}
                    <form onSubmit={handleQuickSearch} className="flex-shrink-0 w-full md:w-80">
                        <div className="relative flex items-center bg-[#0A0F1C] border border-slate-700 rounded-xl p-1.5 focus-within:border-blue-500 transition-colors shadow-inner">
                            <Search className="h-4 w-4 text-slate-400 ml-2.5" />
                            <input
                                type="text"
                                value={searchTicker}
                                onChange={(e) => setSearchTicker(e.target.value)}
                                placeholder="Search company or ticker..."
                                className="w-full bg-transparent border-none text-white text-sm px-2.5 py-1.5 focus:outline-none placeholder-slate-500"
                            />
                            <button
                                type="submit"
                                disabled={!searchTicker.trim()}
                                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-3 py-1.5 rounded-lg transition-colors disabled:opacity-40"
                            >
                                Analyze
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            {/* KPI STAT CARDS */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div 
                    onClick={() => onNavigate && onNavigate('watchlist')}
                    className="bg-[#131B2F] border border-slate-800 hover:border-blue-500/40 p-5 rounded-xl cursor-pointer transition-all hover:bg-slate-850 shadow-md group"
                >
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Saved Watchlist</span>
                        <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center group-hover:bg-blue-500/20">
                            <Bookmark className="w-4 h-4" />
                        </div>
                    </div>
                    <div className="text-2xl font-bold text-white mb-1">{stats?.saved_companies_count ?? 0}</div>
                    <div className="text-xs text-blue-400 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                        Manage watchlist <ArrowRight className="w-3 h-3" />
                    </div>
                </div>

                <div 
                    onClick={() => onNavigate && onNavigate('my-reports')}
                    className="bg-[#131B2F] border border-slate-800 hover:border-indigo-500/40 p-5 rounded-xl cursor-pointer transition-all hover:bg-slate-850 shadow-md group"
                >
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Research Reports</span>
                        <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center group-hover:bg-indigo-500/20">
                            <FileText className="w-4 h-4" />
                        </div>
                    </div>
                    <div className="text-2xl font-bold text-white mb-1">{stats?.reports_count ?? 0}</div>
                    <div className="text-xs text-indigo-400 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                        View my reports <ArrowRight className="w-3 h-3" />
                    </div>
                </div>

                <div 
                    onClick={() => onNavigate && onNavigate('history')}
                    className="bg-[#131B2F] border border-slate-800 hover:border-emerald-500/40 p-5 rounded-xl cursor-pointer transition-all hover:bg-slate-850 shadow-md group"
                >
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Research History</span>
                        <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center group-hover:bg-emerald-500/20">
                            <History className="w-4 h-4" />
                        </div>
                    </div>
                    <div className="text-2xl font-bold text-white mb-1">{stats?.activities_count ?? 0}</div>
                    <div className="text-xs text-emerald-400 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                        Audit research history <ArrowRight className="w-3 h-3" />
                    </div>
                </div>

                <div 
                    onClick={() => onNavigate && onNavigate('subscription')}
                    className="bg-[#131B2F] border border-slate-800 hover:border-amber-500/40 p-5 rounded-xl cursor-pointer transition-all hover:bg-slate-850 shadow-md group"
                >
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Plan & Limits</span>
                        <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center group-hover:bg-amber-500/20">
                            <Crown className="w-4 h-4" />
                        </div>
                    </div>
                    <div className="text-2xl font-bold text-white mb-1 capitalize">
                        {subscription?.tier || 'Free'} Tier
                    </div>
                    <div className="text-xs text-amber-400 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
                        {subscription?.tier === 'premium' ? 'Manage subscription' : 'Upgrade to Premium'} <ArrowRight className="w-3 h-3" />
                    </div>
                </div>
            </div>

            {/* QUICK ACTIONS ROW */}
            <div className="bg-[#131B2F] border border-slate-800 rounded-xl p-5 shadow-sm">
                <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-3">Quick Navigation</h3>
                <div className="flex flex-wrap gap-3">
                    <button
                        onClick={() => onNavigate && onNavigate('single')}
                        className="flex items-center gap-2 bg-[#0A0F1C] hover:bg-slate-800 border border-slate-700/80 text-white text-xs font-medium px-4 py-2.5 rounded-lg transition-colors"
                    >
                        <Search className="w-3.5 h-3.5 text-blue-400" />
                        Company Deep Dive
                    </button>
                    <button
                        onClick={() => onNavigate && onNavigate('compare')}
                        className="flex items-center gap-2 bg-[#0A0F1C] hover:bg-slate-800 border border-slate-700/80 text-white text-xs font-medium px-4 py-2.5 rounded-lg transition-colors"
                    >
                        <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                        Peer Comparison
                    </button>
                    <button
                        onClick={() => onNavigate && onNavigate('report')}
                        className="flex items-center gap-2 bg-[#0A0F1C] hover:bg-slate-800 border border-slate-700/80 text-white text-xs font-medium px-4 py-2.5 rounded-lg transition-colors"
                    >
                        <FileText className="w-3.5 h-3.5 text-indigo-400" />
                        Generate Institutional Report
                    </button>
                    <button
                        onClick={() => onNavigate && onNavigate('watchlist')}
                        className="flex items-center gap-2 bg-[#0A0F1C] hover:bg-slate-800 border border-slate-700/80 text-white text-xs font-medium px-4 py-2.5 rounded-lg transition-colors"
                    >
                        <Bookmark className="w-3.5 h-3.5 text-amber-400" />
                        Company Watchlist
                    </button>
                    <button
                        onClick={() => onNavigate && onNavigate('directory')}
                        className="flex items-center gap-2 bg-[#0A0F1C] hover:bg-slate-800 border border-slate-700/80 text-white text-xs font-medium px-4 py-2.5 rounded-lg transition-colors"
                    >
                        <Building2 className="w-3.5 h-3.5 text-cyan-400" />
                        Company Directory
                    </button>
                </div>
            </div>

            {/* MAIN 2-COLUMN SECTION */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* LEFT 2 COLUMNS: WATCHLIST & RECENT ACTIVITY */}
                <div className="lg:col-span-2 space-y-8">
                    {/* SAVED COMPANIES (WATCHLIST) */}
                    <div className="bg-[#131B2F] border border-slate-800 rounded-xl p-6 shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <Bookmark className="w-5 h-5 text-blue-400" />
                                <h2 className="text-lg font-bold text-white">Saved Companies</h2>
                                <span className="text-xs bg-slate-800 text-slate-300 font-semibold px-2 py-0.5 rounded-full">
                                    {saved_companies?.length || 0}
                                </span>
                            </div>
                            <button
                                onClick={() => onNavigate && onNavigate('watchlist')}
                                className="text-xs text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1 transition-colors"
                            >
                                View All ({stats?.saved_companies_count ?? 0}) <ChevronRight className="w-3.5 h-3.5" />
                            </button>
                        </div>

                        {(!saved_companies || saved_companies.length === 0) ? (
                            <div className="text-center py-8 bg-[#0A0F1C] border border-dashed border-slate-800 rounded-xl">
                                <Bookmark className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                                <p className="text-slate-400 text-sm font-medium">No companies in your watchlist yet.</p>
                                <p className="text-slate-500 text-xs mt-1 mb-4">Save companies during analysis to monitor their fundamentals.</p>
                                <button
                                    onClick={() => onNavigate && onNavigate('watchlist')}
                                    className="inline-flex items-center gap-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-400 border border-blue-500/30 text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors"
                                >
                                    <Plus className="w-3.5 h-3.5" /> Add First Company
                                </button>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                {saved_companies.map((item) => (
                                    <div
                                        key={item.id}
                                        onClick={() => {
                                            if (onSelectTicker) onSelectTicker(item.ticker);
                                            if (onNavigate) onNavigate('single');
                                        }}
                                        className="bg-[#0A0F1C] border border-slate-800 hover:border-blue-500/40 p-4 rounded-xl cursor-pointer transition-all hover:bg-slate-900/60 group relative"
                                    >
                                        <div className="flex items-start justify-between">
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <span className="font-bold text-white text-base group-hover:text-blue-400 transition-colors">
                                                        {item.ticker}
                                                    </span>
                                                    {item.sector && (
                                                        <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded">
                                                            {item.sector}
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="text-xs text-slate-400 font-medium truncate max-w-[180px] mt-0.5">
                                                    {item.company_name || item.ticker}
                                                </div>
                                            </div>
                                            <button
                                                onClick={(e) => handleRemoveWatchlist(item.ticker, e)}
                                                className="text-slate-500 hover:text-red-400 p-1 rounded hover:bg-slate-800 transition-colors"
                                                title="Remove from watchlist"
                                            >
                                                <Trash2 className="w-3.5 h-3.5" />
                                            </button>
                                        </div>

                                        {item.notes && (
                                            <p className="text-xs text-slate-400/80 mt-2 line-clamp-1 italic">
                                                "{item.notes}"
                                            </p>
                                        )}

                                        <div className="flex items-center justify-between mt-3 pt-2.5 border-t border-slate-800/80 text-[11px] text-slate-500">
                                            <span>Added {new Date(item.added_at).toLocaleDateString()}</span>
                                            <span className="text-blue-400 font-medium group-hover:underline flex items-center gap-0.5">
                                                Deep Dive →
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* RECENT RESEARCH ACTIVITY */}
                    <div className="bg-[#131B2F] border border-slate-800 rounded-xl p-6 shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <History className="w-5 h-5 text-emerald-400" />
                                <h2 className="text-lg font-bold text-white">Recent Research History</h2>
                            </div>
                            <button
                                onClick={() => onNavigate && onNavigate('history')}
                                className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1 transition-colors"
                            >
                                Audit Full History ({stats?.activities_count ?? 0}) <ChevronRight className="w-3.5 h-3.5" />
                            </button>
                        </div>

                        {(!recent_activities || recent_activities.length === 0) ? (
                            <div className="text-center py-8 bg-[#0A0F1C] border border-dashed border-slate-800 rounded-xl">
                                <History className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                                <p className="text-slate-400 text-sm font-medium">No research sessions logged yet.</p>
                                <p className="text-slate-500 text-xs mt-1">Start a single company deep dive or ask RAG questions to build your research trail.</p>
                            </div>
                        ) : (
                            <div className="divide-y divide-slate-800 bg-[#0A0F1C] rounded-xl border border-slate-800 overflow-hidden">
                                {recent_activities.map((act) => (
                                    <div
                                        key={act.id}
                                        onClick={() => {
                                            if (onSelectTicker) onSelectTicker(act.ticker);
                                            if (onNavigate) onNavigate(act.research_type === 'report' ? 'my-reports' : 'single');
                                        }}
                                        className="p-3.5 hover:bg-slate-850/60 cursor-pointer transition-colors flex items-center justify-between gap-4"
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center font-bold text-xs text-slate-300">
                                                {act.ticker.slice(0, 3)}
                                            </div>
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <span className="font-semibold text-white text-sm">{act.ticker}</span>
                                                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded capitalize ${
                                                        act.research_type === 'report' 
                                                            ? 'bg-indigo-500/20 text-indigo-400' 
                                                            : act.research_type === 'qualitative'
                                                            ? 'bg-amber-500/20 text-amber-400'
                                                            : 'bg-emerald-500/20 text-emerald-400'
                                                    }`}>
                                                        {act.research_type}
                                                    </span>
                                                </div>
                                                <span className="text-xs text-slate-400 truncate max-w-xs block">
                                                    {act.company_name || act.ticker}
                                                </span>
                                            </div>
                                        </div>

                                        <div className="text-right flex-shrink-0">
                                            <div className="text-[11px] text-slate-500 flex items-center gap-1 justify-end">
                                                <Clock className="w-3 h-3" />
                                                {new Date(act.created_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                                            </div>
                                            <span className="text-xs text-blue-400 hover:underline font-medium">Revisit →</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* RIGHT COLUMN: RECENT REPORTS & SUBSCRIPTION */}
                <div className="space-y-8">
                    {/* RECENT REPORTS */}
                    <div className="bg-[#131B2F] border border-slate-800 rounded-xl p-6 shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <FileText className="w-5 h-5 text-indigo-400" />
                                <h2 className="text-lg font-bold text-white">Recent Reports</h2>
                            </div>
                            <button
                                onClick={() => onNavigate && onNavigate('my-reports')}
                                className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1 transition-colors"
                            >
                                All ({stats?.reports_count ?? 0}) <ChevronRight className="w-3.5 h-3.5" />
                            </button>
                        </div>

                        {(!recent_reports || recent_reports.length === 0) ? (
                            <div className="text-center py-8 bg-[#0A0F1C] border border-dashed border-slate-800 rounded-xl">
                                <FileText className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                                <p className="text-slate-400 text-sm font-medium">No reports generated yet.</p>
                                <p className="text-slate-500 text-xs mt-1 mb-4">Generate 15-section PDFs capped at 50 pages with live metrics.</p>
                                <button
                                    onClick={() => onNavigate && onNavigate('report')}
                                    className="inline-flex items-center gap-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-400 border border-indigo-500/30 text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors"
                                >
                                    <Plus className="w-3.5 h-3.5" /> Generate Report
                                </button>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {recent_reports.map((rep) => (
                                    <div
                                        key={rep.report_id}
                                        onClick={() => {
                                            if (onOpenReport) onOpenReport(rep.report_id);
                                            else if (onNavigate) onNavigate('my-reports');
                                        }}
                                        className="bg-[#0A0F1C] border border-slate-800 hover:border-indigo-500/40 p-4 rounded-xl cursor-pointer transition-all hover:bg-slate-900/60 group"
                                    >
                                        <div className="flex items-start justify-between gap-2">
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <span className="font-bold text-white text-sm group-hover:text-indigo-400 transition-colors">
                                                        {rep.ticker}
                                                    </span>
                                                    <span className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                                                        rep.status === 'completed'
                                                            ? 'bg-emerald-500/20 text-emerald-400'
                                                            : rep.status === 'failed'
                                                            ? 'bg-red-500/20 text-red-400'
                                                            : 'bg-amber-500/20 text-amber-400'
                                                    }`}>
                                                        {rep.status}
                                                    </span>
                                                </div>
                                                <p className="text-xs text-slate-400 font-medium truncate max-w-[200px] mt-0.5">
                                                    {rep.company_name || rep.report_title}
                                                </p>
                                            </div>

                                            <span className="text-xs text-slate-400 font-mono flex-shrink-0">
                                                {rep.page_count} {rep.page_count === 1 ? 'page' : 'pages'}
                                            </span>
                                        </div>

                                        <div className="flex items-center justify-between mt-3 pt-2.5 border-t border-slate-800/80 text-[11px] text-slate-500">
                                            <span>{new Date(rep.generation_date).toLocaleDateString()}</span>
                                            <div className="flex items-center gap-2">
                                                <button
                                                    onClick={(e) => handleDownloadReport(rep.report_id, rep.ticker, e)}
                                                    disabled={rep.status !== 'completed' || downloadingId === rep.report_id}
                                                    className="text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1 hover:underline disabled:opacity-40"
                                                >
                                                    {downloadingId === rep.report_id ? 'Downloading...' : 'PDF ↓'}
                                                </button>
                                                <span className="text-slate-600">|</span>
                                                <span className="text-slate-400 group-hover:text-white font-medium flex items-center gap-0.5">
                                                    Read →
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* SUBSCRIPTION SUMMARY CARD */}
                    <div className="bg-[#131B2F] border border-slate-800 rounded-xl p-6 shadow-sm">
                        <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center gap-2">
                                <Crown className="w-5 h-5 text-amber-400" />
                                <h2 className="text-lg font-bold text-white">Subscription Status</h2>
                            </div>
                            <span className="text-xs px-2.5 py-0.5 rounded-full font-bold uppercase bg-amber-500/20 text-amber-400 border border-amber-500/30">
                                {subscription?.tier || 'Free'}
                            </span>
                        </div>

                        <p className="text-xs text-slate-400 leading-relaxed mb-4">
                            {subscription?.tier === 'premium'
                                ? 'You have full access to institutional 50-page reports, unlimited watchlist monitoring, and qualitative RAG evidence.'
                                : 'You are currently on the Free Tier with foundational valuation metrics. Upgrade to unlock deep institutional reports and unlimited research.'}
                        </p>

                        <div className="space-y-2 mb-5 text-xs text-slate-300">
                            <div className="flex items-center gap-2">
                                <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                                <span>6 Quantitative Valuation Modules</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                                <span>DCF & Intrinsic Fair Value Calculators</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                                <span>Personalized Watchlist & Research Trail</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                                <span>50-Page PDF Institutional Reports</span>
                            </div>
                        </div>

                        <button
                            onClick={() => onNavigate && onNavigate('subscription')}
                            className="w-full bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 transition-all shadow-md shadow-amber-500/10 cursor-pointer"
                        >
                            <Crown className="w-3.5 h-3.5 fill-slate-950" />
                            {subscription?.tier === 'premium' ? 'Manage Subscription Details' : 'Upgrade Plan & Feature Limits'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}