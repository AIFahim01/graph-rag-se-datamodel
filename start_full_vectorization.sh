#!/bin/bash
#
# ULTRATHINK Full Vectorization - Screen Launcher
# Runs vectorization in background with logging
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/vectorization_${TIMESTAMP}.log"
SCREEN_NAME="ultrathink_vectorize"

# Create logs directory
mkdir -p "$LOG_DIR"

echo "=============================================="
echo "🚀 ULTRATHINK Full Vectorization Launcher"
echo "=============================================="
echo ""
echo "📁 Working directory: $SCRIPT_DIR"
echo "📝 Log file: $LOG_FILE"
echo "🖥️  Screen session: $SCREEN_NAME"
echo ""

# Check if screen session already exists
if screen -list | grep -q "$SCREEN_NAME"; then
    echo "⚠️  Screen session '$SCREEN_NAME' already running!"
    echo ""
    echo "Options:"
    echo "  1. Reattach: screen -r $SCREEN_NAME"
    echo "  2. Kill it: screen -X -S $SCREEN_NAME quit"
    echo "  3. View logs: tail -f $LOG_FILE"
    exit 1
fi

# Check if conda environment exists
if ! conda env list | grep -q "ultrathink"; then
    echo "❌ Conda environment 'ultrathink' not found!"
    echo "   Run: ./setup_ultrathink_conda.sh first"
    exit 1
fi

echo "✅ Environment ready"
echo ""
echo "Starting vectorization in background..."
echo ""

# Create screen session and run vectorization
screen -dmS "$SCREEN_NAME" bash -c "
    # Initialize conda
    source ~/miniconda3/etc/profile.d/conda.sh
    conda activate ultrathink

    # Set proxy bypass
    export no_proxy='localhost,127.0.0.1,::1'
    export NO_PROXY='localhost,127.0.0.1,::1'

    # Change to script directory
    cd '$SCRIPT_DIR'

    # Run vectorization with logging
    echo '=========================================='
    echo 'ULTRATHINK Full Vectorization Started'
    echo 'Time: $(date)'
    echo 'Log: $LOG_FILE'
    echo '=========================================='
    echo ''

    python build_vectordb_full_240k_hybrid.py 2>&1 | tee '$LOG_FILE'

    echo ''
    echo '=========================================='
    echo 'Vectorization Complete or Stopped'
    echo 'Time: $(date)'
    echo '=========================================='

    # Keep screen open
    echo ''
    echo 'Press Enter to close this screen session...'
    read
"

# Wait a moment for screen to start
sleep 2

# Check if screen started successfully
if screen -list | grep -q "$SCREEN_NAME"; then
    echo "=============================================="
    echo "✅ Vectorization Started Successfully!"
    echo "=============================================="
    echo ""
    echo "📊 Monitoring Commands:"
    echo ""
    echo "  View live progress:"
    echo "    tail -f $LOG_FILE"
    echo ""
    echo "  Reattach to screen:"
    echo "    screen -r $SCREEN_NAME"
    echo ""
    echo "  Check progress:"
    echo "    grep 'PROGRESS REPORT' $LOG_FILE | tail -5"
    echo ""
    echo "  Monitor in another terminal:"
    echo "    watch -n 5 'tail -20 $LOG_FILE | grep -E \"(BATCH|PROGRESS|%)\"'"
    echo ""
    echo "  Stop vectorization:"
    echo "    screen -X -S $SCREEN_NAME quit"
    echo ""
    echo "=============================================="
    echo "💡 Tip: Detach from screen with Ctrl+A, then D"
    echo "=============================================="
else
    echo "❌ Failed to start screen session"
    exit 1
fi
