#!/bin/sh
# Start both server.py and gateway.py in one container
# server.py: MCP + Dashboard (port 8000)
# gateway.py: OpenAI-compatible Gateway (port 8010)

python server.py &
python gateway.py &

trap "kill $(jobs -p) 2>/dev/null; exit" INT TERM

wait
