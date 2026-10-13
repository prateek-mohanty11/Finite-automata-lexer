"""
Educational DFA trace generator for LexiLab.

IMPORTANT - honesty note:
    PLY builds its lexer from regular expressions and does NOT expose the
    individual DFA states it walks internally. This module therefore does NOT
    inspect PLY's internal automata.

    Instead it does two things:
      1. It runs the REAL PLY lexer (imported from ``lexer.py``) to obtain the
         authoritative token stream (types, lexemes and source positions).
      2. It replays each real token through a small, hand-written DFA that is
         built from the *same token rules* the lexer declares, producing a
         deterministic, character-by-character transition trace.

    Because the trace is derived from the real PLY tokens, token boundaries and
    accepted lexemes can never disagree with the actual lexer output. The state
    names shown (q0, q1, ...) are an educational simulation of those rules, not
    PLY's internal machine.

    A DFA accepting a lexeme only means the lexeme is *lexically* valid. It does
    not imply the program is syntactically or semantically correct.
"""

import os
import sys

# Make sure we can import the sibling lexer module regardless of cwd.
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import lexer as L  # noqa: E402  (reuse the real PLY lexer as the source of truth)


TRACE_NOTE = (
    "Educational DFA simulation of the lexer's token rules. The token "
    "boundaries come from the real PLY lexer, but the state machine shown "
    "here is a hand-built model of each pattern - it is NOT PLY's internal "
    "automaton. Acceptance only means the text is a valid lexeme, not that "
    "the program is syntactically or semantically correct."
)


# ============================================================
# CHARACTER CLASS HELPERS
# ============================================================

def _is_letter(ch):
    return ("a" <= ch <= "z") or ("A" <= ch <= "Z") or ch == "_"


def _is_ident_char(ch):
    return _is_letter(ch) or ("0" <= ch <= "9")


def _is_digit(ch):
    return "0" <= ch <= "9"


def _is_hex(ch):
    return _is_digit(ch) or ("a" <= ch <= "f") or ("A" <= ch <= "F")


def _is_oct(ch):
    return "0" <= ch <= "7"


def _is_bin(ch):
    return ch in ("0", "1")


def _is_ws(ch):
    return ch in (" ", "\t", "\r", "\n", "\v", "\f")


# ============================================================
# TOKEN CATEGORY CLASSIFICATION
# ============================================================

# Single-character operators and the token type PLY emits for them.
SINGLE_OP = {
    "+": "PLUS",
    "-": "MINUS",
    "*": "TIMES",
    "/": "DIVIDE",
    "%": "MOD",
    "=": "ASSIGN",
    "<": "LESS",
    ">": "GREATER",
    "!": "NOT",
    "&": "BIT_AND",
    "|": "BIT_OR",
    "^": "BIT_XOR",
    "~": "BIT_NOT",
}

DELIMS = {
    "LPAREN": "(",
    "RPAREN": ")",
    "LBRACE": "{",
    "RBRACE": "}",
    "LBRACKET": "[",
    "RBRACKET": "]",
    "COMMA": ",",
    "SEMICOLON": ";",
    "COLON": ":",
    "DOT": ".",
}
DELIM_TYPES = set(DELIMS.keys())

CONSTANT_INT = {"INTEGER"}
CONSTANT_FLOAT = {"FLOATING"}
CONSTANT_STR = {"STRING"}
CONSTANT_CHAR = {"CHARACTER"}
IDENT_TYPES = {"IDENTIFIER"}


def classify(token_type):
    """Map a PLY token type to an educational DFA category."""
    if token_type in IDENT_TYPES or token_type in L.reserved.values():
        return "identifier"
    if token_type in CONSTANT_INT:
        return "integer"
    if token_type in CONSTANT_FLOAT:
        return "float"
    if token_type in CONSTANT_STR:
        return "string"
    if token_type in CONSTANT_CHAR:
        return "char"
    if token_type == "PREPROCESSOR":
        return "preprocessor"
    if token_type in DELIM_TYPES:
        return "delimiter"
    return "operator"


CATEGORY_LABELS = {
    "identifier": "Identifier / Keyword",
    "integer": "Integer Constant",
    "float": "Floating-Point Constant",
    "string": "String Literal",
    "char": "Character Constant",
    "preprocessor": "Preprocessor Line",
    "operator": "Operator",
    "delimiter": "Delimiter",
    "whitespace": "Whitespace (ignored)",
    "comment": "Comment (ignored)",
    "error": "Invalid Character",
}


