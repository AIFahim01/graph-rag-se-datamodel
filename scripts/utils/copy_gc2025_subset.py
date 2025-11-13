#!/usr/bin/env python3
"""
Copy HDVC and SYNCON directories from GC_2025 to subset folders
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

def main():
    # Configuration
    gc2025_dir = Path("/mnt/c/Users/z0051yym/Desktop/test_bp_code/knowledge_graph_vector_GC_Data/graph-rag-se-datamodel/GC_2025")
    project_root = Path("/mnt/c/Users/z0051yym/Desktop/test_bp_code/knowledge_graph_vector_GC_Data/graph-rag-se-datamodel")
    dest_base = project_root / "data" / "pdfs"

    hdvc_dir = dest_base / "hdvc"
    syncon_dir = dest_base / "syncon"
    mixed_dir = dest_base / "mixed"

    # Results tracking
    results = {
        'hvdc_folders': [],
        'syncon_folders': [],
        'mixed_folders': [],
        'total_copied': 0,
        'errors': [],
        'start_time': datetime.now().isoformat()
    }

    print("=" * 60)
    print("COPYING GC_2025 HDVC AND SYNCON SUBSET")
    print("=" * 60)

    if not gc2025_dir.exists():
        print(f"ERROR: GC_2025 directory not found: {gc2025_dir}")
        return False

    # Create destination directories
    for dir_path in [hdvc_dir, syncon_dir, mixed_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Find all subdirectories in GC_2025
    for item in gc2025_dir.iterdir():
        if not item.is_dir():
            continue

        folder_name = item.name.lower()
        has_hvdc = 'hvdc' in folder_name
        has_syncon = 'syncon' in folder_name

        if not (has_hvdc or has_syncon):
            continue

        print(f"Processing: {item.name}")

        try:
            # Determine destination
            if has_hvdc and has_syncon:
                dest_dir = mixed_dir
                category = 'mixed'
            elif has_hvdc:
                dest_dir = hdvc_dir
                category = 'hvdc'
            elif has_syncon:
                dest_dir = syncon_dir
                category = 'syncon'

            # Copy directory
            dest_path = dest_dir / item.name
            if dest_path.exists():
                print(f"  → Skipping (already exists): {item.name}")
                continue

            shutil.copytree(item, dest_path)

            # Record result
            folder_info = {
                'name': item.name,
                'original_path': str(item),
                'dest_path': str(dest_path),
                'size_bytes': sum(f.stat().st_size for f in item.rglob('*') if f.is_file()),
                'category': category
            }

            results[f'{category}_folders'].append(folder_info)
            results['total_copied'] += 1

            print(f"  → Copied ({category}): {item.name}")

        except Exception as e:
            error_msg = f"Error copying {item.name}: {str(e)}"
            results['errors'].append(error_msg)
            print(f"  ERROR: {error_msg}")

    # Save results manifest
    manifest_path = dest_base / "gc2025_subset_manifest.json"
    results['end_time'] = datetime.now().isoformat()

    with open(manifest_path, 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    print("=" * 60)
    print("COPY SUMMARY:")
    print(f"HVDC folders copied: {len(results['hvdc_folders'])}")
    print(f"SYNCON folders copied: {len(results['syncon_folders'])}")
    print(f"Mixed folders copied: {len(results['mixed_folders'])}")
    print(f"Total folders copied: {results['total_copied']}")
    print(f"Errors encountered: {len(results['errors'])}")
    if results['errors']:
        for error in results['errors']:
            print(f"  - {error}")
    print(f"Manifest saved to: {manifest_path}")
    print("=" * 60)

    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)