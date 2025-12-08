# app/utils/text_chunker.py

from typing import List, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.models.document_chunk import DocumentChunk
import uuid


def chunk_text_for_embeddings(
    text: str,
    chunk_size: int = 100,
    chunk_overlap: int = 50,
    separators: Optional[List[str]] = None,
    metadata: Optional[dict] = None
) -> List[DocumentChunk]:
    """
    Split raw text into semantic chunks and return DocumentChunk models.
    """

    if separators is None:
        separators = ["\n\n", "\n", ".", "?", "!"]

    splitter = RecursiveCharacterTextSplitter(
        separators=separators,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    raw_chunks = splitter.split_text(text)

    document_chunks = []
    for chunk in raw_chunks:
        document_chunks.append(
            DocumentChunk(
                id=str(uuid.uuid4()),
                content=chunk,
                metadata=metadata or {}
            )
        )

    return document_chunks
