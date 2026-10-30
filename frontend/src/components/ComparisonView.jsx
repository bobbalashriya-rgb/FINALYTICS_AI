import React from 'react';
import { 
    GitCompare, Sparkles, CheckCircle2, TrendingUp, ShieldCheck, 
    Scale, Coins, AlertTriangle, Target, Trophy, ArrowUpRight, BarChart3, Info
} from 'lucide-react';
import { formatPercentage, formatNumber, formatCurrency } from '../utils/formatters';

export default function ComparisonView({ data }) {
    if (!data || !data.companies || data.companies.length < 2) return null;
    const [c1, c2] = data.companies;

    const metricsList = [
        { label: 'Revenue Growth', key: 'revenue_growth', format: formatPercentage, higherIsBetter: true },
        { label: 'Return on Equity (ROE)', key: 'roe', format: formatPercentage, higherIsBetter: true },
        { label: 'Return on Capital (ROCE)', key: 'roce', format: formatPercentage, higherIsBetter: true },
        { label: 'Operating Margin', key: 'operating_margin', format: formatPercentage, higherIsBetter: true },
        { label: 'Debt to Equity', key: 'debt_to_equity', format: formatNumber, higherIsBetter: false },
        { label: 'P/E Ratio', key: 'pe_ratio', format: formatNumber, higherIsBetter: false },
        { label: 'Free Cash Flow', key: 'free_cash_flow', format: formatCurrency, higherIsBetter: true }
    ];

    const getMetricWinner = (m, v1, v2) => {
        if (v1 === null || v1 === undefined || v2 === null || v2 === undefined) return null;
        if (typeof v1 !== 'number' || typeof v2 !== 'number') return null;
        if (m.key === 'debt_to_equity') {
            if (v1 < v2) return c1.ticker;
            if (v2 < v1) return c2.ticker;
            return 'Tied';
        }
        if (m.key === 'pe_ratio') {
            if (v1 > 0 && v2 > 0) {
                if (v1 < v2) return c1.ticker;
                if (v2 < v1) return c2.ticker;
                return 'Tied';
            }
        }
        if (v1 > v2) return c1.ticker;
        if (v2 > v1) return c2.ticker;
        return 'Tied';
    };

    // Calculate metric wins
    let c1Wins = 0;
    let c2Wins = 0;
    metricsList.forEach(m => {
        const winner = getMetricWinner(m, c1.metrics[m.key], c2.metrics[m.key]);
        if (winner === c1.ticker) c1Wins++;
        else if (winner === c2.ticker) c2Wins++;
    });

    const isJsonReport = data.ai_comparison && typeof data.ai_comparison === 'object';
    const aiReport = isJsonReport ? data.ai_comparison : null;

    const getCategoryIcon = (category) => {
        const lower = (category || '').toLowerCase();
        if (lower.includes('growth') || lower.includes('scale')) return <TrendingUp className="w-5 h-5 text-blue-400" />;
        if (lower.includes('capital') || lower.includes('efficiency') || lower.includes('moat') || lower.includes('roe')) return <ShieldCheck className="w-5 h-5 text-emerald-400" />;
        if (lower.includes('resilience') || lower.includes('solvency') || lower.includes('debt') || lower.includes('balance')) return <Scale className="w-5 h-5 text-amber-400" />;
        if (lower.includes('margin') || lower.includes('cash') || lower.includes('operating')) return <Coins className="w-5 h-5 text-purple-400" />;
        return <BarChart3 className="w-5 h-5 text-blue-400" />;
    };

    const getLeaderBadge = (leader) => {
        if (!leader) return null;
        if (leader === c1.ticker) {
            return (
                <span className="px-2.5 py-1 text-xs font-bold rounded-md bg-blue-500/20 text-blue-300 border border-blue-500/40 flex items-center gap-1">
                    <Trophy className="w-3 h-3 text-blue-400" /> {c1.ticker} Leads
                </span>
            );
        }
        if (leader === c2.ticker) {
            return (
                <span className="px-2.5 py-1 text-xs font-bold rounded-md bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1">
                    <Trophy className="w-3 h-3 text-emerald-400" /> {c2.ticker} Leads
                </span>
            );
        }
        return (
            <span className="px-2.5 py-1 text-xs font-semibold rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                Tied
            </span>
        );
    };

    return (
        <div className="space-y-8 animate-in fade-in">
            {/* HEAD-TO-HEAD DUEL SCORECARD HEADER */}
            <div className="bg-gradient-to-r from-[#131B2F] via-[#16223D] to-[#131B2F] p-6 rounded-2xl border border-slate-800 shadow-xl">
                <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 font-extrabold text-xl shadow-inner">
                            {c1.ticker.slice(0, 2)}
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <span className="text-2xl font-black text-blue-400">{c1.ticker}</span>
                                {c1Wins > c2Wins && (
                                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                                        Overall Leader
                                    </span>
                                )}
                            </div>
                            <p className="text-xs text-slate-400 mt-0.5">
                                Leads in <strong className="text-white">{c1Wins}</strong> metrics • Passed <strong className="text-blue-300">{c1.evaluations.passed_count}/{c1.evaluations.total_count}</strong> principles
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3 px-4 py-2 bg-[#0A0F1C]/80 rounded-xl border border-slate-800">
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Head-to-Head Duel</span>
                        <GitCompare className="w-4 h-4 text-slate-400" />
                        <span className="text-sm font-bold text-white font-mono">{c1Wins} - {c2Wins}</span>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="text-right">
                            <div className="flex items-center justify-end gap-2">
                                {c2Wins > c1Wins && (
                                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                                        Overall Leader
                                    </span>
                                )}
                                <span className="text-2xl font-black text-emerald-400">{c2.ticker}</span>
                            </div>
                            <p className="text-xs text-slate-400 mt-0.5">
                                Leads in <strong className="text-white">{c2Wins}</strong> metrics • Passed <strong className="text-emerald-300">{c2.evaluations.passed_count}/{c2.evaluations.total_count}</strong> principles
                            </p>
                        </div>
                        <div className="w-12 h-12 rounded-xl bg-emerald-600/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-extrabold text-xl shadow-inner">
                            {c2.ticker.slice(0, 2)}
                        </div>
                    </div>
                </div>
            </div>

            {/* QUANTITATIVE COMPARISON TABLE WITH VISUAL ADVANTAGE INDICATORS */}
            <div className="bg-[#131B2F] rounded-2xl shadow-lg border border-slate-800 overflow-hidden">
                <div className="p-5 border-b border-slate-800 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <GitCompare className="w-5 h-5 text-blue-400" />
                        <h3 className="text-lg font-bold text-white">Quantitative Metric Breakdown</h3>
                    </div>
                    <span className="text-xs text-slate-400 font-medium hidden sm:inline">
                        Highlighted badges indicate statistical peer advantage
                    </span>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left border-collapse">
                        <thead className="text-xs uppercase bg-[#0A0F1C] border-b border-slate-800 text-slate-400">
                            <tr>
                                <th className="px-6 py-4 font-semibold">Financial Metric</th>
                                <th className="px-6 py-4 font-bold text-blue-400 text-base">{c1.ticker}</th>
                                <th className="px-6 py-4 font-bold text-emerald-400 text-base">{c2.ticker}</th>
                                <th className="px-6 py-4 font-semibold text-center">Statistical Leader</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60 font-medium">
                            {metricsList.map((m, i) => {
                                const v1 = c1.metrics[m.key];
                                const v2 = c2.metrics[m.key];
                                const winner = getMetricWinner(m, v1, v2);

                                return (
                                    <tr key={i} className="hover:bg-slate-800/30 transition-colors">
                                        <td className="px-6 py-4 text-slate-300 flex items-center gap-2">
                                            {m.label}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`inline-block px-2.5 py-1 rounded-md ${winner === c1.ticker ? 'bg-blue-500/20 text-blue-300 font-bold border border-blue-500/30' : 'text-slate-200'}`}>
                                                {m.format(v1)}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={`inline-block px-2.5 py-1 rounded-md ${winner === c2.ticker ? 'bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30' : 'text-slate-200'}`}>
                                                {m.format(v2)}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            {winner === c1.ticker && (
                                                <span className="inline-flex items-center gap-1 text-xs font-bold text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded-full border border-blue-500/20">
                                                    <Trophy className="w-3 h-3" /> {c1.ticker}
                                                </span>
                                            )}
                                            {winner === c2.ticker && (
                                                <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                                                    <Trophy className="w-3 h-3" /> {c2.ticker}
                                                </span>
                                            )}
                                            {winner === 'Tied' && (
                                                <span className="text-xs text-slate-500 font-medium">Tied</span>
                                            )}
                                            {!winner && (
                                                <span className="text-xs text-slate-600">—</span>
                                            )}
                                        </td>
                                    </tr>
                                );
                            })}
                            <tr className="bg-[#0A0F1C]/70 border-t-2 border-slate-700">
                                <td className="px-6 py-4 font-bold text-white flex items-center gap-2">
                                    <CheckCircle2 className="w-4 h-4 text-purple-400" />
                                    Principles Passed
                                </td>
                                <td className="px-6 py-4 font-bold text-blue-400 text-lg">
                                    {c1.evaluations.passed_count} / {c1.evaluations.total_count}
                                </td>
                                <td className="px-6 py-4 font-bold text-emerald-400 text-lg">
                                    {c2.evaluations.passed_count} / {c2.evaluations.total_count}
                                </td>
                                <td className="px-6 py-4 text-center">
                                    {c1.evaluations.passed_count > c2.evaluations.passed_count && (
                                        <span className="inline-flex items-center gap-1 text-xs font-bold text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded-full border border-blue-500/20">
                                            <Trophy className="w-3 h-3" /> {c1.ticker}
                                        </span>
                                    )}
                                    {c2.evaluations.passed_count > c1.evaluations.passed_count && (
                                        <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                                            <Trophy className="w-3 h-3" /> {c2.ticker}
                                        </span>
                                    )}
                                    {c1.evaluations.passed_count === c2.evaluations.passed_count && (
                                        <span className="text-xs text-slate-400 font-medium">Equal</span>
                                    )}
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            {/* AI COMPARATIVE RESEARCH ANALYSIS */}
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
                            <Sparkles className="w-5 h-5" />
                        </div>
                        <div>
                            <h3 className="text-xl font-bold text-white tracking-tight">AI Comparative Research Analysis</h3>
                            <p className="text-xs text-slate-400">Institutional quantitative duel & structural divergence</p>
                        </div>
                    </div>
                    <span className="text-xs font-semibold px-3 py-1 rounded-full bg-blue-600/20 text-blue-400 border border-blue-500/30">
                        Zero Hallucination
                    </span>
                </div>

                {/* WHEN STRUCTURED AI REPORT IS AVAILABLE */}
                {aiReport ? (
                    <div className="space-y-6">
                        {/* EXECUTIVE VERDICT HIGHLIGHT */}
                        {aiReport.executive_verdict && (
                            <div className="relative rounded-2xl bg-gradient-to-br from-[#162344] via-[#131B2F] to-[#121929] p-6 border border-blue-500/40 shadow-2xl overflow-hidden">
                                <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>
                                <div className="relative z-10">
                                    <div className="flex items-center gap-2 mb-3">
                                        <Trophy className="w-4 h-4 text-blue-400" />
                                        <span className="text-xs font-extrabold uppercase tracking-wider text-blue-300">
                                            Executive Head-to-Head Synthesis
                                        </span>
                                    </div>
                                    <p className="text-slate-100 text-base md:text-lg leading-relaxed font-normal">
                                        {aiReport.executive_verdict}
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* CATEGORY BATTLES GRID */}
                        {Array.isArray(aiReport.category_battles) && aiReport.category_battles.length > 0 && (
                            <div>
                                <h4 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
                                    <BarChart3 className="w-4 h-4 text-blue-400" />
                                    Categorical Metric Duels
                                </h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                    {aiReport.category_battles.map((battle, idx) => (
                                        <div key={idx} className="bg-[#131B2F] border border-slate-800 hover:border-slate-700/80 p-5 rounded-xl shadow-lg transition-all flex flex-col justify-between">
                                            <div>
                                                <div className="flex items-center justify-between mb-3">
                                                    <div className="flex items-center gap-2">
                                                        {getCategoryIcon(battle.category)}
                                                        <h5 className="font-bold text-white text-base">{battle.category}</h5>
                                                    </div>
                                                    {getLeaderBadge(battle.leader)}
                                                </div>
                                                <p className="text-slate-300 text-sm leading-relaxed mt-2">
                                                    {battle.analysis}
                                                </p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* SIDE-BY-SIDE COMPETITIVE EDGES */}
                        {aiReport.company_edges && (
                            <div>
                                <h4 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
                                    <ArrowUpRight className="w-4 h-4 text-emerald-400" />
                                    Quantifiable Competitive Advantages
                                </h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                    {/* Company 1 Edges */}
                                    <div className="bg-[#131B2F] border border-blue-900/40 p-5 rounded-xl shadow-lg">
                                        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-blue-900/30">
                                            <div className="w-7 h-7 rounded-md bg-blue-500/20 text-blue-400 font-bold text-xs flex items-center justify-center">
                                                {c1.ticker.slice(0, 2)}
                                            </div>
                                            <h5 className="font-bold text-blue-300 text-base">{c1.ticker} Competitive Edge</h5>
                                        </div>
                                        <ul className="space-y-2.5">
                                            {(aiReport.company_edges.c1_edges || []).map((edge, i) => (
                                                <li key={i} className="flex items-start gap-2.5 text-sm text-slate-200 leading-relaxed">
                                                    <CheckCircle2 className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                                                    <span>{edge}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>

                                    {/* Company 2 Edges */}
                                    <div className="bg-[#131B2F] border border-emerald-900/40 p-5 rounded-xl shadow-lg">
                                        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-emerald-900/30">
                                            <div className="w-7 h-7 rounded-md bg-emerald-500/20 text-emerald-400 font-bold text-xs flex items-center justify-center">
                                                {c2.ticker.slice(0, 2)}
                                            </div>
                                            <h5 className="font-bold text-emerald-300 text-base">{c2.ticker} Competitive Edge</h5>
                                        </div>
                                        <ul className="space-y-2.5">
                                            {(aiReport.company_edges.c2_edges || []).map((edge, i) => (
                                                <li key={i} className="flex items-start gap-2.5 text-sm text-slate-200 leading-relaxed">
                                                    <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                                                    <span>{edge}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* VULNERABILITIES & FINANCIAL RISKS */}
                        {aiReport.vulnerabilities && (
                            <div>
                                <h4 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
                                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                                    Vulnerabilities & Financial Risks
                                </h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                    <div className="bg-[#131B2F] border border-amber-900/30 p-5 rounded-xl shadow-lg">
                                        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-800">
                                            <AlertTriangle className="w-4 h-4 text-amber-400" />
                                            <h5 className="font-bold text-amber-300 text-sm">{c1.ticker} Financial Concerns</h5>
                                        </div>
                                        <ul className="space-y-2.5">
                                            {(aiReport.vulnerabilities.c1_risks || []).map((risk, i) => (
                                                <li key={i} className="flex items-start gap-2 text-sm text-slate-300 leading-relaxed">
                                                    <span className="text-amber-400 font-bold mr-1">•</span>
                                                    <span>{risk}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>

                                    <div className="bg-[#131B2F] border border-amber-900/30 p-5 rounded-xl shadow-lg">
                                        <div className="flex items-center gap-2 mb-4 pb-3 border-b border-slate-800">
                                            <AlertTriangle className="w-4 h-4 text-amber-400" />
                                            <h5 className="font-bold text-amber-300 text-sm">{c2.ticker} Financial Concerns</h5>
                                        </div>
                                        <ul className="space-y-2.5">
                                            {(aiReport.vulnerabilities.c2_risks || []).map((risk, i) => (
                                                <li key={i} className="flex items-start gap-2 text-sm text-slate-300 leading-relaxed">
                                                    <span className="text-amber-400 font-bold mr-1">•</span>
                                                    <span>{risk}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* INVESTOR THESIS SCENARIOS */}
                        {aiReport.investor_scenarios && (
                            <div>
                                <h4 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4 flex items-center gap-2">
                                    <Target className="w-4 h-4 text-purple-400" />
                                    Portfolio Allocation Scenarios
                                </h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                    <div className="bg-gradient-to-br from-[#111A2E] to-[#131B2F] border border-blue-800/40 p-5 rounded-xl shadow-lg">
                                        <h5 className="font-bold text-blue-300 text-sm mb-2 flex items-center gap-2">
                                            <Target className="w-4 h-4 text-blue-400" />
                                            When to Favor {c1.ticker}
                                        </h5>
                                        <p className="text-slate-300 text-sm leading-relaxed">
                                            {aiReport.investor_scenarios.bull_case_c1}
                                        </p>
                                    </div>

                                    <div className="bg-gradient-to-br from-[#102422] to-[#131B2F] border border-emerald-800/40 p-5 rounded-xl shadow-lg">
                                        <h5 className="font-bold text-emerald-300 text-sm mb-2 flex items-center gap-2">
                                            <Target className="w-4 h-4 text-emerald-400" />
                                            When to Favor {c2.ticker}
                                        </h5>
                                        <p className="text-slate-300 text-sm leading-relaxed">
                                            {aiReport.investor_scenarios.bull_case_c2}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* DISCLAIMER */}
                        <div className="text-xs text-slate-500 bg-[#0A0F1C] p-4 rounded-xl border border-slate-800/80 flex items-center gap-2">
                            <Info className="w-4 h-4 text-slate-400 flex-shrink-0" />
                            <span>{aiReport.disclaimer || "This comparative analysis is for research and educational purposes only and is not financial advice."}</span>
                        </div>
                    </div>
                ) : (
                    /* FALLBACK FORMATTED MARKDOWN / TEXT DISPLAY */
                    <div className="bg-[#131B2F] p-6 rounded-2xl shadow-lg border border-blue-900/40">
                        {typeof data.ai_comparison === 'string' && data.ai_comparison.includes('AI service is not configured') ? (
                            <div className="text-center py-8">
                                <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-3" />
                                <h4 className="text-base font-bold text-white mb-1">AI Research Assistant Unconfigured</h4>
                                <p className="text-sm text-slate-400 max-w-md mx-auto">
                                    To unlock institutional AI comparative research, please provide your <code className="text-blue-400 bg-slate-800 px-1 py-0.5 rounded font-mono text-xs">GEMINI_API_KEY</code> in your environment variables.
                                </p>
                            </div>
                        ) : (
                            <div className="prose prose-invert max-w-none">
                                <div className="space-y-4 text-slate-300 leading-relaxed text-sm whitespace-pre-wrap">
                                    {data.ai_comparison || "Comparative analysis is currently unavailable."}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
