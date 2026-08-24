#!/usr/bin/env bash
# Starts Automate Inc. Creates a local virtualenv on first run, then plays.
set -euo pipefail

cd "$(dirname "$0")"

VENV=".venv"

if [ ! -d "$VENV" ]; then
    echo "Erster Start: richte die Umgebung ein …"
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install --quiet --upgrade pip
    "$VENV/bin/pip" install --quiet -e ".[dev]"
    echo "Fertig."
fi

exec "$VENV/bin/python" -m automate_inc "$@"
