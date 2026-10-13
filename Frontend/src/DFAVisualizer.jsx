import { useCallback, useEffect, useMemo, useState } from "react";
import {
    ChevronLeft,
    ChevronRight,
    Play,
    RotateCcw,
    Pause,
    Workflow,
} from "lucide-react";
import DFAGraph from "./DFAGraph.jsx";
import ExecutionTrace from "./ExecutionTrace.jsx";
import "./DFAVisualizer.css";

const SPEEDS = { slow: 1100, normal: 550, fast: 220 };

const STATUS_TEXT = {
    processing: "Processing",
    accept: "Accepted",
    skip: "Ignored",
    error: "Rejected",
};

function displayChar(ch) {
    if (ch === "\n") return "⏎";
    if (ch === "\t") return "⇥";
    if (ch === " ") return "␣";
    if (ch === "\r") return "␍";
    return ch;
}

export default function DFAVisualizer({ trace, source = "" }) {
    const steps = trace?.steps || [];
    const last = steps.length - 1;

    const [cursor, setCursor] = useState(0);
    const [playing, setPlaying] = useState(false);
    const [speed, setSpeed] = useState("normal");

    // Keep playback state sane when a fresh trace arrives.
    useEffect(() => {
        setCursor(0);
        setPlaying(false);
    }, [trace]);

    useEffect(() => {
        if (!playing) return undefined;
        if (cursor >= last) {
            setPlaying(false);
            return undefined;
        }
        const id = window.setTimeout(() => {
            setCursor((c) => Math.min(c + 1, last));
        }, SPEEDS[speed]);
        return () => window.clearTimeout(id);
    }, [playing, cursor, last, speed]);

    const handleStart = useCallback(() => {
        if (steps.length === 0) return;
        setCursor(0);
        setPlaying(true);
    }, [steps.length]);

    const handleReset = useCallback(() => {
        setPlaying(false);
        setCursor(0);
    }, []);

    const handleNext = useCallback(() => {
        setPlaying(false);
        setCursor((c) => Math.min(c + 1, last));
    }, [last]);

    const handlePrev = useCallback(() => {
        setPlaying(false);
        setCursor((c) => Math.max(c - 1, 0));
    }, []);

    const current = steps[cursor];

    const diagram = current && trace.dfas ? trace.dfas[current.dfa] : null;

    const activeEdge = useMemo(() => {
        if (!current || current.from === current.to) {
            return current && current.from === current.to && current.kind === "transition"
                ? { from: current.from, to: current.to }
                : null;
        }
        return { from: current.from, to: current.to };
    }, [current]);

    // State chain for the token currently being scanned.
    const stateHistory = useMemo(() => {
        if (!current) return [];
        const group = [];
        for (let i = 0; i <= cursor; i += 1) {
            const s = steps[i];
            if (s.tokenStart === current.tokenStart && s.dfa === current.dfa) {
                group.push(s);
            }
        }
        const chain = group.length ? [group[0].from] : [];
        group.forEach((s) => chain.push(s.to));
        return chain;
    }, [steps, cursor, current]);

    // Tokens accepted up to (and including) the cursor.
    const acceptedTokens = useMemo(() => {
        const out = [];
        for (let i = 0; i <= cursor && i < steps.length; i += 1) {
            const s = steps[i];
            if (s.status === "accept") out.push(s.tokenType);
        }
        return out;
    }, [steps, cursor]);

    // A focused slice of the input around the current character.
    const inputWindow = useMemo(() => {
        if (!current) return { before: 0, after: 0, chars: [] };
        const focus = Math.min(current.charIndex, source.length);
        const radius = 60;
        const start = Math.max(0, focus - radius);
        const end = Math.min(source.length, focus + radius);
        const chars = [];
        for (let i = start; i < end; i += 1) {
            chars.push({ i, ch: source[i] });
        }
        return { before: start, after: source.length - end, focus, chars };
    }, [current, source]);

    if (!trace || trace.error) {
        return null;
    }

    const progress = last > 0 ? (cursor / last) * 100 : 0;

    return (
        <section className="panel dfa-visualizer">
            <div className="panel-toolbar">
                <h2>
                    <Workflow size={15} />
                    DFA Execution Visualizer
                </h2>
                <span className={`dfa-badge ${current ? current.status : "idle"}`}>
                    {STATUS_TEXT[current?.status] || "Idle"}
                </span>
            </div>

            <p className="dfa-disclaimer">{trace.note}</p>

            {/* Controls */}
            <div className="dfa-controls">
                <button
                    type="button"
                    className="btn primary"
                    onClick={handleStart}
                    disabled={steps.length === 0}
                >
                    <Play size={15} />
                    Start
                </button>
                <button
                    type="button"
                    className="btn"
                    onClick={() => setPlaying((p) => !p)}
                    disabled={steps.length === 0 || (!playing && cursor >= last)}
                >
                    {playing ? <Pause size={15} /> : <Play size={15} />}
                    {playing ? "Pause" : "Resume"}
                </button>
                <button
                    type="button"
                    className="btn"
                    onClick={handlePrev}
                    disabled={cursor <= 0}
                    aria-label="Previous step"
                >
                    <ChevronLeft size={15} />
                    Prev
                </button>
                <button
                    type="button"
                    className="btn"
                    onClick={handleNext}
                    disabled={cursor >= last}
                    aria-label="Next step"
                >
                    Next
                    <ChevronRight size={15} />
                </button>
                <button
                    type="button"
                    className="btn"
                    onClick={handleReset}
                    disabled={steps.length === 0}
                >
                    <RotateCcw size={15} />
                    Reset
                </button>
                <label className="dfa-speed">
                    Speed
                    <select
                        value={speed}
                        onChange={(e) => setSpeed(e.target.value)}
                    >
                        <option value="slow">Slow</option>
                        <option value="normal">Normal</option>
                        <option value="fast">Fast</option>
                    </select>
                </label>
            </div>

            <div className="dfa-progress">
                <div className="dfa-progress-fill" style={{ width: `${progress}%` }} />
                <span className="dfa-progress-label">
                    Step {steps.length ? cursor + 1 : 0} / {steps.length}
                </span>
            </div>

            {/* Top: input processing */}
            <div className="dfa-input">
                <div className="dfa-input-label">Input</div>
                <div className="dfa-input-strip" aria-label="Input characters">
                    {inputWindow.before > 0 && <span className="dfa-input-ellipsis">…</span>}
                    {inputWindow.chars.map(({ i, ch }) => (
                        <span
                            key={i}
                            className={`dfa-char ${i === inputWindow.focus ? "active" : ""} ${current &&
                                    i >= current.tokenStart &&
                                    i < current.charIndex + (current.status === "accept" ? 0 : 1) &&
                                    current.status !== "skip" &&
                                    current.status !== "error"
                                    ? "lexeme"
                                    : ""
                                }`}
                        >
                            {displayChar(ch)}
                        </span>
                    ))}
                    {inputWindow.after > 0 && <span className="dfa-input-ellipsis">…</span>}
                </div>
                <div className="dfa-input-meta">
                    <span>
                        index: <strong>{current ? current.charIndex : "-"}</strong>
                    </span>
                    <span>
                        char: <strong>{current ? displayChar(current.char) || "∅" : "-"}</strong>
                    </span>
                    <span>
                        lexeme: <strong>{current?.lexeme || "-"}</strong>
                    </span>
                    <span>
                        category: <strong>{current?.dfa ? diagramLabel(current.category) : "-"}</strong>
                    </span>
                </div>
            </div>

            {/* Center: state diagram */}
            <div className="dfa-graph-wrap">
                <DFAGraph
                    diagram={diagram}
                    activeState={current ? current.to : null}
                    activeEdge={activeEdge}
                />
            </div>

            {/* Explanation + history */}
            <div className="dfa-explain">
                <div className="dfa-current">
                    <span className="dfa-current-state">
                        {current ? `${current.from} → ${current.to}` : "-"}
                    </span>
                    {current && current.label && (
                        <span className="dfa-current-cond">on {current.label}</span>
                    )}
                    {current?.tokenType && (
                        <span className="dfa-token-chip">{current.tokenType}</span>
                    )}
                </div>
                <p className="dfa-note">{current?.note || "Press Start to begin."}</p>

                <div className="dfa-history">
                    <span className="dfa-history-label">State path</span>
                    <div className="dfa-history-track">
                        {stateHistory.map((s, idx) => (
                            <span
                                key={`${s}-${idx}`}
                                className={`dfa-history-node ${idx === stateHistory.length - 1 ? "active" : ""
                                    }`}
                            >
                                {s}
                            </span>
                        ))}
                    </div>
                </div>

                <div className="dfa-accepted">
                    <span className="dfa-history-label">Tokens emitted</span>
                    <div className="dfa-accepted-track">
                        {acceptedTokens.length ? (
                            acceptedTokens.map((t, idx) => (
                                <span key={`${t}-${idx}`} className="dfa-token-chip">
                                    {t}
                                </span>
                            ))
                        ) : (
                            <span className="dfa-muted">none yet</span>
                        )}
                    </div>
                </div>
            </div>

            {/* Bottom: execution trace */}
            <ExecutionTrace steps={steps} cursor={cursor} />

            {trace.truncated && (
                <p className="dfa-muted dfa-truncated">
                    Trace truncated for very large inputs — the animation covers the first{" "}
                    {steps.length} DFA steps.
                </p>
            )}
        </section>
    );
}

function diagramLabel(category) {
    const map = {
        identifier: "Identifier / Keyword",
        integer: "Integer",
        float: "Float",
        string: "String",
        char: "Char",
        preprocessor: "Preprocessor",
        operator: "Operator",
        delimiter: "Delimiter",
        whitespace: "Whitespace",
        comment: "Comment",
        error: "Invalid",
    };
    return map[category] || category;
}
