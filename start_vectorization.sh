#!/bin/bash
# Simple launcher for ultrathink vectorization
# Works with screen or nohup

cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data
mkdir -p logs

echo "=========================================="
echo "🚀 ULTRATHINK Vectorization Launcher"
echo "=========================================="
echo ""

# Check if screen is available
if command -v screen &> /dev/null; then
    echo "Using: screen"
    echo "Session: ultrathink_vec"
    echo ""

    # Check if session exists
    if screen -list | grep -q "ultrathink_vec"; then
        echo "⚠️  Session already running!"
        echo "   Reattach: screen -r ultrathink_vec"
        exit 1
    fi

    # Launch in screen
    screen -dmS ultrathink_vec bash -c "
        source ~/miniconda3/etc/profile.d/conda.sh
        conda activate ultrathink
        cd /home/ib3/Documents/test_bp/knowledge_graph_vector_GC_Data
        python vectorize_and_store.py 2>&1 | tee logs/vec_\$(date +%Y%m%d_%H%M%S).log
        echo ''
        echo 'Vectorization complete or stopped.'
        echo 'Press Enter to close...'
        read
    "

    echo "✅ Started in screen!"
    echo ""
    echo "Commands:"
    echo "  Reattach: screen -r ultrathink_vec"
    echo "  Monitor: tail -f logs/vec_*.log"
    echo "  Detach: Ctrl+A then D"

else
    echo "Using: nohup (screen not available)"
    echo ""

    # Activate conda
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate ultrathink

    # Run with nohup
    nohup python vectorize_and_store.py > logs/vec_$(date +%Y%m%d_%H%M%S).log 2>&1 &

    echo $! > logs/vectorization.pid
    echo "✅ Started in background!"
    echo ""
    echo "Commands:"
    echo "  Monitor: tail -f logs/vec_*.log"
    echo "  Check: ps -p \$(cat logs/vectorization.pid)"
    echo "  Stop: kill \$(cat logs/vectorization.pid)"
fi

echo "=========================================="
