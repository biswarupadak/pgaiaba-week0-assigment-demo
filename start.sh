#!/usr/bin/env bash
# Start the Kartify Order Assistant locally.
#   ./start.sh          web UI on http://localhost:8501
#   ./start.sh cli      command-line chat (extra args are passed to main.py)
set -euo pipefail
cd "$(dirname "$0")"

# The venv keeps its python under Scripts/ on Windows and bin/ elsewhere.
venv_python() {
    if [ -x .venv/Scripts/python.exe ]; then echo .venv/Scripts/python.exe
    elif [ -x .venv/bin/python ]; then echo .venv/bin/python
    fi
}

if [ -z "$(venv_python)" ]; then
    echo "Creating virtual environment..."
    PY=$(command -v python3 || command -v python)
    "$PY" -m venv .venv
    "$(venv_python)" -m pip install -r requirements.txt
fi
PYTHON=$(venv_python)

if [ ! -f config.json ] && [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "No config.json or OPENAI_API_KEY found."
    echo "Copy config.example.json to config.json and add your OpenAI key."
    exit 1
fi

if [ "${1:-}" = "cli" ]; then
    shift
    exec "$PYTHON" main.py "$@"
fi
exec "$PYTHON" -m streamlit run app.py --server.port 8501
