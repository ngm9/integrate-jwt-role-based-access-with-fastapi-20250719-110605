#!/bin/bash
set -euo pipefail

if ! command -v docker &> /dev/null; then
  echo "[ERROR] Docker not found. Please install Docker first." >&2
  exit 1
fi

echo "[INFO] Building Docker image..."
docker build -t fastapi-jwtauth-fix .
echo "[INFO] Starting container..."
CONTAINER_NAME="fastapi-jwtauth-fix"
if [ $(docker ps -aq -f name=$CONTAINER_NAME) ]; then
  docker rm -f $CONTAINER_NAME >/dev/null 2>&1 || true
fi
docker run -d --name $CONTAINER_NAME --env-file .env -p 8000:8000 fastapi-jwtauth-fix
sleep 2
if docker ps | grep $CONTAINER_NAME &> /dev/null; then
  echo "[INFO] Container started successfully."
else
  echo "[ERROR] Failed to start container." >&2
  exit 2
fi
