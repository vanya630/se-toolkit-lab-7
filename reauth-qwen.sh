# Re-authenticate Qwen Code on VM
# Run these commands on your VM (ssh ivangrishaev@10.93.26.121)

# Option 1: Using npm directly on VM (if Node.js is installed)
cd ~
npm install -g @qwen-code/qwen-code
qwen auth login

# After successful login, restart the proxy:
cd ~/qwen-code-oai-proxy
docker compose up --build -d

# Wait 30 seconds, then test:
sleep 30
curl -s http://localhost:42005/v1/models -H 'Authorization: Bearer my-secret-qwen-key'

# Option 2: If npm is not available on VM, use this Docker command
# (you'll need to complete the auth flow in your browser)
cd ~/qwen-code-oai-proxy
docker compose down
docker run --rm -v ~/.qwen:/root/.qwen -it node:20-alpine sh -c 'npm install -g @qwen-code/qwen-code && qwen auth login'

# Then restart proxy:
docker compose up --build -d

# Test after 30 seconds:
sleep 30
curl -s http://localhost:42005/v1/models -H 'Authorization: Bearer my-secret-qwen-key'
