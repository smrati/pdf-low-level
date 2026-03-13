# PDF Low-Level

A low-level PDF parser with layout-aware text extraction. This library parses PDF files at the syntax level to extract text with accurate positioning information, enabling better layout analysis and content understanding.

## Why Low-Level?

Most PDF libraries hide the complexity of PDF parsing, but they also hide the information needed for accurate layout extraction. By parsing at a low level, we preserve:

- **Text positions** - Exact x,y coordinates of every character
- **Font information** - Font names, sizes, and character widths
- **Graphics state** - Transformation matrices and text state
- **Structure** - Reading order and content stream structure

## Installation

### For Users

```bash
# Using pip
pip install pdf-lowlevel

# Using uv
uv pip install pdf-lowlevel
```

### For Developers

```bash
# Clone the repository
git clone https://github.com/your-repo/pdf-lowlevel.git
cd pdf-lowlevel

# Install with dev dependencies
uv sync --all-extras

# Activate the virtual environment
source .venv/bin/activate
```

## Quick Start

```python
from pdf_lowlevel import PDFExtractor, extract_text, extract_json

# Simple text extraction
text = extract_text("document.pdf")
print(text)

# Get JSON with positions
json_output = extract_json("document.pdf")
print(json_output)

# Full control with PDFExtractor
with PDFExtractor("document.pdf") as extractor:
    result = extractor.extract()
    
    for page in result.pages:
        print(f"Page {page.page_number}: {page.width}x{page.height}")
        for element in page.elements:
            print(f"  Text at ({element.x:.1f}, {element.y:.1f}): {element.text}")
```

## Configuration & Settings

The library provides several configuration options to customize extraction behavior and logging.

### Logging Configuration

Control the verbosity of the library using the `configure_logger` function:

```python
from pdf_lowlevel import configure_logger, PDFExtractor

# Enable debug logging to see detailed extraction progress
configure_logger(level="DEBUG")

# Set logging to WARNING to suppress info messages
configure_logger(level="WARNING")

# Log to a file instead of console
configure_logger(level="DEBUG", sink="extraction.log")

# Custom log format
configure_logger(
    level="INFO",
    format="{time} | {level} | {message}"
)
```

#### Log Levels

| Level | Description |
|-------|-------------|
| `DEBUG` | Detailed parsing info, token positions, font loading |
| `INFO` | Extraction progress, page counts, completion status |
| `WARNING` | Non-critical issues, fallback behaviors |
| `ERROR` | Parsing errors, missing objects |
| `CRITICAL` | Fatal errors |

### Extraction Options

The `PDFExtractor.extract()` method accepts several parameters:

```python
from pdf_lowlevel import PDFExtractor

with PDFExtractor("document.pdf") as extractor:
    result = extractor.extract(
        start_page=0,        # First page to extract (0-indexed)
        end_page=5,          # Last page (exclusive). None = all pages
        include_metadata=True  # Include document metadata
    )
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_page` | int | `0` | First page to extract (0-indexed) |
| `end_page` | int \| None | `None` | Last page (exclusive). `None` extracts all pages |
| `include_metadata` | bool | `True` | Whether to extract document metadata (Title, Author, etc.) |

### Page-Specific Extraction

Extract text from specific pages only:

```python
# Extract only first 3 pages
result = extractor.extract(end_page=3)

# Extract pages 5-10 (0-indexed: pages 5, 6, 7, 8, 9)
result = extractor.extract(start_page=5, end_page=10)

# Extract single page (page 3, 0-indexed)
result = extractor.extract(start_page=3, end_page=4)
```

### Convenience Functions

For quick extraction without fine-grained control:

```python
from pdf_lowlevel import extract_text, extract_json

# Plain text only
text = extract_text("document.pdf")

# JSON with all position data
json_str = extract_json("document.pdf")

# JSON for specific pages
json_str = extract_json("document.pdf", start_page=0, end_page=5)
```

### Accessing Raw Results

The `ExtractionResult` object provides structured access to all data:

```python
from pdf_lowlevel import PDFExtractor

with PDFExtractor("document.pdf") as extractor:
    result = extractor.extract()
    
    # Document info
    print(f"File: {result.filename}")
    print(f"Pages: {result.page_count}")
    
    # Metadata
    title = result.metadata.get("Title", "Unknown")
    author = result.metadata.get("Author", "Unknown")
    
    # Iterate pages
    for page in result.pages:
        print(f"\nPage {page.page_number}: {page.width}x{page.height}")
        
        # Iterate text elements
        for element in page.elements:
            print(f"  [{element.x:.1f}, {element.y:.1f}] {element.text}")
    
    # Export options
    json_str = result.to_json(indent=4)    # Pretty JSON
    plain_text = result.get_all_text()      # All text as string
    data_dict = result.to_dict()            # Python dictionary
```

### Working with Text Elements

Each `TextElement` contains detailed positioning and font information:

```python
for element in page.elements:
    # Text content
    text = element.text
    
    # Position (user space coordinates)
    x, y = element.x, element.y
    
    # Bounding box [x0, y0, x1, y1]
    bbox = element.bbox
    
    # Font info
    font_name = element.font_name
    font_size = element.font_size
    
    # Dimensions
    width = element.width
    height = element.height
    
    # Page location
    page_num = element.page_number
```

### Handling Different Input Types

The library accepts multiple input formats:

```python
# File path (string)
extractor = PDFExtractor("/path/to/document.pdf")

# Path object
from pathlib import Path
extractor = PDFExtractor(Path("document.pdf"))

# File-like object (open file)
with open("document.pdf", "rb") as f:
    extractor = PDFExtractor(f)

# Raw bytes
with open("document.pdf", "rb") as f:
    pdf_bytes = f.read()
extractor = PDFExtractor(pdf_bytes)
```

### Error Handling

```python
from pdf_lowlevel import PDFExtractor
from pdf_lowlevel.parser.reader import PDFParseError

try:
    with PDFExtractor("document.pdf") as extractor:
        result = extractor.extract()
except FileNotFoundError:
    print("File not found")
except PDFParseError as e:
    print(f"PDF parsing error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Memory Management

For large PDFs, use the context manager to ensure proper cleanup:

```python
# Recommended: Use context manager
with PDFExtractor("large.pdf") as extractor:
    result = extractor.extract()
# File handle automatically closed

# Manual cleanup (if not using context manager)
extractor = PDFExtractor("large.pdf")
result = extractor.extract()
extractor.close()  # Don't forget to close!
```

### Integration Examples

#### Filter by Font Size

```python
result = extractor.extract()

# Get only headlines (larger fonts)
headlines = []
for page in result.pages:
    for element in page.elements:
        if element.font_size >= 18:
            headlines.append(element.text)
```

#### Group by Y-Position (Lines)

```python
from collections import defaultdict

result = extractor.extract()

# Group elements by Y coordinate (with tolerance)
lines = defaultdict(list)
for element in result.elements:
    y_rounded = round(element.y / 5) * 5  # 5pt tolerance
    lines[y_rounded].append(element)

# Sort each line by X position and print
for y in sorted(lines.keys(), reverse=True):  # Top to bottom
    line_elements = sorted(lines[y], key=lambda e: e.x)
    line_text = " ".join(e.text for e in line_elements)
    print(line_text)
```

## Output Format

### JSON Structure

```json
{
  "filename": "document.pdf",
  "page_count": 5,
  "pages": [
    {
      "page_number": 1,
      "width": 612,
      "height": 792,
      "elements": [
        {
          "text": "Hello, World!",
          "x": 72.0,
          "y": 720.0,
          "width": 85.5,
          "height": 12.0,
          "bbox": [72.0, 720.0, 157.5, 732.0],
          "font_name": "Helvetica",
          "font_size": 12.0
        }
      ]
    }
  ],
  "metadata": {
    "Title": "Sample Document",
    "Author": "John Doe"
  }
}
```

### TextElement Fields

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | The extracted text content |
| `x` | float | X coordinate (left edge) in user space |
| `y` | float | Y coordinate (baseline) in user space |
| `width` | float | Width of the text |
| `height` | float | Height of the text (font size) |
| `bbox` | [float, float, float, float] | Bounding box [x0, y0, x1, y1] |
| `font_name` | string | Name of the font |
| `font_size` | float | Font size in points |
| `page_number` | int | Page number (1-indexed) |

## Architecture

The library is organized into several layers:

```
src/pdf_lowlevel/
├── parser/           # Low-level PDF parsing
│   ├── tokenizer.py  # Tokenize PDF syntax
│   ├── objects.py    # PDF object types
│   ├── xref.py       # Cross-reference table
│   └── reader.py     # Main PDF reader
├── content/          # Content stream parsing
│   ├── graphics.py   # Graphics state machine
│   └── stream.py     # Content stream interpreter
├── fonts/            # Font handling
│   └── encoding.py   # Character encoding
└── extract.py        # High-level extraction API
```

### Parsing Pipeline

1. **Tokenizer** - Converts PDF bytes to tokens (numbers, strings, names, etc.)
2. **Object Parser** - Parses tokens into PDF objects (dictionaries, arrays, streams)
3. **XRef Table** - Locates objects by their byte offset
4. **Content Stream** - Interprets page content streams and text operators
5. **Font Encoder** - Maps character codes to Unicode
6. **Text Extraction** - Collects positioned text elements

### Supported PDF Features

- ✅ PDF header and version detection
- ✅ Cross-reference tables (classic and compressed)
- ✅ Object streams (ObjStm)
- ✅ Decompression filters:
  - FlateDecode (zlib)
  - LZWDecode
  - ASCII85Decode
  - ASCIIHexDecode
  - RunLengthDecode
- ✅ Text operators:
  - Text state (Tf, Tc, Tw, Tz, TL, Tr, Ts)
  - Text positioning (Td, TD, Tm, T*)
  - Text showing (Tj, TJ, ', ")
- ✅ Font encodings:
  - WinAnsiEncoding
  - MacRomanEncoding
  - ToUnicode CMap
  - Encoding differences

## Development

```bash
# Clone the repository
git clone https://github.com/your-repo/pdf-lowlevel.git
cd pdf-lowlevel

# Install dependencies
uv sync --dev

# Run tests
pytest

# Format code
black src/
isort src/

# Type checking
mypy src/
```

## Limitations

This is an early release with some limitations:

- **No linearized PDF support** - Requires complete PDF files
- **Limited encryption support** - Password-protected PDFs not yet supported
- **Basic layout analysis** - No automatic column/paragraph detection
- **No image extraction** - Text only for now

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please read the contributing guidelines first.

## Acknowledgments

This library implements PDF parsing based on the ISO 32000-1 PDF specification.