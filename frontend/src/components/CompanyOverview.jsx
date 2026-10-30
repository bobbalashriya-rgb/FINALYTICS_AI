import React from 'react';
import { formatCurrency } from '../utils/formatters';

export default function CompanyOverview({ profile }) {
    if (!profile) return null;
    return (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-slate-200">
            <h2 className="text-xl font-bold text-slate-800 mb-2">{profile.name} ({profile.ticker})</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                <div>
                    <p className="text-sm text-slate-500">Sector</p>
                    <p className="font-medium text-slate-900">{profile.sector || 'Data unavailable'}</p>
                </div>
                <div>
                    <p className="text-sm text-slate-500">Industry</p>
                    <p className="font-medium text-slate-900">{profile.industry || 'Data unavailable'}</p>
                </div>
                <div>
                    <p className="text-sm text-slate-500">Current Price</p>
                    <p className="font-medium text-slate-900">{formatCurrency(profile.current_price)}</p>
                </div>
                <div>
                    <p className="text-sm text-slate-500">Market Cap</p>
                    <p className="font-medium text-slate-900">{formatCurrency(profile.market_cap)}</p>
                </div>
            </div>
            <p className="text-xs text-slate-400 mt-4">Source: yfinance (Raw Market Data)</p>
        </div>
    );
}
