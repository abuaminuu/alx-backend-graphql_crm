# monitor_order_cron.sh
#!/bin/bash

echo "=== Order Reminder Cron Status ==="
echo "Time: $(date)"
echo ""

# Check if cron job exists
if crontab -l | grep -q "send_order_reminders"; then
    echo "✅ Cron job scheduled:"
    crontab -l | grep "send_order_reminders"
else
    echo "❌ Cron job not found"
fi

echo ""
echo "📊 Log file status:"
if [ -f "/tmp/order_reminders_log.txt" ]; then
    echo "Log file exists"
    echo "Last modified: $(stat -c %y /tmp/order_reminders_log.txt)"
    echo "Size: $(wc -l < /tmp/order_reminders_log.txt) lines"
    echo ""
    echo "Last 3 entries:"
    tail -3 /tmp/order_reminders_log.txt
else
    echo "Log file not found"
fi

echo ""
echo "🔍 Process check:"
if pgrep -f "send_order_reminders" > /dev/null; then
    echo "Script is currently running"
else
    echo "Script is not running"
fi
