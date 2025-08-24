"""Document processing service that coordinates all parsers."""

from pathlib import Path
from typing import List, Dict, Any, Optional
import os

from .parsers import BaseParser, CSVParser, PDFParser, TextParser
from .parsers.base_parser import ParsedDocument
from .chunking_service import ChunkingService, TextChunk


class DocumentService:
    """Service for processing documents of various formats."""
    
    def __init__(self):
        self.parsers: List[BaseParser] = [
            CSVParser(),
            PDFParser(),
            TextParser(),
        ]
    
    def process_document(self, file_path: str, chunk_size: int = 500, 
                        overlap: int = 100) -> List[TextChunk]:
        """Process a document file and return chunked content."""
        file_path_obj = Path(file_path)
        
        # Validate file exists
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Validate file size (optional safety check)
        max_size = 100 * 1024 * 1024  # 100MB limit
        if file_path_obj.stat().st_size > max_size:
            raise ValueError(f"File too large: {file_path_obj.stat().st_size} bytes. Maximum allowed: {max_size} bytes")
        
        # Find appropriate parser
        parser = self._find_parser(file_path_obj)
        if not parser:
            raise ValueError(f"No parser available for file type: {file_path_obj.suffix}")
        
        # Parse document
        documents = parser.parse(file_path_obj)
        if not documents:
            raise ValueError(f"No content extracted from file: {file_path}")
        
        # Initialize chunking service
        chunking_service = ChunkingService(chunk_size=chunk_size, overlap=overlap)
        
        # Chunk documents
        chunks = chunking_service.chunk_documents(documents)
        
        return chunks
    
    def _find_parser(self, file_path: Path) -> Optional[BaseParser]:
        """Find the appropriate parser for the given file."""
        for parser in self.parsers:
            if parser.can_parse(file_path):
                return parser
        return None
    
    def get_supported_extensions(self) -> Dict[str, str]:
        """Get all supported file extensions and their descriptions."""
        extensions = {}
        
        # CSV/Excel parser
        extensions.update({
            '.csv': 'Comma-separated values file',
            '.xlsx': 'Excel spreadsheet file',
            '.xls': 'Legacy Excel spreadsheet file',
        })
        
        # PDF parser
        extensions['.pdf'] = 'Portable Document Format file'
        
        # Text parser
        extensions.update({
            '.txt': 'Plain text file',
            '.md': 'Markdown file',
            '.markdown': 'Markdown file',
            '.rst': 'reStructuredText file',
        })
        
        return extensions
    
    def validate_file_type(self, file_path: str) -> bool:
        """Check if the file type is supported."""
        file_path_obj = Path(file_path)
        return file_path_obj.suffix.lower() in self.get_supported_extensions()
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get information about a file without processing it."""
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = file_path_obj.stat()
        parser = self._find_parser(file_path_obj)
        
        return {
            'file_name': file_path_obj.name,
            'file_path': str(file_path_obj),
            'file_size': stat.st_size,
            'file_extension': file_path_obj.suffix.lower(),
            'is_supported': parser is not None,
            'parser_type': parser.__class__.__name__ if parser else None,
            'readable': os.access(file_path_obj, os.R_OK)
        }