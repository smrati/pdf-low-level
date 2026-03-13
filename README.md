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