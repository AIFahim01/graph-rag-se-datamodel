# Ngrok Tunneling Setup

## Quick Setup

### 1. Install ngrok
```bash
# Download and install
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Or download directly
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/
```

### 2. Configure ngrok (one-time)
```bash
ngrok config add-authtoken YOUR_AUTHTOKEN
# Get your auth token from: https://dashboard.ngrok.com/get-started/your-authtoken
```

### 3. Tunnel Backend API
```bash
# In new terminal
ngrok http 8000

# Output will show:
# Forwarding: https://xyz123.ngrok.io -> http://localhost:8000
```

### 4. Update Frontend to Use Ngrok URL

Create `.env.local` in frontend folder:
```bash
cd frontend_viewer/frontend
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=https://YOUR_NGROK_URL.ngrok.io
EOF
```

Example: `NEXT_PUBLIC_API_URL=https://abc123.ngrok-free.app`

### 5. Restart Frontend
```bash
# Frontend will now connect to ngrok tunnel
npm run dev
```

---

## 🚀 Complete Startup with Ngrok

### Terminal 1: Neo4j
```bash
docker start neo4j-vector-test
```

### Terminal 2: Backend API
```bash
conda activate hdvc_syncon_vectordb
python frontend_viewer/backend/api_server.py
# Runs on: http://localhost:8000
```

### Terminal 3: Ngrok Tunnel
```bash
ngrok http 8000
# Note the https URL: https://abc123.ngrok-free.app
```

### Terminal 4: Frontend
```bash
# Update .env.local with ngrok URL first!
echo "NEXT_PUBLIC_API_URL=https://YOUR_NGROK_URL" > frontend_viewer/frontend/.env.local

cd frontend_viewer/frontend
nvm use 20
npm run dev
```

---

## 🌐 Access Points

**Local Access:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000

**Remote Access (via ngrok):**
- Backend API: https://YOUR_NGROK_URL.ngrok.io
- Frontend: Deploy to Vercel/Netlify OR tunnel frontend too

---

## Option 2: Tunnel Both Frontend and Backend

### Tunnel Frontend (port 3000)
```bash
# Terminal 5
ngrok http 3000
```

### Tunnel Backend (port 8000)
```bash
# Terminal 3
ngrok http 8000
```

Then update frontend .env.local with backend ngrok URL.

**Access from anywhere:**
- https://frontend-xyz.ngrok.io → Your UI
- https://backend-abc.ngrok.io → Your API

---

## 💡 Pro Tips

### Keep Ngrok Running
```bash
# Use screen to keep ngrok persistent
screen -S ngrok_backend
ngrok http 8000
# Detach: Ctrl+A, D
# Reattach: screen -r ngrok_backend
```

### Static Ngrok Domain (Paid)
```bash
# With ngrok paid plan, get static domain:
ngrok http 8000 --domain=your-static-domain.ngrok.io
```

### Share with Team
Send the ngrok URL to colleagues - they can access your vector DB search!

---

## 🔒 Security Note

Ngrok exposes your API publicly. Consider:
- Add API authentication
- Limit requests with rate limiting
- Use ngrok access control (paid feature)
- Monitor access logs

---

## Test Ngrok Connection

```bash
# From any computer with internet:
curl https://YOUR_NGROK_URL.ngrok.io/api/health

# Should return:
# {"status":"ok","database":"neo4j","chunks":18437,"pdfs":1082,"projects":61}
```
