import { useCallback, useEffect, useMemo, useState } from "react";
import Editor from "@monaco-editor/react";
import {
  Braces,
  Circle,
  Eraser,
  LoaderCircle,
  Play,
  TerminalSquare,
} from "lucide-react";

const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:5000").replace(
  /\/$/,
  ""
);

const DEFAULT_SOURCE = `#include <stdio.h>

int main(void)
{
    int a = 10;
    int b = 20;
    float average = (a + b) / 2.0f;
    char mark = 'A';
    const char *label = "LexiLab";

    if (a >= b)
    {
        printf("%s: a is greater or equal\\n", label);
    }
    else
    {
        printf("sum = %d, average = %f, grade = %c\\n", a + b, average, mark);
    }

    return 0;
}
`;

const STAT_LABELS = [
  ["Total Tokens", "total"],
  ["Keywords", "keywords"],
  ["Identifiers", "identifiers"],
  ["Constants", "constants"],
  ["Operators", "operators"],
  ["Delimiters", "delimiters"],
  ["Preprocessor", "preprocessor"],
  ["Lexical Errors", "errors"],
];

function parseStatistics(stdout) {
  if (!stdout) {
    return null;
  }

  const stats = {};

  for (const [label, key] of STAT_LABELS) {
    const pattern = new RegExp(
      `${label}\\s*:\\s*(\\d+)`,
      "i"
    );
    const match = stdout.match(pattern);
    if (match) {
      stats[key] = Number(match[1]);
    }
  }

  return Object.keys(stats).length ? stats : null;
}

function formatTerminalOutput({ stdout, stderr, error, emptyHint }) {
  const chunks = [];

  if (stdout && stdout.trim()) {
    chunks.push(stdout.replace(/\s+$/, "\n"));
  }

  if (stderr && stderr.trim()) {
    chunks.push(`--- stderr ---\n${stderr.replace(/\s+$/, "\n")}`);
  }

  if (error) {
    chunks.push(error);
  }

  if (!chunks.length) {
    return emptyHint || "No output was returned by the lexer.";
  }

  return chunks.join("\n");
}

