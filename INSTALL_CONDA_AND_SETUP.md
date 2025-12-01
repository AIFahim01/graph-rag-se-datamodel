# 🐍 Install Conda & Setup ULTRATHINK Environment

## Step 0: Install Miniconda (If Not Installed)

### Check if Conda is Already Installed
```bash
conda --version
```

If you see a version number, **skip to Step 1** below.

### Install Miniconda

```bash
# Download Miniconda installer
cd ~
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Make it executable
chmod +x Miniconda3-latest-Linux-x86_64.sh

# Run installer
./Miniconda3-latest-Linux-x86_64.sh

# Follow prompts:
# - Press ENTER to review license
# - Type 'yes' to accept
# - Press ENTER for default location (/home/ib3/miniconda3)
# - Type 'yes' to initialize conda

# Clean up installer
rm Miniconda3-latest-Linux-x86_64.sh
```

### Initialize Conda (After Installation)
```bash
# Close and reopen your terminal, OR:
source ~/.bashrc

# Verify installation
conda --version
# Should show: conda 24.x.x or similar
```

---

## Step 1: Run ULTRATHINK Setup Script

```bash
cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data

# Run the setup script (takes ~5-10 minutes)
./setup_ultrathink_conda.sh
```

**What it does:**
- Creates conda environment named `ultrathink`
- Installs Python 3.10
- Installs PyTorch (CPU version)
- Installs sentence-transformers (BGE model)
- Installs Neo4j driver
- Installs FastAPI and all dependencies

**Expected Output:**
```
✅ ULTRATHINK Environment Setup Complete!
```

---

## Step 2: Activate Environment

```bash
conda activate ultrathink
```

Your prompt should change to:
```
(ultrathink) ib3@hostname:~$
```

---

## Step 3: Verify Installation

```bash
# Check Python version
python --version
# Should show: Python 3.10.x

# Check installed packages
pip list | grep -E "(torch|sentence-transformers|neo4j|fastapi)"

# Should show:
# torch                    2.x.x
# sentence-transformers    2.x.x
# neo4j                    5.x.x
# fastapi                  0.1xx.x
```

---

## Step 4: Run Test Vectorization

```bash
# Make sure you're in the ultrathink environment
conda activate ultrathink

cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data

# Run test
python build_vectordb_test_small.py
```

---

## 🐛 Troubleshooting

### Conda command not found after installation
```bash
# Try:
source ~/miniconda3/bin/activate
# Then:
conda init bash
# Close and reopen terminal
```

### Environment activation doesn't work
```bash
# Initialize conda
conda init bash
# Restart terminal
conda activate ultrathink
```

### PyTorch installation fails
```bash
# Install CPU version manually:
conda activate ultrathink
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### Neo4j connection errors
```bash
# Check if Neo4j is running
systemctl status neo4j
# OR
sudo service neo4j status

# Start if not running
sudo service neo4j start
```

---

## 📋 Quick Reference

### Activate environment
```bash
conda activate ultrathink
```

### Deactivate environment
```bash
conda deactivate
```

### List all environments
```bash
conda env list
```

### Remove environment (if needed)
```bash
conda env remove -n ultrathink
```

### Reinstall from scratch
```bash
conda env remove -n ultrathink -y
./setup_ultrathink_conda.sh
```

---

## ✅ After Setup Complete

See `QUICK_START.md` for running the test system:
1. ✅ Conda environment created
2. ✅ All packages installed
3. 🚀 Ready to run vectorization test
4. 🚀 Ready to start backend
5. 🚀 Ready to test frontend

---

## 💡 Alternative: Use Existing Conda Environment

If you already have a conda environment with Python 3.10+:

```bash
# Activate your existing environment
conda activate your_env_name

# Install requirements manually
pip install -r graph-rag-se-datamodel/requirements.txt
```
