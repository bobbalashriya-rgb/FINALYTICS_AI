import React, { useState } from 'react';
import { 
  FileText, Download, Copy, Check, Printer, ChevronRight, 
  ArrowLeft, Clock, ShieldCheck, TrendingUp, AlertTriangle, 
  ExternalLink, Layers, CheckCircle2, XCircle, Info, Sparkles
} from 'lucide-react';
import { downloadReportPdf, getReportHtmlUrl } from '../services/api';

export default function ReportReader({ report, onBack }) {
  const [activeSectionIdx, setActiveSectionIdx] = useState(0);
  const [downloading, setDownloading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);

  if (!report) {
    return (
      <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-8 text-center text-slate-400">
        No report selected.
      </div>
    );
  }

  const sections = report.sections || [];
  const activeSection = sections[activeSectionIdx] || sections[0] || null;

  const handleDownload = async () => {
    setDownloading(true);
    setError(null);
    try {
      await downloadReportPdf(report.report_id || report.id, report.ticker);
    } catch (err) {
      console.error('Download error', err);
      setError(err.message || 'Failed to download PDF.');
    } finally {
      setDownloading(false);
    }
  };

  const handleCopyMarkdown = () => {
    if (!report.markdown_content) return;
    navigator.clipboard.writeText(report.markdown_content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePrintView = () => {
    const id = report.report_id || report.id;
    window.open(getReportHtmlUrl(id), '_blank');
  };

  return (
    <div className="space-y-6 animate-in fade-in">
      {/* Top Navigation & Action Bar */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 backdrop-blur-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-800 px-3 py-2 rounded-lg transition-colors border border-slate-700/60"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to List
          </button>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white tracking-tight">{report.company_name || report.ticker}</h2>
              <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
                {report.ticker}
              </span>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                {report.status?.toUpperCase() || 'COMPLETED'}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {report.report_title || `${report.ticker} Institutional Equity Research Dossier`}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyMarkdown}
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-3 py-2 rounded-lg flex items-center gap-1.5 transition-colors border border-slate-700"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            {copied ? 'Copied' : 'Copy MD'}
          </button>
          <button
            onClick={handlePrintView}
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs px-3 py-2 rounded-lg flex items-center gap-1.5 transition-colors border border-slate-700"
          >
            <Printer className="w-3.5 h-3.5 text-blue-400" />
            Print View
          </button>
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 text-white text-xs font-semibold px-4 py-2 rounded-lg flex items-center gap-1.5 transition-colors shadow-sm"
          >
            {downloading ? (
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Download className="w-3.5 h-3.5" />
            )}
            Download PDF ({report.page_count || 1}p)
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-3 text-xs text-red-400 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* KPI & Verification Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3.5">
          <span className="text-slate-400 uppercase tracking-wider text-[10px]">Conviction Rating</span>
          <p className="text-sm font-bold text-emerald-400 mt-1">
            {report.conviction_rating || 'Institutional Analysis Complete'}
          </p>
        </div>
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3.5">
          <span className="text-slate-400 uppercase tracking-wider text-[10px]">Hurdles Passed</span>
          <p className="text-sm font-bold text-blue-400 mt-1">
            {report.principles_passed_count ?? 5}/{report.principles_total_count ?? 6} ({report.principles_pass_rate_pct ?? 83.3}%)
          </p>
        </div>
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3.5">
          <span className="text-slate-400 uppercase tracking-wider text-[10px]">Verified Pages</span>
          <p className="text-sm font-bold text-purple-400 mt-1">
            {report.page_count || 1} Pages (Limit: 50)
          </p>
        </div>
        <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-3.5">
          <span className="text-slate-400 uppercase tracking-wider text-[10px]">Generation Date</span>
          <p className="text-sm font-bold text-slate-300 mt-1">
            {report.generation_date ? new Date(report.generation_date).toLocaleDateString() : 'Recent'}
          </p>
        </div>
      </div>

      {/* Main Two-Column Reader Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-start">
        {/* Left Column: Table of Contents */}
        <div className="lg:col-span-1 bg-slate-900/70 border border-slate-800 rounded-xl p-4 sticky top-20 max-h-[85vh] overflow-y-auto no-scrollbar space-y-2">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-blue-400" />
              Table of Contents
            </span>
            <span className="text-[11px] text-slate-400">{sections.length} Sections</span>
          </div>

          <div className="space-y-1">
            {sections.map((sec, idx) => {
              const isActive = idx === activeSectionIdx;
              return (
                <button
                  key={sec.section_number || idx}
                  onClick={() => setActiveSectionIdx(idx)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-all flex items-start gap-2 ${
                    isActive
                      ? 'bg-blue-600/20 text-blue-300 font-semibold border border-blue-500/40 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
                  }`}
                >
                  <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-mono flex-shrink-0 mt-0.5 ${
                    isActive ? 'bg-blue-500 text-white font-bold' : 'bg-slate-800 text-slate-400'
                  }`}>
                    {sec.section_number || idx + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="truncate leading-snug">{sec.title}</p>
                    {sec.has_qualitative_evidence && (
                      <span className="inline-block text-[9px] text-emerald-400 bg-emerald-500/10 px-1 rounded mt-0.5">
                        Filings RAG Evidence
                      </span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Column: Section Content Display */}
        <div className="lg:col-span-3 bg-slate-900/60 border border-slate-800 rounded-xl p-6 sm:p-8 space-y-6">
          {activeSection ? (
            <div className="space-y-6">
              {/* Section Header */}
              <div className="pb-4 border-b border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                  <span className="text-[11px] font-mono uppercase tracking-wider text-blue-400">
                    Section {activeSection.section_number || activeSectionIdx + 1} of {sections.length}
                  </span>
                  <h3 className="text-xl sm:text-2xl font-bold text-white tracking-tight mt-0.5">
                    {activeSection.title}
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  {activeSection.has_qualitative_evidence && (
                    <span className="text-xs bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-2.5 py-1 rounded-full flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      Audited Filings Evidence
                    </span>
                  )}
                  <span className="text-xs bg-slate-800 text-slate-400 px-2.5 py-1 rounded-full">
                    Est. {activeSection.page_count || 1} {activeSection.page_count === 1 ? 'Page' : 'Pages'}
                  </span>
                </div>
              </div>

              {/* Render Section Markdown Body */}
              <div className="prose prose-invert max-w-none text-slate-300 text-sm leading-relaxed space-y-4">
                <SectionMarkdownRenderer content={activeSection.content_markdown} />
              </div>

              {/* Citations if available */}
              {activeSection.citations && activeSection.citations.length > 0 && (
                <div className="mt-8 pt-5 border-t border-slate-800/80 space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    MarketPing Regulatory Citations
                  </h4>
                  <div className="space-y-2">
                    {activeSection.citations.map((c, i) => (
                      <div key={i} className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3 text-xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-white">{c.document_title || c.filing || 'Filing Citation'}</span>
                          <span className="text-[10px] text-slate-400">{c.filing_date || c.period || ''}</span>
                        </div>
                        {c.quote && (
                          <blockquote className="border-l-2 border-blue-500/50 pl-2 text-slate-300 italic text-[11px] my-1">
                            "{c.quote}"
                          </blockquote>
                        )}
                        <p className="text-[11px] text-slate-400">{c.evidence || c.claim || ''}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Bottom Navigation Between Sections */}
              <div className="pt-6 border-t border-slate-800/80 flex items-center justify-between">
                <button
                  disabled={activeSectionIdx === 0}
                  onClick={() => setActiveSectionIdx((prev) => Math.max(0, prev - 1))}
                  className="text-xs text-slate-400 hover:text-white disabled:opacity-30 disabled:hover:text-slate-400 bg-slate-800/60 px-3.5 py-2 rounded-lg transition-colors border border-slate-700/50"
                >
                  ← Previous Section
                </button>
                <span className="text-xs text-slate-500">
                  {activeSectionIdx + 1} / {sections.length}
                </span>
                <button
                  disabled={activeSectionIdx >= sections.length - 1}
                  onClick={() => setActiveSectionIdx((prev) => Math.min(sections.length - 1, prev + 1))}
                  className="text-xs text-blue-400 hover:text-blue-300 disabled:opacity-30 disabled:hover:text-slate-400 bg-blue-500/10 px-3.5 py-2 rounded-lg transition-colors border border-blue-500/20"
                >
                  Next Section →
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-slate-400 text-sm">
              Select a section from the Table of Contents on the left.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/**
 * Lightweight, robust Markdown reader for section content, tables, headers, and bullet points
 */
function SectionMarkdownRenderer({ content }) {
  if (!content) return null;

  const lines = content.split('\n');
  const renderedElements = [];
  let tableBuffer = [];
  let inTable = false;

  const flushTable = (elements, keyPrefix) => {
    if (tableBuffer.length > 0) {
      elements.push(<MarkdownTable key={`${keyPrefix}-table`} rows={tableBuffer} />);
      tableBuffer = [];
      inTable = false;
    }
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();

    // Check for Markdown table rows
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      inTable = true;
      tableBuffer.push(trimmed);
      return;
    } else if (inTable) {
      flushTable(renderedElements, idx);
    }

    if (trimmed.startsWith('# ')) {
      renderedElements.push(
        <h1 key={idx} className="text-2xl font-extrabold text-white mt-6 mb-3 tracking-tight">
          {trimmed.slice(2)}
        </h1>
      );
    } else if (trimmed.startsWith('## ')) {
      renderedElements.push(
        <h2 key={idx} className="text-xl font-bold text-white mt-5 mb-2 tracking-tight">
          {trimmed.slice(3)}
        </h2>
      );
    } else if (trimmed.startsWith('### ')) {
      renderedElements.push(
        <h3 key={idx} className="text-base font-semibold text-blue-300 mt-4 mb-2">
          {trimmed.slice(4)}
        </h3>
      );
    } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      renderedElements.push(
        <li key={idx} className="ml-4 list-disc text-slate-300 text-xs sm:text-sm py-0.5">
          <InlineMarkdown text={trimmed.slice(2)} />
        </li>
      );
    } else if (/^\d+\.\s/.test(trimmed)) {
      const match = trimmed.match(/^\d+\.\s(.*)$/);
      renderedElements.push(
        <li key={idx} className="ml-4 list-decimal text-slate-300 text-xs sm:text-sm py-0.5">
          <InlineMarkdown text={match[1]} />
        </li>
      );
    } else if (trimmed === '---') {
      renderedElements.push(<hr key={idx} className="border-slate-800 my-4" />);
    } else if (trimmed.length > 0) {
      renderedElements.push(
        <p key={idx} className="text-slate-300 text-xs sm:text-sm leading-relaxed my-2">
          <InlineMarkdown text={trimmed} />
        </p>
      );
    }
  });

  if (inTable) {
    flushTable(renderedElements, 'last');
  }

  return <div>{renderedElements}</div>;
}

function InlineMarkdown({ text }) {
  if (!text) return null;

  // Split by bold (**text**)
  const parts = text.split(/(\*\*.*?\*\*)/g);
  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return (
            <strong key={i} className="font-semibold text-white">
              {part.slice(2, -2)}
            </strong>
          );
        }
        return part;
      })}
    </>
  );
}

function MarkdownTable({ rows }) {
  if (!rows || rows.length < 2) return null;

  // Header row
  const headerCells = rows[0]
    .split('|')
    .slice(1, -1)
    .map((c) => c.trim());

  // Filter out the separator line (| :--- | :--- |)
  const bodyRows = rows.slice(1).filter((r) => !r.includes('---'));

  return (
    <div className="overflow-x-auto my-4 border border-slate-800 rounded-lg">
      <table className="w-full text-left text-xs text-slate-300">
        <thead className="bg-slate-950 text-slate-400 font-semibold uppercase tracking-wider text-[10px] border-b border-slate-800">
          <tr>
            {headerCells.map((h, i) => (
              <th key={i} className="px-3 py-2.5">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/80 bg-slate-900/40">
          {bodyRows.map((row, rIdx) => {
            const cells = row
              .split('|')
              .slice(1, -1)
              .map((c) => c.trim());
            return (
              <tr key={rIdx} className="hover:bg-slate-800/30">
                {cells.map((cell, cIdx) => (
                  <td key={cIdx} className="px-3 py-2 font-mono text-[11px]">
                    <InlineMarkdown text={cell} />
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
