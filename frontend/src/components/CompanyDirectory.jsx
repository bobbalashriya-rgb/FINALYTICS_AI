import React, { useState } from 'react';
import { 
    Building2, Search, ExternalLink, Copy, Check, Globe, 
    Layers, GitCompare, ArrowRight, Filter, Sparkles 
} from 'lucide-react';
import { COMPANY_DIRECTORY, searchDirectory } from '../data/companyDirectory';

export default function CompanyDirectory({ onSelectTicker }) {
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedMarket, setSelectedMarket] = useState('All');
    const [selectedSector, setSelectedSector] = useState('All');
    const [copiedTicker, setCopiedTicker] = useState(null);

    const filteredCompanies = searchDirectory(searchQuery, selectedMarket, selectedSector);

    const handleCopy = (ticker) => {
        navigator.clipboard.writeText(ticker);
        setCopiedTicker(ticker);
        setTimeout(() => setCopiedTicker(null), 2000);
    };

    const markets = ['All', 'India (NSE)', 'US (NASDAQ/NYSE)'];
    const sectors = ['All', 'Technology', 'Financial Services', 'Consumer', 'Energy', 'Healthcare', 'Automotive', 'Industrials'];

    return (
        <div className="space-y-6 animate-in fade-in">
            {/* Header Banner */}
            <div className="bg-gradient-to-r from-[#131B2F] via-[#16223D] to-[#131B2F] p-8 rounded-2xl border border-slate-800 shadow-xl">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div>
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold mb-3">
                            <Building2 className="w-4 h-4" /> Yfinance Ticker & Abbreviation Index
                        </div>
                        <h2 className="text-3xl font-extrabold text-white tracking-tight">
                            Listed Companies Directory
                        </h2>
                        <p className="text-slate-400 text-sm mt-1 max-w-2xl leading-relaxed">
                            Search any company by its popular name (e.g. <strong>Infosys</strong>, <strong>Tata</strong>, <strong>Apple</strong>) to find its official Yfinance ticker abbreviation (e.g. <code className="text-blue-300 font-mono bg-slate-900/80 px-1.5 py-0.5 rounded">INFY.NS</code>, <code className="text-blue-300 font-mono bg-slate-900/80 px-1.5 py-0.5 rounded">TCS.NS</code>, <code className="text-blue-300 font-mono bg-slate-900/80 px-1.5 py-0.5 rounded">AAPL</code>) with instant 1-click analysis.
                        </p>
                    </div>

                    <div className="flex items-center gap-3 bg-[#0A0F1C]/90 px-5 py-4 rounded-xl border border-slate-800 flex-shrink-0">
                        <div className="text-center">
                            <span className="text-2xl font-black text-white">{filteredCompanies.length}</span>
                            <span className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Companies</span>
                        </div>
                        <div className="h-8 w-px bg-slate-800"></div>
                        <div className="text-center">
                            <span className="text-2xl font-black text-blue-400">2</span>
                            <span className="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Markets (IN/US)</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Search and Filters */}
            <div className="bg-[#131B2F] p-5 rounded-xl border border-slate-800 shadow-lg space-y-4">
                {/* Search Input */}
                <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-500">
                        <Search className="h-5 w-5" />
                    </div>
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search by company name (e.g. Infosys, Reliance, Apple, Nvidia) or ticker (INFY.NS, NVDA)..."
                        className="block w-full pl-11 pr-4 py-3 bg-[#0A0F1C] border border-slate-700/80 rounded-xl focus:ring-2 focus:ring-blue-500 text-white placeholder-slate-500 shadow-inner outline-none transition-shadow text-sm font-medium"
                    />
                    {searchQuery && (
                        <button
                            onClick={() => setSearchQuery('')}
                            className="absolute inset-y-0 right-0 pr-4 flex items-center text-xs text-slate-400 hover:text-white"
                        >
                            Clear
                        </button>
                    )}
                </div>

                {/* Filter Controls */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-1 border-t border-slate-800/80">
                    {/* Market Tabs */}
                    <div className="flex flex-wrap gap-1.5">
                        <span className="text-xs font-semibold text-slate-400 self-center mr-1 hidden sm:inline">Market:</span>
                        {markets.map(m => (
                            <button
                                key={m}
                                onClick={() => setSelectedMarket(m)}
                                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors ${selectedMarket === m ? 'bg-blue-600 text-white shadow-md' : 'bg-[#0A0F1C] text-slate-400 hover:text-white hover:bg-slate-800/60'}`}
                            >
                                {m}
                            </button>
                        ))}
                    </div>

                    {/* Sector Dropdown */}
                    <div className="flex items-center gap-2 w-full sm:w-auto">
                        <span className="text-xs font-semibold text-slate-400">Sector:</span>
                        <select
                            value={selectedSector}
                            onChange={(e) => setSelectedSector(e.target.value)}
                            className="bg-[#0A0F1C] text-slate-300 border border-slate-700/80 text-xs font-semibold rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        >
                            {sectors.map(s => (
                                <option key={s} value={s}>{s}</option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>

            {/* Company Cards Grid */}
            {filteredCompanies.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                    {filteredCompanies.map((c) => (
                        <div 
                            key={c.ticker}
                            className="bg-[#131B2F] border border-slate-800 hover:border-slate-700/80 rounded-xl p-5 shadow-lg flex flex-col justify-between transition-all hover:shadow-blue-500/5 group"
                        >
                            <div>
                                {/* Card Header */}
                                <div className="flex items-start justify-between gap-2 mb-2">
                                    <div>
                                        <h4 className="font-bold text-white text-base group-hover:text-blue-300 transition-colors">
                                            {c.name}
                                        </h4>
                                        <div className="flex items-center gap-2 mt-1">
                                            <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-[#0A0F1C] text-slate-300 border border-slate-800">
                                                {c.exchange} • {c.country}
                                            </span>
                                            <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20">
                                                {c.sector}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Ticker Badge with Copy Button */}
                                    <div className="flex items-center gap-1 bg-[#0A0F1C] border border-blue-500/30 px-2.5 py-1 rounded-lg">
                                        <code className="text-xs font-extrabold text-blue-400 font-mono tracking-wider">
                                            {c.ticker}
                                        </code>
                                        <button
                                            onClick={() => handleCopy(c.ticker)}
                                            className="text-slate-400 hover:text-white transition-colors p-0.5"
                                            title="Copy ticker symbol"
                                        >
                                            {copiedTicker === c.ticker ? (
                                                <Check className="w-3.5 h-3.5 text-emerald-400" />
                                            ) : (
                                                <Copy className="w-3.5 h-3.5" />
                                            )}
                                        </button>
                                    </div>
                                </div>

                                {/* Description */}
                                <p className="text-xs text-slate-400 line-clamp-2 mt-3 leading-relaxed">
                                    {c.description}
                                </p>
                            </div>

                            {/* Action Buttons */}
                            <div className="flex items-center gap-2 pt-4 mt-4 border-t border-slate-800/80">
                                <button
                                    onClick={() => onSelectTicker && onSelectTicker(c.ticker, 'single')}
                                    className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-3 rounded-lg text-xs flex items-center justify-center gap-1.5 transition-colors shadow-sm"
                                >
                                    Analyze <ArrowRight className="w-3.5 h-3.5" />
                                </button>
                                <button
                                    onClick={() => onSelectTicker && onSelectTicker(c.ticker, 'compare')}
                                    className="bg-[#0A0F1C] hover:bg-slate-800 text-slate-300 hover:text-white font-semibold py-2 px-3 rounded-lg text-xs flex items-center gap-1 border border-slate-700/80 transition-colors"
                                    title="Add to Peer Comparison"
                                >
                                    <GitCompare className="w-3.5 h-3.5 text-slate-400" /> Compare
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="bg-[#131B2F] p-12 rounded-xl border border-slate-800 text-center shadow-lg">
                    <Search className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                    <h3 className="text-base font-bold text-white mb-1">No Companies Found</h3>
                    <p className="text-xs text-slate-400 max-w-sm mx-auto mb-4">
                        We couldn't find a listed company matching "{searchQuery}". You can still analyze any custom ticker directly in Single Analysis.
                    </p>
                    <button
                        onClick={() => { setSearchQuery(''); setSelectedMarket('All'); setSelectedSector('All'); }}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-lg border border-slate-700 transition-colors"
                    >
                        Reset Filters
                    </button>
                </div>
            )}
        </div>
    );
}