# ============================================================
# DIAGRAM CONSTRUCTION
# ============================================================

def _state(sid, x, y, accept=False, accept_type=None, name=None):
    return {
        "id": sid,
        "x": x,
        "y": y,
        "accept": accept,
        "acceptType": accept_type,
        "name": name or sid,
    }


def _edge(src, dst, label):
    return {"from": src, "to": dst, "label": label}


def _diagram(start, states, edges, width, height):
    return {
        "start": start,
        "states": states,
        "edges": edges,
        "width": width,
        "height": height,
    }


# ---- Static diagrams (one per supported pattern) --------------

STATIC_DFAS = {
    "identifier": _diagram(
        "q0",
        [
            _state("q0", 80, 110, name="q0"),
            _state("q1", 340, 110, accept=True, accept_type="IDENTIFIER", name="q1"),
        ],
        [
            _edge("q0", "q1", "[A-Za-z_]"),
            _edge("q1", "q1", "[A-Za-z0-9_]"),
        ],
        480, 200,
    ),
    "integer": _diagram(
        "s0",
        [
            _state("s0", 40, 140, name="s0"),
            _state("dec", 240, 250, accept=True, accept_type="INTEGER", name="dec"),
            _state("z", 240, 50, accept=True, accept_type="INTEGER", name="zero"),
            _state("hx", 470, 30, accept=True, accept_type="INTEGER", name="hex"),
            _state("bn", 470, 120, accept=True, accept_type="INTEGER", name="bin"),
            _state("oc", 470, 210, accept=True, accept_type="INTEGER", name="oct"),
        ],
        [
            _edge("s0", "dec", "[1-9]"),
            _edge("dec", "dec", "[0-9]"),
            _edge("s0", "z", "0"),
            _edge("z", "hx", "[xX]"),
            _edge("z", "bn", "[bB]"),
            _edge("z", "oc", "[0-7]"),
            _edge("hx", "hx", "[0-9a-fA-F]"),
            _edge("bn", "bn", "[01]"),
            _edge("oc", "oc", "[0-7]"),
        ],
        580, 310,
    ),
    "float": _diagram(
        "s0",
        [
            _state("s0", 40, 160, name="s0"),
            _state("i", 180, 250, name="int"),
            _state("d", 180, 60, name="dot"),
            _state("dotB", 350, 250, accept=True, accept_type="FLOATING", name="after-dot"),
            _state("c", 520, 160, accept=True, accept_type="FLOATING", name="frac"),
            _state("e", 660, 285, name="exp"),
            _state("f", 770, 285, name="exp-sign"),
            _state("g", 850, 200, accept=True, accept_type="FLOATING", name="exp-dig"),
            _state("suf", 850, 80, accept=True, accept_type="FLOATING", name="suffix"),
        ],
        [
            _edge("s0", "i", "[0-9]"),
            _edge("i", "i", "[0-9]"),
            _edge("i", "dotB", "'.'"),
            _edge("i", "e", "[eE]"),
            _edge("s0", "d", "'.'"),
            _edge("d", "c", "[0-9]"),
            _edge("dotB", "c", "[0-9]"),
            _edge("dotB", "e", "[eE]"),
            _edge("dotB", "suf", "[fFlL]"),
            _edge("c", "c", "[0-9]"),
            _edge("c", "e", "[eE]"),
            _edge("c", "suf", "[fFlL]"),
            _edge("e", "f", "[+-]"),
            _edge("e", "g", "[0-9]"),
            _edge("f", "g", "[0-9]"),
            _edge("g", "g", "[0-9]"),
            _edge("g", "suf", "[fFlL]"),
        ],
        940, 340,
    ),
    "string": _diagram(
        "s0",
        [
            _state("s0", 50, 130, name="s0"),
            _state("body", 250, 130, name="body"),
            _state("esc", 250, 240, name="escape"),
            _state("done", 510, 130, accept=True, accept_type="STRING", name="close"),
        ],
        [
            _edge("s0", "body", '"'),
            _edge("body", "body", "any char"),
            _edge("body", "esc", "'\\'"),
            _edge("esc", "body", "escaped char"),
            _edge("body", "done", "closing '\"'"),
        ],
        620, 300,
    ),
    "char": _diagram(
        "s0",
        [
            _state("s0", 40, 130, name="s0"),
            _state("body", 200, 130, name="open"),
            _state("esc", 200, 240, name="escape"),
            _state("single", 400, 130, name="value"),
            _state("done", 610, 130, accept=True, accept_type="CHARACTER", name="close"),
        ],
        [
            _edge("s0", "body", "'"),
            _edge("body", "single", "char"),
            _edge("body", "esc", "'\\'"),
            _edge("esc", "single", "escaped char"),
            _edge("single", "done", "'"),
        ],
        720, 300,
    ),
    "preprocessor": _diagram(
        "s0",
        [
            _state("s0", 60, 110, name="s0"),
            _state("p", 320, 110, accept=True, accept_type="PREPROCESSOR", name="line"),
        ],
        [
            _edge("s0", "p", "#"),
            _edge("p", "p", "rest of line"),
        ],
        460, 200,
    ),
    "whitespace": _diagram(
        "s0",
        [
            _state("s0", 80, 110, name="s0"),
            _state("ws", 340, 110, name="skip"),
        ],
        [
            _edge("s0", "ws", "space / tab / newline"),
            _edge("ws", "ws", "whitespace"),
        ],
        480, 200,
    ),
    "error": _diagram(
        "s0",
        [
            _state("s0", 80, 110, name="s0"),
            _state("dead", 340, 110, name="reject"),
        ],
        [_edge("s0", "dead", "unexpected char")],
        480, 200,
    ),
}


