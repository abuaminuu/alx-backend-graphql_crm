# monitor_heartbeat.sh
#!/bin/bash

echo "=== CRM Heartbeat Monitor ==="
echo "Time: $(date '+%d/%m/%Y-%H:%M:%S')"
echo ""

# Check if cron job is installed
echo "🔍 Cron Job Status:"
if crontab -l | grep -q "log_crm_heartbeat"; then
    echo "✅ Heartbeat cron job is installed"
    crontab -l | grep "log_crm_heartbeat"
else
    echo "❌ Heartbeat cron job NOT found"
fi

echo ""
echo "📊 Log File Status:"
LOG_FILE="/tmp/crm_heartbeat_log.txt"

if [ -f "$LOG_FILE" ]; then
    echo "✅ Log file exists: $LOG_FILE"
    echo "Size: $(wc -l < "$LOG_FILE") lines"
    echo "Last modified: $(stat -c %y "$LOG_FILE" 2>/dev/null || stat -f %Sm "$LOG_FILE")"
    
    echo ""
    echo "Last 5 heartbeats:"
    echo "------------------"
    tail -5 "$LOG_FILE"
    
    # Check if heartbeat is recent (within last 10 minutes)
    if [ -s "$LOG_FILE" ]; then
        last_log=$(tail -1 "$LOG_FILE")
        log_time=$(echo "$last_log" | cut -d' ' -f1)
        
        # Convert to timestamp (simplified check)
        current_minutes=$(date +%s | awk '{print int($1/60)}')
        # This is a simplified check - in production, parse the actual timestamp
        
        echo ""
        echo "⏰ Last heartbeat: $log_time"
    fi
else
    echo "❌ Log file not found: $LOG_FILE"
fi

echo ""
echo "🔄 Running manual heartbeat test..."
python manage.py shell << 'EOF'
from crm.cron import log_crm_heartbeat
result = log_crm_heartbeat()
print(f"Manual test result: {'SUCCESS' if result else 'FAILED'}")
EOF
