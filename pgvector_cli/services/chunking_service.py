"""Text chunking service for RAG applications."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List

from .parsers.base_parser import ParsedDocument


@dataclass
class TextChunk:
    """Represents a text chunk with metadata."""
    content: str
    metadata: Dict[str, Any]
    chunk_index: int
    total_chunks: int


class ChunkingService:
    """Service for chunking text content for RAG applications."""

    def __init__(self, chunk_size: int = 500, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_documents(self, documents: List[ParsedDocument]) -> List[TextChunk]:
        """Chunk a list of parsed documents."""
        all_chunks = []
        global_chunk_index = 0

        for doc in documents:
            # 强制所有文档类型都按照用户设置的chunk_size进行分块
            # 不再根据chunk_type进行特殊处理，严格遵守用户设置
            chunks = self._chunk_text_content(doc, global_chunk_index)

            all_chunks.extend(chunks)
            global_chunk_index += len(chunks)

        # Update total chunks count
        for chunk in all_chunks:
            chunk.total_chunks = len(all_chunks)

        return all_chunks


    def _chunk_text_content(self, document: ParsedDocument, start_index: int) -> List[TextChunk]:
        """Apply fixed-size chunking with overlap to text content."""
        text = document.content.strip()

        # 如果文本为空，跳过
        if not text:
            return []

        if len(text) <= self.chunk_size:
            # Text is smaller than chunk size, return as single chunk
            metadata = document.metadata.copy()
            metadata.update({
                'chunking_method': 'single_chunk',
                'original_length': len(text),
                'chunk_length': len(text)
            })

            return [TextChunk(
                content=text,
                metadata=metadata,
                chunk_index=start_index,
                total_chunks=1
            )]

        # Text is larger than chunk_size, must apply sliding window chunking
        # 这里强制对所有超过chunk_size的文本进行分块
        return self._sliding_window_chunk(document, start_index)

    def _sliding_window_chunk(self, document: ParsedDocument, start_index: int) -> List[TextChunk]:
        """Apply sliding window chunking with overlap."""
        text = document.content
        chunks = []

        # Split text into sentences for better chunk boundaries
        sentences = self._split_into_sentences(text)

        if not sentences:
            return [self._create_single_chunk(document, start_index)]

        current_length = 0
        chunk_sentences = []
        chunk_index = 0

        for _i, sentence in enumerate(sentences):
            sentence_length = len(sentence)

            # If adding this sentence would exceed chunk_size, create a chunk
            # 修复核心Bug：检查chunk_sentences而不是current_chunk
            if current_length + sentence_length > self.chunk_size and chunk_sentences:
                # Create chunk
                chunk_content = " ".join(chunk_sentences)
                chunks.append(self._create_chunk_from_content(
                    chunk_content,
                    document,
                    start_index + chunk_index,
                    chunk_index
                ))
                chunk_index += 1

                # Prepare next chunk with overlap
                overlap_sentences = self._get_overlap_sentences(chunk_sentences)
                current_length = len(" ".join(overlap_sentences))
                chunk_sentences = overlap_sentences.copy()

            # Add current sentence
            chunk_sentences.append(sentence)
            current_length += sentence_length + (1 if chunk_sentences and len(chunk_sentences) > 1 else 0)  # +1 for space

        # Add final chunk if there's remaining content
        if chunk_sentences:
            chunk_content = " ".join(chunk_sentences)
            chunks.append(self._create_chunk_from_content(
                chunk_content,
                document,
                start_index + chunk_index,
                chunk_index
            ))

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for better chunking boundaries."""
        # 支持中英文标点符号的句子分割
        sentences = re.split(r'(?<=[.!?。！？])\s*', text)

        # Filter out empty sentences and clean
        sentences = [s.strip() for s in sentences if s.strip()]

        # Handle cases where sentences are too long
        final_sentences = []
        for sentence in sentences:
            if len(sentence) > self.chunk_size:  # If sentence is longer than chunk_size
                # First try to split by punctuation marks
                parts = re.split(r'[,;:]\s+', sentence)

                # If still too long after punctuation splitting, force split by character count
                processed_parts = []
                for part in parts:
                    if len(part) > self.chunk_size:
                        # Force split into chunk_size pieces
                        for i in range(0, len(part), self.chunk_size):
                            processed_parts.append(part[i:i + self.chunk_size])
                    else:
                        processed_parts.append(part)

                final_sentences.extend([p.strip() for p in processed_parts if p.strip()])
            else:
                final_sentences.append(sentence)

        return final_sentences

    def _create_single_chunk(self, document: ParsedDocument, start_index: int) -> TextChunk:
        """Create a single chunk from the entire document content."""
        content = document.content.strip()

        # 保护机制：如果内容过长，强制分割
        if len(content) > 8000:
            content = content[:8000]
            metadata = document.metadata.copy()
            metadata.update({
                'chunking_method': 'single_chunk_truncated',
                'original_length': len(document.content),
                'chunk_length': len(content),
                'fallback_reason': 'no_sentences_detected',
                'truncation_warning': 'Content was truncated to fit API limits'
            })
        else:
            metadata = document.metadata.copy()
            metadata.update({
                'chunking_method': 'single_chunk_fallback',
                'original_length': len(document.content),
                'chunk_length': len(content),
                'fallback_reason': 'no_sentences_detected'
            })

        return TextChunk(
            content=content,
            metadata=metadata,
            chunk_index=start_index,
            total_chunks=1
        )

    def _get_overlap_sentences(self, sentences: List[str]) -> List[str]:
        """Get sentences for overlap based on overlap size."""
        if not sentences:
            return []

        # Calculate how many sentences to include for overlap
        overlap_text = ""
        overlap_sentences = []

        # Start from the end and work backwards
        for sentence in reversed(sentences):
            if len(overlap_text) + len(sentence) <= self.overlap:
                overlap_sentences.insert(0, sentence)
                overlap_text = " ".join(overlap_sentences)
            else:
                break

        return overlap_sentences

    def _create_chunk_from_content(self, content: str, original_doc: ParsedDocument,
                                 global_index: int, local_index: int) -> TextChunk:
        """Create a TextChunk from content and metadata."""
        # 关键保护机制：确保内容不超过API限制
        content = content.strip()
        if len(content) > 8000:  # 留出安全余量，避免接近8192限制
            # 强制分割超长内容
            content = content[:8000]
            metadata = original_doc.metadata.copy()
            metadata.update({
                'chunking_method': 'force_truncated',
                'chunk_size': self.chunk_size,
                'overlap_size': self.overlap,
                'local_chunk_index': local_index,
                'original_length': len(original_doc.content),
                'chunk_length': len(content),
                'truncation_warning': 'Content was truncated to fit API limits'
            })
        else:
            metadata = original_doc.metadata.copy()
            metadata.update({
                'chunking_method': 'sliding_window',
                'chunk_size': self.chunk_size,
                'overlap_size': self.overlap,
                'local_chunk_index': local_index,
                'original_length': len(original_doc.content),
                'chunk_length': len(content)
            })

        return TextChunk(
            content=content,
            metadata=metadata,
            chunk_index=global_index,
            total_chunks=1  # Will be updated later
        )
