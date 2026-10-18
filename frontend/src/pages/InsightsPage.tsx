import { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  Award,
  BookOpen,
  RefreshCw
} from 'lucide-react';

import { getInsights } from '../services/api';
import { InsightsResponse } from '../types';

export const InsightsPage = () => {
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchInsights = async () => {
    setLoading(true);
    try {
      const data = await getInsights();
      setInsights(data);
    } catch (err) {
      console.error('Failed to load insights:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-12 text-slate-400 text-xs">
        Compiling error analytics and learning insights...
      </div>
    );
  }

  if (!insights || insights.total_submissions === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 max-w-lg mx-auto text-center space-y-3">
        <div className="w-12 h-12 rounded-xl bg-indigo-950/40 border border-indigo-500/20 flex items-center justify-center text-indigo-400 mx-auto">
          <BarChart3 className="w-6 h-6" />
        </div>
        <h3 className="font-bold text-slate-200 text-base">No Error Profile Yet</h3>
        <p className="text-xs text-slate-400 leading-relaxed">
          Analyze a few Java programs in the Analyzer tab to begin building your personalized error taxonomy profile and learning recommendations.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col p-4 md:p-6 max-w-[1200px] w-full mx-auto gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-400" />
            Learning Insights & Error Profile
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Identify recurring mistakes and follow targeted recommendations to write cleaner Java code.
          </p>
        </div>

        <button
          onClick={fetchInsights}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-dark-900 hover:bg-dark-850 text-slate-300 border border-dark-800 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

      {/* Top 4 Metrics Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-dark-900 border border-dark-800">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Total Submissions
          </span>
          <span className="text-2xl font-bold text-white font-mono">
            {insights.total_submissions}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-dark-900 border border-dark-800">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Errors Detected
          </span>
          <span className="text-2xl font-bold text-red-400 font-mono">
            {insights.total_errors}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-dark-900 border border-dark-800">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Clean Compilations
          </span>
          <span className="text-2xl font-bold text-emerald-400 font-mono">
            {insights.successful_compilations}
          </span>
        </div>

        <div className="p-4 rounded-xl bg-dark-900 border border-dark-800">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Primary Error Area
          </span>
          <span className="text-sm font-bold text-indigo-300 truncate block">
            {insights.most_common_category || 'None'}
          </span>
        </div>
      </div>

      {/* Improvement Trend Banner */}
      <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/20 flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
          <TrendingUp className="w-5 h-5" />
        </div>
        <div>
          <span className="text-xs font-semibold text-indigo-300 block">
            Skill Trajectory & Trend
          </span>
          <p className="text-xs text-slate-300 mt-0.5">
            {insights.improvement_trend}
          </p>
        </div>
      </div>

      {/* Split Section: Error Profile Distribution vs Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Error Profile Distribution */}
        <div className="lg:col-span-6 bg-dark-900 border border-dark-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Award className="w-4 h-4 text-amber-400" />
              Your Error Profile
            </h3>
            <span className="text-[11px] text-slate-400">Taxonomy Breakdown</span>
          </div>

          <div className="space-y-3.5 pt-2">
            {insights.category_distribution.map((item) => (
              <div key={item.category} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-300 font-medium">
                    {item.display_name}
                  </span>
                  <div className="flex items-center gap-2 font-mono text-slate-400 text-[11px]">
                    <span>{item.count} error{item.count > 1 ? 's' : ''}</span>
                    <span className="font-bold text-white">{item.percentage}%</span>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="h-2 w-full rounded-full bg-dark-950 overflow-hidden border border-dark-800/80">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 to-indigo-600 rounded-full transition-all duration-500"
                    style={{ width: `${item.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {insights.most_common_error && (
            <div className="mt-4 p-3 rounded-lg bg-dark-950 border border-dark-800 text-xs text-slate-300">
              <span className="font-semibold text-amber-400 block mb-0.5">
                Most Frequent Mistake:
              </span>
              Your most common error is <span className="font-mono text-white">{insights.most_common_error}</span>. Review the recommended topics below to reduce this mistake.
            </div>
          )}
        </div>

        {/* Right: Recommended Learning Topics */}
        <div className="lg:col-span-6 bg-dark-900 border border-dark-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-emerald-400" />
              Personalized Recommendations
            </h3>
            <span className="text-[11px] text-slate-400">Targeted Study Plan</span>
          </div>

          <div className="space-y-3 pt-2">
            {insights.recommendations.map((topic, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-dark-950/80 border border-dark-800 space-y-2 text-xs hover:border-dark-700 transition-colors"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold text-slate-100">
                    {topic.title}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-dark-800 text-indigo-400 font-mono text-[10px]">
                    {topic.category}
                  </span>
                </div>

                <p className="text-slate-400 text-[11px] leading-relaxed">
                  {topic.description}
                </p>

                <div className="p-2 rounded bg-emerald-950/20 border border-emerald-900/30 text-emerald-300 text-[11px]">
                  <span className="font-semibold text-emerald-400 block mb-0.5">Key Rule:</span>
                  {topic.key_takeaway}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
