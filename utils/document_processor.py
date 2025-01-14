import os
import pdfplumber
from docx import Document
import logging
from typing import Dict, Any, Optional
from config import ALLOWED_FILE_TYPES, MAX_FILE_SIZE_MB

logger = logging.getLogger(__name__)

class DocumentProcessor:
    @staticmethod
    def get_file_type(filename: str) -> str:
        """Get file type based on extension"""
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.pdf':
            return 'application/pdf'
        elif ext == '.docx':
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif ext == '.txt':
            return 'text/plain'
        elif ext == '.md':
            return 'text/markdown'
        return 'unknown'

    @staticmethod
    def validate_file(file) -> tuple[bool, str]:
        """Validate file type and size"""
        try:
            # Check file size
            file_size_mb = len(file.getvalue()) / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                return False, f"File size exceeds {MAX_FILE_SIZE_MB}MB limit"

            # Check file type
            file_type = DocumentProcessor.get_file_type(file.name)
            if file_type not in ALLOWED_FILE_TYPES:
                return False, f"Unsupported file type: {file_type}"

            return True, "File is valid"
        except Exception as e:
            logger.error(f"Error validating file: {str(e)}")
            return False, "Error validating file"

    @staticmethod
    def extract_text_from_pdf(file) -> Optional[str]:
        """Extract text from PDF file"""
        try:
            text = []
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    text.append(page.extract_text())
            return "\n".join(text)
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return None

    @staticmethod
    def extract_text_from_docx(file) -> Optional[str]:
        """Extract text from DOCX file"""
        try:
            doc = Document(file)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {str(e)}")
            return None

    @staticmethod
    def process_document(file) -> Dict[str, Any]:
        """Process uploaded document and extract text"""
        try:
            # Validate file
            is_valid, message = DocumentProcessor.validate_file(file)
            if not is_valid:
                return {"success": False, "error": message}

            # Determine file type
            file_type = DocumentProcessor.get_file_type(file.name)
            
            if file_type == 'application/pdf':
                text = DocumentProcessor.extract_text_from_pdf(file)
            elif file_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                text = DocumentProcessor.extract_text_from_docx(file)
            elif file_type in ['text/plain', 'text/markdown']:
                text = file.getvalue().decode('utf-8')
            else:
                return {"success": False, "error": "Unsupported file type"}

            if text is None:
                return {"success": False, "error": "Failed to extract text from document"}

            return {"success": True, "text": text}
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return {"success": False, "error": "Error processing document"} 