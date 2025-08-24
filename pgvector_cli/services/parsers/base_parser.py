"""Base parser class for document processing."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List


class ParsedDocument:
    """Represents a parsed document with metadata."""

    def __init__(self, content: str, metadata: Dict[str, Any] = None):
        self.content = content
        self.metadata = metadata or {}


class BaseParser(ABC):
    """Abstract base class for document parsers."""

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file type."""
        pass

    @abstractmethod
    def parse(self, file_path: Path) -> List[ParsedDocument]:
        """Parse the document and return structured content."""
        pass

    def get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Get basic file metadata."""
        stat = file_path.stat()
        return {
            'file_name': file_path.name,
            'file_path': str(file_path),
            'file_size': stat.st_size,
            'file_extension': file_path.suffix.lower(),
            'file_stem': file_path.stem,
        }
