#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
UVICORN="$ROOT_DIR/.venv/bin/uvicorn"
VITE="$ROOT_DIR/frontend/node_modules/.bin/vite"
PYTHON="$ROOT_DIR/.venv/bin/python"

if ! command -v node >/dev/null 2>&1; then
  printf 'Node.js 20+ is required. Install Node.js and npm for your operating system, then run this script again.\n' >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  printf 'npm is required. Install Node.js 20+ (which includes npm), then run this script again.\n' >&2
  exit 1
fi

BASE_PYTHON="$(command -v python3 || command -v python || true)"
if [[ -z "$BASE_PYTHON" ]]; then
  printf 'Python 3.10+ is required. Install Python, then run this script again.\n' >&2
  exit 1
fi

if [[ ! -x "$PYTHON" ]]; then
  printf 'Creating Python environment...\n'
  "$BASE_PYTHON" -m venv "$ROOT_DIR/.venv"
fi

if ! "$PYTHON" -m pip --version >/dev/null 2>&1; then
  if ! "$PYTHON" -m ensurepip --upgrade >/dev/null 2>&1; then
    printf 'pip is unavailable in .venv. Recreate it with Python 3.10+ and run this script again.\n' >&2
    exit 1
  fi
fi

if ! "$PYTHON" -c 'import fastapi, uvicorn' >/dev/null 2>&1; then
  printf 'Installing backend dependencies...\n'
  "$PYTHON" -m pip install -r "$ROOT_DIR/backend/requirements.txt"
fi

if [[ ! -x "$VITE" ]]; then
  printf 'Installing frontend dependencies...\n'
  npm ci --prefix "$ROOT_DIR/frontend"
fi

if [[ ! -x "$UVICORN" ]]; then
  printf 'Uvicorn was not installed from backend/requirements.txt. Check the installation output above.\n' >&2
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
