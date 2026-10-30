import React from 'react';
import { formatCurrency, formatPercentage, formatNumber } from '../utils/formatters';

const MetricCard = ({ title, value, formatter }) => (
    <div className="bg-white p-5 rounded-lg shadow-sm border border-slate-200 hover:shadow-md hover:border-slate-300 transition-all duration-200 group">
        <p className="text-sm font-medium text-slate-500 group-hover:text-blue-600 transition-colors">{title}</p>
        <p className={`text-xl font-bold mt-2 ${value === null ? 'text-slate-400 font-medium text-base' : 'text-slate-900'}`}>
            {formatter(value)}
        </p>
        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
            <span className="text-[10px] uppercase tracking-wider font-semibold text-slate-400">YFinance Calc</span>
        </div>
    </div>
);

export default function MetricGrid({ metrics }) {
    if (!metrics) return null;
    const m = metrics.metrics;
    
    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mt-6 animate-in fade-in slide-in-from-bottom-2">
            <MetricCard title="Revenue" value={m.revenue} formatter={formatCurrency} />
            <MetricCard title="Revenue Growth" value={m.revenue_growth} formatter={formatPercentage} />
            <MetricCard title="Net Profit" value={m.net_profit} formatter={formatCurrency} />
            <MetricCard title="Profit Growth" value={m.profit_growth} formatter={formatPercentage} />
            <MetricCard title="ROE" value={m.roe} formatter={formatPercentage} />
            <MetricCard title="ROCE" value={m.roce} formatter={formatPercentage} />
            <MetricCard title="Debt to Equity" value={m.debt_to_equity} formatter={formatNumber} />
            <MetricCard title="Operating Margin" value={m.operating_margin} formatter={formatPercentage} />
            <MetricCard title="Free Cash Flow" value={m.free_cash_flow} formatter={formatCurrency} />
            <MetricCard title="P/E Ratio" value={m.pe_ratio} formatter={formatNumber} />
        </div>
    );
}
