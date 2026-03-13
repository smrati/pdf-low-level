"""
PDF Parser Package.

Low-level PDF parsing components.
"""

from pdf_lowlevel.parser.objects import (
    PDFIndirectObject,
    PDFIndirectRef,
    PDFName,
    PDFObject,
    PDFObjectType,
    PDFStream,
    PDFNames,
)
from pdf_lowlevel.parser.reader import PDFParseError, PDFReader, open_pdf
from pdf_lowlevel.parser.tokenizer import PDFTokenizer, Token, TokenType, tokenize_pdf
from pdf_lowlevel.parser.xref import XRefEntry, XRefTable, XRefParser, parse_xref

__all__ = [
    # Objects
    "PDFObjectType",
    "PDFIndirectRef",
    "PDFIndirectObject",
    "PDFStream",
    "PDFObject",
    "PDFName",
    "PDFNames",
    # Tokenizer
    "PDFTokenizer",
    "Token",
    "TokenType",
    "tokenize_pdf",
    # XRef
    "XRefEntry",
    "XRefTable",
    "XRefParser",
    "parse_xref",
    # Reader
    "PDFParseError",
    "PDFReader",
    "open_pdf",
]