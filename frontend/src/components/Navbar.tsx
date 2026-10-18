import { Code2, History, BarChart3, ShieldCheck, AlertCircle, Sparkles, Cpu } from 'lucide-react';
import { HealthData } from '../types';

interface NavbarProps {
  activeTab: 'analyzer' | 'history' | 'insights';
  setActiveTab: (tab: 'analyzer' | 'history' | 'insights') => void;
  health: HealthData | null;
}

export const Navbar = ({ activeTab, setActiveTab, health }: NavbarProps) => {
  return (
    <header className="h-14 border-b border-dark-800 bg-dark-900/90 backdrop-blur sticky top-0 z-30 px-4 md:px-6 flex items-center justify-between">
      {/* Brand & Tabs */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => setActiveTab('analyzer')}>
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
            <Code2 className="w-5 h-5" />
          </div>
          <div>
            <span className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
              CodeSense
              <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-indigo-500/15 text-indigo-400 border border-indigo-500/30">
                Compiler AI
              </span>
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-dark-950/60 p-1 rounded-lg border border-dark-800/80">
          <button
            onClick={() => setActiveTab('analyzer')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'analyzer'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-dark-850'
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            Analyzer
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'history'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-dark-850'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            History
          </button>
          <button
            onClick={() => setActiveTab('insights')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              activeTab === 'insights'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-dark-850'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            Insights
          </button>
        </nav>
      </div>

      {/* Right Side Status Badges */}
      <div className="flex items-center gap-2.5 text-xs">
        {/* Language Badge */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-dark-800/90 text-slate-300 border border-dark-700 font-mono">
          <Cpu className="w-3.5 h-3.5 text-indigo-400" />
          <span>Java (javac)</span>
        </div>

        {/* Compiler Health */}
        {health?.compiler?.available ? (
          <div
            title={`Active Compiler: ${health.compiler.version}`}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Compiler:</span> Online
          </div>
        ) : (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>Compiler: Checking...</span>
          </div>
        )}

        {/* AI Service Mode */}
        {health?.ai?.enabled ? (
          <div
            title={`Active AI Model: ${health.ai.model}`}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-purple-500/10 text-purple-400 border border-purple-500/20 font-medium"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">AI:</span> {health.ai.model}
          </div>
        ) : (
          <div
            title="Knowledge Base active for 100% deterministic, instant error explanations"
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-sky-500/10 text-sky-400 border border-sky-500/20 font-medium"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>KB Mode</span>
          </div>
        )}
      </div>
    </header>
  );
};
