#!/bin/bash
# Persistent tunnel manager for Thinker and Scriber

LOGDIR="/Users/malikano/clawd/tunnels/logs"
mkdir -p "$LOGDIR"

# Kill existing tunnels
pkill -f "cloudflared tunnel" 2>/dev/null
sleep 2

# Start Thinker tunnel (port 8585)
nohup cloudflared tunnel --url http://localhost:8585 > "$LOGDIR/thinker_tunnel.log" 2>&1 &
echo $! > "$LOGDIR/thinker_tunnel.pid"

# Start Scriber tunnel (port 8586)
nohup cloudflared tunnel --url http://localhost:8586 > "$LOGDIR/scriber_tunnel.log" 2>&1 &
echo $! > "$LOGDIR/scriber_tunnel.pid"

sleep 8

# Print URLs
echo "=== Tunnel URLs ==="
echo "Thinker: $(grep -o 'https://[^ ]*trycloudflare.com' $LOGDIR/thinker_tunnel.log | head -1)"
echo "Scriber: $(grep -o 'https://[^ ]*trycloudflare.com' $LOGDIR/scriber_tunnel.log | head -1)"
