import React, { useState, useEffect } from 'react';
import { 
  Crown, Check, X, Shield, Sparkles, Zap, Building, 
  ArrowLeft, FileText, CheckCircle2, Clock, AlertTriangle, Info
} from 'lucide-react';
import { fetchSubscriptionStatus } from '../services/api';

export default function SubscriptionView({ onBack, onNavigateGenerate }) {
  const [subStatus, setSubStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchSubscriptionStatus();
      setSubStatus(data);
    } catch (err) {
      console.error('Failed to load subscription status', err);
      setError('Could not retrieve subscription status from backend.');
    } finally {
      setLoading(false);
    }
  };

  const isPremium = subStatus?.tier === 'premium';

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8 animate-in fade-in">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors bg-slate-900/60 border border-slate-800 px-3.5 py-2 rounded-lg"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Reports
        </button>
        <span className="text-xs text-slate-400 flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-blue-400" />
          Finlytics AI Institutional Access
        </span>
      </div>

      {/* Header Banner */}
      <div className="text-center max-w-2xl mx-auto space-y-3">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold">
          <Crown className="w-3.5 h-3.5" />
          Finlytics Subscription Tiers
        </div>
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          Institutional Equity Intelligence
        </h1>
        <p className="text-sm text-slate-400 leading-relaxed">
          Access automated 15-section company valuation dossiers, 50-page ReportLab PDF exports, 
          and deep regulatory filing RAG citations.
        </p>
      </div>

      {/* Current User Status Badge */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 backdrop-blur-sm flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase tracking-wider text-slate-400 font-medium">Your Current Plan:</span>
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                isPremium 
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' 
                  : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
              }`}>
                {loading ? 'Checking...' : (subStatus?.tier_name || 'Standard Analyst (Free Tier)')}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Account: <span className="text-white font-mono">{subStatus?.username || 'Current User'}</span> • Status: <span className="text-emerald-400">Active</span> • Daily Limit: <span className="text-slate-300">{subStatus?.limits?.reports_per_day || '5 reports/day'}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <button
            onClick={onNavigateGenerate}
            className="w-full sm:w-auto bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center justify-center gap-1.5 transition-colors shadow-sm"
          >
            <FileText className="w-4 h-4" />
            Generate Dossier
          </button>
        </div>
      </div>

      {/* Pricing / Feature Comparison Table */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Free Tier Card */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 flex flex-col justify-between space-y-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold text-white">Free Analyst</h3>
                <p className="text-xs text-slate-400 mt-1">Core financial multiples and standard research</p>
              </div>
              <span className="text-2xl font-black text-white">$0 <span className="text-xs font-normal text-slate-400">/mo</span></span>
            </div>

            <div className="pt-4 border-t border-slate-800 space-y-3 text-xs text-slate-300">
              <div className="flex items-center gap-2.5">
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Single company financial metric calculations</span>
              </div>
              <div className="flex items-center gap-2.5">
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>6 Graham & Buffett investment principle hurdles</span>
              </div>
              <div className="flex items-center gap-2.5">
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>15-section institutional dossier generation</span>
              </div>
              <div className="flex items-center gap-2.5">
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Programmatic 50-page PDF report downloads</span>
              </div>
              <div className="flex items-center gap-2.5">
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>MarketPing regulatory filing evidence citations</span>
              </div>
              <div className="flex items-center gap-2.5 text-slate-500">
                <X className="w-4 h-4 text-slate-600 flex-shrink-0" />
                <span>Unlimited batch peer group exports</span>
              </div>
              <div className="flex items-center gap-2.5 text-slate-500">
                <X className="w-4 h-4 text-slate-600 flex-shrink-0" />
                <span>Custom WACC and terminal growth hurdles</span>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800">
            <div className="w-full text-center py-2.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-xs font-medium text-slate-300">
              {isPremium ? 'Included with Account' : 'Current Active Plan'}
            </div>
          </div>
        </div>

        {/* Premium Institutional Tier Card */}
        <div className="bg-gradient-to-b from-blue-950/40 via-slate-900/80 to-slate-900 border-2 border-blue-500/50 rounded-2xl p-6 flex flex-col justify-between space-y-6 relative overflow-hidden shadow-xl shadow-blue-950/30">
          <div className="absolute top-0 right-0 bg-blue-600 text-white font-bold text-[10px] uppercase tracking-widest px-3 py-1 rounded-bl-lg">
            Recommended
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-xl font-bold text-white">Institutional Pro</h3>
                  <Crown className="w-4 h-4 text-amber-400" />
                </div>
                <p className="text-xs text-blue-300/80 mt-1">Enterprise investment research & unbounded RAG</p>
              </div>
              <span className="text-2xl font-black text-white">$99 <span className="text-xs font-normal text-slate-400">/mo</span></span>
            </div>

            <div className="pt-4 border-t border-slate-800 space-y-3 text-xs text-slate-200">
              <div className="flex items-center gap-2.5">
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span className="font-semibold text-white">Everything in Free Analyst, plus:</span>
              </div>
              <div className="flex items-center gap-2.5">
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Unlimited research report generation per day</span>
              </div>
              <div className="flex items-center gap-2.5">
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Configurable WACC hurdle discount & perpetual growth DCF</span>
              </div>
              <div className="flex items-center gap-2.5">
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Deep 3-tier epistemic filings citation retrieval</span>
              </div>
              <div className="flex items-center gap-2.5">
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Full historical valuation multiple percentile bands</span>
              </div>
              <div className="flex items-center gap-2.5">
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Direct PDF streaming and automated markdown export API</span>
              </div>
              <div className="flex items-center gap-2.5">
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>Priority processing queue & dedicated institutional support</span>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800 space-y-2">
            <button
              disabled
              className="w-full text-center py-2.5 rounded-xl bg-blue-600/50 border border-blue-400/40 text-xs font-semibold text-white cursor-not-allowed opacity-90 flex items-center justify-center gap-2"
            >
              <Sparkles className="w-4 h-4 text-amber-300" />
              Upgrade to Institutional Pro (Gateway Coming Soon)
            </button>
            <p className="text-[11px] text-slate-400 text-center flex items-center justify-center gap-1">
              <Info className="w-3.5 h-3.5 text-blue-400" />
              Payment gateway integration is currently in rollout. Free tier includes all 15-section report capabilities.
            </p>
          </div>
        </div>
      </div>

      {/* Feature Transparency Callout */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 text-xs text-slate-400 flex items-start gap-3">
        <Info className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-semibold text-white">Full Transparency & Reproducibility Guarantee</p>
          <p>
            Finlytics AI does not fabricate financial statements or qualitative citations. All valuation multiples are 
            derived directly from verified SEC/BSE/NSE regulatory disclosures and Yahoo Finance market data feeds. 
            Reports generated under your account are strictly isolated and permanently stored in your private workspace.
          </p>
        </div>
      </div>
    </div>
  );
}
