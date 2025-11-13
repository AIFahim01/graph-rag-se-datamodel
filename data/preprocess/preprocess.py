#!/usr/bin/env python3

from pathlib import Path
import time
from processors import FileFilter, DocumentProcessor, OutputManager
from typing import List

class DataPreprocessingOrchestrator:
    def __init__(self, input_folder: Path, output_folder: Path):
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.file_filter = FileFilter()
        self.document_processor = DocumentProcessor("docling")
        self.output_manager = OutputManager(output_folder)
    
    def run(self) -> bool:
        """Run the preprocessing pipeline"""
        if not self.input_folder.exists():
            print(f"Input folder not found: {self.input_folder}")
            return False
        
        processed_count = self._get_single_offer(2, self.input_folder, [])
        print(f"=> Processed {processed_count} offers")
        return processed_count > 0

    def _get_single_offer(self, level: int, current_folder: Path, relative_parents: List[str]) -> int:
        if level == 0:
            success = self._process_single_offer(current_folder, relative_parents.copy())
            return success == True

        print(f"==> Processing folder: {current_folder.name}")
        relative_parents.append(current_folder.name)
        processed_count = 0
        
        offer_folders = self.file_filter.get_offer_folders(current_folder)
        for offer_folder in offer_folders:
            processed_count += self._get_single_offer(level - 1, offer_folder, relative_parents)

        relative_parents.pop()
        print(f"==> Processed folder: {current_folder.name} ({processed_count} offers)")
        return processed_count
    
    def _process_single_offer(self, offer_folder: Path, relative_parents: List[str]) -> bool:
        print(f"===> Processing offer: {offer_folder.name}")
        start_time = time.perf_counter()
        offer_name = offer_folder.name
        
        if self.output_manager.is_offer_processed(offer_name):
            print(f"===> Skipping already processed: {offer_name}")
            return True
        
        supported_files = self.file_filter.scan_folder(offer_folder)
        if not supported_files:
            print(f"===> No supported files in: {offer_name}")
            return False

        files_contents = self.document_processor.process_files(supported_files)
        
        success = self.output_manager.save_offer_documents(start_time, offer_name, relative_parents, files_contents)

        print(f"===> Processed offer: {offer_name} ({success})")
        return success

def main():
    input_folder = r'D:\Data-Model\Data\GC 2025'
    output_folder = r'D:\Data-Model\Data\Processed-offers'

    print(f"=> Input folder: {input_folder}")
    print(f"=> Output folder: {output_folder}")

    orchestrator = DataPreprocessingOrchestrator(input_folder, output_folder)
    success = orchestrator.run()
    
    exit(0 if success else 1)

if __name__ == "__main__":
    main()
