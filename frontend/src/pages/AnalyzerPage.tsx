import { useState } from 'react';
import {
  Play,

  RotateCcw,
  Trash2,
  Sparkles
} from 'lucide-react';

import { MonacoCodeEditor } from '../components/MonacoCodeEditor';
import { AnalysisPanel } from '../components/AnalysisPanel';
import { analyzeCode, compileCodeOnly } from '../services/api';
import { AnalysisResponse, ParsedCompilerError, StaticWarning } from '../types';

const STARTER_CODE = `public class Main {
    public static void main(String[] args) {
        int age = "twenty";
        System.out.println(age);
    }
}`;

const CODE_PRESETS = [
  {
    name: '1. Type Mismatch (int age = "twenty")',
    code: `public class Main {
    public static void main(String[] args) {
        int age = "twenty";
        System.out.println(age);
    }
}`,
  },
  {
    name: '2. Clean Compilation (Success)',
    code: `public class Main {
    public static void main(String[] args) {
        int age = 20;
        System.out.println(age);
    }
}`,
  },
  {
    name: '3. Missing Semicolon',
    code: `public class Main {
    public static void main(String[] args) {
        System.out.println("Hello")
    }
}`,
  },
  {
    name: '4. Undefined Variable',
    code: `public class Main {
    public static void main(String[] args) {
        System.out.println(message);
    }
}`,
  },
  {
    name: '5. Wrong Method / Cannot Find Symbol',
    code: `public class Main {
    public static void main(String[] args) {
        String name = "CodeSense";
        name.nonExistingMethod();
    }
}`,
  },
  {
    name: '6. Code Quality Warnings',
    code: `public class Main {
    public static void main(String[] args) {
        int unusedSecret = 999;
        String user = "admin";
        if (user == "admin") {
            System.out.println("Logged in");
        }
    }
}`,
  },
  {
    name: '7. Division by Zero (int s = 10 / 0)',
    code: `public class Main {
    public static void main(String[] args) {
        int s = 10 / 0;
        System.out.println(s);
    }
}`,
  },
];

