import React from 'react';

const StatusBadge = ({ status }) => {
    switch (status) {
        case 'Pass':
            return <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-medium uppercase tracking-wide">Pass</span>;
        case 'Fail':
            return <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-medium uppercase tracking-wide">Fail</span>;
        case 'Unavailable':
            return <span className="px-2 py-1 bg-slate-100 text-slate-600 rounded text-xs font-medium uppercase tracking-wide">Unavailable</span>;
        default:
            return null;
    }
};

export default function PrincipleEvaluations({ evaluation }) {
    if (!evaluation) return null;

    return (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200 mt-6">
            <div className="flex justify-between items-end mb-4">
                <h3 className="text-lg font-bold text-slate-800">Investment Principles</h3>
                <p className="text-sm font-medium text-slate-600 bg-slate-50 px-3 py-1 rounded">Score: {evaluation.passed_count} / {evaluation.total_count} Passed</p>
            </div>
            
            <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                    <thead className="text-xs text-slate-500 uppercase bg-slate-50 border-b border-slate-200">
                        <tr>
                            <th className="px-4 py-3">Principle</th>
                            <th className="px-4 py-3">Required</th>
                            <th className="px-4 py-3">Actual</th>
                            <th className="px-4 py-3">Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {evaluation.evaluations.map((ev, i) => (
                            <tr key={i} className="border-b border-slate-100 last:border-0 hover:bg-slate-50">
                                <td className="px-4 py-3 font-medium text-slate-900">
                                    {ev.principle_name}
                                    {ev.status === 'Unavailable' && <p className="text-xs text-slate-400 font-normal mt-1">{ev.explanation}</p>}
                                </td>
                                <td className="px-4 py-3 text-slate-600">{ev.required_threshold}</td>
                                <td className="px-4 py-3 text-slate-900 font-medium">
                                    {ev.actual_value !== null ? ev.actual_value.toFixed(4) : 'Data unavailable'}
                                </td>
                                <td className="px-4 py-3"><StatusBadge status={ev.status} /></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            
            <div className="mt-6 p-4 bg-amber-50 rounded-md border border-amber-200">
                <p className="text-xs text-amber-800 font-medium leading-relaxed">
                    {evaluation.summary_text}
                </p>
            </div>
        </div>
    );
}
