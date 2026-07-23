#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/root/ch04}"
PORT="${1:-${CHAT_PORT:-}}"
PID_FILE="${PID_FILE:-$APP_DIR/logs/chat-server.pid}"
LOG_FILE="${LOG_FILE:-$APP_DIR/logs/server.log}"

if [ -z "$PORT" ]; then
  echo "Usage: $0 <port>  (or set CHAT_PORT)" >&2
  exit 2
fi

cd "$APP_DIR"
mkdir -p out logs chat-data
find . -name '*.java' > sources.txt
if [ ! -s sources.txt ]; then
  echo "No Java source files found under $APP_DIR. Upload the project first."
  exit 1
fi

javac -encoding UTF-8 -d out @sources.txt

if [ -f "$PID_FILE" ]; then
  OLD_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
    if ps -p "$OLD_PID" -o args= | grep -q 'com.cncd.ch04.server.MainServer'; then
      echo "Stopping old chat server pid $OLD_PID..."
      kill "$OLD_PID" || true
      sleep 1
    else
      echo "Pid file points to a non-chat process; refusing to stop it: $OLD_PID"
      exit 1
    fi
  fi
fi

nohup java -Dfile.encoding=UTF-8 -cp out com.cncd.ch04.server.MainServer "$PORT" >> "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
echo "Started chat server on port $PORT. Pid: $(cat "$PID_FILE"). Log: $LOG_FILE"
ss -lntp | grep ":$PORT " || true
