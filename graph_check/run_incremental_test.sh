#!/bin/bash
# Incremental Testing Script - Test with increasing dataset sizes

echo "=================================================="
echo "INCREMENTAL DATASET TESTING"
echo "=================================================="
echo ""

# Activate environment
source ../activate_ultrathink.sh

# Test 1: Small (10 files)
echo "🧪 TEST 1: Small Dataset (10 files)"
echo "--------------------------------------------------"
python3 main.py --mode full --sample
if [ $? -eq 0 ]; then
    echo "✅ Small dataset test PASSED"
else
    echo "❌ Small dataset test FAILED"
    exit 1
fi
echo ""

# Ask user if they want to continue
read -p "Continue to medium dataset (100 files)? [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Stopped at user request"
    exit 0
fi

# Test 2: Medium (need to modify config)
echo "🧪 TEST 2: Medium Dataset (100 files)"
echo "--------------------------------------------------"
echo "Note: You would need to modify config.py SAMPLE_MODE to process 100 files"
echo "Skipping for now..."
echo ""

# Ask user if they want to run FULL
read -p "Run FULL dataset (~25,000 files)? This may take 1-3 hours! [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Full dataset test skipped"
    exit 0
fi

# Test 3: Full
echo "🧪 TEST 3: Full Dataset (~25,000 files)"
echo "--------------------------------------------------"
echo "⚠️  This will take 1-3 hours!"
python3 main.py --mode full
if [ $? -eq 0 ]; then
    echo "✅ Full dataset test PASSED"
else
    echo "❌ Full dataset test FAILED"
    exit 1
fi

echo ""
echo "✨ All tests complete!"
