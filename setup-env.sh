#!/bin/bash
# Local Environment Setup Script
# Run this locally to create .env.docker.secret and .env.bot.secret

set -e

echo "=== Lab 7 Local Environment Setup ==="
echo ""

# Get user input
read -p "Enter your university email (e.g., name.surname@innopolis.university): " EMAIL
read -p "Enter your GitHub username: " GITHUB_USERNAME
read -p "Enter your Telegram alias (without @): " TELEGRAM_ALIAS
read -p "Enter your LMS API key (choose a secure value): " LMS_API_KEY
read -p "Enter your Telegram bot token (from BotFather): " BOT_TOKEN
read -p "Enter your Qwen Code API key: " QWEN_API_KEY

cd "$(dirname "$0")"

# Create .env.docker.secret
echo "Creating .env.docker.secret..."
cp .env.docker.example .env.docker.secret

# Replace placeholders
sed -i.bak "s|<lms-api-key>|${LMS_API_KEY}|g" .env.docker.secret
sed -i.bak "s|<lms-api-base-url>|http://localhost:42002|g" .env.docker.secret
sed -i.bak "s|<autochecker-api-login>|${EMAIL}|g" .env.docker.secret
sed -i.bak "s|<autochecker-api-password>|${GITHUB_USERNAME}${TELEGRAM_ALIAS}|g" .env.docker.secret
sed -i.bak "s|<bot-token>|${BOT_TOKEN}|g" .env.docker.secret
sed -i.bak "s|<llm-api-key>|${QWEN_API_KEY}|g" .env.docker.secret
sed -i.bak "s|<llm-api-base-url>|http://localhost:42005/v1|g" .env.docker.secret
sed -i.bak "s|<llm-api-model>|coder-model|g" .env.docker.secret

# Remove backup files
rm -f .env.docker.secret.bak

echo "✓ .env.docker.secret created"

# Create .env.bot.secret
echo "Creating .env.bot.secret..."
cp .env.bot.example .env.bot.secret

sed -i.bak "s|<bot-token>|${BOT_TOKEN}|g" .env.bot.secret
sed -i.bak "s|<lms-api-base-url>|http://localhost:42002|g" .env.bot.secret
sed -i.bak "s|<lms-api-key>|${LMS_API_KEY}|g" .env.bot.secret
sed -i.bak "s|<llm-api-key>|${QWEN_API_KEY}|g" .env.bot.secret
sed -i.bak "s|<llm-api-base-url>|http://localhost:42005/v1|g" .env.bot.secret

rm -f .env.bot.secret.bak

echo "✓ .env.bot.secret created"
echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Start services: docker compose --env-file .env.docker.secret up --build -d"
echo "2. Sync data: curl -X POST http://localhost:42002/pipeline/sync -H 'Authorization: Bearer ${LMS_API_KEY}' -H 'Content-Type: application/json' -d '{}'"
echo "3. Verify: curl -s http://localhost:42002/items/ -H 'Authorization: Bearer ${LMS_API_KEY}' | head -c 100"
