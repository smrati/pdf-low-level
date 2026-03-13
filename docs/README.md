# PDF Low-Level Documentation

Welcome to the **pdf-lowlevel** library documentation. This guide will help you understand the library architecture, implementation details, and how to contribute to the project.

## Overview

`pdf-lowlevel` is a Python library for parsing PDF files at a low level, with a focus on layout-aware text extraction. Unlike high-level PDF libraries that just dump text, this library preserves positioning information, enabling accurate layout reconstruction.

## Documentation Index

### Getting Started
- [Architecture Overview](architecture.md) - High-level system design and data flow
- [PDF Basics](pdf-basics.md) - Understanding the PDF file format

### Core Modules
- [Tokenizer](tokenizer.md) - Converting PDF bytes to tokens
- [Cross-Reference Table](xref.md) - Object location mapping
- [PDF Reader](reader.md) - Main parsing orchestration
- [Objects](objects.md) - PDF object model

### Content Processing
- [Content Streams](content-streams.md) - Parsing page content
- [Graphics State](graphics.md) - Coordinate transformations
- [Fonts & Encoding](fonts.md) - Text decoding

### High-Level API
- [Extractor API](extractor.md) - Simple text extraction interface
- [Text Grouping](grouping.md) - Organizing text into lines/blocks

### Development
- [Contributing](contributing.md) - How to contribute
- [Testing](testing.md) - Test suite overview

## Quick Example

```python
from pdf_lowlevel import PDFExtractor, extract_text, extract_json

# Simple text extraction
text = extract_text("document.pdf")
print(text)

# Full extraction with metadata
with PDFExtractor("document.pdf") as extractor:
    result = extractor.extract(
        grouping_mode="cluster",
        y_tolerance=5.0,
    )
    print(result.to_json())
```

## Installation

```bash
# Using uv (recommended)
uv add pdf-lowlevel

# Using pip
pip install pdf-lowlevel
```

## Project Structure

```
pdf-lowlevel/
├── src/pdf_lowlevel/
│   ├── __init__.py          # Public API exports
│   ├── extract.py           # High-level extraction API
│   ├── logger.py            # Logging configuration
│   ├── parser/              # Low-level PDF parsing
│   │   ├── tokenizer.py     # Lexical analysis
│   │   ├── xref.py          # Cross-reference table
│   │   ├── reader.py        # Main PDF reader
│   │   └── objects.py       # Object model
│   ├── content/             # Content stream processing
│   │   ├── stream.py        # Content stream parser
│   │   ├── graphics.py      # Graphics state machine
│   │   └── grouper.py       # Text grouping algorithms
│   └── fonts/               # Font handling
│       └── encoding.py      # Character encoding
├── tests/                   # Test suite
└── docs/                    # This documentation
```

## License

MIT License