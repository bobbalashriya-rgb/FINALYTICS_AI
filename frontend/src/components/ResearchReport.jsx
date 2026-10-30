import React, { useState, useEffect } from 'react';
import { 
  FileText, Sparkles, Download, Printer, Copy, Check, AlertCircle, 
  Clock, ShieldCheck, Crown, Layers, Search, RefreshCw, Eye, 
  CheckCircle2, ArrowRight, Building2, Zap, Info
} from 'lucide-react';
import { 
  createResearchReport, 
  fetchReportsList, 
  fetchReportDetail, 
  fetchReportStatus, 
  downloadReportPdf, 
  getReportHtmlUrl 
} from '../services/api';
import { COMPANY_DIRECTORY, searchDirectory } from '../data/companyDirectory';
import ReportReader from './ReportReader';
import MyReports from './MyReports';

const POPULAR_COMPANIES = [
  { ticker: 'TCS.NS', name: 'Tata Consultancy Services' },
  { ticker: 'INFY.NS', name: 'Infosys Limited' },
  { ticker: 'RELIANCE.NS', name: 'Reliance Industries' },
  { ticker: 'HDFCBANK.NS', name: 'HDFC Bank' },
  { ticker: 'AAPL', name: 'Apple Inc.' },
  { ticker: 'MSFT', name: 'Microsoft Corporation' },
  { ticker: 'NVDA', name: 'NVIDIA Corporation' },
  { ticker: 'GOOGL', name: 'Alphabet Inc.' },
];

