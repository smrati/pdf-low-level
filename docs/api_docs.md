# API Documentation

This document provides a comprehensive guide for developers who want to use the **pdf-lowlevel** library in their projects.

## Installation

```bash
# Using uv (recommended)
uv add pdf-lowlevel

# Using pip
pip install pdf-lowlevel
```

## Quick Start

```python
from pdf_lowlevel import extract_text, extract_json, PDFExtractor

# Simple text extraction
text = extract_text("document.pdf")
print(text)

# Get structured JSON output
json_data = extract_json("document.pdf")
print(json_data)

# Full control with PDFExtractor class
with PDFExtractor("document.pdf") as extractor:
    result = extractor.extract()
    print(result.get_all_text())
```

---

## Public API Reference

The library exports the following symbols:

```python
from pdf_lowlevel import (
    PDFExtractor,       # Main extractor class
    ExtractionResult,   # Result dataclass
    PageResult,         # Page result dataclass
    TextElement,        # Individual text fragment
    extract_text,       # Convenience function
    extract_json,       # Convenience function
    logger,             # Loguru logger instance
    configure_logger,   # Logger configuration
    __version__,        # Library version
)
```

---

## Convenience Functions

### extract_text()

The simplest way to extract plain text from a PDF.

```python
from pdf_lowlevel import extract_text

text = extract_text(
    "document.pdf",
    grouping_mode="cluster",  # or "tolerance"
    y_tolerance=5.0,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | `str`, `Path`, `BinaryIO`, `bytes` | Required | PDF source |
| `grouping_mode` | `str` | `"cluster"` | Text grouping algorithm |
| `y_tolerance` | `float` | `5.0` | Vertical tolerance for line grouping |

**Returns:** `str` - Plain text with pages separated by double newlines

**Example:**
```python
# From file path
text = extract_text("report.pdf")

# From bytes
with open("report.pdf", "rb") as f:
    pdf_bytes = f.read()
text = extract_text(pdf_bytes)

# From URL (using requests)
import requests
response = requests.get("https://example.com/document.pdf")
text = extract_text(response.content)
```

---

### extract_json()

Extract text with full structure and metadata as JSON.

```python
from pdf_lowlevel import extract_json

