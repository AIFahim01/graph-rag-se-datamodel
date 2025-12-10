# HuggingFace Models with CrewAI - Complete Setup Guide

## What is HuggingFace Inference API?

HuggingFace provides **free hosted LLM inference** for thousands of open-source models:
- ✅ No setup required
- ✅ Access via API
- ✅ Free tier available
- ✅ Qwen3, Llama, Mistral, and more
- ✅ Works anywhere (cloud, local, etc.)

---

## Step 1: Get HuggingFace Token

### 1.1 Create HuggingFace Account
1. Go to https://huggingface.co
2. Click "Sign Up"
3. Create account with email

### 1.2 Create Access Token
1. Go to https://huggingface.co/settings/tokens
2. Click "New token"
3. Set name: `crewai-token`
4. Select type: **Read** (minimum permission)
5. Click "Create token"
6. Copy the token (starts with `hf_`)

### 1.3 Accept Model Licenses
Some models require license acceptance:
1. Go to model page (e.g., https://huggingface.co/meta-llama/Llama-2-7b-chat-hf)
2. Click "Access repository"
3. Accept terms

---

## Step 2: Set Environment Variable

### Terminal:
```bash
export HF_TOKEN='hf_your_token_here'
```

### Persistent (.bashrc or .zshrc):
```bash
echo "export HF_TOKEN='hf_your_token_here'" >> ~/.bashrc
source ~/.bashrc
```

### Windows (PowerShell):
```powershell
[Environment]::SetEnvironmentVariable("HF_TOKEN", "hf_your_token_here", "User")
```

---

## Step 3: Choose Your Model

### Available Models on HuggingFace

| Model | Size | Speed | Quality | Cost | Best For |
|-------|------|-------|---------|------|----------|
| **Qwen3 8B** (RECOMMENDED) | 8B | ⚡ Fast | 👍 Good | FREE | Balanced |
| Qwen3 32B | 32B | Medium | 🌟 Excellent | FREE | High Quality |
| Mistral 7B | 7B | ⚡ Very Fast | 👍 Good | FREE | Speed |
| Llama 2 70B | 70B | Medium | 🌟 Excellent | FREE | Best Quality |
| Zephyr 7B | 7B | ⚡ Fast | 👍 Good | FREE | Conversation |

### With Your HuggingFace Token:
- ✅ Can use **Qwen3** models
- ✅ Can use **Llama2** (need to accept license)
- ✅ Can use **Mistral** (free access)
- ✅ Can use **Zephyr** (free access)

---

## Step 4: Run the System

### Simple (Default: Qwen3 8B)
```bash
export HF_TOKEN='your_huggingface_token_here'
python3 run_advanced_system_huggingface.py
```

**Note:** The system automatically uses the new HuggingFace router endpoint (`https://router.huggingface.co/v1`). If you need a custom endpoint, use:
```bash
export HF_API_ENDPOINT='https://your-custom-endpoint/v1'
```

### With Custom Model
```bash
export HF_TOKEN='your_huggingface_token_here'
export HF_MODEL='qwen3-32b'  # For better quality
python3 run_advanced_system_huggingface.py
```

### With Custom Endpoint
```bash
export HF_TOKEN='your_huggingface_token_here'
export HF_API_ENDPOINT='https://api-inference.huggingface.co/v1'
python3 run_advanced_system_huggingface.py
```

---

## System Architecture

```
HuggingFace Cloud
│
├── Qwen3 8B Model (Free)
├── Qwen3 32B Model (Free)
├── Mistral 7B (Free)
├── Llama 2 70B (Free)
└── Many more...
    │
    └── API Endpoint: https://api-inference.huggingface.co/v1
        │
        └── Your HF Token: YOUR_HF_TOKEN_HERE
            │
            └── LiteLLM (Local)
                │
                └── CrewAI (Local)
                    │
                    ├── Planner Agent
                    ├── Requirements Engineer
                    ├── Coder Agent
                    └── Validator Agent
```

---

## Model Selection Guide

### For Beginners (Start Here)
```bash
export HF_MODEL='qwen3-8b'
```
- Good balance
- Fast enough
- Good quality
- Works on most machines

### For Speed (Fastest)
```bash
export HF_MODEL='mistral-7b'
```
- Extremely fast (5-10 sec per response)
- Good quality
- Lightweight

### For Quality (Best Results)
```bash
export HF_MODEL='qwen3-32b'
# or
export HF_MODEL='llama2-70b'
```
- Excellent quality
- Slower (30-60 sec per response)
- Best for complex tasks

### For Conversation
```bash
export HF_MODEL='zephyr-7b'
```
- Great for multi-turn chat
- Fast enough
- Good quality

---

## Advanced Configuration

### HuggingFace Router Endpoint (Current Default)

The system now uses the new HuggingFace router endpoint:

```bash
export HF_API_ENDPOINT='https://router.huggingface.co/v1'
export HF_TOKEN='hf_your_token'
python3 run_advanced_system_huggingface.py
```

### Custom HuggingFace Inference Endpoint

If you deploy your own inference endpoint:

```bash
export HF_API_ENDPOINT='https://your-custom-endpoint.endpoints.huggingface.co/v1'
export HF_TOKEN='hf_your_token'
python3 run_advanced_system_huggingface.py
```

### Using with LiteLLM Directly

```python
from crewai import LLM

hf_llm = LLM(
    model="huggingface/Qwen/Qwen3-8B-Instruct",
    api_key="hf_your_token",
    base_url="https://api-inference.huggingface.co/v1",
)

agent = Agent(
    role="...",
    goal="...",
    llm=hf_llm,
)
```

---

## Troubleshooting

### Error: "Unauthorized (401)"
```
Solution: Token is incorrect or expired
1. Regenerate token at https://huggingface.co/settings/tokens
2. Set correct token:
   export HF_TOKEN='your_new_token'
```

### Error: "Model not found"
```
Solution: Model requires license acceptance
1. Go to model page on HuggingFace
2. Accept license
3. Try again
```

### Error: "Rate limited"
```
Solution: Too many requests
1. Use smaller model (faster, fewer requests)
2. Wait a few minutes
3. Or use paid HuggingFace Pro for higher limits
```

### Slow Response (30+ seconds)
```
Solution: Model is too large
1. Use smaller model:
   export HF_MODEL='mistral-7b'  # faster
2. Or use paid option for faster inference
```

### Error: "Connection timeout"
```
Solution: HuggingFace API unreachable
1. Check internet connection
2. Check if HuggingFace is up (status.huggingface.co)
3. Try with different model (might be cold-started)
```

---

## Comparison: HuggingFace vs Others

| Feature | HuggingFace | Ollama | OpenAI |
|---------|-----------|--------|--------|
| **Cost** | FREE ✅ | FREE ✅ | $$$ |
| **API Key** | Required | NO | Required |
| **Setup** | 5 min | 10 min | Instant |
| **Speed** | Medium | Fast | Very Fast |
| **Quality** | Good | Medium | Excellent |
| **Models** | 100+ ✅ | 20+ | GPT models |
| **Offline** | NO | YES | NO |
| **GPU** | Yes | Yes | N/A |
| **Private** | Cloud | Local | Cloud |

---

## Performance Tips

1. **First Call Slow:** Models are cold-started (2-3 minutes first time)
2. **Subsequent Calls Faster:** Model stays warm in memory
3. **Smaller Models Faster:** Mistral 7B < Qwen3 8B < Qwen3 32B
4. **Batch Requests:** Send multiple requests together
5. **Caching:** Cache results to avoid repeated API calls

---

## Free Tier Limits

| Tier | Requests/Day | Speed | Best For |
|------|-------------|-------|----------|
| **Free** | 150-500 | Medium | Development, Testing |
| **Pro** ($9/month) | 5000+ | Fast | Production |
| **Enterprise** | Unlimited | Very Fast | Large scale |

---

## Production Deployment

### For Small Projects (Free)
```bash
export HF_MODEL='mistral-7b'  # Fastest free
export HF_TOKEN='your_token'
python3 run_advanced_system_huggingface.py
```

### For Large Projects (Paid)
```bash
# Use HuggingFace Pro ($9/month)
# Higher rate limits
# Faster inference
# Private deployments
```

### For Maximum Performance
```bash
# Deploy custom inference endpoint
# Dedicated infrastructure
# Enterprise support
# Custom models
```

---

## Code Examples

### Example 1: Basic Setup
```python
import os
os.environ['HF_TOKEN'] = 'hf_your_token'

from crewai import LLM, Agent

hf_llm = LLM(
    model="huggingface/Qwen/Qwen3-8B-Instruct",
    api_key=os.environ['HF_TOKEN'],
)

agent = Agent(
    role="Analyst",
    goal="Analyze data",
    llm=hf_llm,
)
```

### Example 2: Multiple Models
```python
from crewai import LLM

# Fast model for quick tasks
fast_llm = LLM(
    model="huggingface/mistralai/Mistral-7B-Instruct-v0.2",
    api_key="hf_token",
)

# Quality model for complex tasks
quality_llm = LLM(
    model="huggingface/meta-llama/Llama-2-70b-chat-hf",
    api_key="hf_token",
)

fast_agent = Agent(role="Fast", goal="Quick tasks", llm=fast_llm)
quality_agent = Agent(role="Quality", goal="Complex tasks", llm=quality_llm)
```

### Example 3: With Error Handling
```python
from crewai import LLM, Agent

try:
    hf_llm = LLM(
        model="huggingface/Qwen/Qwen3-8B-Instruct",
        api_key=os.environ['HF_TOKEN'],
        timeout=300,  # 5 minute timeout
    )
    agent = Agent(role="...", goal="...", llm=hf_llm)
except Exception as e:
    print(f"Error: {e}")
    # Fallback to another model
```

---

## Complete Quick Start

```bash
# 1. Set token
export HF_TOKEN='YOUR_HF_TOKEN_HERE'

# 2. Run system
python3 run_advanced_system_huggingface.py

# 3. See results
# 4-phase pipeline with HuggingFace will execute!
```

---

## Resources

- HuggingFace Home: https://huggingface.co
- API Docs: https://huggingface.co/docs/api-inference
- Token Settings: https://huggingface.co/settings/tokens
- Popular Models: https://huggingface.co/models
- LiteLLM HF Docs: https://docs.litellm.ai/docs/providers/huggingface
- CrewAI LLM Docs: https://docs.crewai.com/en/concepts/llms

---

## Summary

**✅ With HuggingFace + CrewAI:**
- Free access to state-of-the-art models
- No setup required
- Works anywhere
- Perfect for testing and production
- Your Qwen3 token ready to use
- 4-phase multi-agent pipeline

**Quick Command:**
```bash
export HF_TOKEN='YOUR_HF_TOKEN_HERE'
python3 run_advanced_system_huggingface.py
```

**Status:** ✅ Ready to Use!
