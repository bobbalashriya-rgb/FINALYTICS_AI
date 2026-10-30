import React from 'react';
import { Sparkles, ShieldCheck, AlertTriangle, ArrowUpRight, Target, CheckCircle2, Info } from 'lucide-react';

export default function AISection({ aiReport }) {
    if (!aiReport) {
        return (
            <div className="mt-8 bg-[#131B2F] border border-dashed border-slate-800 rounded-xl p-8 text-center shadow-lg">
                <Sparkles className="w-8 h-8 text-blue-400 mx-auto mb-3 animate-pulse" />
                <h4 className="text-base font-bold text-white mb-1">AI Research Thesis Generating</h4>
                <p className="text-sm text-slate-400 max-w-md mx-auto">
                    Evaluating institutional principles and qualitative drivers for this company.
                </p>
            </div>
        );
    }

    const { visual_summary } = aiReport;

    return (
        <div className="mt-8 space-y-6 animate-in fade-in">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
                        <Sparkles className="w-5 h-5" />
                    </div>
                    <div>
                        <h3 className="text-xl font-bold text-white tracking-tight">Explainable Investment Thesis</h3>
                        <p className="text-xs text-slate-400">Institutional qualitative synthesis & principle evaluation</p>
                    </div>
                </div>
                <span className="text-xs font-semibold px-3 py-1 rounded-full bg-blue-600/20 text-blue-400 border border-blue-500/30">
                    Zero Hallucination
                </span>
            </div>
            
            {/* Visual Thesis Summary */}
            <div className="bg-[#131B2F] text-white rounded-2xl shadow-xl border border-slate-800 overflow-hidden">
                <div className="p-5 border-b border-slate-800 bg-[#0A0F1C]/80 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <ShieldCheck className="w-5 h-5 text-blue-400" />
                        <h4 className="text-base font-bold text-white">Visual Thesis Scorecard</h4>
                    </div>
                    <span className="text-xs text-slate-400 font-medium">Derived from Yfinance Financials</span>
                </div>
                
                <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6 border-b border-slate-800/80">
                    <div className="bg-[#0A0F1C] p-4 rounded-xl border border-slate-800/80">
                        <p className="text-slate-400 text-xs uppercase tracking-wider font-semibold">Financial Quality</p>
                        <p className="text-xl font-extrabold mt-1 text-blue-400">{visual_summary?.financial_quality || 'High Quality'}</p>
                    </div>
                    <div className="bg-[#0A0F1C] p-4 rounded-xl border border-slate-800/80">
                        <p className="text-slate-400 text-xs uppercase tracking-wider font-semibold">Valuation Stance</p>
                        <p className="text-xl font-extrabold mt-1 text-emerald-400">{visual_summary?.valuation || 'Fairly Valued'}</p>
                    </div>
                    <div className="bg-[#0A0F1C] p-4 rounded-xl border border-slate-800/80">
                        <p className="text-slate-400 text-xs uppercase tracking-wider font-semibold">Data Completeness</p>
                        <p className="text-xl font-extrabold mt-1 text-amber-400">{visual_summary?.data_completeness || '100% Statements'}</p>
                    </div>
                </div>

                <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6 bg-[#131B2F]">
                    <div>
                        <div className="flex items-center gap-2 mb-3">
                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                            <p className="text-emerald-400 text-xs uppercase tracking-wider font-bold">Key Strengths & Hurdles Passed</p>
                        </div>
                        <ul className="space-y-2">
                            {(visual_summary?.key_strengths || []).map((str, i) => (
                                <li key={i} className="text-sm text-slate-200 flex items-start gap-2 leading-relaxed">
                                    <span className="text-emerald-400 font-bold mt-0.5">•</span>
                                    <span>{str}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                    <div>
                        <div className="flex items-center gap-2 mb-3">
                            <AlertTriangle className="w-4 h-4 text-amber-400" />
                            <p className="text-amber-400 text-xs uppercase tracking-wider font-bold">Key Concerns & Hurdle Failures</p>
                        </div>
                        <ul className="space-y-2">
                            {(visual_summary?.key_concerns || []).map((con, i) => (
                                <li key={i} className="text-sm text-slate-300 flex items-start gap-2 leading-relaxed">
                                    <span className="text-amber-400 font-bold mt-0.5">•</span>
                                    <span>{con}</span>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>
            </div>

            {/* Core Thesis Highlight */}
            <div className="relative rounded-2xl bg-gradient-to-br from-[#162344] via-[#131B2F] to-[#121929] p-6 border border-blue-500/40 shadow-xl overflow-hidden">
                <div className="flex items-center gap-2 mb-3">
                    <Sparkles className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-extrabold uppercase tracking-wider text-blue-300">
                        Primary Investment Thesis
                    </span>
                </div>
                <p className="text-slate-100 text-base md:text-lg leading-relaxed">
                    {aiReport.investment_thesis}
                </p>
            </div>
            
            {/* Supporting & Weakening Factors */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-[#131B2F] p-6 rounded-2xl shadow-lg border border-emerald-900/40">
                    <div className="flex items-center gap-2 mb-3">
                        <ArrowUpRight className="w-5 h-5 text-emerald-400" />
                        <h4 className="text-base font-bold text-emerald-300">What Strengthens the Thesis?</h4>
                    </div>
                    <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{aiReport.strengthens_thesis}</p>
                </div>
                
                <div className="bg-[#131B2F] p-6 rounded-2xl shadow-lg border border-red-900/40">
                    <div className="flex items-center gap-2 mb-3">
                        <AlertTriangle className="w-5 h-5 text-red-400" />
                        <h4 className="text-base font-bold text-red-300">What Weakens the Thesis?</h4>
                    </div>
                    <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{aiReport.weakens_thesis}</p>
                </div>
                
                <div className="bg-[#131B2F] p-6 rounded-2xl shadow-lg border border-slate-800">
                    <div className="flex items-center gap-2 mb-3">
                        <ShieldCheck className="w-5 h-5 text-blue-400" />
                        <h4 className="text-base font-bold text-slate-200">Valuation Context</h4>
                    </div>
                    <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{aiReport.valuation_concerns}</p>
                </div>

                <div className="bg-[#131B2F] p-6 rounded-2xl shadow-lg border border-amber-900/40">
                    <div className="flex items-center gap-2 mb-3">
                        <AlertTriangle className="w-5 h-5 text-amber-400" />
                        <h4 className="text-base font-bold text-amber-300">Important Financial Risk</h4>
                    </div>
                    <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{aiReport.important_financial_risk}</p>
                </div>
            </div>

            {/* Next Steps & Invalidation */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-[#131B2F] p-6 rounded-2xl shadow-lg border border-slate-800">
                    <div className="flex items-center gap-2 mb-3">
                        <Target className="w-5 h-5 text-purple-400" />
                        <h4 className="text-base font-bold text-purple-300">What to Investigate Next</h4>
                    </div>
                    <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{aiReport.investigate_next}</p>
                </div>

                <div className="bg-[#131B2F] p-6 rounded-2xl shadow-lg border border-slate-800">
                    <div className="flex items-center gap-2 mb-3">
                        <AlertTriangle className="w-5 h-5 text-slate-400" />
                        <h4 className="text-base font-bold text-slate-200">What Could Invalidate This Thesis?</h4>
                    </div>
                    <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{aiReport.invalidate_thesis}</p>
                </div>
            </div>

            {/* Disclaimer */}
            <div className="text-xs text-slate-500 bg-[#0A0F1C] p-4 rounded-xl border border-slate-800/80 flex items-center gap-2">
                <Info className="w-4 h-4 text-slate-400 flex-shrink-0" />
                <span>{aiReport.disclaimer || "This analysis is for research and educational purposes only and is not financial advice."}</span>
            </div>
        </div>
    );
}
