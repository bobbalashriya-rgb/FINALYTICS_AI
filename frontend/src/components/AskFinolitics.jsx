import React, { useState } from 'react';
import { askFinolitics } from '../services/api';
import { Loader2, FileSearch, ArrowRight } from 'lucide-react';

export default function AskFinolitics({ context, onNavigateQualitative, ticker }) {
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState('');
    const [loading, setLoading] = useState(false);

    const handleAsk = async (e) => {
        e.preventDefault();
        if(!question.trim()) return;
        setLoading(true);
        try {
            const res = await askFinolitics(context, question);
            setAnswer(res.answer);
        } catch (err) {
            setAnswer("Error: " + err.message);
        } finally {
            setLoading(false);
        }
    };

    const isQualitativeQuery = answer && (
        answer.toLowerCase().includes('qualitative') ||
        answer.toLowerCase().includes('annual report') ||
        answer.toLowerCase().includes('filing') ||
        answer.toLowerCase().includes('unavailable in the current data') ||
        answer.toLowerCase().includes('not disclose')
    );

    return (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200 mt-6">
            <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-bold text-slate-800">Ask Finolitics</h3>
                {onNavigateQualitative && (
                    <button
                        type="button"
                        onClick={() => onNavigateQualitative(ticker)}
                        className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1 bg-blue-50 px-2.5 py-1 rounded-md border border-blue-200 transition cursor-pointer"
                    >
                        <FileSearch className="w-3.5 h-3.5" />
                        <span>Qualitative Filings Hub</span>
                    </button>
                )}
            </div>
            <p className="text-sm text-slate-500 mb-4">
                Ask interactive questions strictly about quantitative metrics or indexed qualitative filings.
            </p>
            <form onSubmit={handleAsk} className="flex gap-4 mb-4">
                <input 
                    type="text" 
                    value={question} 
                    onChange={(e)=>setQuestion(e.target.value)} 
                    placeholder="e.g. Why did the company fail my valuation principle? Or ask about client concentration..."
                    className="flex-1 border border-slate-300 rounded-md px-4 py-2 text-sm focus:ring-blue-500 focus:border-blue-500 outline-none shadow-inner"
                    disabled={loading}
                />
                <button type="submit" disabled={loading || !question.trim()} className="bg-blue-600 text-white px-5 py-2 rounded-md text-sm font-medium disabled:opacity-50 flex items-center hover:bg-blue-700 transition cursor-pointer">
                    {loading && <Loader2 className="animate-spin h-4 w-4 mr-2" />} Ask AI
                </button>
            </form>
            {answer && (
                <div className="p-5 bg-blue-50 border border-blue-100 rounded-md shadow-sm">
                    <p className="text-blue-900 whitespace-pre-wrap text-sm leading-relaxed">{answer}</p>
                    {isQualitativeQuery && onNavigateQualitative && (
                        <div className="mt-4 pt-3 border-t border-blue-200/60 flex items-center justify-between flex-wrap gap-2">
                            <p className="text-xs text-blue-800 font-medium">
                                Need deeper insights from MD&A, client concentration, or Annual Report filings?
                            </p>
                            <button
                                type="button"
                                onClick={() => onNavigateQualitative(ticker)}
                                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-semibold shadow-sm transition cursor-pointer"
                            >
                                <FileSearch className="w-3.5 h-3.5" />
                                <span>Open Qualitative Research & Ingest Filings</span>
                                <ArrowRight className="w-3 h-3" />
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
