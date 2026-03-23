#!/bin/bash
# Fix script for Task 2 - Backend Integration
# Run this on your VM: bash fix-vm.sh

set -e

echo "=== Task 2 Fix Script ==="
echo ""

# Step 1: Get correct API key from backend container
echo "[1/6] Getting API key from backend..."
LMS_API_KEY=$(docker exec se-toolkit-lab-7-backend-1 env | grep LMS_API_KEY | cut -d= -f2)
echo "API Key: $LMS_API_KEY"

# Step 2: Create .env.bot.secret
echo ""
echo "[2/6] Creating .env.bot.secret..."
cd ~/se-toolkit-lab-7
cat > .env.bot.secret << EOF
BOT_TOKEN=placeholder-bot-token
LMS_API_BASE_URL=http://localhost:42002
LMS_API_KEY=$LMS_API_KEY
LLM_API_KEY=placeholder-llm-key
LLM_API_BASE_URL=http://localhost:42005/v1
LLM_API_MODEL=coder-model
EOF
echo "Created .env.bot.secret"

# Step 3: Run ETL sync
echo ""
echo "[3/6] Running ETL sync..."
curl -s -X POST http://localhost:42002/pipeline/sync \
  -H "Authorization: Bearer $LMS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{}'
echo ""

# Step 4: Verify backend has data
echo ""
echo "[4/6] Verifying backend data..."
ITEM_COUNT=$(curl -s http://localhost:42002/items/ -H "Authorization: Bearer $LMS_API_KEY" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
echo "Items in database: $ITEM_COUNT"

# Step 5: Test bot commands
echo ""
echo "[5/6] Testing bot commands..."
cd ~/se-toolkit-lab-7/bot

echo "Testing /start..."
timeout 30 uv run bot.py --test "/start" || echo "TIMEOUT on /start"

echo ""
echo "Testing /help..."
timeout 30 uv run bot.py --test "/help" || echo "TIMEOUT on /help"

echo ""
echo "Testing /health..."
timeout 30 uv run bot.py --test "/health" || echo "TIMEOUT on /health"

echo ""
echo "Testing /labs..."
timeout 30 uv run bot.py --test "/labs" || echo "TIMEOUT on /labs"

echo ""
echo "Testing /scores lab-04..."
timeout 30 uv run bot.py --test "/scores lab-04" || echo "TIMEOUT on /scores lab-04"

# Step 6: Summary
echo ""
echo "=== [6/6] Summary ==="
echo "If all tests above showed output (not TIMEOUT), you're ready!"
echo ""
echo "Files created/updated:"
echo "  - ~/se-toolkit-lab-7/.env.bot.secret"
echo ""
echo "Next step: Submit to autochecker"
