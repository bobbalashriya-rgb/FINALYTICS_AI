import React, { useState } from 'react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export default function HistoricalCharts({ historicalData, priceData }) {
    const [chartType, setChartType] = useState('price'); // 'price' or 'financials'

    if ((!historicalData || historicalData.length === 0) && (!priceData || priceData.length === 0)) return null;

    return (
        <div className="bg-[#131B2F] p-6 rounded-xl shadow-sm border border-slate-800 mt-6">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h3 className="text-lg font-bold text-white">Interactive Market & Financial Trends</h3>
                    <p className="text-xs text-slate-400">Source: Real-time yfinance data</p>
                </div>
                <div className="flex gap-2">
                    <button 
                        onClick={() => setChartType('price')}
                        className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${chartType === 'price' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
                    >
                        Stock Price
                    </button>
                    <button 
                        onClick={() => setChartType('financials')}
                        className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${chartType === 'financials' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-300 hover:bg-slate-700'}`}
                    >
                        Financials
                    </button>
                </div>
            </div>

            <div className="h-80">
                {chartType === 'price' && priceData && priceData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={priceData}>
                            <defs>
                                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1E293B" />
                            <XAxis 
                                dataKey="date" 
                                stroke="#64748B" 
                                tick={{fill: '#64748B', fontSize: 12}} 
                                minTickGap={30}
                            />
                            <YAxis 
                                stroke="#64748B" 
                                tick={{fill: '#64748B', fontSize: 12}}
                                domain={['auto', 'auto']}
                                tickFormatter={(v) => `$${v.toFixed(0)}`}
                            />
                            <Tooltip 
                                contentStyle={{ backgroundColor: '#0A0F1C', borderColor: '#1E293B', color: '#F8FAFC' }}
                                itemStyle={{ color: '#E2E8F0' }}
                            />
                            <Area type="monotone" dataKey="close" stroke="#3B82F6" fillOpacity={1} fill="url(#colorPrice)" name="Close Price" strokeWidth={2} />
                        </AreaChart>
                    </ResponsiveContainer>
                ) : chartType === 'financials' && historicalData && historicalData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={historicalData}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1E293B" />
                            <XAxis dataKey="date" stroke="#64748B" tick={{fill: '#64748B', fontSize: 12}} />
                            <YAxis yAxisId="left" stroke="#64748B" tick={{fill: '#64748B', fontSize: 12}} tickFormatter={(v) => `$${(v/1000000).toFixed(0)}M`} />
                            <YAxis yAxisId="right" orientation="right" stroke="#64748B" tick={{fill: '#64748B', fontSize: 12}} tickFormatter={(v) => `${(v*100).toFixed(0)}%`} />
                            <Tooltip 
                                contentStyle={{ backgroundColor: '#0A0F1C', borderColor: '#1E293B', color: '#F8FAFC' }}
                            />
                            <Legend wrapperStyle={{ paddingTop: '10px' }} />
                            <Line yAxisId="left" type="monotone" dataKey="revenue" stroke="#3B82F6" name="Revenue" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                            <Line yAxisId="left" type="monotone" dataKey="net_profit" stroke="#10B981" name="Net Profit" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                            <Line yAxisId="right" type="monotone" dataKey="operating_margin" stroke="#A855F7" name="Operating Margin" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                        </LineChart>
                    </ResponsiveContainer>
                ) : (
                    <div className="flex h-full items-center justify-center text-slate-500">
                        No historical data available for this view.
                    </div>
                )}
            </div>
        </div>
    );
}
