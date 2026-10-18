#!/usr/bin/env bash
set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# Preserve the existing command while supporting the project's uv environment.
if [[ $# -eq 0 ]]; then
    set -- upgrade head
fi
if command -v uv >/dev/null 2>&1; then
    uv sync --project "$BACKEND_DIR" >&2
    exec uv run --project "$BACKEND_DIR" alembic -c "$BACKEND_DIR/alembic.ini" "$@"
fi
VENV_DIR="$BACKEND_DIR/.venv"
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/python" -m ensurepip >&2
"$VENV_DIR/bin/python" -m pip install -r "$BACKEND_DIR/requirements-migrations.txt" >&2
exec "$VENV_DIR/bin/python" -m alembic -c "$BACKEND_DIR/alembic.ini" "$@"
