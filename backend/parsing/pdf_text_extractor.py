"""PDF text extraction service using PyMuPDF (fitz)."""

from __future__ import annotations

import logging
from pathlib import Path
import fitz  # PyMuPDF

from backend.domain.exceptions.parsing_exceptions import DocumentParsingError
from backend.utils.text_cleaning import clean_extracted_text

logger = logging.getLogger(__name__)


def extract_text(pdf_path: str | Path) -> str:
    """Extract text page-by-page from a PDF file using PyMuPDF (fitz).

    Preserves paragraph spacing by extracting text in blocks, removes unnecessary
    whitespace, and returns a single cleaned text string. Handles and logs errors
    robustly.

    Args:
        pdf_path: Absolute or relative path to the PDF file.

    Returns:
        The extracted and cleaned plain text string.

    Raises:
        DocumentParsingError: If the PDF cannot be opened or parsed.
    """
    path_str = str(pdf_path)
    logger.info("Starting PDF text extraction for: %s", path_str)

    try:
        doc = fitz.open(path_str)
    except Exception as exc:
        logger.error("Failed to open PDF file %s: %s", path_str, exc)
        raise DocumentParsingError(f"Failed to open PDF file: {exc}") from exc

    try:
        pages_text = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Extract text blocks to help preserve paragraph layout and boundaries.
            # Each block: (x0, y0, x1, y1, "text", block_no, block_type)
            blocks = page.get_text("blocks")
            
            page_blocks = []
            for block in blocks:
                # block_type 0 is text
                if block[6] == 0:
                    text_content = block[4].strip()
                    if text_content:
                        page_blocks.append(text_content)
            
            # Join blocks with double newline to preserve paragraph spacing on the page
            page_text = "\n\n".join(page_blocks)
            pages_text.append(page_text)
            
        # Join all pages with double newline
        full_text = "\n\n".join(pages_text)
        
        # Clean the extracted text using the shared cleaner helper
        cleaned_text = clean_extracted_text(full_text)
        
        logger.info(
            "Successfully extracted text from %s. Total length: %d chars.",
            path_str,
            len(cleaned_text),
        )
        return cleaned_text
    except Exception as exc:
        logger.error("Failed to parse text blocks from PDF file %s: %s", path_str, exc)
        raise DocumentParsingError(f"Failed to parse PDF content: {exc}") from exc
    finally:
        doc.close()
