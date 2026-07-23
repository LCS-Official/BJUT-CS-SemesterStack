#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/root/ch04}"
PID_FILE="${PID_FILE:-$APP_DIR/logs/chat-server.pid}"

if [ ! -f "$PID_FILE" ]; then
  echo "No pid file found: $PID_FILE"
  exit 0
fi

PID="$(cat "$PID_FILE" 2>/dev/null || true)"
if [ -z "$PID" ]; then
  rm -f "$PID_FILE"
  echo "Empty pid file removed."
  exit 0
fi

if ! kill -0 "$PID" 2>/dev/null; then
  rm -f "$PID_FILE"
  echo "Chat server pid $PID is not running."
  exit 0
fi

if ! ps -p "$PID" -o args= | grep -q 'com.cncd.ch04.server.MainServer'; then
  echo "Pid $PID is not this chat server. Refusing to stop it."
  exit 1
fi

kill "$PID"
rm -f "$PID_FILE"
echo "Stopped chat server pid $PID."
