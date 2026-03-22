#!/bin/bash
# Lab 7 VM Setup Script
# Run this on your VM after SSH access is restored

set -e

echo "=== Lab 7 VM Setup ==="

# 1. Stop Lab 6 services if running
echo "[1/8] Stopping Lab 6 services..."
if [ -d ~/se-toolkit-lab-6 ]; then
    cd ~/se-toolkit-lab-6
    docker compose --env-file .env.docker.secret down 2>/dev/null || true
    cd ~
fi

# 2. Clone or update lab-7 repo
echo "[2/8] Setting up lab-7 repo..."
if [ -d ~/se-toolkit-lab-7 ]; then
    echo "Repo exists, pulling latest..."
    cd ~/se-toolkit-lab-7
    git pull origin main 2>/dev/null || true
    cd ~
else
    echo "Cloning repo..."
    # Replace YOUR_GITHUB_USERNAME with your actual username
    git clone https://github.com/vanya630/se-toolkit-lab-7 ~/se-toolkit-lab-7
fi

# 3. Create environment file
echo "[3/8] Creating .env.docker.secret..."
cd ~/se-toolkit-lab-7
if [ ! -f .env.docker.secret ]; then
    cp .env.docker.example .env.docker.secret
    
    # Edit these values manually!
    echo "WARNING: You must edit .env.docker.secret manually!"
    echo "Set: AUTOCHECKER_API_LOGIN, AUTOCHECKER_API_PASSWORD, LMS_API_KEY"
fi

# 4. Configure Docker DNS
echo "[4/8] Configuring Docker DNS..."
sudo tee /etc/docker/daemon.json <<'EOF'
{
  "dns": ["8.8.8.8", "8.8.4.4"]
}
EOF
sudo systemctl restart docker

# 5. Start services
echo "[5/8] Starting Docker services..."
docker compose --env-file .env.docker.secret down -v 2>/dev/null || true
docker compose --env-file .env.docker.secret up --build -d

# Wait for services to be ready
echo "Waiting for backend to be ready..."
sleep 10

# 6. Check service status
echo "[6/8] Checking service status..."
docker compose --env-file .env.docker.secret ps

# 7. Populate database (you need to set LMS_API_KEY first!)
echo "[7/8] Populating database..."
echo "Run this manually after setting LMS_API_KEY in .env.docker.secret:"
echo "  curl -X POST http://localhost:42002/pipeline/sync \\"
echo "    -H 'Authorization: Bearer YOUR_LMS_API_KEY' \\"
echo "    -H 'Content-Type: application/json' -d '{}'"

# 8. Set up SSH for autochecker
echo "[8/8] Setting up SSH for autochecker..."
mkdir -p ~/.ssh
echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKiL0DDQZw7L0Uf1c9cNlREY7IS6ZkIbGVWNsClqGNCZ se-toolkit-autochecker' >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit ~/se-toolkit-lab-7/.env.docker.secret with your credentials"
echo "2. Restart services: cd ~/se-toolkit-lab-7 && docker compose --env-file .env.docker.secret up --build -d"
echo "3. Sync data: curl -X POST http://localhost:42002/pipeline/sync -H 'Authorization: Bearer YOUR_LMS_API_KEY' -H 'Content-Type: application/json' -d '{}'"
echo "4. Test: curl -s http://localhost:42002/items/ -H 'Authorization: Bearer YOUR_LMS_API_KEY' | head -c 100"
