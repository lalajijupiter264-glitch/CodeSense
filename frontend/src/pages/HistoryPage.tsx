import { useState, useEffect } from 'react';
import {
  History,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  RefreshCw,
  X,
  Code
} from 'lucide-react';
import { getHistory, getSubmissionDetail } from '../services/api';
import { SubmissionSummary, AnalysisResponse } from '../types';
import { ErrorCard } from '../components/ErrorCard';

export const HistoryPage = () => {
  const [submissions, setSubmissions] = useState<SubmissionSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedSubmission, setSelectedSubmission] = useState<AnalysisResponse | null>(null);


  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await getHistory();
      setSubmissions(data.submissions);
    } catch (err) {
      console.error('Failed to load history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleInspect = async (subId: string) => {
    try {
      const detail = await getSubmissionDetail(subId);
      setSelectedSubmission(detail);
    } catch (err) {
      console.error('Failed to load detail:', err);
    }
  };


  return (
    <div className="flex-1 flex flex-col p-4 md:p-6 max-w-[1200px] w-full mx-auto gap-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <History className="w-5 h-5 text-indigo-400" />
            Analysis & Error History
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Review your previous Java compilations, detected errors, and improvements over time.
          </p>
        </div>

        <button
          onClick={fetchHistory}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-dark-900 hover:bg-dark-850 text-slate-300 border border-dark-800 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* History Table / Cards */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 text-xs">
          Loading submission history...
        </div>
      ) : submissions.length === 0 ? (
        <div className="p-12 text-center bg-dark-900 border border-dark-800 rounded-xl space-y-2">
          <History className="w-10 h-10 text-slate-500 mx-auto mb-2" />
          <h3 className="font-semibold text-slate-300 text-sm">No Analyses Recorded Yet</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Run an analysis in the Analyzer tab to begin tracking your code submissions and compiler diagnostics.
          </p>
        </div>
      ) : (
        <div className="bg-dark-900 border border-dark-800 rounded-xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-dark-800 bg-dark-950/60 text-slate-400 uppercase tracking-wider font-semibold text-[11px]">
                  <th className="p-3.5 pl-5">Date & Time</th>
                  <th className="p-3.5">Language</th>
                  <th className="p-3.5">Status</th>
                  <th className="p-3.5">Errors & Types</th>
                  <th className="p-3.5">Duration</th>
                  <th className="p-3.5 text-right pr-5">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dark-800/60">
                {submissions.map((sub) => {
                  const dateStr = new Date(sub.created_at).toLocaleString();
                  return (
                    <tr
                      key={sub.id}
                      className="hover:bg-dark-850/50 transition-colors cursor-pointer"
                      onClick={() => handleInspect(sub.id)}
                    >
                      <td className="p-3.5 pl-5 font-mono text-slate-300">
                        {dateStr}
                      </td>
                      <td className="p-3.5 font-medium text-slate-300">
                        <span className="px-2 py-0.5 rounded bg-dark-800 text-indigo-300 font-mono text-[11px] border border-dark-700">
                          {sub.language.toUpperCase()}
                        </span>
                      </td>
                      <td className="p-3.5">
                        {sub.compile_success ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-[11px] font-medium border border-emerald-500/20">
                            <CheckCircle2 className="w-3 h-3" /> Clean
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 text-[11px] font-medium border border-red-500/20">
                            <AlertCircle className="w-3 h-3" /> {sub.error_count} Error{sub.error_count > 1 ? 's' : ''}
                          </span>
                        )}
                      </td>
                      <td className="p-3.5 text-slate-300">
                        {sub.main_error_type ? (
                          <div className="flex items-center gap-1.5">
                            <span className="font-semibold text-slate-200">
                              {sub.main_error_type}
                            </span>
                            {sub.error_count > 1 && (
                              <span className="text-slate-400 text-[11px]">
                                + {sub.error_count - 1} more
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-400 italic">None</span>
                        )}
                      </td>
                      <td className="p-3.5 font-mono text-slate-400">
                        {sub.compilation_time_ms}ms
                      </td>
                      <td className="p-3.5 text-right pr-5">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleInspect(sub.id);
                          }}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-dark-800 hover:bg-dark-700 text-slate-200 text-xs font-medium border border-dark-700 transition-colors"
                        >
                          <ExternalLink className="w-3 h-3 text-slate-400" />
                          Inspect
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Submission Detail Modal */}
      {selectedSubmission && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-dark-900 border border-dark-800 rounded-2xl max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-4 border-b border-dark-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Code className="w-5 h-5 text-indigo-400" />
                <h3 className="font-bold text-sm text-white">
                  Submission Diagnostics
                </h3>
                <span className="text-xs text-slate-400 font-mono">
                  ({selectedSubmission.compilation_time_ms}ms)
                </span>
              </div>
              <button
                onClick={() => setSelectedSubmission(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-dark-800 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-5 space-y-4">
              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-400">Result:</span>
                {selectedSubmission.success ? (
                  <span className="text-emerald-400 font-semibold text-xs flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Successful Compilation
                  </span>
                ) : (
                  <span className="text-red-400 font-semibold text-xs flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5" /> {selectedSubmission.errors.length} Compiler Error(s)
                  </span>
                )}
              </div>

              {/* Errors list */}
              {selectedSubmission.errors.length > 0 && (
                <div className="space-y-3">
                  <h4 className="text-xs uppercase font-bold text-slate-400 tracking-wider">
                    Errors & Explanations
                  </h4>
                  {selectedSubmission.errors.map((detail, idx) => (
                    <ErrorCard
                      key={idx}
                      index={idx}
                      detail={detail}
                      isSelected={false}
                      onSelect={() => {}}
                    />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
