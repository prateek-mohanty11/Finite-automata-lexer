const NODE_R = 28;

function nodeCenter(diagram, id) {
    const s = diagram.states.find((st) => st.id === id);
    return s ? { x: s.x, y: s.y, state: s } : null;
}

function shorten(x1, y1, x2, y2, padStart, padEnd) {
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len = Math.hypot(dx, dy) || 1;
    const ux = dx / len;
    const uy = dy / len;
    return {
        sx: x1 + ux * padStart,
        sy: y1 + uy * padStart,
        tx: x2 - ux * padEnd,
        ty: y2 - uy * padEnd,
    };
}

export default function DFAGraph({ diagram, activeState, activeEdge }) {
    if (!diagram) {
        return (
            <div className="dfa-graph empty">
                <p>No state diagram for this step.</p>
            </div>
        );
    }

    const { width, height, start } = diagram;

    const isActiveEdge = (edge) =>
        activeEdge && edge.from === activeEdge.from && edge.to === activeEdge.to;

    return (
        <div className="dfa-graph" role="img" aria-label="DFA state diagram">
            <svg
                viewBox={`0 0 ${width} ${height}`}
                width={width}
                height={height}
                preserveAspectRatio="xMidYMid meet"
                className="dfa-svg"
            >
                <defs>
                    <marker
                        id="dfa-arrow"
                        markerWidth="10"
                        markerHeight="10"
                        refX="8"
                        refY="3"
                        orient="auto"
                        markerUnits="userSpaceOnUse"
                    >
                        <path d="M0,0 L8,3 L0,6 Z" className="dfa-arrow-head" />
                    </marker>
                    <marker
                        id="dfa-arrow-active"
                        markerWidth="10"
                        markerHeight="10"
                        refX="8"
                        refY="3"
                        orient="auto"
                        markerUnits="userSpaceOnUse"
                    >
                        <path d="M0,0 L8,3 L0,6 Z" className="dfa-arrow-head active" />
                    </marker>
                </defs>

                {/* Start marker arrow into the start state */}
                {(() => {
                    const c = nodeCenter(diagram, start);
                    if (!c) return null;
                    return (
                        <g className="dfa-startmark">
                            <line
                                x1={c.x - NODE_R - 34}
                                y1={c.y}
                                x2={c.x - NODE_R - 4}
                                y2={c.y}
                                markerEnd="url(#dfa-arrow)"
                            />
                            <text x={c.x - NODE_R - 38} y={c.y + 4} textAnchor="end">
                                start
                            </text>
                        </g>
                    );
                })()}

                {/* Edges */}
                {diagram.edges.map((edge, i) => {
                    const from = nodeCenter(diagram, edge.from);
                    const to = nodeCenter(diagram, edge.to);
                    if (!from || !to) return null;
                    const active = isActiveEdge(edge);

                    if (edge.from === edge.to) {
                        // Self-loop drawn above the node.
                        const cx = from.x;
                        const cy = from.y - NODE_R;
                        const path = `M ${cx - 16} ${cy} q 16 -34 32 0`;
                        return (
                            <g key={i} className={`dfa-edge ${active ? "active" : ""}`}>
                                <path
                                    d={path}
                                    fill="none"
                                    markerEnd={`url(#${active ? "dfa-arrow-active" : "dfa-arrow"})`}
                                />
                                <text
                                    x={cx}
                                    y={cy - 34}
                                    textAnchor="middle"
                                    className="dfa-elabel"
                                >
                                    {edge.label}
                                </text>
                            </g>
                        );
                    }

                    const { sx, sy, tx, ty } = shorten(
                        from.x,
                        from.y,
                        to.x,
                        to.y,
                        NODE_R + 2,
                        NODE_R + 6,
                    );
                    const mx = (sx + tx) / 2;
                    const my = (sy + ty) / 2;
                    return (
                        <g key={i} className={`dfa-edge ${active ? "active" : ""}`}>
                            <line
                                x1={sx}
                                y1={sy}
                                x2={tx}
                                y2={ty}
                                markerEnd={`url(#${active ? "dfa-arrow-active" : "dfa-arrow"})`}
                            />
                            <text
                                x={mx}
                                y={my - 6}
                                textAnchor="middle"
                                className="dfa-elabel"
                            >
                                {edge.label}
                            </text>
                        </g>
                    );
                })}

                {/* States */}
                {diagram.states.map((s) => {
                    const isActive = activeState === s.id;
                    const isStart = s.id === start;
                    const cls = [
                        "dfa-state",
                        s.accept ? "accept" : "",
                        isActive ? "active" : "",
                        s.id === "dead" || s.id === "reject" ? "reject" : "",
                    ]
                        .filter(Boolean)
                        .join(" ");
                    return (
                        <g
                            key={s.id}
                            className={cls}
                            transform={`translate(${s.x}, ${s.y})`}
                        >
                            <circle r={NODE_R} className="dfa-node" />
                            {s.accept && <circle r={NODE_R - 5} className="dfa-node-inner" />}
                            <text y={4} textAnchor="middle" className="dfa-node-label">
                                {s.name}
                            </text>
                            {isStart && <circle r={NODE_R + 1} className="dfa-node-ring" />}
                            {s.accept && s.acceptType && (
                                <text
                                    y={NODE_R + 16}
                                    textAnchor="middle"
                                    className="dfa-accept-tag"
                                >
                                    {s.acceptType}
                                </text>
                            )}
                        </g>
                    );
                })}
            </svg>
        </div>
    );
}
