import React, { useState } from 'react';
import Dashboard from './pages/Dashboard';
import { 
  LayoutDashboard, Search, Settings, BookOpen, Building2, 
  FileText, Layers, Crown, Bookmark, History, User, FileSearch 
} from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('account'); // Default landing page set to Sign In / Sign Up ('account')
  const [resetKey, setResetKey] = useState(0);

  const handleNav = (tab) => {
    setActiveTab(tab);
    setResetKey((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen bg-[#0A0F1C] font-sans text-slate-50 selection:bg-blue-500/30">
      <header className="border-b border-slate-800/60 sticky top-0 z-10 bg-[#0A0F1C]/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 py-3 sm:px-6 lg:px-8 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 cursor-pointer flex-shrink-0" onClick={() => handleNav('overview')}>
            <div className="w-8 h-8 bg-[#3B82F6] rounded-md flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-blue-500/20">F</div>
            <h1 className="text-xl font-bold text-white tracking-tight">Finlytics AI</h1>
          </div>
          <nav className="flex space-x-1 overflow-x-auto py-1 no-scrollbar">
            <button 
              onClick={() => handleNav('overview')}
              className={`flex items-center gap-2 text-sm px-3.5 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${activeTab === 'overview' ? 'text-blue-400 bg-blue-500/10' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'}`}>
              <LayoutDashboard className="w-4 h-4" />
              Dashboard
            </button>
            <button 
              onClick={() => handleNav('watchlist')}
              className={`flex items-center gap-2 text-sm px-3.5 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${activeTab === 'watchlist' ? 'text-blue-400 bg-blue-500/10' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'}`}>
              <Bookmark className="w-4 h-4" />
              Watchlist
            </button>
            <button 
              onClick={() => handleNav('history')}
              className={`flex items-center gap-2 text-sm px-3.5 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${activeTab === 'history' ? 'text-blue-400 bg-blue-500/10' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'}`}>
              <History className="w-4 h-4" />
              History
            </button>
            <button 
              onClick={() => handleNav('single')}
              className={`flex items-center gap-2 text-sm px-3.5 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${activeTab === 'single' ? 'text-blue-400 bg-blue-500/10' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'}`}>
              <Search className="w-4 h-4" />
              Company Deep Dive
            </button>
            <button 
              onClick={() => handleNav('qualitative')}
              className={`flex items-center gap-2 text-sm px-3.5 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${activeTab === 'qualitative' ? 'text-blue-400 bg-blue-500/10' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'}`}>
              <FileSearch className="w-4 h-4" />
              Qualitative Research
            </button>
            <button 
              onClick={() => handleNav('compare')}
              className={`flex items-center gap-2 text-sm px-3.5 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${activeTab === 'compare' ? 'text-blue-400 bg-blue-500/10' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'}`}>
              <Settings className="w-4 h-4" />
              Peer Comparison
            </button>
            <button 
              onClick={() => handleNav('report')}
              className={`flex items-center gap-2 text-sm px-3.5 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${activeTab === 'report' ? 'text-blue-400 bg-blue-500/10' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'}`}>
              <FileText className="w-4 h-4" />
              Institutional Report
            </button>
            <button 
              onClick={() => handleNav('my-reports')}
              className={`flex items-center gap-2 text-sm px-3.5 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${activeTab === 'my-reports' ? 'text-blue-400 bg-blue-500/10' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'}`}>
              <Layers className="w-4 h-4" />
              My Reports
            </button>
            <button 
              onClick={() => handleNav('directory')}
              className={`flex items-center gap-2 text-sm px-3.5 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${activeTab === 'directory' ? 'text-blue-400 bg-blue-500/10' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'}`}>
              <Building2 className="w-4 h-4" />
              Directory
            </button>
            <button 
              onClick={() => handleNav('config')}
              className={`flex items-center gap-2 text-sm px-3.5 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${activeTab === 'config' ? 'text-blue-400 bg-blue-500/10' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'}`}>
              <BookOpen className="w-4 h-4" />
              Principles
            </button>
          </nav>

          <div className="flex items-center gap-2.5 flex-shrink-0">
            <button
              onClick={() => handleNav('subscription')}
              className="bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-bold text-xs px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all shadow-md shadow-amber-500/10 cursor-pointer"
            >
              <Crown className="w-3.5 h-3.5 fill-slate-950" />
              Subscribe
            </button>
            <button
              onClick={() => handleNav('account')}
              className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-medium border transition-colors ${
                activeTab === 'account'
                  ? 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                  : 'bg-[#131B2F] text-slate-300 hover:text-white border-slate-700/80 hover:bg-slate-800'
              }`}
            >
              <User className="w-3.5 h-3.5" />
              {typeof localStorage !== 'undefined' && localStorage.getItem('finlytics_token') ? 'Account' : 'Sign In'}
            </button>
          </div>
        </div>
      </header>
      <main>
        <Dashboard externalMode={activeTab} setExternalMode={setActiveTab} resetKey={resetKey} />
      </main>
    </div>
  );
}

export default App;