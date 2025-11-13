from pathlib import Path
from typing import List

class FileFilter:
    SUPPORTED_EXTENSIONS = {'.pdf'}
    
    def scan_folder(self, folder_path: Path) -> List[Path]:
        """Returns list of supported files in folder"""
        if not folder_path.exists():
            return []

        supported_files = []
        for item in folder_path.iterdir():
            if item.is_file() and item.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                supported_files.append(item)
            elif item.is_dir() and not item.name.startswith('.'):
                supported_files.extend(self.scan_folder(item))

        return supported_files
    
    def get_offer_folders(self, input_folder: Path) -> List[Path]:
        """Get all offer folders from input directory"""
        if not input_folder.exists():
            return []
            
        return [item for item in input_folder.iterdir() 
                if item.is_dir() and not item.name.startswith('.')]
