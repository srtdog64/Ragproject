# ui/file_loaders.py
"""
File loading utilities for the document widget
"""
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import json
import PyPDF2
import logging

logger = logging.getLogger(__name__)

class FileLoader:
    """Load individual files into document format"""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.md', '.txt', '.json'}
    
    def load_file(self, filepath: str) -> Optional[Dict]:
        """
        Load a single file and return as document dict
        
        Args:
            filepath: Path to the file
            
        Returns:
            Document dict with id, title, source, and text
        """
        path = Path(filepath)
        
        if not path.exists():
            logger.error(f"File not found: {filepath}")
            return None
            
        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            logger.warning(f"Unsupported file type: {path.suffix}")
            return None
        
        try:
            # Generate unique ID from file path
            doc_id = hashlib.md5(str(path).encode()).hexdigest()[:12]
            
            # Load based on file type
            if path.suffix.lower() == '.pdf':
                text = self._load_pdf(path)
            elif path.suffix.lower() == '.md':
                text = self._load_text(path)
            elif path.suffix.lower() == '.txt':
                text = self._load_text(path)
            elif path.suffix.lower() == '.json':
                return self._load_json(path)
            else:
                return None
            
            if not text:
                return None
                
            # Create document
            doc = {
                "id": f"doc_{doc_id}",
                "title": path.stem,  # Filename without extension
                "source": str(path.parent),
                "text": text
            }
            
            logger.info(f"Loaded file: {path.name} ({len(text)} chars)")
            return doc
            
        except Exception as e:
            logger.error(f"Error loading file {filepath}: {e}")
            return None
    
    def _load_pdf(self, path: Path) -> str:
        """Load text from PDF file"""
        try:
            text_parts = []
            with open(path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_parts.append(page.extract_text())
            return '\n'.join(text_parts)
        except Exception as e:
            logger.error(f"Error reading PDF {path}: {e}")
            return ""
    
    def _load_text(self, path: Path) -> str:
        """Load text from text/markdown file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(path, 'r', encoding='cp949') as f:
                    return f.read()
            except:
                logger.error(f"Could not decode file {path}")
                return ""
        except Exception as e:
            logger.error(f"Error reading text file {path}: {e}")
            return ""
    
    def _load_json(self, path: Path) -> Optional[Dict]:
        """Load document from JSON file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # If it's already a proper document format
            if isinstance(data, dict) and 'text' in data:
                # Ensure required fields
                if 'id' not in data:
                    data['id'] = hashlib.md5(str(path).encode()).hexdigest()[:12]
                if 'title' not in data:
                    data['title'] = path.stem
                if 'source' not in data:
                    data['source'] = str(path.parent)
                return data
            
            # If it's just text content in JSON
            elif isinstance(data, dict):
                text = json.dumps(data, indent=2, ensure_ascii=False)
                return {
                    "id": hashlib.md5(str(path).encode()).hexdigest()[:12],
                    "title": path.stem,
                    "source": str(path.parent),
                    "text": text
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading JSON {path}: {e}")
            return None


class BatchLoader:
    """Load multiple files from a directory"""
    
    def __init__(self):
        self.file_loader = FileLoader()
    
    def load_directory(self, directory: str, recursive: bool = False) -> List[Dict]:
        """
        Load all supported files from a directory
        
        Args:
            directory: Path to directory
            recursive: Whether to search subdirectories
            
        Returns:
            List of document dicts
        """
        dir_path = Path(directory)
        
        if not dir_path.exists() or not dir_path.is_dir():
            logger.error(f"Invalid directory: {directory}")
            return []
        
        documents = []
        
        # Get all files
        if recursive:
            files = [f for f in dir_path.rglob('*') if f.is_file()]
        else:
            files = [f for f in dir_path.iterdir() if f.is_file()]
        
        # Filter and load supported files
        for file_path in files:
            if file_path.suffix.lower() in FileLoader.SUPPORTED_EXTENSIONS:
                doc = self.file_loader.load_file(str(file_path))
                if doc:
                    documents.append(doc)
        
        logger.info(f"Loaded {len(documents)} documents from {directory}")
        return documents
    
    def load_files(self, filepaths: List[str]) -> List[Dict]:
        """
        Load multiple specific files
        
        Args:
            filepaths: List of file paths
            
        Returns:
            List of document dicts
        """
        documents = []
        
        for filepath in filepaths:
            doc = self.file_loader.load_file(filepath)
            if doc:
                documents.append(doc)
        
        return documents
