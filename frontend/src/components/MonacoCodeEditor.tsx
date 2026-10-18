import { useRef, useEffect } from 'react';
import Editor, { OnMount } from '@monaco-editor/react';
import { ParsedCompilerError } from '../types';
import { StaticWarning } from '../types';

interface MonacoCodeEditorProps {
  code: string;
  onChange: (value: string | undefined) => void;
  errors: ParsedCompilerError[];
  warnings: StaticWarning[];
  selectedLine?: number | null;
  selectedColumn?: number | null;
}

export const MonacoCodeEditor = ({
  code,
  onChange,
  errors,
  warnings,
  selectedLine,
  selectedColumn,
}: MonacoCodeEditorProps) => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const editorRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const monacoRef = useRef<any>(null);
  const decorationsRef = useRef<string[]>([]);

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;

    // Define custom dark theme
    monaco.editor.defineTheme('codesense-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'comment', foreground: '64748b', fontStyle: 'italic' },
        { token: 'keyword', foreground: '818cf8', fontStyle: 'bold' },
        { token: 'string', foreground: '34d399' },
        { token: 'number', foreground: 'f59e0b' },
        { token: 'type', foreground: '38bdf8' },
      ],
      colors: {
        'editor.background': '#0d111c',
        'editor.foreground': '#f1f5f9',
        'editor.lineHighlightBackground': '#161e3150',
        'editorLineNumber.foreground': '#475569',
        'editorLineNumber.activeForeground': '#818cf8',
        'editorGutter.background': '#090d16',
        'editorCursor.foreground': '#818cf8',
      },
    });
    monaco.editor.setTheme('codesense-dark');
  };

  // Synchronize Markers (Squiggly underlines) whenever errors or warnings change
  useEffect(() => {
    if (!monacoRef.current || !editorRef.current) return;
    const monaco = monacoRef.current;
    const model = editorRef.current.getModel();
    if (!model) return;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const markers: any[] = [];

    // Compiler errors
    errors.forEach((err) => {
      const line = Math.max(1, err.line);
      const col = err.column || 1;
      const lineLength = model.getLineLength(line) || 80;
      markers.push({
        severity: monaco.MarkerSeverity.Error,
        message: err.message,
        startLineNumber: line,
        startColumn: col > 1 ? col - 1 : 1,
        endLineNumber: line,
        endColumn: Math.max(col + 5, lineLength + 1),
      });
    });

    // Static warnings
    warnings.forEach((warn) => {
      const line = Math.max(1, warn.line);
      const lineLength = model.getLineLength(line) || 80;
      markers.push({
        severity: monaco.MarkerSeverity.Warning,
        message: `${warn.title}: ${warn.message}`,
        startLineNumber: line,
        startColumn: 1,
        endLineNumber: line,
        endColumn: lineLength + 1,
      });
    });

    monaco.editor.setModelMarkers(model, 'codesense-diagnostics', markers);
  }, [errors, warnings]);

  // Handle scrolling and highlighting for selected line and column
  useEffect(() => {
    if (!editorRef.current || !monacoRef.current || !selectedLine) return;
    const editor = editorRef.current;
    const monaco = monacoRef.current;
    const col = selectedColumn || 1;

    editor.revealPositionInCenter({ lineNumber: selectedLine, column: col });
    editor.setPosition({ lineNumber: selectedLine, column: col });

    // Apply high-contrast line decoration
    decorationsRef.current = editor.deltaDecorations(decorationsRef.current, [
      {
        range: new monaco.Range(selectedLine, 1, selectedLine, 1),
        options: {
          isWholeLine: true,
          className: 'monaco-error-line-highlight',
          glyphMarginClassName: 'monaco-error-glyph',
        },
      },
    ]);
  }, [selectedLine, selectedColumn]);

  return (
    <div className="w-full h-full relative rounded-b-lg overflow-hidden border border-dark-800 bg-[#0d111c]">
      <Editor
        height="100%"
        defaultLanguage="java"
        theme="codesense-dark"
        value={code}
        onChange={onChange}
        onMount={handleEditorDidMount}
        options={{
          fontSize: 14,
          fontFamily: "'JetBrains Mono', 'Fira Code', Menlo, monospace",
          fontLigatures: true,
          lineNumbers: 'on',
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          smoothScrolling: true,
          cursorBlinking: 'smooth',
          renderLineHighlight: 'all',
          automaticLayout: true,
          tabSize: 4,
          glyphMargin: true,
          wordWrap: 'on',
          padding: { top: 12, bottom: 12 },
        }}
      />
    </div>
  );
};
