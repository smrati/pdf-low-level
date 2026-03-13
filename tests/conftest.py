"""
Shared fixtures for pdf-lowlevel tests.

Provides sample PDFs, test data, and common utilities.
"""

import pytest
from io import BytesIO
from typing import BinaryIO


# ============================================================================
# Minimal PDF Fixtures - Created with correct byte offsets
# ============================================================================

def _create_minimal_pdf() -> bytes:
    """Create a minimal valid PDF with correct byte offsets."""
    lines = [
        b"%PDF-1.4",
        b"1 0 obj",
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"endobj",
        b"2 0 obj",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"endobj",
        b"3 0 obj",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>",
        b"endobj",
    ]
    
    # Calculate offsets
    content = b"\n".join(lines) + b"\n"
    xref_offset = len(content)
    
    # Build xref table
    # Object 0 is always free at offset 0 with gen 65535
    # Objects 1, 2, 3 start at their respective line offsets
    offsets = {}
    current_offset = 0
    for i, line in enumerate(lines):
        if line.startswith(b"1 0 obj"):
            offsets[1] = current_offset
        elif line.startswith(b"2 0 obj"):
            offsets[2] = current_offset
        elif line.startswith(b"3 0 obj"):
            offsets[3] = current_offset
        current_offset += len(line) + 1  # +1 for newline
    
    xref_lines = [
        b"xref",
        b"0 4",
        b"0000000000 65535 f ",
        f"{offsets[1]:010d} 00000 n ".encode(),
        f"{offsets[2]:010d} 00000 n ".encode(),
        f"{offsets[3]:010d} 00000 n ".encode(),
        b"trailer",
        b"<< /Root 1 0 R /Size 4 >>",
        b"startxref",
        str(xref_offset).encode(),
        b"%%EOF",
    ]
    
    return content + b"\n".join(xref_lines) + b"\n"


def _create_text_pdf() -> bytes:
    """Create a PDF with simple text content."""
    lines = [
        b"%PDF-1.4",
        b"1 0 obj",
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"endobj",
        b"2 0 obj",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"endobj",
        b"3 0 obj",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]",
        b"   /Resources << /Font << /F1 4 0 R >> >>",
        b"   /Contents 5 0 R",
        b">>",
        b"endobj",
        b"4 0 obj",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica",
        b"   /Encoding /WinAnsiEncoding",
        b">>",
        b"endobj",
        b"5 0 obj",
        b"<< /Length 44 >>",
        b"stream",
        b"BT",
        b"/F1 12 Tf",
        b"72 720 Td",
        b"(Hello, World!) Tj",
        b"ET",
        b"endstream",
        b"endobj",
    ]
    
    content = b"\n".join(lines) + b"\n"
    xref_offset = len(content)
    
    # Calculate offsets for objects
    offsets = {}
    current_offset = 0
    for line in lines:
        for obj_num in [1, 2, 3, 4, 5]:
            if line.startswith(f"{obj_num} 0 obj".encode()):
                offsets[obj_num] = current_offset
        current_offset += len(line) + 1
    
    xref_lines = [
        b"xref",
        b"0 6",
        b"0000000000 65535 f ",
        f"{offsets[1]:010d} 00000 n ".encode(),
        f"{offsets[2]:010d} 00000 n ".encode(),
        f"{offsets[3]:010d} 00000 n ".encode(),
        f"{offsets[4]:010d} 00000 n ".encode(),
        f"{offsets[5]:010d} 00000 n ".encode(),
        b"trailer",
        b"<< /Root 1 0 R /Size 6 >>",
        b"startxref",
        str(xref_offset).encode(),
        b"%%EOF",
    ]
    
    return content + b"\n".join(xref_lines) + b"\n"


def _create_multi_page_pdf() -> bytes:
    """Create a PDF with 3 pages."""
    lines = [
        b"%PDF-1.4",
        b"1 0 obj",
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"endobj",
        b"2 0 obj",
        b"<< /Type /Pages /Kids [3 0 R 4 0 R 5 0 R] /Count 3 >>",
        b"endobj",
        b"3 0 obj",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>",
        b"endobj",
        b"4 0 obj",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>",
        b"endobj",
        b"5 0 obj",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>",
        b"endobj",
    ]
    
    content = b"\n".join(lines) + b"\n"
    xref_offset = len(content)
    
    offsets = {}
    current_offset = 0
    for line in lines:
        for obj_num in [1, 2, 3, 4, 5]:
            if line.startswith(f"{obj_num} 0 obj".encode()):
                offsets[obj_num] = current_offset
        current_offset += len(line) + 1
    
    xref_lines = [
        b"xref",
        b"0 6",
        b"0000000000 65535 f ",
        f"{offsets[1]:010d} 00000 n ".encode(),
        f"{offsets[2]:010d} 00000 n ".encode(),
        f"{offsets[3]:010d} 00000 n ".encode(),
        f"{offsets[4]:010d} 00000 n ".encode(),
        f"{offsets[5]:010d} 00000 n ".encode(),
        b"trailer",
        b"<< /Root 1 0 R /Size 6 >>",
        b"startxref",
        str(xref_offset).encode(),
        b"%%EOF",
    ]
    
    return content + b"\n".join(xref_lines) + b"\n"


