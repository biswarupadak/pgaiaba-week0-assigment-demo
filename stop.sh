#!/usr/bin/env bash
# Stop the Kartify Order Assistant web UI started by start.sh / start.bat.
#   ./stop.sh           stops whatever is listening on port 8501
#   ./stop.sh 8502      another port
set -euo pipefail
PORT="${1:-8501}"

case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*)
        pids=$(netstat -ano | awk -v p=":$PORT" '$2 ~ p"$" && $4 == "LISTENING" {print $5}' | sort -u)
        ;;
    *)
        pids=$(lsof -ti "tcp:$PORT" -sTCP:LISTEN 2>/dev/null || true)
        ;;
esac

if [ -z "$pids" ]; then
    echo "Nothing is listening on port $PORT."
    exit 0
fi

for pid in $pids; do
    echo "Stopping process $pid on port $PORT"
    case "$(uname -s)" in
        MINGW*|MSYS*|CYGWIN*) MSYS_NO_PATHCONV=1 taskkill /PID "$pid" /T /F >/dev/null ;;
        *) kill "$pid" ;;
    esac
done
