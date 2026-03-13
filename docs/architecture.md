# Architecture Overview

This document describes the high-level architecture of the pdf-lowlevel library.

## Design Philosophy

The library is designed with a **layered architecture**:

1. **Low-level parsing** - Tokenization and raw object extraction
2. **Structure parsing** - Cross-reference tables, object resolution
3. **Content interpretation** - Graphics state, content streams
4. **High-level API** - Simple extraction interface

This separation allows developers to use the library at whatever level suits their needs.

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PDF File (bytes)                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            Tokenizer                                     │
│  • Converts raw bytes to tokens                                          │
│  • Handles PDF syntax: strings, names, numbers, arrays, dicts           │
│  • Source: parser/tokenizer.py                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         XRef Parser                                      │
│  • Locates cross-reference table                                        │
│  • Maps object numbers to byte offsets                                  │
│  • Parses trailer dictionary                                            │
│  • Source: parser/xref.py                                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           PDF Reader                                     │
│  • Orchestrates parsing process                                         │
│  • Resolves indirect object references                                  │
│  • Loads page tree                                                      │
│  • Decompresses streams (Flate, LZW, etc.)                             │
│  • Source: parser/reader.py                                             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      Content Stream Parser                               │
│  • Parses PDF operators (BT, ET, Tf, Tj, TJ, etc.)                     │
│  • Maintains graphics state stack                                       │
│  • Extracts text with positions                                         │
│  • Source: content/stream.py                                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Text Grouper                                    │
│  • Groups text fragments into lines                                     │
│  • Organizes lines into blocks/paragraphs                               │
│  • Two algorithms: cluster vs tolerance                                 │
│  • Source: content/grouper.py                                           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Extraction Result                                 │
│  • Structured output with pages, elements, metadata                     │
│  • JSON serialization support                                           │
│  • Source: extract.py                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Tokenizer (`parser/tokenizer.py`)

The **PDFTokenizer** class performs lexical analysis:

```python
from pdf_lowlevel.parser.tokenizer import PDFTokenizer, TokenType

tokenizer = PDFTokenizer(pdf_bytes)
for token in tokenizer.tokenize():
    print(f"{token.type.name}: {token.value}")
```

**Token Types:**
- Literals: `INTEGER`, `REAL`, `STRING`, `HEX_STRING`, `NAME`, `BOOLEAN`, `NULL`
- Structures: `ARRAY_START/END`, `DICT_START/END`
- Objects: `OBJ_START/END`, `STREAM_START/END`
- Keywords: `XREF`, `TRAILER`, `STARTXREF`, `ENDOFFILE`

### 2. XRef Parser (`parser/xref.py`)

Handles the cross-reference table:

```python
from pdf_lowlevel.parser.xref import parse_xref, find_xref_offset

xref_table = parse_xref(file_handle)
offset = xref_table.get_offset(object_number)
root_ref = xref_table.get_root_ref()
```

**Key Classes:**
- `XRefEntry` - Single entry (offset, generation, type)
- `XRefTable` - Collection with trailer info
- `XRefParser` - Parses traditional xref tables
- `IndirectRef` - Represents `n m R` references

### 3. PDF Reader (`parser/reader.py`)

Main orchestrator:

```python
from pdf_lowlevel.parser.reader import PDFReader, open_pdf

with open_pdf("document.pdf") as pdf:
    print(f"Pages: {pdf.page_count}")
    content = pdf.get_page_contents(0)
    media_box = pdf.get_page_media_box(0)
```

**Responsibilities:**
- Header validation
- Object resolution via xref
- Stream decompression
- Page tree traversal

### 4. Content Stream Parser (`content/stream.py`)

Interprets page content:

```python
from pdf_lowlevel.content.stream import ContentStreamParser

parser = ContentStreamParser(stream_data)
elements = parser.parse()
for elem in elements:
    print(f"'{elem.text}' at ({elem.x}, {elem.y})")
```

**Text Operators Handled:**
| Operator | Description |
|----------|-------------|
| `BT/ET` | Begin/End text object |
| `Tf` | Set font and size |
| `Td/TD/T*` | Move text position |
| `Tm` | Set text matrix |
| `Tj/'` | Show text |
| `TJ` | Show text with positioning |
| `Tc/Tw/Tz` | Spacing parameters |

### 5. Text Grouper (`content/grouper.py`)

Organizes fragments:

```python
from pdf_lowlevel.content.grouper import TextGrouper, GroupingMode

grouper = TextGrouper(elements, grouping_mode="cluster")
lines = grouper.group_into_lines()
blocks = grouper.group_into_blocks()
```

**Grouping Algorithms:**
- **Cluster** (default): Nearest-neighbor clustering, more accurate
- **Tolerance**: Y-quantization, faster but may misorder

## Object Model

PDF objects are represented as Python types:

| PDF Type | Python Type |
|----------|-------------|
| Integer | `int` |
| Real | `float` |
| String | `bytes` |
| Name | `PDFName` |
| Boolean | `bool` |
| Null | `None` |
| Array | `list` |
| Dictionary | `dict` |
| Stream | `PDFStream` |
| Indirect Ref | `PDFIndirectRef` |
| Indirect Object | `PDFIndirectObject` |

## Graphics State

The graphics state stack manages:

```python
from pdf_lowlevel.content.graphics import GraphicsStateStack

stack = GraphicsStateStack()
stack.save()  # q operator
stack.restore()  # Q operator
```

**Tracked State:**
- Current Transformation Matrix (CTM)
- Text state (font, size, spacing)
- Text position matrix

## Error Handling

The library uses custom exceptions:

```python
from pdf_lowlevel.parser.reader import PDFParseError

try:
    with open_pdf("corrupt.pdf") as pdf:
        ...
except PDFParseError as e:
    print(f"PDF parsing failed: {e}")
```

## Logging

Uses loguru for configurable logging:

```python
from pdf_lowlevel import configure_logger

# Enable debug logging
configure_logger(level="DEBUG")
```

## Design Decisions

### Why Not Use Existing Libraries?

1. **pdfminer.six** - Good but complex, hard to customize
2. **PyMuPDF** - Fast but C-based, limited Python customization
3. **pypdf** - Focuses on manipulation, not extraction

This library provides:
- Pure Python implementation
- Access to low-level structures
- Extensible text grouping algorithms
- Clear separation of concerns

### Why Two Grouping Algorithms?

- **Cluster**: Better for documents with sub-pixel Y variations (common in generated PDFs)
- **Tolerance**: Faster for well-formed documents with consistent baselines

### Memory Considerations

The library processes content streams page-by-page, not loading the entire file into memory. However, the object cache can grow large for documents with many indirect objects.

## Extension Points

1. **Custom font resolvers** - Implement `font_resolver` callback
2. **New stream filters** - Add to `_apply_filter()` method
3. **Text grouping** - Add new algorithms to `TextGrouper`
4. **Content operators** - Extend `_operator_handlers` dict