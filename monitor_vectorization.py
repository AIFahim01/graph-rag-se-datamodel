#!/usr/bin/env python3
"""
Real-time Vectorization Monitor
Shows live progress, stats, and ETA
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime, timedelta

CHECKPOINT_FILE = Path(__file__).parent / "logs" / "checkpoint.json"
LOG_FILE = Path(__file__).parent / "logs" / "vectorization_full.log"
TOTAL_PAGES = 240806

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def format_time(seconds):
    """Format seconds to human readable time"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds/60)}m {int(seconds%60)}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"

def get_latest_log_lines(n=10):
    """Get last N lines from log file"""
    if not LOG_FILE.exists():
        return []

    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()
        return lines[-n:] if len(lines) >= n else lines

def main():
    print("Starting monitor... (Ctrl+C to exit)")
    time.sleep(1)

    try:
        while True:
            clear_screen()

            # Read checkpoint
            if CHECKPOINT_FILE.exists():
                with open(CHECKPOINT_FILE, 'r') as f:
                    checkpoint = json.load(f)

                pages_done = checkpoint.get('pages_processed', 0)
                errors = checkpoint.get('errors', 0)
                timestamp = checkpoint.get('timestamp', '')
                last_batch = checkpoint.get('last_batch', 0)

                # Calculate progress
                progress_pct = (pages_done / TOTAL_PAGES * 100) if TOTAL_PAGES > 0 else 0

                # Parse timestamp
                if timestamp:
                    try:
                        start_dt = datetime.fromisoformat(checkpoint.get('start_time', timestamp))
                        current_dt = datetime.now()
                        elapsed = (current_dt - start_dt).total_seconds()
                        speed = pages_done / elapsed if elapsed > 0 else 0
                        remaining_pages = TOTAL_PAGES - pages_done
                        eta_seconds = remaining_pages / speed if speed > 0 else 0
                    except:
                        elapsed = 0
                        speed = 0
                        eta_seconds = 0
                else:
                    elapsed = 0
                    speed = 0
                    eta_seconds = 0

                print("╔" + "═" * 68 + "╗")
                print("║" + " ULTRATHINK VECTORIZATION MONITOR".center(68) + "║")
                print("╠" + "═" * 68 + "╣")
                print(f"║ Status: {'🟢 RUNNING'.ljust(66)} ║")
                print(f"║ Progress: {pages_done:,}/{TOTAL_PAGES:,} pages ({progress_pct:.1f}%)".ljust(69) + "║")
                print(f"║ Batch: {last_batch}/241".ljust(69) + "║")
                print(f"║ Speed: {speed:.2f} pages/sec".ljust(69) + "║")
                print(f"║ Elapsed: {format_time(elapsed)}".ljust(69) + "║")
                print(f"║ ETA: {format_time(eta_seconds)} remaining".ljust(69) + "║")
                print(f"║ Errors: {errors} ({errors/pages_done*100:.2f}% if pages_done > 0 else 0)".ljust(69) + "║")
                print("╠" + "═" * 68 + "╣")

                # Progress bar
                bar_width = 60
                filled = int(bar_width * progress_pct / 100)
                bar = "█" * filled + "░" * (bar_width - filled)
                print(f"║ {bar} ║")

                print("╠" + "═" * 68 + "╣")
                print("║ Recent Activity:".ljust(69) + "║")
                print("╠" + "═" * 68 + "╣")

                # Show recent log lines
                recent_logs = get_latest_log_lines(5)
                for line in recent_logs:
                    line = line.strip()
                    if len(line) > 66:
                        line = line[:63] + "..."
                    print(f"║ {line.ljust(66)} ║")

                print("╚" + "═" * 68 + "╝")

            else:
                print("╔" + "═" * 68 + "╗")
                print("║" + " ULTRATHINK VECTORIZATION MONITOR".center(68) + "║")
                print("╠" + "═" * 68 + "╣")
                print("║ Status: ⚪ NOT RUNNING".ljust(69) + "║")
                print("║".ljust(69) + "║")
                print("║ No checkpoint file found.".ljust(69) + "║")
                print("║ Start vectorization with:".ljust(69) + "║")
                print("║   ./start_full_vectorization.sh".ljust(69) + "║")
                print("╚" + "═" * 68 + "╝")

            print("")
            print("Refreshing in 5 seconds... (Ctrl+C to exit)")

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n\n✅ Monitor stopped.")

if __name__ == "__main__":
    main()
