#!/usr/bin/env python3
"""
Test the preprocessing pipeline on our HDVC/SYNCON subset
"""

import sys
from pathlib import Path

# Add the data/preprocess directory to path
preprocess_dir = Path(__file__).parent / "data" / "preprocess"
sys.path.insert(0, str(preprocess_dir))

try:
    from processors import FileFilter, DocumentProcessor, OutputManager

    def test_preprocessing():
        # Configure paths for our subset
        input_base = Path(__file__).parent / "data" / "pdfs"
        output_base = Path(__file__).parent / "data" / "processed_subset"
        output_base.mkdir(parents=True, exist_ok=True)

        # Test on a small sample: one HVDC folder and one SYNCON folder
        test_folders = [
            input_base / "hdvc" / "GC25_002_HVDC_SE_RnD_POD",
            input_base / "syncon" / "GC25_016_SynCon_SEC_Group_1"
        ]

        # Initialize components
        file_filter = FileFilter()
        document_processor = DocumentProcessor()
        output_manager = OutputManager(output_base)

        print("=" * 60)
        print("TESTING PREPROCESSING PIPELINE ON SUBSET")
        print("=" * 60)

        results = []

        for test_folder in test_folders:
            if not test_folder.exists():
                print(f"Skipping non-existent folder: {test_folder}")
                continue

            print(f"\nTesting folder: {test_folder.name}")

            # Scan for supported files
            supported_files = file_filter.scan_folder(test_folder)
            print(f"Found {len(supported_files)} supported files")

            if supported_files:
                # Process first few files as a test
                test_files = supported_files[:3]  # Test first 3 files

                files_content = []
                for file_path in test_files:
                    print(f"  Processing: {file_path.name}")
                    content, success = document_processor.process_file(file_path)
                    files_content.append((file_path, content, success))
                    print(f"    Success: {success}")
                    if success:
                        print(f"    Content length: {len(content)} chars")

                # Save processed content
                folder_name = test_folder.name + "_test"
                success = output_manager.save_offer_documents(folder_name, 0, files_content)

                results.append({
                    'folder': test_folder.name,
                    'files_found': len(supported_files),
                    'files_processed': len(test_files),
                    'processing_success': success
                })

        # Print summary
        print("\n" + "=" * 60)
        print("PREPROCESSING TEST SUMMARY:")
        for result in results:
            print(f"Folder: {result['folder']}")
            print(f"  Files found: {result['files_found']}")
            print(f"  Files tested: {result['files_processed']}")
            print(f"  Processing success: {result['processing_success']}")
        print("=" * 60)

        return len(results) > 0

except ImportError as e:
    print(f"Error importing preprocessing modules: {e}")
    print("Make sure the preprocessing pipeline is set up correctly")

if __name__ == "__main__":
    try:
        success = test_preprocessing()
        exit(0 if success else 1)
    except Exception as e:
        print(f"Error running test: {e}")
        exit(1)