# file_loader.py
"""
File loader module for PDF and Markdown files
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Optional
import hashlib


class MarkdownLoader:
    """Load and parse Markdown files"""
    
    @staticmethod
    def load(filepath: str) -> Dict:
        """Load a markdown file and extract content"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract title from first # heading or filename
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else Path(filepath).stem
            
            # Remove code blocks temporarily to avoid confusion
            code_blocks = []
            def replace_code(match):
                code_blocks.append(match.group(0))
                return f"[CODE_BLOCK_{len(code_blocks)-1}]"
            
            content_no_code = re.sub(r'```[\s\S]*?```', replace_code, content)
            
            # Split into sections by headers
            sections = re.split(r'^#{1,6}\s+', content_no_code, flags=re.MULTILINE)
            
            # Restore code blocks
            for i, block in enumerate(code_blocks):
                for j, section in enumerate(sections):
                    sections[j] = section.replace(f"[CODE_BLOCK_{i}]", block)
            
            # Clean up the content
            full_text = '\n\n'.join(sections).strip()
            
            return {
                "id": hashlib.md5(filepath.encode()).hexdigest()[:8],
                "title": title,
                "source": f"file://{filepath}",
                "text": full_text,
                "type": "markdown"
            }
        except Exception as e:
            raise Exception(f"Failed to load markdown file: {str(e)}")


class PDFLoader:
    """Load and parse PDF files"""
    
    @staticmethod
    def load(filepath: str) -> Dict:
        """Load a PDF file and extract text"""
        try:
            # Try PyPDF2 first
            try:
                import PyPDF2
                return PDFLoader._load_with_pypdf2(filepath)
            except ImportError:
                pass
            
            # Try pdfplumber
            try:
                import pdfplumber
                return PDFLoader._load_with_pdfplumber(filepath)
            except ImportError:
                pass
            
            # Fallback to basic method
            return PDFLoader._load_basic(filepath)
            
        except Exception as e:
            raise Exception(f"Failed to load PDF file: {str(e)}")
    
    @staticmethod
    def _load_with_pypdf2(filepath: str) -> Dict:
        """Load PDF using PyPDF2"""
        import PyPDF2
        
        text_parts = []
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)
            
            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text.strip():
                    text_parts.append(text)
        
        full_text = '\n\n'.join(text_parts)
        title = Path(filepath).stem
        
        return {
            "id": hashlib.md5(filepath.encode()).hexdigest()[:8],
            "title": title,
            "source": f"file://{filepath}",
            "text": full_text,
            "type": "pdf",
            "pages": num_pages
        }
    
    @staticmethod
    def _load_with_pdfplumber(filepath: str) -> Dict:
        """Load PDF using pdfplumber"""
        import pdfplumber
        
        text_parts = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        
        full_text = '\n\n'.join(text_parts)
        title = Path(filepath).stem
        
        return {
            "id": hashlib.md5(filepath.encode()).hexdigest()[:8],
            "title": title,
            "source": f"file://{filepath}",
            "text": full_text,
            "type": "pdf",
            "pages": len(pdf.pages)
        }
    
    @staticmethod
    def _load_basic(filepath: str) -> Dict:
        """Basic fallback loader"""
        # This is a fallback that just creates a placeholder
        # In production, you'd want to ensure at least one PDF library is installed
        title = Path(filepath).stem
        
        return {
            "id": hashlib.md5(filepath.encode()).hexdigest()[:8],
            "title": title,
            "source": f"file://{filepath}",
            "text": f"[PDF content from {title} - PDF library required for text extraction]",
            "type": "pdf",
            "note": "Install PyPDF2 or pdfplumber for PDF text extraction"
        }


class FileLoader:
    """Main file loader that handles different file types"""
    
    SUPPORTED_EXTENSIONS = {
        '.md': 'markdown',
        '.markdown': 'markdown',
        '.pdf': 'pdf',
        '.txt': 'text'
    }
    
    @classmethod
    def load_file(cls, filepath: str) -> Dict:
        """Load a file based on its extension"""
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        ext = path.suffix.lower()
        
        if ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}")
        
        if ext in ['.md', '.markdown']:
            return MarkdownLoader.load(filepath)
        elif ext == '.pdf':
            return PDFLoader.load(filepath)
        elif ext == '.txt':
            return cls._load_text_file(filepath)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    @staticmethod
    def _load_text_file(filepath: str) -> Dict:
        """Load a plain text file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        title = Path(filepath).stem
        
        return {
            "id": hashlib.md5(filepath.encode()).hexdigest()[:8],
            "title": title,
            "source": f"file://{filepath}",
            "text": content,
            "type": "text"
        }
    
    @classmethod
    def scan_directory(cls, directory: str, recursive: bool = False) -> List[str]:
        """Scan directory for supported files"""
        supported_files = []
        path = Path(directory)
        
        if not path.exists() or not path.is_dir():
            return supported_files
        
        pattern = "**/*" if recursive else "*"
        
        for file_path in path.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in cls.SUPPORTED_EXTENSIONS:
                supported_files.append(str(file_path))
        
        return supported_files


class BatchLoader:
    """Load multiple files in batch"""
    
    @staticmethod
    def load_files(filepaths: List[str]) -> List[Dict]:
        """Load multiple files"""
        documents = []
        errors = []
        
        for filepath in filepaths:
            try:
                doc = FileLoader.load_file(filepath)
                documents.append(doc)
            except Exception as e:
                errors.append(f"{filepath}: {str(e)}")
        
        if errors:
            print("Errors loading some files:")
            for error in errors:
                print(f"  - {error}")
        
        return documents
    
    @staticmethod
    def load_directory(directory: str, recursive: bool = False) -> List[Dict]:
        """Load all supported files from a directory"""
        files = FileLoader.scan_directory(directory, recursive)
        return BatchLoader.load_files(files)
