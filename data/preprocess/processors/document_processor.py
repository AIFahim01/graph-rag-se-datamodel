import logging
from pathlib import Path
from typing import List
#--- docling imports starts
from docling_core.types.doc.base import ImageRefMode
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, smolvlm_picture_description
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling_core.types.doc.document import PictureDescriptionData
#--- docling imports ends
from PIL.Image import Image
import re

# from .image_processor import VllmImageExtractor

class DocumentExtractedResponse:
    file_path: Path
    success: bool
    full_content: str
    content_pages: List[str] = []
    pages: List[Image] = []
    pictures: List[Image] = []
    tables: List[Image] = []
    annotation_texts: List[str] = []
    caption_texts: List[str] = []

class DocumentProcessor:
    def __init__(self, ocr: str):
        self.ocr = ocr
        # self.image_processor = VllmImageExtractor()

        if self.ocr == 'docling':
            pipeline_options = PdfPipelineOptions()

            pipeline_options.do_code_enrichment = True
            pipeline_options.do_formula_enrichment = True
            pipeline_options.do_picture_description = True

            pipeline_options.picture_description_options = (
                smolvlm_picture_description
            )

            pipeline_options.picture_description_options.prompt = (
                "Describe the image in three sentences. Be consise and accurate."
            )

            pipeline_options.accelerator_options = AcceleratorOptions(
                device=AcceleratorDevice.CUDA
            )
            pipeline_options.images_scale = 2.0
            pipeline_options.generate_page_images = True
            pipeline_options.generate_picture_images = True

            self.docling_pdf_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(
                        pipeline_options=pipeline_options,
                        backend=PyPdfiumDocumentBackend)
                }
            )
        else:
            raise ValueError(f"Unsupported OCR engine: {self.ocr}")
    
    def process_file(self, file_path: Path) -> tuple[bool, str, DocumentExtractedResponse]:
        """Process file and return (file_path, markdown_content, success)"""
        if not file_path.exists():
            return False, "File doesn't exist to extract", DocumentExtractedResponse()
            
        ext = file_path.suffix.lower()
        
        if ext == '.pdf':
            return self._process_pdf(file_path)
        elif ext == '.docx':
            return self._process_docx(file_path)
        elif ext in {'.png', '.jpg', '.jpeg'}:
            return self._process_image(file_path)

        logging.warning(f"Unsupported file type '{ext}' for '{file_path.name}'.")
        return False, f"# Unsupported file type: {file_path.name}\n\n[Unsupported file type]", DocumentExtractedResponse()

    def _process_pdf(self, file_path: Path) -> tuple[bool, str, DocumentExtractedResponse]:
        try:
            if self.ocr == "docling":
                result = self.docling_pdf_converter.convert(file_path)
                doc = result.document
                
                pages = []
                content_pages = []
                page_numbers = []
                for page in doc.pages.values():
                    page_no = page.page_no
                    page_numbers.append(page_no)
                    page_content = doc.export_to_markdown(
                        page_no=page_no,
                        image_mode=ImageRefMode.PLACEHOLDER,
                    )
                    content_pages.append(page_content)

                    page_img = getattr(page.image, "pil_image", None) or getattr(page.image, "image", None)
                    if page_img is not None:
                        pages.append(page_img)

                pictures = []
                all_annotation = []
                all_captions = []
                for picture in doc.pictures:
                    pictures.append(picture.get_image(doc))
                    caption: str = picture.caption_text(doc=doc) or ''
                    all_captions.append(caption)
                    annot = ''
                    for ann in picture.annotations:
                        if not isinstance(ann, PictureDescriptionData):
                            continue
                        annot += ann.provenance + ": " + ann.text + "\n"
                    all_annotation.append(annot)
                
                logging.info(f"Extracted {len(doc.pages)} pages, {len(doc.pictures)} pictures, and {len(doc.tables)} tables from '{file_path.name}'.")

                tables = []
                for table in doc.tables:
                    tables.append(table.get_image(doc))

                # all_imagedata = self.image_processor.extract_images(pictures)

                pattern = re.compile(r"<!--\s*image\s*-->")
                replacer = make_image_replacer(all_captions, all_annotation)

                full_content = ''
                for idx, page_no in enumerate(page_numbers):
                    page_content = content_pages[idx]
                    page_content = pattern.sub(replacer, page_content)
                    content_pages[idx] = page_content
                    full_content += f"\n<!-- page {page_no} -->\n{page_content}"
                
                extracted_response = DocumentExtractedResponse()
                extracted_response.file_path = file_path
                extracted_response.success = True
                extracted_response.full_content = full_content
                extracted_response.content_pages = content_pages
                extracted_response.pages = pages
                extracted_response.pictures = pictures
                extracted_response.tables = tables
                extracted_response.annotation_texts = all_annotation
                
                return True, "Successfully Extracted", extracted_response
            return False, "Ocr library support not found", DocumentExtractedResponse()
        except Exception as e:
            logging.error(f"Error processing PDF '{file_path.name}': {e}")
            return False, str(e), DocumentExtractedResponse()
    
    def _process_docx(self, file_path: Path) -> tuple[bool, str, DocumentExtractedResponse]:
        logging.warning(f"DOCX processing not implemented. Skipping '{file_path.name}'.")
        # TODO: Implement Docling integration  
        return False, f"# DOCX: {file_path.name}\n\n[DOCX processing placeholder]", DocumentExtractedResponse()
    
    def _process_image(self, file_path: Path) -> tuple[bool, str, DocumentExtractedResponse]:
        logging.warning(f"Image processing not implemented. Skipping '{file_path.name}'.")
        # TODO: Implement DeepSeek-OCR integration
        return False, f"# Image: {file_path.name}\n\n[OCR processing placeholder]", DocumentExtractedResponse()    

def make_image_replacer(captions, annotations):
    i = 0
    def _repl(_):
        nonlocal i
        cap = (captions[i] or "").strip() if i < len(captions) else ""
        ann = (annotations[i] or "").strip() if i < len(annotations) else ""
        i += 1
        lines = [f"<!-- image {i}"]
        if cap: lines.append(f"caption: {cap}")
        if ann: lines.append(f"annotation: {ann}")
        return "\n".join(lines) + " -->"
    return _repl