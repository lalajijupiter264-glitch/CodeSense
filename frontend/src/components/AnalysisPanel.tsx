import { useState } from 'react';
import {
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  Clock,
  Sparkles,
  Info,
  Terminal,
  Code,
  ShieldCheck,
  Cpu
} from 'lucide-react';
import { AnalysisResponse, ErrorDetail } from '../types';
import { ErrorCard } from './ErrorCard';

interface AnalysisPanelProps {
  analysis: AnalysisResponse | null;
  loading: boolean;
  selectedErrorIndex: number;
  onSelectError: (index: number) => void;
  onApplyFix?: (fixSnippet: string, line: number) => void;
}

export const AnalysisPanel = ({
  analysis,
  loading,
  selectedErrorIndex,
  onSelectError,
  onApplyFix,
}: AnalysisPanelProps) => {
  const [activeTab, setActiveTab] = useState<'errors' | 'explanation' | 'warnings'>('errors');

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center bg-dark-900 border border-dark-800 rounded-lg">
        <div className="w-12 h-12 rounded-full border-2 border-indigo-500/30 border-t-indigo-500 animate-spin mb-4" />
        <h3 className="font-semibold text-slate-200 text-sm mb-1">Analyzing Code</h3>
        <p className="text-xs text-slate-400 max-w-xs leading-relaxed">
          Invoking OpenJDK javac, parsing diagnostics, and compiling educational explanations...
        </p>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center bg-dark-900 border border-dark-800 rounded-lg">
        <div className="w-12 h-12 rounded-xl bg-dark-800/80 border border-dark-700/80 flex items-center justify-center text-slate-400 mb-4">
          <Terminal className="w-6 h-6" />
        </div>
        <h3 className="font-semibold text-slate-200 text-sm mb-1.5">Ready to Analyze</h3>
        <p className="text-xs text-slate-400 max-w-xs leading-relaxed">
          Write or paste Java code into the editor and click <span className="text-indigo-400 font-semibold">"Analyze Code"</span> to detect compiler errors and inspect beginner-friendly fixes.
        </p>
      </div>
    );
  }

  const hasErrors = analysis.errors.length > 0;
  const hasWarnings = analysis.warnings.length > 0;
  const selectedDetail: ErrorDetail | undefined = analysis.errors[selectedErrorIndex];

  // PHASE 6: If compilation succeeded with zero errors
  if (analysis.success || (!hasErrors && analysis.exit_code === 0)) {
    return (
      <div className="h-full flex flex-col bg-dark-900 border border-dark-800 rounded-lg overflow-hidden">
        {/* Success Header Banner */}
        <div className="p-4 border-b border-dark-800 bg-emerald-950/20 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <span className="font-semibold text-emerald-400 text-sm">
              Compilation Succeeded
            </span>
          </div>
          <span className="text-xs px-2.5 py-1 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-mono font-medium">
            Exit Code {analysis.exit_code}
          </span>
        </div>

        {/* Clean Success Content */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col items-center justify-center text-center max-w-lg mx-auto w-full space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shadow-xl shadow-emerald-500/5">
            <ShieldCheck className="w-8 h-8" />
          </div>

          <div>
            <h3 className="text-lg font-bold text-slate-100 flex items-center justify-center gap-2 mb-2">
              <span className="text-emerald-400">✓</span> No compiler errors found
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed max-w-sm mx-auto">
              {analysis.summary_message || 'Your Java code compiled cleanly with zero diagnostic errors.'}
            </p>
          </div>

          {/* Compilation Metrics Grid */}
          <div className="grid grid-cols-3 gap-3 w-full">
            <div className="p-3 rounded-xl bg-dark-950/70 border border-dark-800 text-center">
              <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1 flex items-center justify-center gap-1">
                <Code className="w-3 h-3" /> Language
              </span>
              <span className="text-sm font-mono font-semibold text-slate-200">
                {analysis.language ? analysis.language.toUpperCase() : 'JAVA'}
              </span>
            </div>

            <div className="p-3 rounded-xl bg-dark-950/70 border border-dark-800 text-center">
              <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1 flex items-center justify-center gap-1">
                <Clock className="w-3 h-3" /> Time
              </span>
              <span className="text-sm font-mono font-semibold text-emerald-400">
                {analysis.compilation_time_ms} ms
              </span>
            </div>

            <div className="p-3 rounded-xl bg-dark-950/70 border border-dark-800 text-center">
              <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1 flex items-center justify-center gap-1">
                <Cpu className="w-3 h-3" /> Exit Code
              </span>
              <span className="text-sm font-mono font-semibold text-slate-200">
                {analysis.exit_code}
              </span>
            </div>
          </div>

          {/* If there are any static warnings/suggestions on clean build */}
          {hasWarnings && (
            <div className="w-full text-left pt-4 border-t border-dark-800">
              <h4 className="text-xs font-semibold text-amber-400 flex items-center gap-1.5 mb-3">
                <AlertTriangle className="w-3.5 h-3.5" />
                Code Suggestions ({analysis.warnings.length})
              </h4>
              <div className="space-y-2">
                {analysis.warnings.map((w, idx) => (
                  <div key={w.id || idx} className="p-3 rounded-lg bg-amber-950/15 border border-amber-900/30 text-xs">
                    <span className="font-semibold text-amber-300 block mb-0.5">{w.title} (Line {w.line})</span>
                    <p className="text-slate-300 text-[11px]">{w.message}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ERRORS DETECTED: Show full diagnostics interface
  return (
    <div className="h-full flex flex-col bg-dark-900 border border-dark-800 rounded-lg overflow-hidden">
      {/* Top Header & Metrics */}
      <div className="p-3.5 border-b border-dark-800 bg-dark-950/40 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-red-500/10 text-red-400 border border-red-500/20 text-xs font-semibold">
            <AlertCircle className="w-3.5 h-3.5" />
            {analysis.errors.length} Error{analysis.errors.length > 1 ? 's' : ''}
          </span>

          {hasWarnings && (
            <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20 text-xs font-medium">
              <AlertTriangle className="w-3.5 h-3.5" />
              {analysis.warnings.length} Suggestion{analysis.warnings.length > 1 ? 's' : ''}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>{analysis.compilation_time_ms}ms</span>
          <span className="text-slate-600">|</span>
          <span>Exit {analysis.exit_code}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center border-b border-dark-800 px-3 bg-dark-950/20">
        <button
          onClick={() => setActiveTab('errors')}
          className={`flex items-center gap-1.5 px-3 py-2.5 text-xs font-medium border-b-2 transition-all ${
            activeTab === 'errors'
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <span>Errors</span>
          {hasErrors && (
            <span className="px-1.5 py-0.2 rounded-full bg-red-500/20 text-red-400 text-[10px] font-bold">
              {analysis.errors.length}
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('explanation')}
          className={`flex items-center gap-1.5 px-3 py-2.5 text-xs font-medium border-b-2 transition-all ${
            activeTab === 'explanation'
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Detailed Explanation</span>
        </button>

        {hasWarnings && (
          <button
            onClick={() => setActiveTab('warnings')}
            className={`flex items-center gap-1.5 px-3 py-2.5 text-xs font-medium border-b-2 transition-all ${
              activeTab === 'warnings'
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>Suggestions</span>
            <span className="px-1.5 py-0.2 rounded-full bg-amber-500/20 text-amber-400 text-[10px] font-bold">
              {analysis.warnings.length}
            </span>
          </button>
        )}
      </div>

      {/* Tab Content Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* TAB 1: ERRORS LIST */}
        {activeTab === 'errors' && (
          <div className="space-y-4">
            {analysis.errors.map((detail, idx) => (
              <ErrorCard
                key={detail.error.id || idx}
                index={idx}
                detail={detail}
                isSelected={selectedErrorIndex === idx}
                onSelect={() => onSelectError(idx)}
                onApplyFix={onApplyFix}
              />
            ))}
          </div>
        )}

        {/* TAB 2: DETAILED EXPLANATION */}
        {activeTab === 'explanation' && (
          <>
            {selectedDetail ? (
              <div className="space-y-4 text-xs">
                <div className="p-4 rounded-xl bg-dark-950/80 border border-dark-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-white">
                      {selectedDetail.explanation?.title || selectedDetail.classification.subcategory}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-dark-800 text-slate-400 font-mono">
                      Line {selectedDetail.error.line}:{selectedDetail.error.column || 1}
                    </span>
                  </div>

                  <p className="text-slate-300 leading-relaxed text-xs">
                    {selectedDetail.explanation?.what_happened}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-900/30 space-y-2">
                  <span className="font-semibold text-indigo-400 flex items-center gap-1.5">
                    <Info className="w-4 h-4" /> Root Cause Analysis
                  </span>
                  <p className="text-slate-300 leading-relaxed">
                    {selectedDetail.explanation?.why_it_happened}
                  </p>
                </div>

                {selectedDetail.explanation?.suggested_fix && (
                  <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-900/30 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-emerald-400 flex items-center gap-1.5">
                        <Code className="w-4 h-4" /> Recommended Correction
                      </span>
                      {onApplyFix && selectedDetail.explanation.fix_available && selectedDetail.explanation.corrected_code && (
                        <button
                          type="button"
                          onClick={() => onApplyFix(selectedDetail.explanation?.corrected_code || '', selectedDetail.error.line)}
                          className="px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-medium"
                        >
                          Apply Fix
                        </button>
                      )}
                    </div>
                    <p className="text-emerald-200/90 text-xs leading-relaxed mb-2">
                      {selectedDetail.explanation.suggested_fix}
                    </p>
                    {selectedDetail.explanation.fix_available && selectedDetail.explanation.corrected_code ? (
                      <pre className="p-2.5 rounded bg-dark-950 font-mono text-emerald-300 text-xs overflow-x-auto border border-emerald-900/40">
                        {selectedDetail.explanation.corrected_code}
                      </pre>
                    ) : (
                      <div className="p-2.5 rounded bg-dark-950/70 border border-slate-800 text-slate-400 text-[11px]">
                        <span className="font-semibold text-slate-300 block mb-0.5">Automatic fix is not available for this error.</span>
                        <span>{selectedDetail.explanation.fix_explanation || "A safe automatic correction could not be determined reliably without ambiguity."}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="p-6 text-center text-slate-400 text-xs">
                Select an error from the Errors tab to see its deep explanation.
              </div>
            )}
          </>
        )}

        {/* TAB 3: STATIC ANALYSIS WARNINGS */}
        {activeTab === 'warnings' && (
          <div className="space-y-3">
            {analysis.warnings.map((w, idx) => (
              <div
                key={w.id || idx}
                className="p-3.5 rounded-xl bg-dark-950/70 border border-amber-500/20 text-xs space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-amber-300 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                    {w.title}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-dark-800 text-slate-400 font-mono text-[11px]">
                    Line {w.line}
                  </span>
                </div>

                <p className="text-slate-300">{w.message}</p>

                {w.why_it_matters && (
                  <p className="text-slate-400 text-[11px] italic">
                    Why it matters: {w.why_it_matters}
                  </p>
                )}

                {w.suggestion && (
                  <div className="p-2 rounded bg-amber-950/20 border border-amber-900/30 text-amber-200/90 font-mono text-[11px]">
                    Suggestion: {w.suggestion}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
