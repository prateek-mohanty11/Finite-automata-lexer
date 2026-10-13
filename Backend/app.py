import os
import shutil
import subprocess
import sys
import tempfile

from flask import Flask, jsonify, request
from flask_cors import CORS


BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
LEXER_PATH = os.path.join(BACKEND_DIR, "lexer.py")

# Make the sibling dfa_trace module importable no matter the working directory.
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

try:
    from dfa_trace import generate_trace as _generate_trace
except Exception:  # pragma: no cover - trace is an optional enhancement
    _generate_trace = None

MAX_SOURCE_CHARS = 100_000
ANALYZE_TIMEOUT_SECONDS = 15
MAX_TRACE_STEPS = 4000

app = Flask(__name__)

_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
allowed_origins = [
    origin.strip()
    for origin in os.environ.get("FRONTEND_ORIGIN", _default_origins).split(",")
    if origin.strip()
]
CORS(app, origins=allowed_origins)


def _error_response(message, status_code, **extra):
    payload = {
        "success": False,
        "error": message,
        "stdout": extra.get("stdout", ""),
        "stderr": extra.get("stderr", ""),
        "exit_code": extra.get("exit_code"),
    }
    return jsonify(payload), status_code


@app.get("/api/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "LexiLab",
            "lexer": os.path.isfile(LEXER_PATH),
        }
    )


@app.post("/api/analyze")
def analyze():
    if not request.is_json:
        return _error_response(
            "Request must be JSON with a source_code field.",
            400,
        )

    try:
        payload = request.get_json(force=False, silent=False)
    except Exception:
        return _error_response("Malformed JSON body.", 400)

    if not isinstance(payload, dict):
        return _error_response("JSON body must be an object.", 400)

    if "source_code" not in payload:
        return _error_response("Missing required field: source_code.", 400)

    source_code = payload["source_code"]

    if not isinstance(source_code, str):
        return _error_response("source_code must be a string.", 400)

    if len(source_code) > MAX_SOURCE_CHARS:
        return _error_response(
            f"source_code exceeds the {MAX_SOURCE_CHARS} character limit.",
            413,
        )

    if not os.path.isfile(LEXER_PATH):
        return _error_response(
            f"Lexer was not found at {LEXER_PATH}.",
            500,
        )

    temp_dir = tempfile.mkdtemp(prefix="lexilab_")
    input_path = os.path.join(temp_dir, "input.c")

    try:
        with open(input_path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(source_code)

        child_env = os.environ.copy()
        child_env["PYTHONIOENCODING"] = "utf-8"
        child_env["PYTHONUTF8"] = "1"

        completed = subprocess.run(
            [sys.executable, LEXER_PATH, input_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=ANALYZE_TIMEOUT_SECONDS,
            cwd=BACKEND_DIR,
            env=child_env,
        )

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        exit_code = completed.returncode
        success = exit_code == 0

        # Build the educational DFA trace from the same source. This is an
        # additive enhancement; any failure here must not break /api/analyze.
        trace = None
        if _generate_trace is not None:
            try:
                trace = _generate_trace(source_code, max_steps=MAX_TRACE_STEPS)
            except Exception as trace_exc:  # pragma: no cover
                trace = {"error": f"Trace generation unavailable: {trace_exc}"}

        return jsonify(
            {
                "success": success,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
                "trace": trace,
                "error": None if success else "Lexer process exited with a non-zero status.",
            }
        )

    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")

        return _error_response(
            f"Lexical analysis timed out after {ANALYZE_TIMEOUT_SECONDS} seconds.",
            504,
            stdout=stdout,
            stderr=stderr,
            exit_code=None,
        )

    except FileNotFoundError:
        return _error_response(
            "Python interpreter or lexer script could not be executed.",
            500,
        )

    except Exception as exc:
        return _error_response(
            f"Unexpected backend error: {exc}",
            500,
        )

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=debug)
