# 🦙 Using Local Ollama with GraphRAG

## Why Use Ollama?
- ✅ **100% Local & Private** - No data sent to cloud
- ✅ **No API Costs** - Free to use
- ✅ **Fast** - Runs on your GPU
- ✅ **Multiple Models** - Llama 3, Mistral, Phi-3, etc.

---

## Step 1: Install Ollama

### Windows:
Download and install from: https://ollama.com/download/windows

### Linux/WSL:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

---

## Step 2: Start Ollama Server

```bash
ollama serve
```

(Keep this running in the background)

---

## Step 3: Pull a Model

Choose one model:

```bash
# Llama 3 (8B - recommended, good balance)
ollama pull llama3

# Mistral (7B - faster, good for technical content)
ollama pull mistral

# Phi-3 (3.8B - very fast, smaller)
ollama pull phi3

# Llama 3.1 (8B - latest version)
ollama pull llama3.1

# Qwen 2.5 (7B - excellent for technical docs)
ollama pull qwen2.5:7b
```

---

## Step 4: Run GraphRAG with Ollama

### Interactive Mode:
```bash
# With Llama 3
python ollama_graphrag_chat.py --interactive --model llama3

# With Mistral
python ollama_graphrag_chat.py --interactive --model mistral
```

### Single Query:
```bash
python ollama_graphrag_chat.py \
  --query "What protection systems are used in HVDC converters?" \
  --model llama3
```

---

## Comparison: Azure vs Ollama

| Feature | Azure OpenAI (GPT-4) | Local Ollama (Llama 3) |
|---------|---------------------|------------------------|
| **Cost** | ~$0.03 per query | Free |
| **Privacy** | Data sent to cloud | 100% local |
| **Speed** | 2-5 seconds | 5-15 seconds (GPU) |
| **Quality** | Excellent | Very Good |
| **Setup** | Need API key | Install Ollama |
| **Internet** | Required | Not required |

---

## Recommended Models for HVDC/SYNCON

1. **Llama 3** (8B) - Best all-around, great for technical Q&A
2. **Qwen 2.5** (7B) - Excellent with technical documents
3. **Mistral** (7B) - Fast and accurate
4. **Phi-3** (3.8B) - Fastest, good for simple queries

---

## GPU Requirements

- **NVIDIA GPU**: Recommended (RTX 3060+ or better)
- **Apple M1/M2**: Works great
- **CPU Only**: Works but slower (1-2 minutes per query)

---

## Usage Examples

```bash
# Ask about HVDC protection
python ollama_graphrag_chat.py \
  --query "What protection systems connect to HVDC converters?" \
  --model llama3

# Ask about VSC technology
python ollama_graphrag_chat.py \
  --query "What is the role of VSC in HVDC systems?" \
  --model mistral

# Interactive chat session
python ollama_graphrag_chat.py --interactive --model qwen2.5:7b
```

---

## Troubleshooting

**Error: "Cannot connect to Ollama"**
- Make sure `ollama serve` is running
- Check: http://localhost:11434 should show "Ollama is running"

**Error: "Model not found"**
- Run: `ollama pull llama3` first
- List available models: `ollama list`

**Slow responses?**
- Use smaller model: `--model phi3`
- Check GPU is being used: `nvidia-smi` (NVIDIA) or `ollama ps`

---

## Both Options Available!

You can use **BOTH** Azure and Ollama:

- **Azure OpenAI**: `python true_graphrag_chat.py --interactive`
- **Local Ollama**: `python ollama_graphrag_chat.py --interactive --model llama3`

Try both and see which you prefer!
