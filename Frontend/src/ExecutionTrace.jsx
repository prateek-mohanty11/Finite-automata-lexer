import { useEffect, useRef } from "react";

const STATUS_LABEL = {
    processing: "reading",
    accept: "accepted",
    skip: "ignored",
    error: "error",
};

function statusClass(status) {
    if (status === "accept") return "ok";
    if (status === "error") return "bad";
    if (status === "skip") return "muted";
    return "run";
}

export default function ExecutionTrace({ steps, cursor }) {
    const activeRef = useRef(null);

    useEffect(() => {
        if (activeRef.current) {
            activeRef.current.scrollIntoView({ block: "nearest" });
        }
    }, [cursor]);

    if (!steps || steps.length === 0) {
        return <div className="dfa-trace empty">No execution steps.</div>;
    }

    // Render a window around the cursor to stay fast on large inputs.
    const windowSize = 120;
    let lo = Math.max(0, cursor - Math.floor(windowSize / 2));
    let hi = Math.min(steps.length, lo + windowSize);
    lo = Math.max(0, hi - windowSize);

    const visible = steps.slice(lo, hi);

    return (
        <div className="dfa-trace">
            <div className="dfa-trace-head">
                <span>#</span>
                <span>Char</span>
                <span>From</span>
                <span>Condition</span>
                <span>To</span>
                <span>Status</span>
            </div>
            <div className="dfa-trace-body">
                {lo > 0 && <div className="dfa-trace-more">… {lo} earlier steps</div>}
                {visible.map((s) => {
                    const index = s.stepNo - 1;
                    const active = index === cursor;
                    return (
                        <div
                            key={s.stepNo}
                            ref={active ? activeRef : null}
                            className={`dfa-trace-row ${active ? "active" : ""} ${statusClass(
                                s.status
                            )}`}
                        >
                            <span className="c-num">{s.stepNo}</span>
                            <span className="c-char">
                                {s.char === "" ? "␥" : s.char === " " ? "␣" : s.char}
                            </span>
                            <span className="c-state">{s.from}</span>
                            <span className="c-cond">{s.label}</span>
                            <span className="c-state">{s.to}</span>
                            <span className="c-status">{STATUS_LABEL[s.status] || s.status}</span>
                        </div>
                    );
                })}
                {hi < steps.length && (
                    <div className="dfa-trace-more">… {steps.length - hi} later steps</div>
                )}
            </div>
        </div>
    );
}
