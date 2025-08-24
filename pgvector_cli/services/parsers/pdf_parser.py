"""PDF parser using pymupdf4llm for optimal text extraction."""

import re
from pathlib import Path
from typing import Any, Dict, List

from .base_parser import BaseParser, ParsedDocument


class PDFParser(BaseParser):
    """Parser for PDF files using pymupdf4llm."""

    def can_parse(self, file_path: Path) -> bool:
        """Check if file is PDF format."""
        return file_path.suffix.lower() == '.pdf'

    def parse(self, file_path: Path) -> List[ParsedDocument]:
        """Parse PDF file and extract text content."""
        try:
            import pymupdf4llm

            # Extract text with markdown formatting
            markdown_text = pymupdf4llm.to_markdown(str(file_path))

            if not markdown_text or not markdown_text.strip():
                return []

            # Get base metadata
            base_metadata = self.get_file_metadata(file_path)
            base_metadata.update({
                'parser_type': 'pdf',
                'extraction_method': 'pymupdf4llm'
            })

            # Split content into logical sections
            documents = self._split_into_sections(markdown_text, base_metadata)

            return documents

        except ImportError:
            # Fallback error if pymupdf4llm is not available
            base_metadata = self.get_file_metadata(file_path)
            base_metadata['error'] = 'pymupdf4llm not available'

            return [ParsedDocument(
                content=f"Error: pymupdf4llm not available for parsing {file_path.name}",
                metadata=base_metadata
            )]
        except Exception as e:
            base_metadata = self.get_file_metadata(file_path)
            base_metadata['error'] = str(e)

            return [ParsedDocument(
                content=f"Error parsing PDF {file_path.name}: {str(e)}",
                metadata=base_metadata
            )]

    def _split_into_sections(self, text: str, base_metadata: Dict[str, Any]) -> List[ParsedDocument]:
        """Split markdown text into logical sections."""
        documents = []

        # Split by headers (markdown style)
        sections = re.split(r'\n(?=#{1,6}\s)', text)

        if len(sections) <= 1:
            # No clear sections, split by paragraphs to avoid huge documents
            # 按段落分割，避免产生超大的单个文档
            paragraphs = self._split_by_paragraphs(text)
            documents = []

            for idx, paragraph in enumerate(paragraphs):
                if not paragraph.strip():
                    continue

                metadata = base_metadata.copy()
                metadata.update({
                    'chunk_type': 'pdf_paragraph',
                    'chunk_id': f"para_{idx}",
                    'section_number': idx + 1
                })

                documents.append(ParsedDocument(content=paragraph.strip(), metadata=metadata))

            return documents if documents else [ParsedDocument(
                content=text.strip(),
                metadata={**base_metadata, 'chunk_type': 'pdf_paragraph', 'chunk_id': 'single'}
            )]

        # Process each section
        for idx, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue

            # Extract section title if available
            lines = section.split('\n')
            title = ""
            if lines and lines[0].startswith('#'):
                title = re.sub(r'^#+\s*', '', lines[0]).strip()

            metadata = base_metadata.copy()
            metadata.update({
                'chunk_type': 'pdf_section',
                'chunk_id': f"section_{idx}",
                'section_number': idx + 1,
                'section_title': title,
                'has_title': bool(title)
            })

            documents.append(ParsedDocument(content=section, metadata=metadata))

        return documents

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """Split text by paragraphs to avoid huge document blocks."""
        # Split by double newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', text)

        # Filter out empty paragraphs and clean
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        # If still too few paragraphs, split by single newlines
        if len(paragraphs) <= 2 and len(text) > 2000:
            paragraphs = text.split('\n')
            paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs
