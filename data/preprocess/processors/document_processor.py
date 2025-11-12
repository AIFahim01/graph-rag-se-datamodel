from pathlib import Path
from typing import List, Tuple
#--- docling imports starts
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
#--- docling imports ends
from PIL import Image

class DocumentExtractedResponse:
    success: bool
    content: str
    pages: List[str]
    images: List[Image]
    tables: List[Image]

    def __init__(self, file_path: Path, success: bool, content: str, pages: List[str] = [], images: List[Image] = [], tables: List[Image] = []):
        self.file_path = file_path
        self.success = success
        if self.success == True:
            self.content = content
            self.pages = pages
            self.images = images
            self.tables = tables

class DocumentProcessor:
    def __init__(self, ocr: str):
        self.ocr = ocr

        if self.ocr == 'docling':
            pipeline_options = PdfPipelineOptions()

            pipeline_options.do_code_enrichment = True
            pipeline_options.do_formula_enrichment = True

            pipeline_options.accelerator_options = AcceleratorOptions(
                device=AcceleratorDevice.CUDA,
                cuda_use_flash_attention2 = True
            )
            pipeline_options.images_scale = 2.0
            pipeline_options.generate_page_images = True
            pipeline_options.generate_picture_images = True

            self.docling_pdf_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
        else:
            raise ValueError(f"Unsupported OCR engine: {self.ocr}")
    
    def process_file(self, file_path: Path) -> tuple[Path, str, bool]:
        """Process file and return (file_path, markdown_content, success)"""
        if not file_path.exists():
            return file_path, "", False
            
        ext = file_path.suffix.lower()
        
        if ext == '.pdf':
            return self._process_pdf(file_path)
        elif ext == '.docx':
            return self._process_docx(file_path)
        elif ext in {'.png', '.jpg', '.jpeg'}:
            return self._process_image(file_path)

        return file_path, f"# Unsupported file type: {file_path.name}\n\n[Unsupported file type]", False

    def process_files(self, file_paths: List[Path]) -> List[DocumentExtractedResponse]:
        """Process files and return list of DocumentExtractedResponse object"""
        pdf_paths = [fp for fp in file_paths if fp.exists() and fp.suffix.lower() == ".pdf"]
        if not pdf_paths:
            return []
        return self._process_pdfs(pdf_paths)

    # private methods
    def _process_pdf(self, file_path: Path) -> tuple[Path, str, bool]:
        if self.ocr == "docling":
            print(f"===> Starting Processing PDF with Docling: {file_path}")
            doc = self.docling_pdf_converter.convert(file_path).document

            full_content = ''
            for page in doc.pages.values():
                page_no = page.page_no
                full_content += f"\n<!-- page {page_no} -->\n"
                page_content = doc.export_to_markdown(
                    page_no=page_no,
                    image_mode=ImageRefMode.PLACEHOLDER,
                )
                full_content += f"{page_content}"

            print(f"===> Finished Processing PDF with Docling: {file_path}")
            return file_path, full_content, True
        return file_path, f"# PDF: {file_path.name}\n\n[PDF processing failed]", False


    def _process_pdfs(self, file_paths: List[Path]) -> List[DocumentExtractedResponse]:
        if self.ocr == "docling":
            print(f"===> Starting Processing PDF with Docling: {file_paths}")
            results = self.docling_pdf_converter.convert_all(file_paths)

            contents: List[DocumentExtractedResponse] = []
            for fp, res in zip(file_paths, results):
                doc = res.document
                full_content = doc.export_to_markdown()
                pages = []
                for page in doc.pages.values():
                    page_no = page.page_no
                    # full_content += f"\n<!-- page {page_no} -->\n"
                    page_content = doc.export_to_markdown(
                        page_no=page_no,
                        image_mode=ImageRefMode.PLACEHOLDER,
                    )
                    pages.append(page_content)
                    # full_content += f"{page_content}"
                images = []
                tables = []
                for element, _level in doc.iterate_items():
                    if isinstance(element, TableItem):
                        tables.append(element.get_image(doc))
                    if isinstance(element, PictureItem):
                        images.append(element.get_image(doc))
                
                contents.append(DocumentExtractedResponse(fp, True, full_content, pages, images, tables))

            print(f"===> Finished Processing PDF with Docling: {len(file_paths)} files")
            return contents
        return []
    
    def _process_docx(self, file_path: Path) -> tuple[str, bool]:
        # TODO: Implement Docling integration  
        return f"# DOCX: {file_path.name}\n\n[DOCX processing placeholder]", True
    
    def _process_image(self, file_path: Path) -> tuple[str, bool]:
        # TODO: Implement DeepSeek-OCR integration
        return f"# Image: {file_path.name}\n\n[OCR processing placeholder]", True