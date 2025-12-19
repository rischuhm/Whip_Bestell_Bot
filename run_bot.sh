#!/bin/bash
# Script to run the Telegram bot

cd "$(dirname "$0")"
source venv/bin/activate

# Check if bot is already running
if [ -f bot.pid ] && ps -p $(cat bot.pid) > /dev/null 2>&1; then
    echo "Bot is already running (PID: $(cat bot.pid))"
    echo "To stop it, run: kill $(cat bot.pid)"
    exit 1
fi

# Start the bot
echo "Starting bot..."
nohup python bot.py > bot.log 2>&1 &
echo $! > bot.pid
sleep 2

if ps -p $(cat bot.pid) > /dev/null 2>&1; then
    echo "✅ Bot started successfully! (PID: $(cat bot.pid))"
    echo "📋 Logs: tail -f bot.log"
    echo "🛑 Stop: kill $(cat bot.pid)"
else
    echo "❌ Bot failed to start. Check bot.log:"
    cat bot.log
    exit 1
fi

