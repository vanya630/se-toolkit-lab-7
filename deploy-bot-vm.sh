#!/bin/bash
# Deploy bot on VM - run this on your VM

set -e

echo "=== Deploying SE Toolkit Bot ==="

# Set bot token
BOT_TOKEN="8707129062:AAGSXBqg-qaWUOULA4GJ-rWyD9o-iud6SBs"

# Update .env.bot.secret
cd ~/se-toolkit-lab-7
sed -i "s|BOT_TOKEN=<bot-token>|BOT_TOKEN=$BOT_TOKEN|" .env.bot.secret
sed -i "s|LMS_API_BASE_URL=<lms-api-base-url>|LMS_API_BASE_URL=http://localhost:42002|" .env.bot.secret

echo "Environment configured:"
cat .env.bot.secret

# Kill any running bot
pkill -f "bot.py" 2>/dev/null || true

# Start the bot
cd ~/se-toolkit-lab-7/bot
export PATH=$HOME/.local/bin:$PATH
nohup uv run bot.py > ../bot.log 2>&1 &

echo ""
echo "Bot started! Check logs: tail -20 ~/se-toolkit-lab-7/bot.log"
echo "Send /start to your bot in Telegram to test"