export default function ResearchReport({ initialTicker = 'TCS', onNavigateSubscription }) {
  const [subView, setSubView] = useState('generator'); // 'generator', 'reader', 'my-reports'
  const [ticker, setTicker] = useState(initialTicker);
  const [reportTitle, setReportTitle] = useState('');
  const [activeReport, setActiveReport] = useState(null);
  const [recentReports, setRecentReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generatingStatus, setGeneratingStatus] = useState(null);
  const [error, setError] = useState(null);
  const [downloading, setDownloading] = useState(false);

  // Search autocomplete
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  useEffect(() => {
    loadRecentReports();
  }, []);

  const loadRecentReports = async () => {
    try {
      const data = await fetchReportsList();
      const items = Array.isArray(data.results) ? data.results : (Array.isArray(data) ? data : []);
      setRecentReports(items.slice(0, 5));
    } catch (err) {
      console.warn('Could not load recent reports', err);
    }
  };

  const handleTickerInput = (val) => {
    setTicker(val);
    if (val.trim().length >= 1) {
      const matches = searchDirectory(val).slice(0, 5);
      setSuggestions(matches);
      setShowSuggestions(true);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const selectCompany = (item) => {
    setTicker(item.ticker);
    setReportTitle(`Institutional Equity Research: ${item.shortName || item.name}`);
    setShowSuggestions(false);
  };

  const handleGenerate = async (e) => {
    if (e) e.preventDefault();
    const cleanTicker = ticker.trim().toUpperCase();
    if (!cleanTicker) return;

    setLoading(true);
    setError(null);
    setGeneratingStatus('Initiating generation pipeline...');

    try {
      // Step 1: Request report creation
      setGeneratingStatus('Fetching normalized financial statements & calculating valuation multiples...');
      const created = await createResearchReport(cleanTicker, reportTitle.trim() || undefined);
      
      const reportId = created.report_id || created.id;

      // Step 2: Poll status if still processing, or load completed report
      if (created.status === 'completed') {
        setActiveReport(created);
        setSubView('reader');
      } else {
        setGeneratingStatus('Evaluating 6 Graham & Buffett principles and synthesizing 15 sections...');
        // Poll status every 1.5 seconds up to 30 seconds
        let attempts = 0;
        const maxAttempts = 20;
        const pollTimer = setInterval(async () => {
          attempts++;
          try {
            const statusData = await fetchReportStatus(reportId);
            if (statusData.status === 'completed') {
              clearInterval(pollTimer);
              const fullDetail = await fetchReportDetail(reportId);
              setActiveReport(fullDetail);
              setSubView('reader');
              setLoading(false);
              loadRecentReports();
            } else if (statusData.status === 'failed') {
              clearInterval(pollTimer);
              setError(statusData.error_details || 'Report generation encountered an error.');
              setLoading(false);
            }
          } catch (pollErr) {
            clearInterval(pollTimer);
            setError(pollErr.message || 'Status check failed.');
            setLoading(false);
          }
          if (attempts >= maxAttempts) {
            clearInterval(pollTimer);
            setLoading(false);
            // Attempt to load detail directly
            fetchReportDetail(reportId).then((r) => {
              setActiveReport(r);
              setSubView('reader');
            }).catch(console.error);
          }
        }, 1500);
        return;
      }
      loadRecentReports();
    } catch (err) {
      console.error('Generation error', err);
      setError(err.message || 'Failed to generate 15-section research report.');
    } finally {
      setLoading(false);
      setGeneratingStatus(null);
    }
  };

  const handleOpenReport = async (reportId) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchReportDetail(reportId);
      setActiveReport(data);
      setSubView('reader');
    } catch (err) {
      setError(err.message || 'Failed to open research report.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = async (reportId, reportTicker) => {
    setDownloading(true);
    try {
      await downloadReportPdf(reportId, reportTicker);
    } catch (err) {
      alert(`Download failed: ${err.message}`);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner with Subscribe Button */}
      <div className="bg-gradient-to-r from-blue-950/40 via-slate-900 to-slate-900 border border-blue-500/30 rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white tracking-tight">Institutional Research Dossier</h2>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                15 Sections • Max 50 Pages
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Automated multi-factor quantitative valuation, DCF cash flow modeling, and MarketPing regulatory RAG citations.
            </p>
          </div>
        </div>

        {/* View Switcher & Subscribe CTA */}
        <div className="flex items-center gap-2.5 w-full sm:w-auto justify-end">
          <button
            onClick={() => setSubView('my-reports')}
            className={`text-xs px-3.5 py-2 rounded-lg font-medium transition-colors flex items-center gap-1.5 border ${
              subView === 'my-reports'
                ? 'bg-blue-600/20 text-blue-300 border-blue-500/40'
                : 'bg-slate-800/80 text-slate-300 border-slate-700 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Layers className="w-4 h-4" />
            My Reports
          </button>

          {subView !== 'generator' && (
            <button
              onClick={() => setSubView('generator')}
              className="text-xs px-3.5 py-2 rounded-lg font-medium bg-slate-800/80 text-slate-300 border border-slate-700 hover:text-white hover:bg-slate-800 transition-colors"
            >
              New Report
            </button>
          )}

          {/* Clearly Visible Subscribe Button */}
          <button
            onClick={onNavigateSubscription}
            className="bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs px-4 py-2 rounded-lg flex items-center gap-1.5 transition-all shadow-md shadow-amber-500/10 cursor-pointer"
          >
            <Crown className="w-4 h-4 fill-slate-950" />
            Subscribe
          </button>
        </div>
      </div>

      {/* ERROR NOTICE */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-xs text-red-400 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* SUBVIEW 1: GENERATOR PAGE */}
      {subView === 'generator' && (
        <div className="space-y-6 animate-in fade-in">
          {/* Main Generator Card */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm space-y-6">
            <div className="max-w-2xl">
              <h3 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-blue-400" />
                Select Company for Research Report
              </h3>
              <p className="text-xs text-slate-400 mt-1">
                Choose from verified NSE, BSE, or US listed equities with available financial statement models 
                and qualitative filing disclosures.
              </p>
            </div>

            <form onSubmit={handleGenerate} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Ticker Input with Autocomplete */}
                <div className="relative md:col-span-1">
                  <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                    Company Ticker
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={ticker}
                      onChange={(e) => handleTickerInput(e.target.value.toUpperCase())}
                      placeholder="e.g. TCS.NS, AAPL, INFY"
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2.5 text-sm font-mono text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                    />
                    <Search className="w-4 h-4 absolute right-3 top-3 text-slate-500 pointer-events-none" />
                  </div>

                  {/* Suggestions Dropdown */}
                  {showSuggestions && suggestions.length > 0 && (
                    <div className="absolute top-full left-0 right-0 mt-1 bg-slate-950 border border-slate-800 rounded-xl shadow-2xl z-20 max-h-56 overflow-y-auto no-scrollbar divide-y divide-slate-800/80">
                      {suggestions.map((item, idx) => (
                        <div
                          key={idx}
                          onClick={() => selectCompany(item)}
                          className="px-3.5 py-2.5 hover:bg-slate-800/60 cursor-pointer transition-colors text-xs flex items-center justify-between"
                        >
                          <div>
                            <p className="font-semibold text-white">{item.shortName || item.name}</p>
                            <span className="text-[10px] text-slate-400">{item.country} • {item.sector}</span>
                          </div>
                          <span className="font-mono text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded text-[11px]">
                            {item.ticker}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Optional Custom Report Title */}
                <div className="md:col-span-2">
                  <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider mb-1">
                    Report Title (Optional)
                  </label>
                  <input
                    type="text"
                    value={reportTitle}
                    onChange={(e) => setReportTitle(e.target.value)}
                    placeholder={`Institutional Equity Research: ${ticker || 'Company'}`}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                  />
                </div>
              </div>

              {/* Popular Curated Companies */}
              <div className="pt-2">
                <span className="text-[11px] text-slate-400 font-medium">Quick Pick Researched Companies:</span>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {POPULAR_COMPANIES.map((c) => (
                    <button
                      key={c.ticker}
                      type="button"
                      onClick={() => {
                        setTicker(c.ticker);
                        setReportTitle(`Institutional Equity Research: ${c.name}`);
                      }}
                      className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all border ${
                        ticker === c.ticker
                          ? 'bg-blue-600/20 text-blue-300 border-blue-500/50 font-semibold'
                          : 'bg-slate-950/80 text-slate-400 border-slate-800 hover:text-white hover:bg-slate-800'
                      }`}
                    >
                      <span className="font-mono">{c.ticker}</span>
                      <span className="text-[10px] text-slate-400 ml-1.5">({c.name.split(' ')[0]})</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Action Submit Button */}
              <div className="pt-4 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">
                <div className="text-xs text-slate-400 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span>Strictly grounded in actual filings & financial statements. Capped at 50 PDF pages.</span>
                </div>

                <button
                  type="submit"
                  disabled={loading || !ticker.trim()}
                  className="w-full sm:w-auto bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 text-white font-semibold text-xs px-6 py-2.5 rounded-lg flex items-center justify-center gap-2 transition-all shadow-md shadow-blue-600/20"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Generating Dossier...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      Generate Detailed Research Report
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Loading / Progress State Card */}
          {loading && (
            <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-8 text-center space-y-4">
              <div className="w-12 h-12 border-3 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto" />
              <div className="space-y-1.5">
                <h4 className="text-base font-bold text-white">Synthesizing 15-Section Research Dossier</h4>
                <p className="text-xs text-blue-400 font-mono animate-pulse">
                  {generatingStatus || 'Processing valuation models and qualitative RAG evidence...'}
                </p>
                <p className="text-[11px] text-slate-500 max-w-md mx-auto">
                  Running multi-stage valuation modules (Absolute, Growth, Historical, Relative, DCF, and Quality/Risk),
                  evaluating Graham & Buffett hurdles, and assembling the verified ReportLab PDF.
                </p>
              </div>

              {/* Progress Stepper */}
              <div className="max-w-lg mx-auto pt-4 grid grid-cols-4 gap-2 text-[10px]">
                <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-300">
                  1. Financials
                </div>
                <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-300">
                  2. Valuation
                </div>
                <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-300">
                  3. RAG Filings
                </div>
                <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-300">
                  4. PDF &lt;=50p
                </div>
              </div>
            </div>
          )}

          {/* Recent Reports Quick Access Shelf */}
          {recentReports.length > 0 && !loading && (
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-blue-400" />
                  Your Recent Reports
                </span>
                <button
                  onClick={() => setSubView('my-reports')}
                  className="text-xs text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1"
                >
                  View All ({recentReports.length})
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {recentReports.map((r) => {
                  const id = r.report_id || r.id;
                  return (
                    <div
                      key={id}
                      onClick={() => handleOpenReport(id)}
                      className="bg-slate-950/60 hover:bg-slate-800/60 border border-slate-800 hover:border-blue-500/40 rounded-xl p-3.5 cursor-pointer transition-all space-y-2 group"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-white group-hover:text-blue-400 transition-colors font-mono">
                          {r.ticker}
                        </span>
                        <span className="text-[10px] text-purple-400 font-mono bg-purple-500/10 px-1.5 py-0.5 rounded border border-purple-500/20">
                          {r.page_count || 1}p
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 truncate">
                        {r.report_title || r.company_name || `${r.ticker} Research`}
                      </p>
                      <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1 border-t border-slate-800/80">
                        <span>{r.generation_date ? new Date(r.generation_date).toLocaleDateString() : 'Recent'}</span>
                        <span className="text-emerald-400 font-medium">
                          {r.principles_pass_rate_pct != null ? `${r.principles_pass_rate_pct}% pass` : 'Ready'}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {/* SUBVIEW 2: REPORT READER */}
      {subView === 'reader' && (
        <ReportReader
          report={activeReport}
          onBack={() => setSubView('generator')}
        />
      )}

      {/* SUBVIEW 3: MY REPORTS LIST */}
      {subView === 'my-reports' && (
        <MyReports
          onSelectReport={(reportId) => handleOpenReport(reportId)}
          onNavigateGenerate={() => setSubView('generator')}
        />
      )}
    </div>
  );
}