def _operator_diagram(lexeme, token_type):
    """Build a tiny longest-match DFA for a specific operator lexeme.

    For a 2-character operator the intermediate state is itself accepting,
    which demonstrates how the machine distinguishes a completed shorter
    token (e.g. ``=``) from a longer possible operator (e.g. ``==``).
    """
    if len(lexeme) <= 1:
        return _diagram(
            "q0",
            [
                _state("q0", 80, 110, name="q0"),
                _state("q1", 340, 110, accept=True, accept_type=token_type, name="q1"),
            ],
            [_edge("q0", "q1", lexeme or "?")],
            480, 200,
        )

    first = lexeme[0]
    second = lexeme[1]
    prefix_type = SINGLE_OP.get(first, token_type)
    return _diagram(
        "q0",
        [
            _state("q0", 60, 130, name="q0"),
            _state("q1", 320, 60, accept=True, accept_type=prefix_type, name="q1"),
            _state("q2", 560, 175, accept=True, accept_type=token_type, name="q2"),
        ],
        [
            _edge("q0", "q1", first),
            _edge("q1", "q2", second),
        ],
        680, 240,
    )


def _delimiter_diagram(lexeme, token_type):
    return _diagram(
        "q0",
        [
            _state("q0", 80, 110, name="q0"),
            _state("q1", 340, 110, accept=True, accept_type=token_type, name="q1"),
        ],
        [_edge("q0", "q1", lexeme)],
        480, 200,
    )


# ============================================================
# STATIC PATTERN WALKERS (transition resolvers)
# ============================================================

def _resolve_identifier(state, ch):
    if state == "q0" and _is_letter(ch):
        return ("q1", "[A-Za-z_]")
    if state == "q1" and _is_ident_char(ch):
        return ("q1", "[A-Za-z0-9_]")
    return None


def _resolve_integer(state, ch):
    if state == "s0":
        if "1" <= ch <= "9":
            return ("dec", "[1-9]")
        if ch == "0":
            return ("z", "0")
    elif state == "dec" and _is_digit(ch):
        return ("dec", "[0-9]")
    elif state == "z":
        if ch in ("x", "X"):
            return ("hx", "[xX]")
        if ch in ("b", "B"):
            return ("bn", "[bB]")
        if _is_oct(ch):
            return ("oc", "[0-7]")
    elif state == "hx" and _is_hex(ch):
        return ("hx", "[0-9a-fA-F]")
    elif state == "bn" and _is_bin(ch):
        return ("bn", "[01]")
    elif state == "oc" and _is_oct(ch):
        return ("oc", "[0-7]")
    return None


