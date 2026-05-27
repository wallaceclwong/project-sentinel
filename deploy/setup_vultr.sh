#!/bin/bash
# WeatherNext Pro — Vultr VM Setup Script
# Run this ON the Vultr VM after uploading the project.
#
# Usage:
#   1. scp -r weathernext_pro/ root@YOUR_VULTR_IP:/root/
#   2. ssh root@YOUR_VULTR_IP
#   3. cd /root/weathernext_pro
#   4. bash deploy/setup_vultr.sh

set -e

APP_DIR="/root/weathernext_pro"
SERVICE_NAME="weathernext"
PYTHON="python3"

echo "=== WeatherNext Pro — Vultr Setup ==="

# 1. Install Python + pip if missing
echo "[1/5] Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "Installing Python 3..."
    apt-get update -qq && apt-get install -y python3 python3-pip python3-venv
else
    echo "Python3 found: $(python3 --version)"
fi

# 2. Create venv and install deps
echo "[2/5] Setting up virtual environment..."
cd "$APP_DIR"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "Dependencies installed."

# 3. Check .env
echo "[3/5] Checking .env..."
if [ ! -f "$APP_DIR/.env" ]; then
    echo "ERROR: No .env file found!"
    echo "Copy .env.example to .env and fill in your API keys:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Verify GMAPS key is set
if grep -q "GMAPS_API_KEY=$" "$APP_DIR/.env" || grep -q "GMAPS_API_KEY=\"\"" "$APP_DIR/.env"; then
    echo "WARNING: GMAPS_API_KEY appears empty in .env — scanner won't get forecasts!"
fi

echo ".env found."

# 4. Create directories
echo "[4/5] Creating data/logs directories..."
mkdir -p "$APP_DIR/data" "$APP_DIR/logs"

# 5. Install systemd service
echo "[5/5] Installing systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=WeatherNext Pro — Polymarket Temperature Scanner
After=network.target

[Service]
Type=simple
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/venv/bin/python main.py
Restart=always
RestartSec=60
StandardOutput=journal
StandardError=journal

# Env vars from .env are loaded by python-dotenv inside the app
# But set PATH so venv python is used
Environment=PATH=${APP_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl start ${SERVICE_NAME}

echo ""
echo "=== DONE ==="
echo ""
echo "Scanner is now running as a systemd service."
echo ""
echo "Useful commands:"
echo "  systemctl status weathernext       # Check status"
echo "  journalctl -u weathernext -f       # Watch live logs"
echo "  systemctl restart weathernext      # Restart"
echo "  systemctl stop weathernext         # Stop"
echo ""
echo "Signals are logged to: ${APP_DIR}/data/signals.jsonl"
echo "App logs are at:       ${APP_DIR}/logs/weathernext_pro.log"
echo ""
echo "To score predictions:"
echo "  cd ${APP_DIR} && source venv/bin/activate"
echo "  python resolve_signals.py"
echo "  python score_signals.py --by-city"
