#!/bin/bash
set -euo pipefail

./install.sh

if curl -s http://localhost:8000/docs > /dev/null; then
    echo "[SUCCESS] FastAPI app is running at http://localhost:8000/docs"
else
    echo "[ERROR] FastAPI app is not reachable!" >&2
    exit 3
fi
