# PROJECT SENTINEL - Command Reference

## 🚀 Quick Start Commands

### Development Workflow
```bash
sentinel-dev          # Activate venv + change to project dir
sentinel-info          # Show complete project status
test-sentinel          # Run all component tests
```

### Service Management
```bash
start-sentinel         # Start sentinel service
stop-sentinel          # Stop sentinel service  
restart-sentinel       # Restart sentinel service
sentinel-status        # Check service status
watch-sentinel         # Monitor service in real-time
```

### File Navigation
```bash
sentinel               # Go to project directory
logs                   # Go to logs and tail files
ll                     # Detailed file listing
la                     # Show hidden files
..                     # Go up one directory
...                    # Go up two directories
```

### Git Operations
```bash
gs                     # git status
ga                     # git add
gc "message"           # git commit with message
gp                     # git push
gl                     # git pull
gd                     # git diff
gb                     # git branch
gco                    # git checkout
```

### Python Environment
```bash
venv                   # Activate virtual environment
py                     # python3 shortcut
pip                    # pip3 shortcut
```

### System Monitoring
```bash
check-disk             # Show disk usage
clean-data             # Clean old data files
```

## 📊 Custom Functions

### `sentinel-info()`
Displays comprehensive project status:
- Project directories
- Service status
- Disk usage
- Network info

### `sentinel-dev()`
One-command development setup:
- Changes to project directory
- Activates virtual environment
- Shows confirmation

### `test-sentinel()`
Runs component health checks:
- Python environment
- Virtual environment
- Core scripts
- Tailscale connectivity

## 🔧 Environment Variables

```bash
$SENTINEL_HOME         # Project directory
$SENTINEL_VENV         # Virtual environment path
$SENTINEL_LOGS         # Logs directory
$SENTINEL_DATA         # Data lake directory
```

## 🎯 Tips & Tricks

1. **Auto-completion**: Tab completion works for git commands and files
2. **History**: Enhanced history with timestamps and duplicates ignored
3. **Prompt**: Color-coded prompt shows git branch and status
4. **Fast Navigation**: Use `..` and `...` for quick directory jumps
5. **Service Control**: All service commands include status feedback

## 🚨 Troubleshooting

### Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Service Problems
```bash
# Check detailed logs
sudo journalctl -u sentinel -f

# Restart with fresh config
sudo systemctl daemon-reload
sudo systemctl restart sentinel
```

### Network Issues
```bash
# Check Tailscale status
tailscale status

# Restart Tailscale
sudo systemctl restart tailscaled
```
