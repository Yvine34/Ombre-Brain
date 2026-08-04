#!/bin/sh
# Start both server.py and gateway.py in one container
# server.py: MCP + Dashboard (port 8000)
# gateway.py: OpenAI-compatible Gateway (port 8010)

python server.py &
SERVER_PID=$!

python gateway.py &
GATEWAY_PID=$!

# If either process exits, stop the other and exit
trap "kill $SERVER_PID $GATEWAY_PID 2>/dev/null; exit" INT TERM

wait -n
kill $SERVER_PID $GATEWAY_PID 2>/dev/null
exit 1
