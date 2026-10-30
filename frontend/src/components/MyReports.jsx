import React, { useState, useEffect } from 'react';
import { 
  FileText, Search, Filter, ArrowUpDown, Download, Eye, 
  Trash2, Clock, CheckCircle2, AlertCircle, RefreshCw, Plus, 
  ChevronLeft, ChevronRight, Layers, FileDown, ShieldCheck
} from 'lucide-react';
import { fetchReportsList, downloadReportPdf, deleteReport } from '../services/api';

export default function MyReports({ onSelectReport, onNavigateGenerate }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [downloadingId, setDownloadingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  // Search & Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('date_desc'); // date_desc, date_asc, ticker_asc, pages_desc
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    loadReports();
  }, [statusFilter, currentPage]);

  const loadReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchReportsList({
        status: statusFilter,
        page: currentPage
      });
      // Handles both paginated DRF response ({ count, results }) and plain array
      if (data && Array.isArray(data.results)) {
        setReports(data.results);
        setTotalCount(data.count || data.results.length);
      } else if (Array.isArray(data)) {
        setReports(data);
        setTotalCount(data.length);
      } else {
        setReports([]);
        setTotalCount(0);
      }
    } catch (err) {
      console.error('Failed to load reports', err);
      setError(err.message || 'Failed to load research reports.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (e, r) => {
    e.stopPropagation();
    const id = r.report_id || r.id;
    setDownloadingId(id);
    try {
      await downloadReportPdf(id, r.ticker);
    } catch (err) {
      alert(`Download failed: ${err.message}`);
    } finally {
      setDownloadingId(null);
    }
  };

  const handleDelete = async (e, r) => {
    e.stopPropagation();
    const id = r.report_id || r.id;
    if (!window.confirm(`Are you sure you want to delete the report for ${r.ticker}?`)) {
      return;
    }
    setDeletingId(id);
    try {
      await deleteReport(id);
      setReports((prev) => prev.filter((item) => (item.report_id || item.id) !== id));
      setTotalCount((prev) => Math.max(0, prev - 1));
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  // Client-side search and sorting on current page items
  const filteredReports = reports
    .filter((r) => {
      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      const ticker = (r.ticker || '').toLowerCase();
      const name = (r.company_name || '').toLowerCase();
      const title = (r.report_title || '').toLowerCase();
      return ticker.includes(q) || name.includes(q) || title.includes(q);
    })
    .sort((a, b) => {
      if (sortBy === 'date_desc') {
        return new Date(b.generation_date || b.created_at || 0) - new Date(a.generation_date || a.created_at || 0);
      } else if (sortBy === 'date_asc') {
        return new Date(a.generation_date || a.created_at || 0) - new Date(b.generation_date || b.created_at || 0);
      } else if (sortBy === 'ticker_asc') {
        return (a.ticker || '').localeCompare(b.ticker || '');
      } else if (sortBy === 'pages_desc') {
        return (b.page_count || 0) - (a.page_count || 0);
      }
      return 0;
    });

  const totalPages = Math.ceil(totalCount / pageSize) || 1;

  return (
    <div className="space-y-6 animate-in fade-in">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400">
              <Layers className="w-5 h-5" />
            </span>
            <h2 className="text-xl font-bold text-white tracking-tight">My Research Reports</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Access, view, and download all 15-section institutional investment dossiers generated under your account.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadReports}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700"
            title="Refresh list"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={onNavigateGenerate}
            className="bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs px-3.5 py-2 rounded-lg flex items-center gap-1.5 transition-colors shadow-sm"
          >
            <Plus className="w-4 h-4" />
            Generate New Report
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-slate-900/70 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-3 text-xs">
        {/* Search Input */}
        <div className="relative w-full md:w-72">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by ticker or company..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        {/* Filter & Sort Controls */}
        <div className="flex items-center gap-3 w-full md:w-auto justify-end">
          {/* Status Filter */}
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="all">All Statuses</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>
          </div>

          {/* Sort By */}
          <div className="flex items-center gap-1.5">
            <span className="text-slate-400">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-blue-500"
            >
              <option value="date_desc">Newest First</option>
              <option value="date_asc">Oldest First</option>
              <option value="ticker_asc">Ticker A-Z</option>
              <option value="pages_desc">Most Pages</option>
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-xs text-red-400 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Reports Table / Card List */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 space-y-3">
            <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto" />
            <p className="text-xs">Loading your saved research reports...</p>
          </div>
        ) : filteredReports.length === 0 ? (
          <div className="p-12 text-center text-slate-400 space-y-4">
            <FileText className="w-10 h-10 mx-auto text-slate-600" />
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-white">No reports found</h3>
              <p className="text-xs text-slate-500">
                {searchQuery || statusFilter !== 'all'
                  ? 'Try clearing your search query or status filter.'
                  : 'You have not generated any institutional research reports yet.'}
              </p>
            </div>
            <button
              onClick={onNavigateGenerate}
              className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2 rounded-lg inline-flex items-center gap-1.5 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              Generate Your First Dossier
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950 text-slate-400 font-semibold uppercase tracking-wider text-[10px] border-b border-slate-800">
                <tr>
                  <th className="px-4 py-3">Company & Ticker</th>
                  <th className="px-4 py-3">Report Title</th>
                  <th className="px-4 py-3">Date Generated</th>
                  <th className="px-4 py-3 text-center">Pages</th>
                  <th className="px-4 py-3">Hurdle Score</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {filteredReports.map((r) => {
                  const id = r.report_id || r.id;
                  const isCompleted = r.status === 'completed';
                  const isFailed = r.status === 'failed';
                  const isProcessing = r.status === 'processing' || r.status === 'pending';

                  return (
                    <tr
                      key={id}
                      onClick={() => onSelectReport(id)}
                      className="hover:bg-slate-800/40 cursor-pointer transition-colors group"
                    >
                      {/* Ticker & Name */}
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-400 font-bold font-mono text-xs">
                            {(r.ticker || '??').slice(0, 2)}
                          </div>
                          <div>
                            <div className="font-bold text-white group-hover:text-blue-400 transition-colors">
                              {r.ticker}
                            </div>
                            <div className="text-[11px] text-slate-400 truncate max-w-[140px]">
                              {r.company_name || r.ticker}
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Report Title */}
                      <td className="px-4 py-3.5">
                        <div className="font-medium text-slate-200 truncate max-w-[220px]">
                          {r.report_title || `${r.ticker} Institutional Equity Research`}
                        </div>
                        <div className="text-[10px] text-slate-400 capitalize">
                          {r.report_type?.replace(/_/g, ' ') || 'Equity Research'}
                        </div>
                      </td>

                      {/* Date */}
                      <td className="px-4 py-3.5 text-slate-400 whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5 text-slate-500" />
                          <span>
                            {r.generation_date
                              ? new Date(r.generation_date).toLocaleDateString()
                              : 'Recent'}
                          </span>
                        </div>
                      </td>

                      {/* Page Count */}
                      <td className="px-4 py-3.5 text-center whitespace-nowrap">
                        <span className="font-mono text-purple-400 font-semibold bg-purple-500/10 px-2 py-0.5 rounded border border-purple-500/20">
                          {r.page_count || 1} / 50p
                        </span>
                      </td>

                      {/* Hurdle / Conviction */}
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        {r.principles_pass_rate_pct != null ? (
                          <div className="flex items-center gap-1.5">
                            <span className="text-emerald-400 font-semibold font-mono">
                              {r.principles_pass_rate_pct}%
                            </span>
                            <span className="text-[10px] text-slate-400">
                              ({r.conviction_rating ? r.conviction_rating.split(' ')[0] : 'Evaluated'})
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-500 text-[11px]">N/A</span>
                        )}
                      </td>

                      {/* Status Badge */}
                      <td className="px-4 py-3.5 whitespace-nowrap">
                        {isCompleted && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            <CheckCircle2 className="w-3 h-3" />
                            Completed
                          </span>
                        )}
                        {isProcessing && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse">
                            <RefreshCw className="w-3 h-3 animate-spin" />
                            Processing
                          </span>
                        )}
                        {isFailed && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
                            <AlertCircle className="w-3 h-3" />
                            Failed
                          </span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="px-4 py-3.5 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectReport(id);
                            }}
                            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                            title="View Report"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                          {isCompleted && (
                            <button
                              onClick={(e) => handleDownload(e, r)}
                              disabled={downloadingId === id}
                              className="p-1.5 rounded-lg bg-blue-600/20 hover:bg-blue-600 text-blue-400 hover:text-white transition-colors border border-blue-500/30"
                              title="Download PDF"
                            >
                              {downloadingId === id ? (
                                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                              ) : (
                                <Download className="w-3.5 h-3.5" />
                              )}
                            </button>
                          )}
                          <button
                            onClick={(e) => handleDelete(e, r)}
                            disabled={deletingId === id}
                            className="p-1.5 rounded-lg bg-slate-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition-colors"
                            title="Delete Report"
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
        )}

        {/* Pagination Footer */}
        {totalCount > pageSize && (
          <div className="px-4 py-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>
              Showing {(currentPage - 1) * pageSize + 1} to{' '}
              {Math.min(currentPage * pageSize, totalCount)} of {totalCount} reports
            </span>
            <div className="flex items-center gap-1.5">
              <button
                disabled={currentPage <= 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                className="p-1.5 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:opacity-30 disabled:hover:bg-slate-800"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <span className="px-2 font-mono">
                {currentPage} / {totalPages}
              </span>
              <button
                disabled={currentPage >= totalPages}
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                className="p-1.5 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 disabled:opacity-30 disabled:hover:bg-slate-800"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
