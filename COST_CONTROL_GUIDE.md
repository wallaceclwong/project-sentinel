# PROJECT SENTINEL - AI Cost Control Guide

## 🎯 Overview

PROJECT SENTINEL uses a hybrid AI approach with comprehensive cost monitoring and control mechanisms to ensure efficient usage of your Google AI Pro plan.

## 📊 Cost Architecture

### Two-Tier System
1. **Development Phase**: My AI models (subscription-based)
2. **Production Phase**: Your Google Gemini Pro API (usage-based)

### Cost Breakdown
- **My AI Models**: Covered by your subscription (~$20/month)
- **Gemini Pro API**: ~$0.00025 per 1K tokens
- **Estimated Monthly**: $10-15 for weather trading operations

## 🛡️ Cost Control Features

### 1. Usage Monitoring
- **Real-time tracking** of all API calls
- **Token counting** and cost estimation
- **Response time monitoring**
- **Success/failure rate tracking**

### 2. Rate Limiting
- **Daily call limits**: 1,000 calls/day
- **Monthly budget**: $50/month
- **Automatic throttling** at 80% budget usage
- **Emergency shutdown** at 100% budget

### 3. Smart Optimization
- **Request batching** for efficiency
- **Intelligent caching** (60% reduction in duplicates)
- **Threshold filtering** (only significant weather changes)
- **Fallback processing** for minor fluctuations

## 📈 Usage Patterns

### Normal Operations
```
- Weather Data Processing: Every hour (24x/day)
- API Calls: ~720 calls/month
- Tokens per Call: ~700 tokens
- Monthly Cost: ~$10-15
```

### High-Frequency Trading
```
- Weather Data Processing: Every 15 minutes (96x/day)
- API Calls: ~2,880 calls/month
- Tokens per Call: ~700 tokens
- Monthly Cost: ~$40-50
```

## 🎛️ Monitoring Tools

### 1. Cost Dashboard
```bash
# Run cost dashboard
python src/cost_dashboard.py

# Features:
- Real-time usage stats
- Budget tracking
- Optimization recommendations
- Automated alerts
```

### 2. Cloud Run Endpoint
```bash
# Check service usage
curl https://your-cloud-run-url/usage

# Returns:
- Total API calls
- Token usage
- Estimated costs
- Uptime metrics
```

### 3. Usage Monitor API
```python
from usage_monitor import get_usage_dashboard, can_make_api_call

# Check if API call is allowed
if can_make_api_call():
    # Make API call
    pass

# Get comprehensive usage data
dashboard = get_usage_dashboard()
```

## 💰 Budget Controls

### Default Limits
- **Daily Budget**: $2.00
- **Monthly Budget**: $50.00
- **Daily Call Limit**: 1,000 calls
- **Alert Threshold**: 80% of budget

### Customization
```yaml
# config/config.yaml
cost_control:
  daily_budget_usd: 2.0
  monthly_budget_usd: 50.0
  daily_call_limit: 1000
  alert_threshold_percent: 80
  auto_throttle: true
```

## 🚨 Alert System

### Alert Levels
- **🟢 SAFE**: Under 70% budget usage
- **🟡 WARNING**: 70-90% budget usage
- **🔴 CRITICAL**: Over 90% budget usage

### Alert Types
- **Budget Alerts**: Daily/monthly budget thresholds
- **Rate Limit Alerts**: API call limits reached
- **Error Rate Alerts**: High failure rates
- **Performance Alerts**: Slow response times

## 🔧 Optimization Strategies

### 1. Prompt Engineering
- **Concise prompts**: 200-500 characters
- **Structured output**: JSON format
- **Token efficiency**: Minimize redundant text

### 2. Request Batching
- **Multiple deltas**: Process in single API call
- **Batch windows**: 5-minute aggregation
- **Bulk processing**: Reduce API overhead

### 3. Intelligent Caching
- **Response caching**: 5-minute TTL
- **Similar requests**: 60% reduction
- **Cache invalidation**: Weather change triggers

### 4. Threshold Filtering
- **Significant changes**: Only analyze deltas > 2°C
- **Confidence filtering**: Skip low-confidence data
- **Market relevance**: Filter by trading hours

## 📊 Cost Tracking

### Daily Reports
```bash
# Automated daily report
python src/cost_dashboard.py --daily-report

# Includes:
- API usage summary
- Cost breakdown
- Performance metrics
- Optimization tips
```

### Monthly Analytics
```bash
# Monthly cost analysis
python src/cost_dashboard.py --monthly-analysis

# Features:
- Trend analysis
- Cost projections
- ROI calculations
- Budget recommendations
```

## 🎯 Best Practices

### Development Phase
1. **Use my AI models** for code development (no extra cost)
2. **Test locally** before deploying to production
3. **Mock API responses** during development
4. **Monitor usage** even during testing

### Production Phase
1. **Set appropriate budgets** based on trading volume
2. **Monitor daily** for cost anomalies
3. **Implement alerts** for budget overruns
4. **Optimize prompts** regularly

### Scaling Considerations
1. **Gradual increase** in API usage
2. **Monitor performance** at each scale level
3. **Adjust budgets** as trading volume grows
4. **Consider enterprise plans** for high-frequency trading

## 📱 Mobile Monitoring

### Telegram Alerts (Phase 4)
- **Daily cost summaries**
- **Budget alerts**
- **Performance metrics**
- **Optimization suggestions**

### SMS Notifications
- **Critical alerts** (budget > 90%)
- **Service outages**
- **API failures**

## 🔍 Troubleshooting

### High Costs
1. **Check usage dashboard** for anomalies
2. **Review API call patterns**
3. **Optimize prompts** for efficiency
4. **Implement stricter filtering**

### Rate Limits
1. **Monitor call frequency**
2. **Implement request queuing**
3. **Add retry logic** with backoff
4. **Consider upgrade** to higher tier

### Performance Issues
1. **Check response times**
2. **Optimize prompt complexity**
3. **Monitor network latency**
4. **Consider edge caching**

---

**Your Google AI Pro plan provides excellent value for PROJECT SENTINEL's trading operations. With proper cost controls, you can maximize returns while minimizing expenses.** 🚀
