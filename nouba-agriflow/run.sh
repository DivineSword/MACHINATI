#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
UVICORN="$ROOT_DIR/.venv/bin/uvicorn"
VITE="$ROOT_DIR/frontend/node_modules/.bin/vite"
PYTHON="$ROOT_DIR/.venv/bin/python"

if ! command -v node >/dev/null 2>&1; then
  printf 'Node.js is required to run Vite. Install it with: sudo dnf install nodejs npm\n' >&2
  exit 1
fi

if [[ ! -x "$UVICORN" ]]; then
  printf 'Missing %s. From the project root, run: python3 -m venv .venv && .venv/bin/python -m pip install -r backend/requirements.txt\n' "$UVICORN" >&2
  exit 1
fi

if [[ ! -x "$VITE" ]]; then
  printf 'Missing %s. Install frontend dependencies with npm ci first.\n' "$VITE" >&2
  exit 1
fi

if ! "$PYTHON" -c 'import fastapi' >/dev/null 2>&1; then
  printf 'FastAPI is missing from .venv. From the project root, install backend requirements with: .venv/bin/python -m pip install -r backend/requirements.txt\n' >&2
  exit 1
fi

BACKEND_PID=''
cleanup() {
  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID"
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

pushd "$ROOT_DIR/backend" >/dev/null
"$UVICORN" app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
popd >/dev/null

cd "$ROOT_DIR/frontend"
printf 'Frontend: http://127.0.0.1:5173\nBackend:  http://127.0.0.1:8000\nPress Ctrl+C to stop both.\n'
"$VITE" --host 127.0.0.1 --port 5173 --strictPort --open /
