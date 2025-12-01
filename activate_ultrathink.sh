#!/bin/bash
# Quick activation script for ultrathink environment
# Use: source activate_ultrathink.sh

# Initialize conda
source /home/ib3/miniconda3/etc/profile.d/conda.sh

# Activate ultrathink environment
conda activate ultrathink

echo "✅ Ultrathink environment activated!"
echo ""
echo "Python: $(python --version)"
echo "Conda env: $CONDA_DEFAULT_ENV"
echo ""
echo "🚀 Ready to run:"
echo "   python build_vectordb_test_small.py"
