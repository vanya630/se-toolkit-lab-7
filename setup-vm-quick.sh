#!/bin/bash
# Quick Setup Script for Lab 7 VM
set -e

echo "=== Lab 7 Quick Setup ==="

# 1. Install Docker (if not installed)
if ! command -v docker &> /dev/null; then
    echo "[1/8] Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker $USER
else
    echo "[1/8] Docker already installed"
fi

# 2. Configure Docker DNS
echo "[2/8] Configuring Docker DNS..."
sudo tee /etc/docker/daemon.json <<'EOF'
{
  "dns": ["8.8.8.8", "8.8.4.4"]
}
EOF
sudo systemctl restart docker

# 3. Install uv
if ! command -v uv &> /dev/null; then
    echo "[3/8] Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
else
    echo "[3/8] uv already installed"
fi

# 4. Clone/pull repo
echo "[4/8] Setting up repo..."
cd ~
if [ -d ~/se-toolkit-lab-7 ]; then
    cd ~/se-toolkit-lab-7 && git pull
else
    git clone https://github.com/vanya630/se-toolkit-lab-7 ~/se-toolkit-lab-7
fi

# 5. Setup .env.docker.secret
echo "[5/8] Configuring .env.docker.secret..."
cd ~/se-toolkit-lab-7
cp .env.docker.example .env.docker.secret
sed -i 's|LMS_API_KEY=.*|LMS_API_KEY=lab7-secret-key-root|' .env.docker.secret
sed -i 's|REGISTRY_PREFIX=.*|REGISTRY_PREFIX=|' .env.docker.secret

# 6. Start backend
echo "[6/8] Starting Docker services..."
docker compose --env-file .env.docker.secret up -d --build
sleep 30

# 7. Run ETL sync
echo "[7/8] Running ETL sync..."
curl -X POST http://localhost:42002/pipeline/sync \
  -H "Authorization: Bearer lab7-secret-key-root" \
  -H "Content-Type: application/json" \
  -d '{}'
echo ""

# 8. Setup Qwen Code API
echo "[8/8] Setting up Qwen Code API..."
cd ~
if [ ! -d ~/qwen-code-oai-proxy ]; then
    git clone https://github.com/innopolis-se-toolkit/qwen-code-oai-proxy ~/qwen-code-oai-proxy
fi
cd ~/qwen-code-oai-proxy

cat > .env <<'QWENEOF'
PORT=8080
HOST_ADDRESS=127.0.0.1
CONTAINER_ADDRESS=0.0.0.0
QWEN_CODE_API_HOST_PORT=42005
LOG_LEVEL=error
QWEN_CODE_AUTH_USE=true
QWEN_CODE_API_KEY=my-secret-qwen-key
QWENEOF

mkdir -p ~/.qwen
cat > ~/.qwen/oauth_creds.json <<'QWENCREDS'
{
  "access_token": "27539Eai-QC3XIFPmRP5bR3wW1ytS7odusf4OghXNs-StSyhTqhEs_gYo_HCHThb_TVr28cUaGT4_N9EwzUGKg",
  "token_type": "Bearer",
  "refresh_token": "l_AIt3EuiD7USAk_uX2IFBgZ8-l3rMgb1RM6b93PA5Cwa8QbyCdDqGGFMbLWir48sG-_frdlcxV9JMAoZU5ttg",
  "resource_url": "portal.qwen.ai",
  "expiry_date": 1774154556331
}
QWENCREDS

docker compose up --build -d
sleep 15

# Test Qwen API
curl -s http://localhost:42005/v1/models -H "Authorization: Bearer my-secret-qwen-key" | head -c 100
echo ""

# Setup bot
echo ""
echo "=== Setting up bot ==="
cd ~/se-toolkit-lab-7
cp .env.bot.example .env.bot.secret
cat > .env.bot.secret <<'BOTENV'
BOT_TOKEN=8707129062:AAGSXBqg-qaWUOULA4GJ-rWyD9o-iud6SBs
LMS_API_BASE_URL=http://localhost:42002
LMS_API_KEY=lab7-secret-key-root
LLM_API_MODEL=coder-model
LLM_API_KEY=my-secret-qwen-key
LLM_API_BASE_URL=http://localhost:42005/v1
BOTENV

export PATH=$HOME/.local/bin:$PATH
cd ~/se-toolkit-lab-7/bot
uv sync

# Test bot commands
echo ""
echo "=== Testing bot commands ==="
uv run bot.py --test "/health"
uv run bot.py --test "/labs"
uv run bot.py --test "/scores lab-04"

# Setup SSH for autochecker
echo ""
echo "=== Setting up SSH for autochecker ==="
mkdir -p ~/.ssh
echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKiL0DDQZw7L0Uf1c9cNlREY7IS6ZkIbGVWNsClqGNCZ se-toolkit-autochecker' >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# Start bot
echo ""
echo "=== Starting bot ==="
pkill -f "bot.py" 2>/dev/null || true
cd ~/se-toolkit-lab-7/bot
nohup uv run bot.py > ../bot.log 2>&1 &
sleep 5

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "Bot status:"
ps aux | grep bot.py | grep -v grep || echo "Bot not running"
echo ""
echo "Bot log (last 10 lines):"
tail -10 ~/se-toolkit-lab-7/bot.log
echo ""
echo "Services:"
docker compose --env-file ~/se-toolkit-lab-7/.env.docker.secret ps
echo ""
echo "Qwen API status:"
docker compose -f ~/qwen-code-oai-proxy/docker-compose.yml ps
