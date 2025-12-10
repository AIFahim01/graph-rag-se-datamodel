# Ollama Setup Guide for Advanced Multi-Agent System

## What is Ollama?

Ollama is a local LLM server that runs AI models on your machine without needing API keys or internet connection.

### Advantages
✅ No API keys required
✅ Free to use
✅ Fast local execution
✅ Privacy (data stays on your machine)
✅ Works offline

### Models Available

| Model | Size | Speed | Quality | RAM Required |
|-------|------|-------|---------|--------------|
| **mistral** | 4.1GB | Fast ⚡ | Good 👍 | 8GB (recommended) |
| orca-mini | 1.3GB | Very Fast ⚡⚡ | Fair | 4GB |
| phi | 2.7GB | Very Fast ⚡⚡ | Fair | 4GB |
| neural-chat | 4.1GB | Fast ⚡ | Good 👍 | 8GB |
| llama2 | 3.8GB | Medium ⚡ | Good 👍 | 8GB |
| dolphin-mixtral | 26GB | Medium ⚡ | Excellent 🌟 | 16GB+ |

## Installation

### Step 1: Install Ollama

**macOS/Linux:**
```bash
# Download from https://ollama.ai/download
# Or use homebrew
brew install ollama
```

**Windows:**
- Download from https://ollama.ai/download
- Run the installer

**Docker:**
```bash
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

### Step 2: Verify Installation
```bash
ollama --version
```

## Quick Start

### Terminal 1: Start Ollama Server
```bash
ollama serve
```

You should see:
```
Listening on 127.0.0.1:11434
```

### Terminal 2: Download a Model

**Option A: Fast Model (Recommended for first time)**
```bash
ollama pull mistral
```
Downloads: 4.1GB, ~2-5 minutes depending on internet

**Option B: Super Fast (If low on space)**
```bash
ollama pull orca-mini
```
Downloads: 1.3GB

**Option C: High Quality (If you have 16GB+ RAM)**
```bash
ollama pull dolphin-mixtral
```
Downloads: 26GB

### Terminal 2: Run Advanced System
```bash
cd /mnt/c/Users/User/PycharmProjects/graph-rag-se-datamodel
python3 run_advanced_system_ollama.py
```

## Usage with Advanced System

### Run with Default Model (mistral)
```bash
python3 run_advanced_system_ollama.py
```

### Run with Custom Model
```bash
export OLLAMA_MODEL=phi
python3 run_advanced_system_ollama.py
```

### Run with Custom Ollama URL
```bash
export OLLAMA_URL=http://192.168.1.100:11434
python3 run_advanced_system_ollama.py
```

### Run with Both Custom
```bash
export OLLAMA_URL=http://localhost:11434
export OLLAMA_MODEL=neural-chat
python3 run_advanced_system_ollama.py
```

## Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_URL` | http://localhost:11434 | Ollama server address |
| `OLLAMA_MODEL` | mistral | Model to use |

### Configuration File (optional)
Create `.env` file:
```bash
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=mistral
```

## System Architecture with Ollama

```
Your Machine
├── Ollama Server (Terminal 1)
│   ├── Running at http://localhost:11434
│   └── Model: mistral (4.1GB)
│
└── Advanced Multi-Agent System (Terminal 2)
    ├── CrewAI Framework
    ├── 4 Agents
    │   ├── Planner
    │   ├── Requirements Engineer
    │   ├── Coder
    │   └── Validator
    └── LLM: Ollama (local, no API key needed)
```

## Troubleshooting

### Error: "Cannot connect to Ollama"
**Solution 1:** Ensure Ollama server is running
```bash
# Terminal 1
ollama serve
```

**Solution 2:** Check URL is correct
```bash
# Test connection
curl http://localhost:11434
```

**Solution 3:** Use correct IP for remote
```bash
export OLLAMA_URL=http://192.168.1.100:11434
python3 run_advanced_system_ollama.py
```

### Error: "Model not found"
**Solution:** Pull the model first
```bash
ollama pull mistral
```

### Slow Response
**Solution 1:** Use faster model
```bash
export OLLAMA_MODEL=orca-mini
python3 run_advanced_system_ollama.py
```

**Solution 2:** Check system resources
```bash
free -h  # Check available RAM
```

### Out of Memory
**Solution 1:** Use smaller model
```bash
ollama pull orca-mini
export OLLAMA_MODEL=orca-mini
python3 run_advanced_system_ollama.py
```

**Solution 2:** Increase swap
```bash
# Linux
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Model Recommendations

### For Learning (First Time)
```bash
ollama pull mistral
```
- Good balance of speed and quality
- Fast responses
- Works on 8GB RAM

### For Maximum Speed
```bash
ollama pull orca-mini
```
- Very fast (1-2 seconds per response)
- Works on 4GB RAM
- Slightly lower quality

### For Best Quality
```bash
ollama pull dolphin-mixtral
```
- Excellent responses
- Requires 16GB+ RAM
- Slower (30-60 seconds per response)

## Running Both Systems

### Simple System (No Ollama needed)
```bash
python3 crewai_official_final.py
```
✅ Fastest
✅ No setup
❌ Needs API key

### Advanced System with Ollama
```bash
ollama serve  # Terminal 1
python3 run_advanced_system_ollama.py  # Terminal 2
```
✅ No API key
✅ Dynamic tool creation
✅ 4 specialized agents
⚠️ Slower responses

## Advanced Configuration

### Using GPU Acceleration

**NVIDIA GPU:**
```bash
# Install CUDA
# Then run Ollama - it auto-detects GPU
ollama serve
```

**AMD GPU:**
```bash
# Install ROCm
export HSA_OVERRIDE_GFX_VERSION=gfx90c
ollama serve
```

### Docker Deployment
```bash
docker run -d \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama

# In another terminal
docker exec ollama ollama pull mistral
```

### Production Setup
```bash
# Use systemd service
sudo systemctl enable ollama
sudo systemctl start ollama

# Then
python3 run_advanced_system_ollama.py
```

## Performance Tips

1. **First Run Slow:** Model is being loaded into memory (happens once)
2. **Use GPU:** Much faster if available
3. **Smaller Model:** Faster responses, less memory
4. **Warm Up:** Models are faster after first few calls
5. **Close Other Apps:** Free up RAM for better performance

## API Details

### Ollama HTTP API
```bash
# Test connection
curl http://localhost:11434

# List models
curl http://localhost:11434/api/tags

# Generate response
curl http://localhost:11434/api/generate -d '{
  "model": "mistral",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

### CrewAI Configuration
```python
from crewai import LLM

ollama_llm = LLM(
    model="ollama/mistral",
    base_url="http://localhost:11434",
)

agent = Agent(
    role="...",
    goal="...",
    llm=ollama_llm,
)
```

## Summary

**Quick Start:**
```bash
# Terminal 1
ollama serve

# Terminal 2
ollama pull mistral

# Terminal 3
python3 run_advanced_system_ollama.py
```

**Status:**
✅ Ollama configuration ready
✅ CrewAI integration complete
✅ 4 agents with Ollama LLM
✅ No API keys needed
✅ All features working

---

For more details visit: https://ollama.ai