def _resolve_float(state, ch):
    if state == "s0":
        if _is_digit(ch):
            return ("i", "[0-9]")
        if ch == ".":
            return ("d", "'.'")
    elif state == "i":
        if _is_digit(ch):
            return ("i", "[0-9]")
        if ch == ".":
            return ("dotB", "'.'")
        if ch in ("e", "E"):
            return ("e", "[eE]")
    elif state == "d" and _is_digit(ch):
        return ("c", "[0-9]")
    elif state == "dotB":
        if _is_digit(ch):
            return ("c", "[0-9]")
        if ch in ("e", "E"):
            return ("e", "[eE]")
        if ch in ("f", "F", "l", "L"):
            return ("suf", "[fFlL]")
    elif state == "c":
        if _is_digit(ch):
            return ("c", "[0-9]")
        if ch in ("e", "E"):
            return ("e", "[eE]")
        if ch in ("f", "F", "l", "L"):
            return ("suf", "[fFlL]")
    elif state == "e":
        if ch in ("+", "-"):
            return ("f", "[+-]")
        if _is_digit(ch):
            return ("g", "[0-9]")
    elif state == "f" and _is_digit(ch):
        return ("g", "[0-9]")
    elif state == "g":
        if _is_digit(ch):
            return ("g", "[0-9]")
        if ch in ("f", "F", "l", "L"):
            return ("suf", "[fFlL]")
    return None


def _resolve_string(state, ch):
    if state == "s0" and ch == '"':
        return ("body", '"')
    if state == "body":
        if ch == '"':
            return ("done", "closing '\"'")
        if ch == "\\":
            return ("esc", "'\\'")
        return ("body", "any char")
    if state == "esc":
        return ("body", "escaped char")
    return None


def _resolve_char(state, ch):
    if state == "s0" and ch == "'":
        return ("body", "'")
    if state == "body":
        if ch == "\\":
            return ("esc", "'\\'")
        return ("single", "char")
    if state == "esc":
        return ("single", "escaped char")
    if state == "single" and ch == "'":
        return ("done", "'")
    return None


def _resolve_preprocessor(state, ch):
    if state == "s0" and ch == "#":
        return ("p", "#")
    if state == "p" and ch != "\n":
        return ("p", "rest of line")
    return None


STATIC_RESOLVERS = {
    "identifier": _resolve_identifier,
    "integer": _resolve_integer,
    "float": _resolve_float,
    "string": _resolve_string,
    "char": _resolve_char,
    "preprocessor": _resolve_preprocessor,
}


# ============================================================
# TRACE GENERATION
# ============================================================

class _Builder:
    def __init__(self, source, max_steps):
        self.source = source
        self.max_steps = max_steps
        self.dfas = {}
        self.steps = []
        self.tokens = []
        self.truncated = False
        self._n = 0

    def add_dfa(self, dfa_id, diagram):
        self.dfas[dfa_id] = diagram
        return dfa_id

    def ensure_static(self, category):
        dfa_id = category
        if dfa_id not in self.dfas:
            self.dfas[dfa_id] = STATIC_DFAS[category]
        return dfa_id

    @property
    def full(self):
        return len(self.steps) >= self.max_steps

    def push(self, step):
        if self.full:
            self.truncated = True
            return False
        self._n += 1
        step["stepNo"] = self._n
        self.steps.append(step)
        return True


def _state_name(diagram, sid):
    for s in diagram["states"]:
        if s["id"] == sid:
            return s["name"]
    return sid


def _walk_static(builder, category, dfa_id, lexeme, token_start, token_type):
    diagram = STATIC_DFAS[category]
    resolver = STATIC_RESOLVERS[category]
    state = diagram["start"]
    consumed = 0
    for offset, ch in enumerate(lexeme):
        nxt = resolver(state, ch)
        if nxt is None:
            return None
        to, label = nxt
        char_index = token_start + offset
        builder.push({
            "kind": "transition",
            "status": "processing",
            "category": category,
            "dfa": dfa_id,
            "char": ch,
            "charIndex": char_index,
            "from": state,
            "to": to,
            "label": label,
            "lexeme": lexeme[: offset + 1],
            "tokenStart": token_start,
            "note": (
                f"Read '{_pretty(ch)}': {CATEGORY_LABELS[category]} moves "
                f"{_state_name(diagram, state)} -> {_state_name(diagram, to)} "
                f"on {label}."
            ),
        })
        state = to
        consumed += 1
        if builder.truncated:
            return None
    return state


