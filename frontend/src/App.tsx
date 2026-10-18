import { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { AnalyzerPage } from './pages/AnalyzerPage';
import { HistoryPage } from './pages/HistoryPage';
import { InsightsPage } from './pages/InsightsPage';
import { getHealth } from './services/api';
import { HealthData } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<'analyzer' | 'history' | 'insights'>('analyzer');
  const [health, setHealth] = useState<HealthData | null>(null);

  useEffect(() => {
    getHealth()
      .then((data) => setHealth(data))
      .catch((err) => console.error('Health check failed:', err));
  }, []);

  return (
    <div className="min-h-screen bg-dark-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Navigation */}
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} health={health} />

      {/* Main Pages Content */}
      <main className="flex-1 flex flex-col">
        {activeTab === 'analyzer' && <AnalyzerPage />}
        {activeTab === 'history' && <HistoryPage />}
        {activeTab === 'insights' && <InsightsPage />}
      </main>

      {/* Minimal Footer */}
      <footer className="h-8 border-t border-dark-800/80 bg-dark-950 px-6 flex items-center justify-between text-[11px] text-slate-400">
        <div>
          <span>CodeSense — Compiler Diagnostic & Error Reduction System</span>
        </div>
        <div className="flex items-center gap-4">
          <span>Source of Truth: OpenJDK javac</span>
          <span className="text-slate-400">•</span>
          <span>FastAPI</span>
        </div>
      </footer>
    </div>
  );
}
