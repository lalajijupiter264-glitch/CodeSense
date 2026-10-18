import { useState } from 'react';
import {
  Lightbulb,
  CheckCircle2,
  Shield,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Wrench,
  HelpCircle,
  Code2,
  Copy,
  Check,
  GraduationCap,
  AlertCircle
} from 'lucide-react';

import { ErrorDetail } from '../types';

interface ErrorCardProps {
  index: number;
  detail: ErrorDetail;
  isSelected: boolean;
  onSelect: () => void;
  onApplyFix?: (fixSnippet: string, line: number) => void;
}

export const ErrorCard = ({
  index,
  detail,
  isSelected,
  onSelect,
  onApplyFix,
}: ErrorCardProps) => {
  const [expanded, setExpanded] = useState(true);
  const [copied, setCopied] = useState(false);
  const { error, classification, explanation } = detail;

  const handleCopy = (text: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Extract Expected and Received types from message if present
  let expectedType: string | null = null;
  let receivedType: string | null = null;
  if (classification.category === 'TYPE_ERROR' && error.message.includes('cannot be converted to')) {
    const parts = error.message.split('cannot be converted to');
    if (parts.length === 2) {
      receivedType = parts[0].replace('incompatible types:', '').trim();
      expectedType = parts[1].trim();
    }
  }

  const confidencePercent = classification.confidence
    ? Math.round(classification.confidence > 1 ? classification.confidence : classification.confidence * 100)
    : 95;

  return (
    <div
      onClick={onSelect}
      className={`rounded-xl border transition-all cursor-pointer overflow-hidden ${
        isSelected
          ? 'border-red-500/80 bg-dark-900/95 shadow-lg shadow-red-500/10 ring-1 ring-red-500/40'
          : 'border-dark-800 bg-dark-900/50 hover:border-dark-700 hover:bg-dark-900/70'
      }`}
    >
      {/* Header */}
      <div className="p-4 flex items-start justify-between gap-3 border-b border-dark-800/60 bg-dark-950/40">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-400 font-mono text-xs font-bold border border-red-500/30">
            ERROR #{index + 1}
          </span>

          {/* Category */}
          <span className="text-[11px] px-2 py-0.5 rounded bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 font-mono font-medium">
            {classification.category}
          </span>

          {/* Subcategory */}
          <span className="text-[11px] px-2 py-0.5 rounded bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 font-mono font-medium">
            {classification.subcategory}
          </span>

          {/* Confidence */}
          <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-mono font-medium">
            {confidencePercent}% match
          </span>

          {/* Line & Column */}
          <span className="text-xs px-2 py-0.5 rounded bg-dark-800 text-slate-300 border border-dark-700 font-mono">
            Line {error.line}{error.column ? `:${error.column}` : ''}
          </span>

          {/* Primary Badge */}
          {error.is_primary && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-400 font-bold border border-amber-500/30 uppercase tracking-wider">
              Primary Error
            </span>
          )}

          {/* Difficulty Badge */}
          {explanation?.difficulty && (
            <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/15 text-purple-300 font-bold border border-purple-500/30 uppercase tracking-wider">
              {explanation.difficulty}
            </span>
          )}
        </div>

        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            setExpanded(!expanded);
          }}
          className="text-slate-400 hover:text-slate-200 p-1 rounded-md hover:bg-dark-800 transition-colors"
          title={expanded ? 'Collapse' : 'Expand'}
        >
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Compiler Message & Snippet */}
      <div className="p-4 space-y-3.5">
        {/* Title */}
        {explanation?.title && (
          <h4 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{explanation.title}</span>
          </h4>
        )}

        <div>
          <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block mb-1">
            Compiler Message
          </span>
          <p className="font-mono text-xs text-red-300/95 bg-red-950/25 border border-red-900/40 p-2.5 rounded-lg break-words leading-relaxed">
            {error.message}
          </p>
        </div>

        {/* Expected vs Received Box */}
        {expectedType && receivedType && (
          <div className="grid grid-cols-2 gap-2 p-3 rounded-lg bg-dark-950/80 border border-dark-800">
            <div className="border-r border-dark-800/80 pr-2">
              <span className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5">Expected Type</span>
              <span className="font-mono text-emerald-400 font-medium text-xs">{expectedType}</span>
            </div>
            <div className="pl-2">
              <span className="text-[10px] uppercase font-bold text-slate-400 block mb-0.5">Received Type</span>
              <span className="font-mono text-red-400 font-medium text-xs">{receivedType}</span>
            </div>
          </div>
        )}

        {/* Collapsible Explanations & Fix */}
        {expanded && explanation && (
          <div className="space-y-4 pt-2 border-t border-dark-800/80 text-xs">
            {/* 1. What happened */}
            {explanation.what_happened && (
              <div>
                <div className="flex items-center gap-1.5 text-sky-400 font-semibold mb-1">
                  <HelpCircle className="w-3.5 h-3.5" />
                  <span>What happened</span>
                </div>
                <p className="text-slate-300 leading-relaxed pl-5">
                  {explanation.what_happened}
                </p>
              </div>
            )}

            {/* 2. Why it happened */}
            {explanation.why_it_happened && (
              <div>
                <div className="flex items-center gap-1.5 text-indigo-400 font-semibold mb-1">
                  <Lightbulb className="w-3.5 h-3.5" />
                  <span>Why it happened</span>
                </div>
                <p className="text-slate-300 leading-relaxed pl-5">
                  {explanation.why_it_happened}
                </p>
              </div>
            )}

            {/* 3. Problematic Code */}
            {(explanation.problematic_code || error.code_snippet) && (
              <div>
                <div className="flex items-center gap-1.5 text-rose-400 font-semibold mb-1">
                  <Code2 className="w-3.5 h-3.5" />
                  <span>Problematic Code (Line {error.line})</span>
                </div>
                <div className="bg-dark-950 rounded-lg p-2.5 border border-red-900/30 font-mono text-xs text-rose-300 overflow-x-auto pl-3">
                  <pre>{explanation.problematic_code || error.code_snippet}</pre>
                </div>
              </div>
            )}

            {/* 4. Suggested Fix */}
            {explanation.suggested_fix && (
              <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-900/30">
                <div className="flex items-center gap-1.5 text-emerald-400 font-semibold mb-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Suggested Fix</span>
                </div>
                <p className="text-emerald-200/90 text-xs leading-relaxed pl-5 mb-2">
                  {explanation.suggested_fix}
                </p>
              </div>
            )}

            {/* 5. Corrected Code / Fix Status */}
            {explanation.fix_available && explanation.corrected_code ? (
              <div className="p-3 rounded-lg bg-dark-950 border border-emerald-500/30">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] font-semibold text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Validated Corrected Code
                    </span>
                    {explanation.validated && (
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-mono">
                        Compiler Verified
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={(e) => handleCopy(explanation.corrected_code || '', e)}
                      className="flex items-center gap-1 px-2 py-0.5 rounded bg-dark-800 hover:bg-dark-700 text-slate-300 text-[11px] transition-colors border border-dark-700"
                      title="Copy corrected code"
                    >
                      {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      <span>{copied ? 'Copied' : 'Copy'}</span>
                    </button>

                    {onApplyFix && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onApplyFix(explanation.corrected_code || '', error.line);
                        }}
                        className="flex items-center gap-1 px-2.5 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-medium transition-all shadow-sm shadow-emerald-600/20"
                      >
                        <Wrench className="w-3 h-3" />
                        Apply Fix
                      </button>
                    )}
                  </div>
                </div>

                <div className="font-mono text-emerald-300 text-xs bg-dark-900/80 p-2.5 rounded border border-emerald-900/30 overflow-x-auto">
                  <pre>{explanation.corrected_code}</pre>
                </div>
              </div>
            ) : (
              <div className="p-3 rounded-lg bg-dark-950/60 border border-slate-800/80 text-xs">
                <div className="flex items-center gap-1.5 text-slate-400 font-medium mb-1">
                  <HelpCircle className="w-3.5 h-3.5 text-amber-400/80" />
                  <span className="text-slate-300 font-semibold">Automatic fix is not available for this error.</span>
                </div>
                <p className="text-slate-400 pl-5 text-[11px] leading-relaxed">
                  {explanation.fix_explanation || "A safe automatic correction cannot be determined reliably without ambiguity. Check the suggested fix explanation above."}
                </p>
              </div>
            )}

            {/* 6. How to prevent it */}
            {explanation.prevention_tip && (
              <div>
                <div className="flex items-center gap-1.5 text-amber-400 font-semibold mb-1">
                  <Shield className="w-3.5 h-3.5" />
                  <span>How to prevent it</span>
                </div>
                <p className="text-slate-300 leading-relaxed pl-5">
                  {explanation.prevention_tip}
                </p>
              </div>
            )}

            {/* 7. Concept to learn next */}
            {explanation.concept_to_learn && (
              <div className="flex items-center justify-between gap-2 pt-2 border-t border-dark-800/60">
                <div className="flex items-center gap-2">
                  <GraduationCap className="w-4 h-4 text-indigo-400" />
                  <span className="text-slate-400 text-[11px]">Recommended Concept:</span>
                  <span className="px-2 py-0.5 rounded-full bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 font-medium text-[11px]">
                    {explanation.concept_to_learn}
                  </span>
                </div>
                {explanation.ai_generated && (
                  <span className="flex items-center gap-1 text-[10px] text-purple-400">
                    <Sparkles className="w-3 h-3" /> AI Generated
                  </span>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
