
from pathlib import Path
import time
from datetime import datetime
from processors import FileFilter, DocumentProcessor, OutputManager
from typing import List, Dict, Any
import json
import logging
from console_watcher import start_progress, advance_progress, end_progress, log

class DataPreprocessingOrchestrator:
    def __init__(self, input_folder: str, output_folder: str):
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.file_filter = FileFilter(extensions=[".pdf"])
        self.document_processor = DocumentProcessor("docling")
        self.output_manager = OutputManager(self.output_folder, self.input_folder)
        self.processed_offers_file = self.output_folder / "processed_files.json"
        self.failed_log_file = self.output_folder / "failed_log.json"
        self.processed_offers = self._load_processed_offers(self.processed_offers_file)
        self.failed_logs = self._load_processed_offers(self.failed_log_file)
    
    def run(self) -> bool:
        """Run the preprocessing pipeline"""
        if not self.input_folder.exists():
            logging.error(f"Input folder not found: {self.input_folder}")
            return False
        
        unprocessed_files = self._get_unprocessed_files()
        if not unprocessed_files:
            logging.info("No new files to process.")
            return False
        
        logging.info(f"Found {len(unprocessed_files)} new files to process.")
        start_progress(len(unprocessed_files))
        
        processed_count = self._process_all_files(unprocessed_files)
        end_progress()
        logging.info(f"Processing complete. Succeeded: {processed_count}, Failed: {len(unprocessed_files) - processed_count}.")
        return processed_count > 0
    
    def _get_unprocessed_files(self) -> List[Path]:
        supported_files = self.file_filter.scan_folder(self.input_folder)
        logging.info(f"Scanned input folder: {len(supported_files)} PDF files found.")
        unprocessed_files = [f for f in supported_files if str(f.relative_to(self.input_folder)) not in self.processed_offers]
        return unprocessed_files
    
    def _process_all_files(self, file_paths: List[Path]) -> int:
        count = 0
        idx = 0
        for f in file_paths:
            
            idx += 1
            relative_path = str(f.relative_to(self.input_folder))

            start_time = time.perf_counter()
            
            success, message, files_content = self.document_processor.process_file(f)
            if not success:
                logging.error(f"Failed to process '{f.name}': {message}")
                self.failed_logs[relative_path] = {
                    "last_attempt": datetime.now().isoformat(),
                    "stage": "processing",
                    "error_message": message,
                }
                self._save_processed_offers(self.failed_log_file, self.failed_logs)
                advance_progress()
                continue
            
            success, message = self.output_manager.save_processed_file(files_content)
            if not success:
                logging.error(f"Failed to save '{f.name}': {message}")
                self.failed_logs[relative_path] = {
                    "last_attempt": datetime.now().isoformat(),
                    "stage": "saving",
                    "error_message": message,
                }
                self._save_processed_offers(self.failed_log_file, self.failed_logs)
                advance_progress()
                continue

            count += 1
            end_time = time.perf_counter()
            duration = round(end_time - start_time, 2)
            logging.info(f"Processed '{f.name}' successfully in {duration}s.")
            
            self.processed_offers[relative_path] = {
                "last_processed": datetime.now().isoformat(),
                "page_count": len(files_content.content_pages),
                "duration_seconds": duration,
                "ocr_used": self.document_processor.ocr
            }
            self.failed_logs.pop(relative_path, None)
            self._save_processed_offers(self.processed_offers_file, self.processed_offers)
            self._save_processed_offers(self.failed_log_file, self.failed_logs)
            advance_progress()
        
        return count
    
    def _load_processed_offers(self, file_path: Path) -> Dict[str, Any]:
        if not file_path.exists():
            return {}
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error loading processed offers from {file_path}: {e}")
            return {}

    def _save_processed_offers(self, file_path: Path, data: Dict[str, Any]) -> None:
        try:
            self.output_folder.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            logging.error(f"Error saving processed offers to {file_path}: {e}")