def _create_indirect_ref_pdf() -> bytes:
    """Create a PDF with Info dictionary (indirect reference in trailer)."""
    lines = [
        b"%PDF-1.4",
        b"1 0 obj",
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"endobj",
        b"2 0 obj",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"endobj",
        b"3 0 obj",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>",
        b"endobj",
        b"4 0 obj",
        b"<< /Title (Test Document) /Author (Test Author) >>",
        b"endobj",
    ]
    
    content = b"\n".join(lines) + b"\n"
    xref_offset = len(content)
    
    offsets = {}
    current_offset = 0
    for line in lines:
        for obj_num in [1, 2, 3, 4]:
            if line.startswith(f"{obj_num} 0 obj".encode()):
                offsets[obj_num] = current_offset
        current_offset += len(line) + 1
    
    xref_lines = [
        b"xref",
        b"0 5",
        b"0000000000 65535 f ",
        f"{offsets[1]:010d} 00000 n ".encode(),
        f"{offsets[2]:010d} 00000 n ".encode(),
        f"{offsets[3]:010d} 00000 n ".encode(),
        f"{offsets[4]:010d} 00000 n ".encode(),
        b"trailer",
        b"<< /Root 1 0 R /Info 4 0 R /Size 5 >>",
        b"startxref",
        str(xref_offset).encode(),
        b"%%EOF",
    ]
    
    return content + b"\n".join(xref_lines) + b"\n"


# ============================================================================
# PDF Fixtures
# ============================================================================


@pytest.fixture
def minimal_pdf_bytes() -> bytes:
    """A minimal valid PDF file with no pages content."""
    return _create_minimal_pdf()


@pytest.fixture
def minimal_pdf(minimal_pdf_bytes) -> BinaryIO:
    """Minimal PDF as a file-like object."""
    return BytesIO(minimal_pdf_bytes)


@pytest.fixture
def text_pdf_bytes() -> bytes:
    """A PDF with simple text content."""
    return _create_text_pdf()


@pytest.fixture
def text_pdf(text_pdf_bytes) -> BinaryIO:
    """PDF with text content as a file-like object."""
    return BytesIO(text_pdf_bytes)


@pytest.fixture
def multi_page_pdf_bytes() -> bytes:
    """A PDF with 3 pages."""
    return _create_multi_page_pdf()


@pytest.fixture
def multi_page_pdf(multi_page_pdf_bytes) -> BinaryIO:
    """Multi-page PDF as a file-like object."""
    return BytesIO(multi_page_pdf_bytes)


@pytest.fixture
def indirect_ref_pdf_bytes() -> bytes:
    """A PDF with multiple indirect references in trailer."""
    return _create_indirect_ref_pdf()


@pytest.fixture
def indirect_ref_pdf(indirect_ref_pdf_bytes) -> BinaryIO:
    """PDF with indirect references as a file-like object."""
    return BytesIO(indirect_ref_pdf_bytes)


# ============================================================================
# Invalid/Error PDF Fixtures
# ============================================================================


@pytest.fixture
def invalid_pdf_bytes() -> bytes:
    """Invalid PDF content (not a PDF)."""
    return b"This is not a PDF file"


@pytest.fixture
def empty_pdf_bytes() -> bytes:
    """Empty file."""
    return b""


@pytest.fixture
def truncated_pdf_bytes() -> bytes:
    """Truncated PDF (missing EOF)."""
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog >>
endobj
"""


# ============================================================================
# Tokenizer Test Data
# ============================================================================


@pytest.fixture
def tokenizer_test_cases():
    """Test cases for tokenizer."""
    return {
        "integers": [
            (b"123", "INTEGER", 123),
            (b"0", "INTEGER", 0),
            (b"-42", "INTEGER", -42),
            (b"+99", "INTEGER", 99),
        ],
        "reals": [
            (b"3.14", "REAL", 3.14),
            (b"-0.5", "REAL", -0.5),
            (b"12.0", "REAL", 12.0),
        ],
        "names": [
            (b"/Name", "NAME", "Name"),
            (b"/Type", "NAME", "Type"),
            (b"/Helvetica", "NAME", "Helvetica"),
            (b"/A;Name_With-Various***Chars", "NAME", "A;Name_With-Various***Chars"),
        ],
        "strings": [
            (b"(Hello)", "STRING", b"Hello"),
            (b"(Hello World)", "STRING", b"Hello World"),
            (b"(())", "STRING", b"()"),  # Nested parens
        ],
        "hex_strings": [
            (b"<48656C6C6F>", "HEX_STRING", b"Hello"),
            (b"<00>", "HEX_STRING", b"\x00"),
        ],
        "booleans": [
            (b"true", "BOOLEAN", True),
            (b"false", "BOOLEAN", False),
        ],
        "null": [
            (b"null", "NULL", None),
        ],
    }


# ============================================================================
# Utility Fixtures
# ============================================================================


@pytest.fixture
def suppress_logging():
    """Suppress loguru logging during tests."""
    from pdf_lowlevel.logger import logger

    # Remove existing handlers and add null handler
    logger.remove()
    logger.add(
        lambda msg: None,
        level="CRITICAL",
    )
    yield
    # Restore default logging
    logger.remove()
    import sys
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
    )