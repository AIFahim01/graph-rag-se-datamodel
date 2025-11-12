#!/usr/bin/env python3
"""
Script to copy HDVC and SYNCON files from G:\ultrathink with 1-year filter
Run this script from Windows to access G: drive properly
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime, timedelta
import re

def main():
    # Configuration
    source_dir = Path(r"G:\ultrathink")  # Source directory
    project_root = Path(__file__).parent
    dest_base = project_root / "data" / "pdfs"

    # Target directories
    hdvc_dir = dest_base / "hdvc"
    syncon_dir = dest_base / "syncon"
    mixed_dir = dest_base / "mixed"

    # Date filter (1 year back from today)
    one_year_ago = datetime.now() - timedelta(days=365)

    # File extensions to copy
    supported_extensions = {'.pdf', '.docx', '.png', '.jpg', '.jpeg'}

    # Results tracking
    results = {
        'hdvc_files': [],
        'syncon_files': [],
        'mixed_files': [],
        'total_copied': 0,
        'total_skipped': 0,
        'errors': []
    }

    print(f"Copying files from: {source_dir}")
    print(f"Target directories: {dest_base}")
    print(f"Date filter: Files modified after {one_year_ago.strftime('%Y-%m-%d')}")
    print("=" * 60)

    if not source_dir.exists():
        print(f"ERROR: Source directory not found: {source_dir}")
        return False

    # Create destination directories
    for dir_path in [hdvc_dir, syncon_dir, mixed_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Walk through source directory
    for root, dirs, files in os.walk(source_dir):
        root_path = Path(root)
        relative_path = root_path.relative_to(source_dir)

        print(f"Scanning: {relative_path}")

        for filename in files:
            file_path = root_path / filename

            # Check file extension
            if file_path.suffix.lower() not in supported_extensions:
                continue

            try:
                # Check file modification date
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime < one_year_ago:
                    results['total_skipped'] += 1
                    continue

                # Check file content for keywords
                filename_lower = filename.lower()
                path_lower = str(relative_path).lower()

                has_hdvc = 'hdvc' in filename_lower or 'hdvc' in path_lower
                has_syncon = 'syncon' in filename_lower or 'syncon' in path_lower

                # Determine destination
                if has_hdvc and has_syncon:
                    dest_dir = mixed_dir
                    category = 'mixed'
                elif has_hdvc:
                    dest_dir = hdvc_dir
                    category = 'hdvc'
                elif has_syncon:
                    dest_dir = syncon_dir
                    category = 'syncon'
                else:
                    # Skip files that don't contain keywords
                    continue

                # Create subdirectory structure in destination
                dest_subdir = dest_dir / relative_path
                dest_subdir.mkdir(parents=True, exist_ok=True)

                # Copy file
                dest_file = dest_subdir / filename
                shutil.copy2(file_path, dest_file)

                # Record result
                file_info = {
                    'original_path': str(file_path),
                    'dest_path': str(dest_file),
                    'size_bytes': file_path.stat().st_size,
                    'modified_date': file_mtime.isoformat(),
                    'category': category
                }

                results[f'{category}_files'].append(file_info)
                results['total_copied'] += 1

                print(f"  → Copied ({category}): {filename}")

            except Exception as e:
                error_msg = f"Error processing {file_path}: {str(e)}"
                results['errors'].append(error_msg)
                print(f"  ERROR: {error_msg}")

    # Save results manifest
    manifest_path = dest_base / "copy_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("=" * 60)
    print("COPY SUMMARY:")
    print(f"HDVC files copied: {len(results['hdvc_files'])}")
    print(f"SYNCON files copied: {len(results['syncon_files'])}")
    print(f"Mixed files copied: {len(results['mixed_files'])}")
    print(f"Total files copied: {results['total_copied']}")
    print(f"Files skipped (old): {results['total_skipped']}")
    print(f"Errors encountered: {len(results['errors'])}")
    print(f"Manifest saved to: {manifest_path}")

    return True

if __name__ == "__main__":
    success = main()
    input("\nPress Enter to exit...")
    exit(0 if success else 1)