def _pretty(ch):
    if ch == " ":
        return "␣ (space)"
    if ch == "\t":
        return "\\t"
    if ch == "\n":
        return "\\n"
    if ch == "\r":
        return "\\r"
    return ch


def _emit_accept(builder, category, dfa_id, lexeme, token_start, token_type, final_state):
    diagram = builder.dfas[dfa_id]
    if final_state is None:
        # Fallback: point to the first accepting state we can find.
        final_state = next(
            (s["id"] for s in diagram["states"] if s["accept"]),
            diagram["start"],
        )
    builder.push({
        "kind": "accept",
        "status": "accept",
        "category": category,
        "dfa": dfa_id,
        "char": "",
        "charIndex": token_start + len(lexeme),
        "from": final_state,
        "to": final_state,
        "label": "boundary",
        "lexeme": lexeme,
        "tokenStart": token_start,
        "tokenType": token_type,
        "acceptState": final_state,
        "note": (
            f"Token boundary reached. The DFA sits on accepting state "
            f"'{_state_name(diagram, final_state)}', so the lexer emits "
            f"{token_type} '{lexeme}'."
        ),
    })


def _walk_operator(builder, lexeme, token_start, token_type):
    dfa_id = builder.add_dfa(f"operator:{lexeme}", _operator_diagram(lexeme, token_type))
    diagram = builder.dfas[dfa_id]
    state = "q0"
    for offset, ch in enumerate(lexeme):
        to = "q1" if offset == 0 else "q2"
        label = ch
        builder.push({
            "kind": "transition",
            "status": "processing",
            "category": "operator",
            "dfa": dfa_id,
            "char": ch,
            "charIndex": token_start + offset,
            "from": state,
            "to": to,
            "label": label,
            "lexeme": lexeme[: offset + 1],
            "tokenStart": token_start,
            "note": (
                f"Read '{_pretty(ch)}': operator DFA moves "
                f"{_state_name(diagram, state)} -> {_state_name(diagram, to)}."
                + ("  Intermediate state is accepting (a shorter operator could end here)."
                   if offset == 0 and len(lexeme) > 1 else "")
            ),
        })
        state = to
    return dfa_id, state


def _walk_delimiter(builder, lexeme, token_start, token_type):
    dfa_id = builder.add_dfa(f"delimiter:{lexeme}", _delimiter_diagram(lexeme, token_type))
    diagram = builder.dfas[dfa_id]
    builder.push({
        "kind": "transition",
        "status": "processing",
        "category": "delimiter",
        "dfa": dfa_id,
        "char": lexeme,
        "charIndex": token_start,
        "from": "q0",
        "to": "q1",
        "label": lexeme,
        "lexeme": lexeme,
        "tokenStart": token_start,
        "note": (
            f"Read '{_pretty(lexeme)}': a delimiter is recognized in a single "
            f"transition into its accepting state."
        ),
    })
    return dfa_id, "q1"


