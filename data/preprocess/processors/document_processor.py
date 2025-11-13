from pathlib import Path
from typing import List
#--- docling imports starts
from docling_core.types.doc import ImageRefMode
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, granite_picture_description
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
#--- docling imports ends
from PIL import Image

class ImageAnnotationData:
    ref: str
    uri: str
    caption: str
    annotation_prov: List[str] = []
    annotation_text: List[str] = []

class DocumentExtractedResponse:
    file_path: Path
    success: bool
    full_content: str
    content_pages: List[str] = []
    pages: List[Image] = []
    pictures: List[Image] = []
    tables: List[Image] = []
    image_contents: List[ImageAnnotationData] = []

class DocumentProcessor:
    def __init__(self, ocr: str):
        self.ocr = ocr

        if self.ocr == 'docling':
            pipeline_options = PdfPipelineOptions()

            pipeline_options.do_code_enrichment = True
            pipeline_options.do_formula_enrichment = True
            pipeline_options.do_picture_description = True

            pipeline_options.picture_description_options = (
                granite_picture_description
            )

            pipeline_options.picture_description_options.prompt = (
                "You are an image captioning model. "
                "Describe exactly what appears in the figure in 2–4 sentences. "
                "Focus on structure (axes, labels, blocks, arrows, relationships), "
                "not decorative aspects. Do not hallucinate text that is not visible."
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
            print(f"====> Starting Extracting Content from PDF with Docling: {file_path.name}")
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

            print(f"====> Finished Extracting Content from PDF with Docling: {file_path.name}")
            return file_path, full_content, True
        return file_path, f"# PDF: {file_path.name}\n\n[PDF processing failed]", False


    def _process_pdfs(self, file_paths: List[Path]) -> List[DocumentExtractedResponse]:
        if self.ocr == "docling":
            print(f"====> Starting Extracting Content from PDFs with Docling: {[fp.name for fp in file_paths]}")
            results = self.docling_pdf_converter.convert_all(file_paths)

            contents: List[DocumentExtractedResponse] = []
            for fp, res in zip(file_paths, results):
                doc = res.document

                full_content = ''
                pages = []
                content_pages = []
                for page in doc.pages.values():
                    page_no = page.page_no
                    page_content = doc.export_to_markdown(
                        page_no=page_no,
                        image_mode=ImageRefMode.PLACEHOLDER,
                    )
                    content_pages.append(page_content)
                    pages.append(page.image.pil_image)

                    full_content += f"\n<!-- page {page_no} -->\n"
                    full_content += f"{page_content}"


                pictures = []
                all_imagedata = []
                for picture in doc.pictures:
                    pictures.append(picture.get_image(doc))
                    imagedata = ImageAnnotationData()
                    imagedata.ref = picture.self_ref
                    imagedata.uri = str(picture.image.uri)
                    imagedata.caption = picture.caption_text(doc=doc)

                    for ann in picture.annotations:
                        imagedata.annotation_text.append(ann.text)
                        imagedata.annotation_prov.append(ann.provenance)
                    all_imagedata.append(imagedata)

                tables = []
                for table in doc.tables:
                    tables.append(table.get_image(doc))
                
                extracted_response = DocumentExtractedResponse()
                extracted_response.file_path = fp
                extracted_response.success = True
                extracted_response.full_content = full_content
                extracted_response.content_pages = content_pages
                extracted_response.pages = pages
                extracted_response.pictures = pictures
                extracted_response.tables = tables
                extracted_response.image_contents = all_imagedata

                contents.append(extracted_response)

            print(f"====> Finished Extracting Content from PDFs with Docling: {len(contents)} files")
            return contents
        return []
    
    def _process_docx(self, file_path: Path) -> tuple[str, bool]:
        # TODO: Implement Docling integration  
        return f"# DOCX: {file_path.name}\n\n[DOCX processing placeholder]", True
    
    def _process_image(self, file_path: Path) -> tuple[str, bool]:
        # TODO: Implement DeepSeek-OCR integration
        return f"# Image: {file_path.name}\n\n[OCR processing placeholder]", True