export const AnalyzerPage = () => {
  const [code, setCode] = useState<string>(STARTER_CODE);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedErrorIndex, setSelectedErrorIndex] = useState<number>(0);
  const [selectedLine, setSelectedLine] = useState<number | null>(null);
  const [selectedColumn, setSelectedColumn] = useState<number | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);
  const [statusText, setStatusText] = useState<string>('');

  const handleAnalyze = async () => {
    setLoading(true);
    setApiError(null);
    setStatusText('Compiling via javac...');
    try {
      const result = await analyzeCode(code);
      setAnalysis(result);
      setSelectedErrorIndex(0);
      if (result.errors.length > 0) {
        setSelectedLine(result.errors[0].error.line);
        setSelectedColumn(result.errors[0].error.column || null);
      } else {
        setSelectedLine(null);
        setSelectedColumn(null);
      }
    } catch (err: any) {
      console.error('Analysis failed:', err);
      setApiError(err.message || 'Analysis failed. Please check the backend connection.');
    } finally {
      setLoading(false);
      setStatusText('');
    }
  };

  const handleCompileOnly = async () => {
    setLoading(true);
    setStatusText('Compiling...');
    try {
      const comp = await compileCodeOnly(code);
      const errors = comp.errors || [];
      // Wrap into minimal AnalysisResponse
      setAnalysis({
        submission_id: 'quick-compile',
        language: 'java',
        success: comp.success,
        exit_code: comp.exit_code,
        compilation_time_ms: comp.compilation_time_ms,
        raw_output: comp.raw_stderr || comp.raw_stdout,
        errors: errors.map((e: ParsedCompilerError) => ({
          error: e,
          classification: {
            category: 'COMPILER_ERROR',
            subcategory: e.compiler_code,
            severity: e.severity.toUpperCase(),
            confidence: 0.9,
            description: e.message,
          },
        })),
        warnings: [],
        primary_error: null,
        summary_message: comp.success ? 'Compilation successful!' : `Compilation failed with ${errors.length} error(s).`,
      });
    } catch (err) {
      console.error('Quick compile failed:', err);
    } finally {
      setLoading(false);
      setStatusText('');
    }
  };

  const handleSelectError = (index: number) => {
    setSelectedErrorIndex(index);
    if (analysis && analysis.errors[index]) {
      setSelectedLine(analysis.errors[index].error.line);
      setSelectedColumn(analysis.errors[index].error.column || null);
    }
  };

  const handleApplyFix = (fixSnippet: string, targetLine: number) => {
    if (!fixSnippet) return;
    // If the fix is a complete validated program, replace entire source
    if (fixSnippet.includes('class ') || fixSnippet.includes('import ') || fixSnippet.split('\n').length > 2) {
      setCode(fixSnippet);
      return;
    }
    const lines = code.split('\n');
    if (targetLine > 0 && targetLine <= lines.length) {
      const currentIndent = lines[targetLine - 1].match(/^\s*/)?.[0] || '        ';
      const cleanFix = fixSnippet.trim();
      lines[targetLine - 1] = currentIndent + cleanFix;
      setCode(lines.join('\n'));
    }
  };

  const handlePresetSelect = (presetCode: string) => {
    setCode(presetCode);
    setAnalysis(null);
    setSelectedLine(null);
    setSelectedColumn(null);
    setApiError(null);
  };

  const errors: ParsedCompilerError[] = analysis ? analysis.errors.map((e) => e.error) : [];
  const warnings: StaticWarning[] = analysis ? analysis.warnings : [];

  return (
    <div className="flex-1 flex flex-col p-4 md:p-6 max-w-[1600px] w-full mx-auto gap-4">
      {/* API Connection / Runtime Error Banner */}
      {apiError && (
        <div className="bg-red-950/40 border border-red-800/80 rounded-xl p-3.5 flex items-center justify-between gap-3 text-xs text-red-200 shadow-md">
          <div className="flex items-center gap-2.5">
            <span className="w-2 h-2 rounded-full bg-red-400 animate-ping" />
            <span className="font-semibold">{apiError}</span>
          </div>
          <button
            onClick={() => setApiError(null)}
            className="text-red-400 hover:text-red-200 text-xs px-2 py-1 rounded bg-red-900/30 hover:bg-red-900/50 transition-colors"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Top Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-dark-900 border border-dark-800 p-2.5 rounded-xl">
        <div className="flex items-center gap-2 flex-wrap">
          {/* Preset Selector */}
          <div className="relative inline-block text-left">
            <select
              onChange={(e) => handlePresetSelect(e.target.value)}
              className="bg-dark-950 text-slate-200 border border-dark-700/90 rounded-lg px-3 py-1.5 text-xs font-medium focus:outline-none focus:border-indigo-500 cursor-pointer"
              defaultValue=""
            >
              <option value="" disabled>
                Load Preset Test Case...
              </option>
              {CODE_PRESETS.map((p) => (
                <option key={p.name} value={p.code}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => {
              setCode(STARTER_CODE);
              setAnalysis(null);
              setSelectedLine(null);
              setSelectedColumn(null);
              setApiError(null);
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-dark-800 transition-colors border border-transparent hover:border-dark-700"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset Starter
          </button>

          <button
            onClick={() => {
              setCode('');
              setAnalysis(null);
              setSelectedLine(null);
              setSelectedColumn(null);
              setApiError(null);
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-red-400 hover:bg-dark-800 transition-colors border border-transparent hover:border-dark-700"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Clear
          </button>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleCompileOnly}
            disabled={loading || !code.trim()}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium bg-dark-800 hover:bg-dark-700 text-slate-200 border border-dark-700 transition-all disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 text-slate-400" />
            Compile Only
          </button>

          <button
            onClick={handleAnalyze}
            disabled={loading || !code.trim()}
            className="flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-500 hover:to-indigo-600 text-white shadow-md shadow-indigo-600/25 transition-all disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-indigo-200" />
            {loading ? (statusText || 'Analyzing...') : 'Analyze Code'}
          </button>
        </div>
      </div>

      {/* Main Split Grid */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 min-h-[550px]">
        {/* Left Side: Monaco Editor */}
        <div className="lg:col-span-7 flex flex-col min-h-[450px]">
          <div className="bg-dark-900 border border-b-0 border-dark-800 px-4 py-2 rounded-t-lg flex items-center justify-between text-xs text-slate-400">
            <span className="font-mono text-slate-300 font-medium">Main.java</span>
            <span className="text-[11px]">OpenJDK 17 / javac</span>
          </div>
          <div className="flex-1 min-h-[450px]">
            <MonacoCodeEditor
              code={code}
              onChange={(val) => setCode(val || '')}
              errors={errors}
              warnings={warnings}
              selectedLine={selectedLine}
              selectedColumn={selectedColumn}
            />
          </div>
        </div>

        {/* Right Side: Analysis Results Panel */}
        <div className="lg:col-span-5 flex flex-col min-h-[450px]">
          <AnalysisPanel
            analysis={analysis}
            loading={loading}
            selectedErrorIndex={selectedErrorIndex}
            onSelectError={handleSelectError}
            onApplyFix={handleApplyFix}
          />
        </div>
      </div>
    </div>
  );
};
