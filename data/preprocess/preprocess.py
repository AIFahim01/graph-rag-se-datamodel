#!/usr/bin/env python3

from pathlib import Path
from processors import FileFilter, DocumentProcessor, OutputManager

class DataPreprocessingOrchestrator:
    def __init__(self, input_folder: Path, output_folder: Path):
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.file_filter = FileFilter()
        self.document_processor = DocumentProcessor()
        self.output_manager = OutputManager(output_folder)
    
    def run(self) -> bool:
        """Run the preprocessing pipeline"""
        if not self.input_folder.exists():
            print(f"Input folder not found: {self.input_folder}")
            return False
        
        offer_folders = self.file_filter.get_offer_folders(self.input_folder)
        if not offer_folders:
            print("No offer folders found")
            return False
        
        processed_count = 0
        for offer_folder in offer_folders:
            print("=" * 40)
            print(f"Processing offer: {offer_folder.name}")
            if self._process_single_offer(offer_folder):
                processed_count += 1
            print("=" * 40)
        
        print(f"Processed {processed_count}/{len(offer_folders)} offers")
        return processed_count > 0
    
    def _process_single_offer(self, offer_folder: Path) -> bool:
        offer_name = offer_folder.name
        
        if self.output_manager.is_offer_processed(offer_name):
            print(f"Skipping already processed: {offer_name}")
            return True
        
        supported_files = self.file_filter.scan_folder(offer_folder)
        if not supported_files:
            print(f"No supported files in: {offer_name}")
            return False
        
        files_content = []
        for file_path in supported_files:
            content, success = self.document_processor.process_file(file_path)
            files_content.append((file_path, content, success))
        
        success = self.output_manager.save_offer_documents(offer_name, files_content)
        if success:
            print(f"Processed: {offer_name} ({len(supported_files)} files)")
        
        return success

def main():
    input_folder = r'D:\Data-Model\Data\GC 2025'
    output_folder = r'D:\Data-Model\Data\Processed'

    print(f"Input folder: {input_folder}")
    print(f"Output folder: {output_folder}")

    _ = input("Press Enter to continue...")

    orchestrator = DataPreprocessingOrchestrator(input_folder, output_folder)
    success = orchestrator.run()
    
    exit(0 if success else 1)

if __name__ == "__main__":
    main()