# TELEGRAM BOT SETUP GUIDE

## 🤖 AUTOMATED POLYMARKET SCANNER - TELEGRAM INTEGRATION

### 📋 WHAT THIS SYSTEM DOES
- **Daily Scanning**: Automatically checks all Polymarket weather markets
- **Pattern Analysis**: Applies your 95.9% win rate system
- **Edge Detection**: Identifies statistical disagreements
- **Telegram Alerts**: Instant notifications for opportunities
- **24/7 Monitoring**: Runs continuously for new markets

### 🔧 STEP 1: CREATE TELEGRAM BOT

1. **Open Telegram** and search for **@BotFather**
2. **Send**: `/newbot`
3. **Bot Name**: `Project Sentinel Scanner`
4. **Bot Username**: `project_sentinel_bot` (or similar)
5. **Get Token**: BotFather will give you a token like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### 🔧 STEP 2: GET YOUR CHAT ID

1. **Start your bot**: Send `/start` to your new bot
2. **Get Chat ID**: Use this method:
   - Send any message to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Look for `chat_id` in the response (usually a number like `123456789`)

### 🔧 STEP 3: CONFIGURE THE SCANNER

1. **Edit the scanner file**:
   ```python
   # In automated_polymarket_scanner.py, update these lines:
   self.telegram_bot_token = "YOUR_BOT_TOKEN_HERE"
   self.telegram_chat_id = "YOUR_CHAT_ID_HERE"
   ```

2. **Test the bot**:
   ```bash
   cd "/Users/wallace/Documents/ project-sentinel/src"
   python3 automated_polymarket_scanner.py
   ```

### 🔧 STEP 4: AUTOMATE DAILY EXECUTION

**Option A: Cron Job (Mac/Linux)**
```bash
# Edit crontab
crontab -e

# Add this line for daily 9 AM scanning
0 9 * * * cd "/Users/wallace/Documents/ project-sentinel/src" && python3 automated_polymarket_scanner.py
```

**Option B: Python Schedule**
```python
# Add to the scanner for automatic scheduling
import schedule
import time

schedule.every().day.at("09:00").run(daily_scan)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 📱 ALERT MESSAGE FORMAT

**You'll receive alerts like this:**
```
🌡️ POLYMARKET WEATHER OPPORTUNITY ALERT

📍 Location: New York
📅 Date: 2 days ahead
🎯 Market Type: precipitation
📊 Edge Score: 0.43
🔥 Recommendation: STRONG BUY
💰 Position Size: LARGE ($20-50)
📈 Confidence: 88.0%

🔍 Analysis Details:
• Forecast: 3.68 inches
• Confidence: 83.3%
• Patterns: wet_pattern_good_conf
• Best Match: no

⚡ Action Required: Check Polymarket for this market!

🕐 Alert Time: 2026-03-04 09:00:00
🤖 System: Project Sentinel 95.9% Win Rate
```

### ⚙️ CONFIGURATION OPTIONS

**Alert Thresholds:**
```python
# In the scanner, adjust these values:
self.min_edge_score = 0.2      # Minimum edge to alert
self.min_confidence = 0.75    # Minimum confidence to alert
```

**Scanning Frequency:**
- **Daily**: Once per day at 9 AM
- **Twice Daily**: 9 AM and 6 PM
- **Hourly**: Every hour (more alerts, more noise)

**Market Types:**
- **Temperature**: Daily temperature predictions
- **Precipitation**: Rain/snow predictions
- **Extreme Weather**: Heat waves, storms, etc.

### 🔒 SECURITY CONSIDERATIONS

**Keep Your Token Safe:**
- Never share your bot token publicly
- Use environment variables for production
- Restrict bot commands to authorized users

**Bot Security:**
```python
# Add user authorization
AUTHORIZED_USERS = [123456789]  # Your chat ID

if update.message.chat_id not in AUTHORIZED_USERS:
    return
```

### 📊 MONITORING & LOGGING

**Daily Reports:**
- Scan results saved to JSON files
- Alert history tracked
- Performance metrics recorded

**Log Files:**
```
daily_scan_20260304.json
daily_scan_20260305.json
# etc.
```

### 🚀 ADVANCED FEATURES

**Custom Alert Filters:**
- Minimum edge score
- Minimum confidence
- Specific cities only
- Market type preferences

**Alert Frequency Control:**
- Rate limiting
- Consolidated alerts
- Quiet hours

**Integration with Trading:**
- Direct Polymarket links
- One-click execution
- Portfolio tracking

### 💡 TROUBLESHOOTING

**Bot Not Responding:**
- Check token is correct
- Verify chat ID
- Ensure bot is running

**No Alerts:**
- Check edge thresholds
- Verify market data
- Review scan logs

**Telegram API Issues:**
- Check internet connection
- Verify token permissions
- Review rate limits

### 🎯 NEXT STEPS

1. **Create Telegram Bot** using BotFather
2. **Get Chat ID** from getUpdates API
3. **Configure Scanner** with your credentials
4. **Test Alert System** with manual run
5. **Schedule Daily Scans** using cron or scheduler
6. **Monitor Performance** and adjust thresholds

### 📞 SUPPORT

**For Issues:**
- Check log files for errors
- Verify Telegram API status
- Review configuration settings
- Test bot manually first

**🎉 YOUR AUTOMATED SCANNING SYSTEM WILL BE READY IN MINUTES!**

This system will automatically find opportunities and alert you instantly, eliminating the need for manual market searching.
