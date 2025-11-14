
from pathlib import Path
import time
from datetime import datetime
from processors import FileFilter, DocumentProcessor, OutputManager
from typing import List, Dict, Any
import json

class DataPreprocessingOrchestrator:
    def __init__(self, input_folder: str, output_folder: str):
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.file_filter = FileFilter()
        self.document_processor = DocumentProcessor("docling")
        self.output_manager = OutputManager(self.output_folder, self.input_folder)
        self.processed_offers_file = self.output_folder / "processed_files.json"
        self.failed_log_file = self.output_folder / "failed_log.json"
        self.processed_offers = self._load_processed_offers(self.processed_offers_file)
        self.failed_logs = self._load_processed_offers(self.failed_log_file)
    
    def run(self) -> bool:
        """Run the preprocessing pipeline"""
        if not self.input_folder.exists():
            print(f"Input folder not found: {self.input_folder}")
            return False
        
        unprocessed_files = self._get_unprocessed_files()
        if not unprocessed_files:
            print("No unprocessed files found.")
            return False
        
        print(f"=> Total unprocessed files found: {len(unprocessed_files)}")
        
        processed_count = self._process_all_files(unprocessed_files)
        print(f"=> Processed {processed_count} files and failed {len(unprocessed_files) - processed_count} files")
        return processed_count > 0
    
    def _get_unprocessed_files(self) -> List[Path]:
        supported_files = self.file_filter.scan_folder(self.input_folder)
        print(f"=> Total pdf files found: {len(supported_files)}")
        unprocessed_files = []
        for f in supported_files:
            relative_path = str(f.relative_to(self.input_folder))
            if relative_path not in self.processed_offers:
                unprocessed_files.append(f)
        return unprocessed_files
    
    def _process_all_files(self, file_paths: List[Path]) -> int:
        count = 0
        idx = 0
        for f in file_paths:
            idx += 1
            print(f"==> Starting Processing file {idx}/{len(file_paths)}: {f.stem}")
            relative_path = str(f.relative_to(self.input_folder))

            start_time = time.perf_counter()
            
            success, message, files_content = self.document_processor.process_file(f)
            if not success:
                print(f"Failed to process file {f}: {message}")
                self.failed_logs[relative_path] = {
                    "last_attempt": datetime.now().isoformat(),
                    "stage": "processing",
                    "error_message": message,
                }
                self._save_processed_offers(self.failed_log_file, self.failed_logs)
                continue
            print(f"==> Finished extracting file: {f.stem}")
            success, message = self.output_manager.save_processed_file(files_content)
            if not success:
                print(f"Failed to save processed file {f}: {message}")
                self.failed_logs[relative_path] = {
                    "last_attempt": datetime.now().isoformat(),
                    "stage": "saving",
                    "error_message": message,
                }
                self._save_processed_offers(self.failed_log_file, self.failed_logs)
                continue
            print(f"==> Finished saving extraction: {f.stem}")
            count += 1
            end_time = time.perf_counter()
            
            self.processed_offers[relative_path] = {
                "last_processed": datetime.now().isoformat(),
                "page_count": len(files_content.content_pages),
                "duration_seconds": round(end_time - start_time, 3),
                "ocr_used": self.document_processor.ocr
            }
            self.failed_logs.pop(relative_path, None)
            self._save_processed_offers(self.processed_offers_file, self.processed_offers)
            self._save_processed_offers(self.failed_log_file, self.failed_logs)
            print(f"=> Total Processed: {count}/{len(file_paths)} files")
        
        return count
    
    def _load_processed_offers(self, file_path: Path) -> Dict[str, Any]:
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    return data
            except Exception as e:
                print(f"Error loading processed offers from {file_path}: {e}")
                pass
        return {}
    
    def _save_processed_offers(self, file_path: Path, data: Dict[str, Any]) -> None:
        try:
            self.output_folder.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving processed offers to {file_path}: {e}")