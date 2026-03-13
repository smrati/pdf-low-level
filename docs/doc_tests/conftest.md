# Test Fixtures (conftest.py)

This document describes the shared fixtures and test utilities defined in `tests/conftest.py`.

## Overview

The `conftest.py` file provides:
- Dynamically generated PDF files for testing
- Test data for tokenizer tests
- Utility fixtures for logging suppression

## PDF Generator Functions

### _create_minimal_pdf()

Creates a minimal valid PDF with no page content.

**Structure:**
```
%PDF-1.4
1 0 obj  << /Type /Catalog /Pages 2 0 R >>  endobj
2 0 obj  << /Type /Pages /Kids [3 0 R] /Count 1 >>  endobj
3 0 obj  << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>  endobj
xref
0 4
0000000000 65535 f 
000000nnnn 00000 n  (object 1 offset)
000000nnnn 00000 n  (object 2 offset)
000000nnnn 00000 n  (object 3 offset)
trailer
<< /Root 1 0 R /Size 4 >>
startxref
nnn
%%EOF
```

**Returns:** `bytes` - Minimal valid PDF

### _create_text_pdf()

Creates a PDF with simple text content ("Hello, World!").

**Structure:**
```
%PDF-1.4
1 0 obj  << /Type /Catalog /Pages 2 0 R >>  endobj
2 0 obj  << /Type /Pages /Kids [3 0 R] /Count 1 >>  endobj
3 0 obj  << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
          /Resources << /Font << /F1 4 0 R >> >>
          /Contents 5 0 R >>  endobj
4 0 obj  << /Type /Font /Subtype /Type1 /BaseFont /Helvetica
          /Encoding /WinAnsiEncoding >>  endobj
5 0 obj  << /Length 44 >>
stream
BT
/F1 12 Tf
72 720 Td
(Hello, World!) Tj
ET
endstream
endobj
xref + trailer
```

**Returns:** `bytes` - PDF with text content

### _create_multi_page_pdf()

Creates a PDF with 3 empty pages.

**Structure:**
```
%PDF-1.4
1 0 obj  << /Type /Catalog /Pages 2 0 R >>  endobj
2 0 obj  << /Type /Pages /Kids [3 0 R 4 0 R 5 0 R] /Count 3 >>  endobj
3 0 obj  << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>  endobj
4 0 obj  << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>  endobj
5 0 obj  << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>  endobj
xref + trailer
```

**Returns:** `bytes` - 3-page PDF

### _create_indirect_ref_pdf()

Creates a PDF with Info dictionary (indirect reference in trailer).

**Structure:**
```
%PDF-1.4
1 0 obj  << /Type /Catalog /Pages 2 0 R >>  endobj
2 0 obj  << /Type /Pages /Kids [3 0 R] /Count 1 >>  endobj
3 0 obj  << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>  endobj
4 0 obj  << /Title (Test Document) /Author (Test Author) >>  endobj
xref
trailer
<< /Root 1 0 R /Info 4 0 R /Size 5 >>
startxref
%%EOF
```

**Returns:** `bytes` - PDF with indirect references

## PDF Fixtures

### Bytes Fixtures

| Fixture | Type | Description |
|---------|------|-------------|
| `minimal_pdf_bytes` | `bytes` | Minimal valid PDF |
| `text_pdf_bytes` | `bytes` | PDF with text content |
| `multi_page_pdf_bytes` | `bytes` | 3-page PDF |
| `indirect_ref_pdf_bytes` | `bytes` | PDF with Info dict |

### File-like Object Fixtures

| Fixture | Type | Description |
|---------|------|-------------|
| `minimal_pdf` | `BinaryIO` | Minimal PDF as BytesIO |
| `text_pdf` | `BinaryIO` | Text PDF as BytesIO |
| `multi_page_pdf` | `BinaryIO` | Multi-page PDF as BytesIO |
| `indirect_ref_pdf` | `BinaryIO` | Indirect ref PDF as BytesIO |

## Error Case Fixtures

| Fixture | Type | Description |
|---------|------|-------------|
| `invalid_pdf_bytes` | `bytes` | "This is not a PDF file" |
| `empty_pdf_bytes` | `bytes` | Empty byte string `b""` |
| `truncated_pdf_bytes` | `bytes` | PDF missing EOF marker |

## Tokenizer Test Data

### tokenizer_test_cases

Dictionary of test cases for tokenizer:

```python
@pytest.fixture
def tokenizer_test_cases():
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
        ],
        "strings": [
            (b"(Hello)", "STRING", b"Hello"),
            (b"(Hello World)", "STRING", b"Hello World"),
            (b"(())", "STRING", b"()"),
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
```

## Utility Fixtures

### suppress_logging

Suppresses loguru logging during tests.

```python
@pytest.fixture
def suppress_logging():
    """Suppress loguru logging during tests."""
    from pdf_lowlevel.logger import logger

    logger.remove()
    logger.add(lambda msg: None, level="CRITICAL")
    yield
    # Restore default logging
    logger.remove()
    import sys
    logger.add(sys.stderr, format="...", level="INFO", colorize=True)
```

## Byte Offset Calculation

The PDF generators calculate byte offsets for the xref table:

```python
def _create_minimal_pdf() -> bytes:
    lines = [
        b"%PDF-1.4",
        b"1 0 obj",
        # ...
    ]
    
    content = b"\n".join(lines) + b"\n"
    
    # Calculate offsets for each object
    offsets = {}
    current_offset = 0
    for line in lines:
        if line.startswith(b"1 0 obj"):
            offsets[1] = current_offset
        # ...
        current_offset += len(line) + 1  # +1 for newline
    
    # Build xref with calculated offsets
    xref_lines = [
        b"xref",
        b"0 4",
        b"0000000000 65535 f ",
        f"{offsets[1]:010d} 00000 n ".encode(),
        # ...
    ]
```

**Important:** Offsets must be exact byte positions for the PDF to be valid.

## Usage Examples

### Using Fixtures in Tests

```python
def test_with_bytes_fixture(minimal_pdf_bytes):
    """Using bytes fixture."""
    reader = PDFReader(minimal_pdf_bytes)
    reader.read()
    assert reader.page_count == 1

def test_with_file_like_fixture(minimal_pdf):
    """Using file-like fixture."""
    reader = PDFReader(minimal_pdf)
    reader.read()
    # minimal_pdf is a BytesIO object

def test_with_test_cases(tokenizer_test_cases):
    """Using tokenizer test cases."""
    for input_bytes, expected_type, expected_value in tokenizer_test_cases["integers"]:
        tokenizer = PDFTokenizer(input_bytes)
        token = tokenizer.next_token()
        assert token.type.name == expected_type
        assert token.value == expected_value
```

## Adding New Fixtures

To add a new PDF fixture:

1. **Create generator function** `_create_xxx_pdf()`
2. **Calculate byte offsets** correctly
3. **Add bytes fixture**:
   ```python
   @pytest.fixture
   def xxx_pdf_bytes() -> bytes:
       return _create_xxx_pdf()
   ```
4. **Add file-like fixture**:
   ```python
   @pytest.fixture
   def xxx_pdf(xxx_pdf_bytes) -> BinaryIO:
       return BytesIO(xxx_pdf_bytes)