def _walk_gap(builder, source, start, end):
    """Emit steps for the characters between two tokens (whitespace,
    comments, or invalid characters)."""
    pos = start
    while pos < end:
        ch = source[pos]
        if builder.truncated or builder.full:
            builder.truncated = True
            return

        if _is_ws(ch):
            ws_run = ch
            j = pos + 1
            while j < end and _is_ws(source[j]):
                ws_run += source[j]
                j += 1
            dfa_id = builder.ensure_static("whitespace")
            diagram = builder.dfas[dfa_id]
            state = "s0"
            for k, wc in enumerate(ws_run):
                to = "ws"
                builder.push({
                    "kind": "skip",
                    "status": "skip",
                    "category": "whitespace",
                    "dfa": dfa_id,
                    "char": wc,
                    "charIndex": pos + k,
                    "from": state,
                    "to": to,
                    "label": "whitespace",
                    "lexeme": "",
                    "tokenStart": pos,
                    "note": (
                        f"Ignored whitespace '{_pretty(wc)}': it is skipped by "
                        f"the lexer and produces no token."
                    ),
                })
                state = to
            pos = j
            continue

        # Comment?
        if source.startswith("//", pos):
            nl = source.find("\n", pos)
            stop = end if nl == -1 else min(end, nl)
            builder.push({
                "kind": "skip",
                "status": "skip",
                "category": "comment",
                "dfa": builder.ensure_static("whitespace"),
                "char": source[pos],
                "charIndex": pos,
                "from": "s0",
                "to": "ws",
                "label": "comment",
                "lexeme": "",
                "tokenStart": pos,
                "note": "Single-line comment is stripped by the lexer; no token.",
            })
            pos = stop if stop > pos else pos + 1
            continue

        if source.startswith("/*", pos):
            close = source.find("*/", pos)
            stop = end if close == -1 else min(end, close + 2)
            builder.push({
                "kind": "skip",
                "status": "skip",
                "category": "comment",
                "dfa": builder.ensure_static("whitespace"),
                "char": source[pos],
                "charIndex": pos,
                "from": "s0",
                "to": "ws",
                "label": "comment",
                "lexeme": "",
                "tokenStart": pos,
                "note": "Multi-line comment is stripped by the lexer; no token.",
            })
            pos = stop if stop > pos else pos + 1
            continue

        # Anything else in a gap is an invalid character.
        dfa_id = builder.ensure_static("error")
        builder.push({
            "kind": "error",
            "status": "error",
            "category": "error",
            "dfa": dfa_id,
            "char": ch,
            "charIndex": pos,
            "from": "s0",
            "to": "dead",
            "label": "unexpected char",
            "lexeme": "",
            "tokenStart": pos,
            "note": (
                f"No DFA accepts '{_pretty(ch)}' in this position. The real "
                f"lexer reports an error and skips the character."
            ),
        })
        pos += 1


def generate_trace(source, max_steps=4000):
    """Produce an educational DFA trace consistent with the real PLY lexer."""
    if not isinstance(source, str):
        source = ""

    # Run the REAL PLY lexer to obtain authoritative tokens.
    L.lexical_errors.clear()
    L.lexer.lineno = 1
    L.lexer.input(source)

    real_tokens = []
    while True:
        tok = L.lexer.token()
        if tok is None:
            break
        real_tokens.append((tok.type, tok.value, tok.lineno, tok.lexpos))

    builder = _Builder(source, max_steps)

    pos = 0
    for token_type, value, lineno, lexpos in real_tokens:
        # Gap (whitespace / comment / error) before this token.
        gap_start = pos
        gap_end = min(lexpos, len(source))
        if gap_end > gap_start:
            _walk_gap(builder, source, gap_start, gap_end)

        lexeme = value if isinstance(value, str) else str(value)
        category = classify(token_type)

        if builder.full:
            builder.truncated = True
            break

        if category == "operator":
            dfa_id, final_state = _walk_operator(builder, lexeme, lexpos, token_type)
        elif category == "delimiter":
            dfa_id, final_state = _walk_delimiter(builder, lexeme, lexpos, token_type)
        else:
            dfa_id = builder.ensure_static(category)
            final_state = _walk_static(
                builder, category, dfa_id, lexeme, lexpos, token_type
            )

        _emit_accept(builder, category, dfa_id, lexeme, lexpos, token_type, final_state)
        builder.tokens.append({
            "type": token_type,
            "lexeme": lexeme,
            "category": category,
            "line": lineno,
            "index": lexpos,
        })

        pos = lexpos + len(lexeme)

    # Trailing gap after the last token.
    if pos < len(source) and not builder.full:
        _walk_gap(builder, source, pos, len(source))

    # Only ship the DFA diagrams actually referenced by steps.
    used = {s["dfa"] for s in builder.steps if "dfa" in s}
    dfas_out = {k: v for k, v in builder.dfas.items() if k in used}

    return {
        "note": TRACE_NOTE,
        "dfas": dfas_out,
        "steps": builder.steps,
        "tokens": builder.tokens,
        "errorCount": len(L.lexical_errors),
        "truncated": builder.truncated,
        "stepCount": len(builder.steps),
    }


if __name__ == "__main__":
    import json

    demo = "int count = 42;\nfloat x = 3.14e-2;\na == b; @\n"
    print(json.dumps(generate_trace(demo), indent=2)[:4000])
