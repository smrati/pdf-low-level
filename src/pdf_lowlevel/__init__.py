"""
PDF Low-Level: A low-level PDF parser with layout-aware text extraction.

This library provides tools to parse PDF files at a low level, extracting
text with accurate positioning information for layout analysis.
"""

__version__ = "0.1.0"

from pdf_lowlevel.extract import (
    ExtractionResult,
    PageResult,
    PDFExtractor,
    extract_json,
    extract_text,
)
from pdf_lowlevel.content.stream import TextElement
from pdf_lowlevel.logger import logger, configure_logger

__all__ = [
    "PDFExtractor",
    "ExtractionResult",
    "PageResult",
    "TextElement",
    "extract_text",
    "extract_json",
    "logger",
    "configure_logger",
    "__version__",
]
