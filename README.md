# PROJECT SENTINEL: Weather Derivatives Trading System

**Master Deployment Plan v2026.03.02**

## Overview
PROJECT SENTINEL is an automated weather derivatives trading system that processes WeatherNext 2 ensemble forecasts, validates trades using Gemini Pro AI, and executes on Polymarket with Telegram alerts.

## Architecture
```
Tokyo (Vultr) → HTTPS/Tailscale → Hong Kong (GCP Cloud Run) → Polymarket API
Weather Data → Gemini Pro → Trade Signals → Execution → Telegram Alerts
```

## Phases

### ✅ Phase 1: Infrastructure Handshake
- [x] Vultr High-Frequency Node (Tokyo, Ubuntu 24.04)
- [x] Tailscale SSH transport (no public Port 22)
- [x] UFW firewall with tailscale0 interface
- [x] Project directory at `/home/ubuntu/project-sentinel`

### ✅ Phase 2: Data Ingestion Engine
- [x] WeatherNext 2 ensemble forecast processing (64-member)
- [x] Python Data Watcher with Dask + Xarray
- [x] Parallel chunk processing on 2GB RAM instance
- [x] 24-hour rolling data lake storage
- [x] Weather delta calculation and scoring

### ✅ Phase 3: Reasoning Logic
- [x] GCP Cloud Run service (Hong Kong)
- [x] Gemini Pro 1.5/2.0 integration
- [x] Secure HTTPS/Tailscale bridge
- [x] Weather delta scoring algorithm
- [x] Trade validation against Polymarket sentiment
- [x] AI-powered BUY/SELL/HOLD signals

### 🚧 Phase 4: Execution & Alerting (Pending)
- [ ] Polymarket CLOB API integration
- [ ] Telegram messaging bridge to Pixel 9 Pro XL
- [ ] 2FA-style trade confirmation (Beta week)

## Quick Start

### Local Development
```bash
# Clone repository
git clone <repository-url>
cd project-sentinel

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run data watcher
python src/data_watcher.py
```

### Remote Development (Tokyo)
```bash
# Connect via Windsurf with optimized shell
# Custom profile loads automatically with:
# - Enhanced colored prompt with git status
# - Project-specific aliases (sentinel, logs, venv)
# - Auto virtual environment activation
# - System-wide sentinel commands

# Available commands:
sentinel-info          # Show project status
sentinel-dev           # Activate venv + change to project dir
test-sentinel          # Run component tests
start-sentinel         # Start sentinel service
logs                   # Monitor log files
venv                   # Activate virtual environment
```

### Shell Configuration Features
- **Enhanced Prompt**: Color-coded with git branch status
- **Smart Aliases**: Quick navigation and git commands
- **Auto-completion**: Git and command completion
- **Project Shortcuts**: Direct access to logs, data, venv
- **System Commands**: Global sentinel utilities

### GCP Cloud Run Deployment
```bash
# Set credentials
export GEMINI_API_KEY="your-api-key"
export GCP_PROJECT_ID="your-project-id"

# Deploy reasoning service
./deploy_cloud_run.sh
```

## Configuration

### Main Config (`config/config.yaml`)
```yaml
data_lake:
  path: "/home/ubuntu/project-sentinel/data"
  retention_hours: 24

weather_api:
  base_url: "https://weathernext-api.com"
  ensemble_members: 64

gcp_bridge:
  cloud_run_url: "https://sentinel-reasoning-xxxxx-uc.a.run.app"
  timeout_seconds: 30
```

### Environment Variables
```bash
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
export GEMINI_API_KEY="your-gemini-key"
```

## System Components

### Data Watcher (`src/data_watcher.py`)
- Fetches WeatherNext 2 ensemble forecasts
- Calculates weather deltas between consecutive forecasts
- Stores data in rolling 24-hour data lake
- Sends deltas to Gemini Pro for validation

### GCP Bridge (`src/gcp_bridge.py`)
- Secure HTTPS communication with Cloud Run service
- Weather delta impact scoring
- Market sentiment integration
- Trade signal processing

### Cloud Run Service (`cloud_run/main.py`)
- FastAPI service with Gemini Pro integration
- Trade validation endpoint
- Health monitoring
- CORS support for Tailscale bridge

## Monitoring

### Logs
```bash
# Tokyo node
tail -f /home/ubuntu/project-sentinel/logs/data_watcher.log

# GCP Cloud Run
gcloud logs read "resource.type=cloud_run" --limit 50
```

### Health Checks
```bash
# Local service
curl http://localhost:8787/health

# GCP service
curl https://sentinel-reasoning-xxxxx-uc.a.run.app/health
```

## Performance

### Tokyo Node (Vultr 2GB RAM)
- Dask workers: 2 processes, 1 thread each
- Memory limit: 800MB per worker
- Dashboard: http://localhost:8787

### GCP Cloud Run
- Memory: 512Mi
- CPU: 1 vCPU
- Timeout: 30s
- Max instances: 10

## Security

### Network
- Tailscale VPN for all communications
- No public ports exposed (except Cloud Run HTTPS)
- UFW firewall with tailscale0 only

### API Security
- Environment variables for credentials
- GCP Secret Manager recommended for production
- API key usage restrictions

## Cost Estimates

### Vultr Tokyo
- $6/month (2GB RAM High Frequency)

### GCP Cloud Run
- ~$0.000024 per 100ms execution
- ~$20/month for moderate usage

### Gemini Pro API
- ~$0.00025 per 1K characters
- ~$10/month for weather analysis

**Total Estimated: ~$36/month**

## Development Status

### Completed Features
- ✅ Weather data ingestion and processing
- ✅ Ensemble forecast delta calculation
- ✅ Rolling data lake storage
- ✅ AI-powered trade validation
- ✅ Secure cross-region communication

### Next Steps
- 🔄 Polymarket CLOB API integration
- 🔄 Telegram alert system
- 🔄 Trade execution with 2FA confirmation
- 🔄 Production deployment and monitoring

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

This project is proprietary and confidential.

---

**PROJECT SENTINEL** - Weather-Driven Trading Intelligence
*Deployed: March 2, 2026*