export default function App() {
  const [source, setSource] = useState(DEFAULT_SOURCE);
  const [terminal, setTerminal] = useState(
    "Ready. Write C source in the editor, then click Analyze."
  );
  const [stats, setStats] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState("idle");
  const [backendStatus, setBackendStatus] = useState("checking");

  const checkHealth = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/health`);
      if (!response.ok) {
        setBackendStatus("offline");
        return;
      }
      const data = await response.json();
      setBackendStatus(data.status === "ok" ? "online" : "offline");
    } catch {
      setBackendStatus("offline");
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const timer = window.setInterval(checkHealth, 8000);
    return () => window.clearInterval(timer);
  }, [checkHealth]);

  const backendLabel = useMemo(() => {
    if (backendStatus === "online") return "Backend connected";
    if (backendStatus === "checking") return "Checking backend";
    return "Backend offline";
  }, [backendStatus]);

  const analysisLabel = useMemo(() => {
    if (analyzing) return "Analyzing";
    if (analysisStatus === "success") return "Completed";
    if (analysisStatus === "error") return "Failed";
    return "Idle";
  }, [analyzing, analysisStatus]);

  async function handleAnalyze() {
    if (analyzing) {
      return;
    }

    setAnalyzing(true);
    setAnalysisStatus("running");
    setStats(null);
    setTerminal("Running lexical analysis...");

    try {
      const response = await fetch(`${API_URL}/api/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ source_code: source }),
      });

      let data;
      try {
        data = await response.json();
      } catch {
        setAnalysisStatus("error");
        setTerminal(
          `The backend returned a non-JSON response (HTTP ${response.status}).`
        );
        return;
      }

      const output = formatTerminalOutput({
        stdout: data.stdout,
        stderr: data.stderr,
        error: data.error,
        emptyHint: "The lexer finished but produced no output.",
      });

      setTerminal(output);
      setStats(parseStatistics(data.stdout || ""));

      if (response.ok && data.success) {
        setAnalysisStatus("success");
        setBackendStatus("online");
      } else {
        setAnalysisStatus("error");
        if (response.ok) {
          setBackendStatus("online");
        }
      }
    } catch {
      setAnalysisStatus("error");
      setBackendStatus("offline");
      setStats(null);
      setTerminal(
        `Could not reach the LexiLab backend at ${API_URL}.\n` +
          "Start Flask in a separate terminal, then try Analyze again."
      );
    } finally {
      setAnalyzing(false);
    }
  }

  function handleClear() {
    if (analyzing) {
      return;
    }

    setSource("");
    setStats(null);
    setAnalysisStatus("idle");
    setTerminal("Editor and terminal cleared.");
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <div className="brand-icon" aria-hidden="true">
            <Braces size={18} />
          </div>
          <div>
            <h1>LexiLab</h1>
            <p>Finite Automata · Lexical Analysis</p>
          </div>
        </div>

        <div className="status-group">
          <span className={`status-chip ${backendStatus}`}>
            <Circle size={8} fill="currentColor" />
            {backendLabel}
          </span>
          <span className={`status-chip analysis ${analysisStatus}`}>
            {analyzing ? (
              <LoaderCircle size={14} className="spin" />
            ) : (
              <TerminalSquare size={14} />
            )}
            {analysisLabel}
          </span>
        </div>
      </header>

      <main className="workspace">
        <div className="editor-column">
          <section className="panel editor-panel">
            <div className="panel-toolbar">
              <div className="file-tab">
                <span className="file-dot" />
                main.c
              </div>
              <div className="actions">
                <button
                  type="button"
                  className="btn primary"
                  onClick={handleAnalyze}
                  disabled={analyzing}
                >
                  {analyzing ? (
                    <LoaderCircle size={16} className="spin" />
                  ) : (
                    <Play size={16} />
                  )}
                  {analyzing ? "Analyzing..." : "Analyze"}
                </button>
                <button
                  type="button"
                  className="btn"
                  onClick={handleClear}
                  disabled={analyzing}
                >
                  <Eraser size={16} />
                  Clear
                </button>
              </div>
            </div>

            <div className="editor-wrap">
              <Editor
                height="100%"
                language="c"
                theme="vs-dark"
                value={source}
                onChange={(value) => setSource(value ?? "")}
                options={{
                  minimap: { enabled: false },
                  fontSize: 14,
                  fontFamily:
                    "Cascadia Code, Consolas, 'Courier New', monospace",
                  lineNumbers: "on",
                  automaticLayout: true,
                  tabSize: 4,
                  insertSpaces: true,
                  autoIndent: "full",
                  detectIndentation: true,
                  scrollBeyondLastLine: false,
                  wordWrap: "off",
                  scrollbar: {
                    vertical: "auto",
                    horizontal: "auto",
                    alwaysConsumeMouseWheel: false,
                  },
                  padding: { top: 12 },
                  renderLineHighlight: "all",
                }}
              />
            </div>
          </section>

          {stats && (
            <section className="panel stats-panel">
              <div className="panel-toolbar">
                <h2>Token statistics</h2>
              </div>
              <div className="stats-grid">
                {STAT_LABELS.map(([label, key]) => (
                  <div
                    key={key}
                    className={`stat-card ${key === "errors" && stats[key] ? "warn" : ""}`}
                  >
                    <span>{label}</span>
                    <strong>{stats[key] ?? 0}</strong>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>

        <section className="panel terminal-panel">
          <div className="panel-toolbar">
            <h2>
              <TerminalSquare size={15} />
              Terminal
            </h2>
            <span className={`run-indicator ${analysisStatus}`}>
              {analyzing ? "running" : analysisStatus}
            </span>
          </div>
          <pre
            className={`terminal-output ${analysisStatus}`}
            aria-live="polite"
          >
            {terminal}
          </pre>
        </section>
      </main>
    </div>
  );
}