json_str = extract_json(
    "document.pdf",
    start_page=0,
    end_page=10,
    grouping_mode="cluster",
    y_tolerance=5.0,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | `str`, `Path`, `BinaryIO`, `bytes` | Required | PDF source |
| `start_page` | `int` | `0` | First page (0-indexed) |
| `end_page` | `int` | `None` | Last page (exclusive, None = all) |
| `grouping_mode` | `str` | `"cluster"` | Text grouping algorithm |
| `y_tolerance` | `float` | `5.0` | Vertical tolerance for line grouping |

**Returns:** `str` - JSON string with full extraction results

**Example:**
```python
import json

# Get JSON and parse it
json_str = extract_json("document.pdf")
data = json.loads(json_str)

# Access structured data
for page in data["pages"]:
    print(f"Page {page['page_number']}: {len(page['elements'])} elements")
    print(page["text"])
```

---

## PDFExtractor Class

The main class for full control over extraction.

### Constructor

```python
from pdf_lowlevel import PDFExtractor

extractor = PDFExtractor(source)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | `str`, `Path`, `BinaryIO`, `bytes` | PDF source - file path, file object, or bytes |

**Supported Input Types:**

```python
# File path (string)
extractor = PDFExtractor("/path/to/document.pdf")

# Path object
from pathlib import Path
extractor = PDFExtractor(Path("/path/to/document.pdf"))

# Bytes
with open("document.pdf", "rb") as f:
    pdf_bytes = f.read()
extractor = PDFExtractor(pdf_bytes)

# File-like object
file_obj = open("document.pdf", "rb")
extractor = PDFExtractor(file_obj)
# Remember to close: file_obj.close()

# BytesIO
from io import BytesIO
extractor = PDFExtractor(BytesIO(pdf_bytes))
```

### Context Manager Usage (Recommended)

```python
from pdf_lowlevel import PDFExtractor

# Automatically closes file handle
with PDFExtractor("document.pdf") as extractor:
    result = extractor.extract()
    print(result.get_all_text())
```

### extract() Method

The main extraction method with full parameter control.

```python
result = extractor.extract(
    start_page=0,
    end_page=None,
    include_metadata=True,
    
    # Grouping parameters
    grouping_mode="cluster",
    y_tolerance=5.0,
    x_tolerance=5.0,
    space_width=3.0,
    line_gap_threshold=1.5,
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_page` | `int` | `0` | First page to extract (0-indexed) |
| `end_page` | `int` | `None` | Last page (exclusive). None = all pages |
| `include_metadata` | `bool` | `True` | Include document metadata |
| `grouping_mode` | `str` | `"cluster"` | Algorithm for grouping text |
| `y_tolerance` | `float` | `5.0` | Vertical tolerance for line grouping (points) |
| `x_tolerance` | `float` | `5.0` | Horizontal tolerance for merging (points) |
| `space_width` | `float` | `3.0` | Gap threshold for inserting spaces |
| `line_gap_threshold` | `float` | `1.5` | Multiplier for paragraph break detection |

**Returns:** `ExtractionResult` - See [ExtractionResult](#extractionresult-class)

### close() Method

Manually close the PDF reader (only needed if not using context manager).

```python
extractor = PDFExtractor("document.pdf")
result = extractor.extract()
extractor.close()  # Clean up
```

---

## ExtractionResult Class

The result of extracting text from a PDF.

### Attributes

```python
@dataclass
class ExtractionResult:
    filename: str              # PDF filename
    page_count: int            # Total pages in PDF
    pages: List[PageResult]    # Extracted pages
    metadata: Dict[str, Any]   # Document metadata
    grouping_config: GroupingConfig  # Grouping settings used
```

### Methods

#### to_dict()

Convert to dictionary for further processing.

```python
result = extractor.extract()
data = result.to_dict()
# data["pages"], data["metadata"], etc.
```

#### to_json()

Convert to JSON string.

```python
result = extractor.extract()
json_str = result.to_json(indent=2)
print(json_str)
```

#### get_all_text()

Get all text as a single string.

```python
result = extractor.extract()
full_text = result.get_all_text()
print(full_text)
```

### Example: Working with ExtractionResult

```python
from pdf_lowlevel import PDFExtractor

with PDFExtractor("document.pdf") as extractor:
    result = extractor.extract()
    
    # Access metadata
    print(f"Title: {result.metadata.get('Title', 'Unknown')}")
    print(f"Author: {result.metadata.get('Author', 'Unknown')}")
    
    # Iterate pages
    for page in result.pages:
        print(f"Page {page.page_number}:")
        print(page.get_text())
    
    # Export to JSON
    with open("output.json", "w") as f:
        f.write(result.to_json())
```

---

## PageResult Class

Result of extracting text from a single page.

### Attributes

```python
@dataclass
class PageResult:
    page_number: int              # Page number (1-indexed)
    width: float                  # Page width in points
    height: float                 # Page height in points
    elements: List[TextElement]   # Raw text fragments
    lines: List[TextLine]         # Grouped lines
    blocks: List[TextBlock]       # Grouped paragraphs
```

### Methods

#### get_text()

Get page text as a string (lines joined by newline).

```python
page_text = page.get_text()
```

#### get_text_with_blocks()

Get page text with paragraph separation.

```python
page_text = page.get_text_with_blocks()  # Paragraphs separated by \n\n
```

#### to_dict()

Convert to dictionary.

```python
page_dict = page.to_dict()
```

### Example: Working with PageResult

```python
for page in result.pages:
    print(f"\n=== Page {page.page_number} ({page.width}x{page.height}) ===\n")
    
    # Get plain text
    print(page.get_text())
    
    # Access individual elements with positions
    for elem in page.elements:
        print(f"'{elem.text}' at ({elem.x:.1f}, {elem.y:.1f})")
    
    # Access grouped lines
    for line in page.lines:
        print(f"Line at y={line.y}: {line.text}")
```

---

## TextElement Class

An individual text fragment with position information.

### Attributes

```python
@dataclass
class TextElement:
    text: str                    # Decoded text content
    x: float                     # Lower-left X in user space
    y: float                     # Baseline Y in user space
    width: float                 # Text width
    height: float                # Text height (font size)
    font_name: Optional[str]     # Font name from PDF
    font_size: float             # Font size in points
    page_number: int             # Page number (1-indexed)
    
    # Text state
    char_spacing: float          # Character spacing (Tc)
    word_spacing: float          # Word spacing (Tw)
    horizontal_scaling: float    # Horizontal scaling % (Tz)
    text_render_mode: int        # Render mode (Tr)
```

### Properties

```python
# Bounding box as tuple
bbox = element.bbox  # (x0, y0, x1, y1)
```

### Methods

```python
# Convert to dictionary
elem_dict = element.to_dict()
```

### Example: Filtering Elements

```python
# Get all elements from a specific region
for elem in page.elements:
    if 100 <= elem.x <= 500 and 600 <= elem.y <= 700:
        print(f"'{elem.text}' in region")

# Filter by font size (find headers)
for elem in page.elements:
    if elem.font_size > 14:
        print(f"Header: '{elem.text}'")

# Filter by position (left column)
for elem in page.elements:
    if elem.x < 300:  # Left half of page
        print(f"'{elem.text}'")
```

---

## Text Grouping Parameters

Fine-tune how text fragments are grouped into lines and paragraphs.

### grouping_mode

Choose the algorithm for grouping text into lines.

```python
result = extractor.extract(grouping_mode="cluster")  # or "tolerance"
```

| Mode | Description | Best For |
|------|-------------|----------|
| `"cluster"` | Nearest-neighbor clustering | Generated PDFs, variable positioning |
| `"tolerance"` | Y-coordinate quantization | Well-formed PDFs, faster processing |

### y_tolerance

Vertical tolerance for grouping into lines (in points).

```python
result = extractor.extract(y_tolerance=5.0)
```

- **Smaller** (e.g., `2.0`): More lines, stricter grouping
- **Larger** (e.g., `10.0`): Fewer lines, more aggressive grouping

**When to adjust:**
- Large fonts: increase tolerance
- Sub-pixel Y variations: increase tolerance
- Dense text (tables): decrease tolerance

### x_tolerance

Horizontal tolerance for merging overlapping fragments.

```python
result = extractor.extract(x_tolerance=5.0)
```

Used to detect overlapping or very close fragments (kerning).

### space_width

Minimum gap to insert a space between fragments.

```python
result = extractor.extract(space_width=3.0)
```

- **Smaller** (e.g., `1.0`): Fewer spaces inserted
- **Larger** (e.g., `5.0`): More spaces inserted

**When to adjust:**
- Missing spaces in output: decrease value
- Extra spaces between letters: increase value

### line_gap_threshold

Multiplier for detecting paragraph breaks.

```python
result = extractor.extract(line_gap_threshold=1.5)
```

If the gap between lines exceeds `avg_line_height * threshold`, a new paragraph is started.

- **Smaller** (e.g., `1.2`): More paragraph breaks
- **Larger** (e.g., `2.0`): Fewer paragraph breaks

---

## Complete Examples

### Example 1: Basic Text Extraction

```python
from pdf_lowlevel import extract_text

# Simple extraction
text = extract_text("document.pdf")
print(text)
```

### Example 2: Extract Specific Pages

```python
from pdf_lowlevel import PDFExtractor

with PDFExtractor("large_document.pdf") as extractor:
    # Extract only first 5 pages
    result = extractor.extract(start_page=0, end_page=5)
    print(result.get_all_text())
```

### Example 3: Get Structured JSON

```python
from pdf_lowlevel import extract_json
import json

json_str = extract_json("document.pdf")
data = json.loads(json_str)

# Access structured data
for page in data["pages"]:
    print(f"Page {page['page_number']}:")
    for line in page["lines"]:
        print(f"  {line['text']}")
```

### Example 4: Custom Grouping Settings

```python
from pdf_lowlevel import PDFExtractor

with PDFExtractor("complex_layout.pdf") as extractor:
    result = extractor.extract(
        grouping_mode="cluster",
        y_tolerance=8.0,        # More aggressive line grouping
        x_tolerance=3.0,        # Stricter horizontal merging
        space_width=2.0,        # Fewer spaces
        line_gap_threshold=2.0, # Fewer paragraph breaks
    )
    print(result.get_all_text())
```

### Example 5: Extract with Positions

```python
from pdf_lowlevel import PDFExtractor

with PDFExtractor("document.pdf") as extractor:
    result = extractor.extract()
    
    for page in result.pages:
        print(f"\n=== Page {page.page_number} ===")
        
        for elem in page.elements:
            print(f"'{elem.text}' at ({elem.x:.1f}, {elem.y:.1f}), "
                  f"font={elem.font_name}, size={elem.font_size}")
```

### Example 6: Filter by Region

```python
from pdf_lowlevel import PDFExtractor

def extract_region(pdf_path, x1, y1, x2, y2):
    """Extract text from a specific region of each page."""
    with PDFExtractor(pdf_path) as extractor:
        result = extractor.extract()
        
        region_text = []
        for page in result.pages:
            for elem in page.elements:
                if x1 <= elem.x <= x2 and y1 <= elem.y <= y2:
                    region_text.append(elem.text)
        
        return " ".join(region_text)

# Extract header region (top of page)
header_text = extract_region("document.pdf", 0, 700, 612, 792)
print(header_text)
```

### Example 7: Extract Metadata

```python
from pdf_lowlevel import PDFExtractor

with PDFExtractor("document.pdf") as extractor:
    result = extractor.extract(include_metadata=True)
    
    print("Document Metadata:")
    for key, value in result.metadata.items():
        print(f"  {key}: {value}")
```

### Example 8: Process In-Memory PDF

```python
from pdf_lowlevel import extract_text
import requests

# Download PDF
response = requests.get("https://example.com/document.pdf")
pdf_bytes = response.content

# Extract text without saving to disk
text = extract_text(pdf_bytes)
print(text)
```

### Example 9: Export to JSON File

```python
from pdf_lowlevel import PDFExtractor

with PDFExtractor("document.pdf") as extractor:
    result = extractor.extract()
    
    # Write to file
    with open("extraction_result.json", "w", encoding="utf-8") as f:
        f.write(result.to_json(indent=2))
```

### Example 10: Access Low-Level Reader

```python
from pdf_lowlevel.parser.reader import open_pdf

# Use low-level API for more control
with open_pdf("document.pdf") as pdf:
    print(f"PDF Version: {pdf.version}")
    print(f"Page Count: {pdf.page_count}")
    
    for i in range(pdf.page_count):
        content = pdf.get_page_contents(i)
        media_box = pdf.get_page_media_box(i)
        print(f"Page {i+1}: {media_box}")
```

---

## Logging

Configure logging for debugging:

```python
from pdf_lowlevel import configure_logger

# Enable debug logging
configure_logger(level="DEBUG")

# Now use the library - debug messages will be printed
from pdf_lowlevel import extract_text
text = extract_text("document.pdf")
```

---

## Error Handling

```python
from pdf_lowlevel import PDFExtractor
from pdf_lowlevel.parser.reader import PDFParseError

try:
    with PDFExtractor("document.pdf") as extractor:
        result = extractor.extract()
        print(result.get_all_text())
except FileNotFoundError:
    print("File not found")
except PDFParseError as e:
    print(f"PDF parsing error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Performance Tips

1. **Use page ranges** when you don't need all pages:
   ```python
   result = extractor.extract(start_page=0, end_page=5)
   ```

2. **Disable metadata** if not needed:
   ```python
   result = extractor.extract(include_metadata=False)
   ```

3. **Use tolerance mode** for faster processing of well-formed PDFs:
   ```python
   result = extractor.extract(grouping_mode="tolerance")
   ```

4. **Reuse extractor** for multiple extractions:
   ```python
   with PDFExtractor("large.pdf") as extractor:
       first = extractor.extract(end_page=10)
       last = extractor.extract(start_page=90)
   ```

---

## Output Format Reference

### JSON Structure

```json
{
  "filename": "document.pdf",
  "page_count": 10,
  "pages": [
    {
      "page_number": 1,
      "width": 612,
      "height": 792,
      "text": "Page text here...",
      "elements": [
        {
          "text": "Hello",
          "x": 100,
          "y": 700,
          "width": 30,
          "height": 12,
          "font_name": "Helvetica",
          "font_size": 12,
          "bbox": [100, 700, 130, 712]
        }
      ],
      "lines": [
        {
          "text": "Line of text",
          "y": 700,
          "x_start": 100,
          "x_end": 300,
          "fragment_count": 3
        }
      ],
      "blocks": [
        {
          "text": "Paragraph text...",
          "line_count": 5,
          "x_start": 100,
          "x_end": 500,
          "y_start": 700,
          "y_end": 600
        }
      ]
    }
  ],
  "metadata": {
    "Title": "Document Title",
    "Author": "John Doe"
  },
  "grouping_config": {
    "y_tolerance": 5.0,
    "x_tolerance": 5.0,
    "space_width": 3.0,
    "line_gap_threshold": 1.5,
    "grouping_mode": "cluster"
  }
}