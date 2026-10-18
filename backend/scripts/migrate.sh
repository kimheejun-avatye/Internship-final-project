#!/usr/bin/env bash
set -euo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$BACKEND_DIR/.venv"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
    python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/python" -m pip install -r "$BACKEND_DIR/requirements-migrations.txt" >&2

# With no arguments, apply all pending migrations. Otherwise forward Alembic args.
if [[ $# -eq 0 ]]; then
    set -- upgrade head
fi
exec "$VENV_DIR/bin/python" -m alembic -c "$BACKEND_DIR/alembic.ini" "$@"
