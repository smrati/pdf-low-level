# Extractor API

The high-level extraction API provides a simple interface for extracting text from PDFs.

## Overview

**Source:** `src/pdf_lowlevel/extract.py`

The `PDFExtractor` class and convenience functions (`extract_text`, `extract_json`) provide easy access to PDF content with layout preservation.

## Quick Start

### extract_text()

Simplest way to get plain text:

```python
from pdf_lowlevel import extract_text

text = extract_text("document.pdf")
print(text)
```

### extract_json()

Get structured extraction results:

```python
from pdf_lowlevel import extract_json
import json

json_str = extract_json("document.pdf")
data = json.loads(json_str)

for page in data["pages"]:
    print(f"Page {page['page_number']}: {page['text']}")
```

### PDFExtractor Class

Full control with the class interface:

```python
from pdf_lowlevel import PDFExtractor

with PDFExtractor("document.pdf") as extractor:
    result = extractor.extract(
        start_page=0,
        end_page=5,
        grouping_mode="cluster",
        y_tolerance=5.0,
    )
    
    # Access results
    for page in result.pages:
        print(f"Page {page.page_number}")
        for element in page.elements:
            print(f"  '{element.text}' at ({element.x}, {element.y})")
```

## PDFExtractor Class

### Constructor

```python
class PDFExtractor:
    def __init__(self, source: Union[str, Path, BinaryIO, bytes]):
        """
        Initialize the extractor.
        
        Args:
            source: PDF source - file path, file-like object, or bytes
        """
```

### extract() Method

```python
def extract(
    self,
    start_page: int = 0,
    end_page: Optional[int] = None,
    include_metadata: bool = True,
    *,
    grouping_mode: str = "cluster",
    y_tolerance: float = 5.0,
    x_tolerance: float = 5.0,
    space_width: float = 3.0,
    line_gap_threshold: float = 1.5,
) -> ExtractionResult:
    """
    Extract text from the PDF.
    
    Args:
        start_page: First page to extract (0-indexed)
        end_page: Last page (exclusive). None = all pages
        include_metadata: Include document metadata
        
        grouping_mode: "cluster" or "tolerance"
        y_tolerance: Vertical tolerance for line grouping (points)
        x_tolerance: Horizontal tolerance for merging (points)
        space_width: Minimum gap for space insertion (points)
        line_gap_threshold: Paragraph break detection multiplier
    
    Returns:
        ExtractionResult with pages and metadata
    """
```

### Context Manager

```python
with PDFExtractor("doc.pdf") as extractor:
    result = extractor.extract()
# Automatically closes file handle
```

## ExtractionResult

```python
@dataclass
class ExtractionResult:
    filename: str = ""
    page_count: int = 0
    pages: List[PageResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    grouping_config: GroupingConfig = field(default_factory=GroupingConfig)
```

### Methods

```python
# Convert to dictionary
d = result.to_dict()

# Convert to JSON string
json_str = result.to_json(indent=2)

# Get all text as single string
text = result.get_all_text()
```

### Example Output

```python
{
    "filename": "document.pdf",
    "page_count": 3,
    "pages": [
        {
            "page_number": 1,
            "width": 612,
            "height": 792,
            "text": "Hello World\nThis is page 1",
            "elements": [...],
            "lines": [...],
            "blocks": [...]
        },
        ...
    ],
    "metadata": {
        "Title": "My Document",
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
```

## PageResult

```python
@dataclass
class PageResult:
    page_number: int      # 1-indexed
    width: float          # Page width in points
    height: float         # Page height in points
    elements: List[TextElement]
    lines: List[TextLine]
    blocks: List[TextBlock]
```

### Methods

```python
# Get page text (lines joined by newline)
text = page.get_text()

# Get text with paragraph separation
text = page.get_text_with_blocks()

# Convert to dictionary
d = page.to_dict()
```

## TextElement

```python
@dataclass
class TextElement:
    text: str
    x: float              # Lower-left x
    y: float              # Baseline y
    width: float          # Text width
    height: float         # Font size
    font_name: Optional[str]
    font_size: float
    page_number: int
    
    # Additional metadata
    char_spacing: float
    word_spacing: float
    horizontal_scaling: float
    text_render_mode: int
```

### Properties

```python
# Bounding box
bbox = element.bbox  # (x0, y0, x1, y1)
```

### Methods

```python
d = element.to_dict()
```

## Text Grouping

Two algorithms for grouping text into lines:

### Cluster Mode (Default)

```python
result = extractor.extract(grouping_mode="cluster")
```

Uses nearest-neighbor clustering:
- More accurate for documents with variable positioning
- Handles sub-pixel Y variations
- Better for generated PDFs

### Tolerance Mode

```python
result = extractor.extract(grouping_mode="tolerance")
```

Uses Y-quantization:
- Groups by Y buckets of `y_tolerance` size
- Faster but may misorder characters
- Better for well-formed PDFs with consistent baselines

### Tuning Parameters

```python
result = extractor.extract(
    y_tolerance=10.0,     # Larger = more aggressive grouping
    x_tolerance=5.0,      # Merge nearby fragments
    space_width=3.0,      # Gap threshold for spaces
    line_gap_threshold=2.0,  # Larger = fewer paragraph breaks
)
```

## Input Types

The extractor accepts multiple input types:

```python
# File path (string)
extract_text("/path/to/document.pdf")

# Path object
from pathlib import Path
extract_text(Path("/path/to/document.pdf"))

# Bytes
with open("document.pdf", "rb") as f:
    pdf_bytes = f.read()
extract_text(pdf_bytes)

# File-like object
file_obj = open("document.pdf", "rb")
extract_text(file_obj)
file_obj.close()

# BytesIO
from io import BytesIO
extract_text(BytesIO(pdf_bytes))
```

## Metadata

Document metadata is extracted when `include_metadata=True`:

```python
result = extractor.extract(include_metadata=True)
print(result.metadata)
# {'Title': 'My Doc', 'Author': 'John', 'Creator': 'LaTeX'}
```

Common metadata fields:
- `Title`
- `Author`
- `Subject`
- `Keywords`
- `Creator`
- `Producer`
- `CreationDate`
- `ModDate`

## Page Ranges

Extract specific pages:

```python
# First 5 pages
result = extractor.extract(start_page=0, end_page=5)

# Pages 3-5 (0-indexed, so page numbers 3, 4)
result = extractor.extract(start_page=2, end_page=5)

# Single page
result = extractor.extract(start_page=0, end_page=1)
```

## Working with Results

### Iterate All Elements

```python
for page in result.pages:
    for element in page.elements:
        print(f"'{element.text}' at ({element.x:.1f}, {element.y:.1f})")
```

### Get Text by Page

```python
for page in result.pages:
    print(f"--- Page {page.page_number} ---")
    print(page.get_text())
```

### Get All Text

```python
full_text = result.get_all_text()
print(full_text)
```

### JSON Export

```python
import json

# Get JSON string
json_str = result.to_json()

# Write to file
with open("output.json", "w") as f:
    f.write(json_str)

# Parse for processing
data = json.loads(json_str)
```

## Logging

Enable debug logging for troubleshooting:

```python
from pdf_lowlevel import configure_logger

configure_logger(level="DEBUG")
```

## Error Handling

```python
from pdf_lowlevel import PDFExtractor

try:
    with PDFExtractor("corrupt.pdf") as extractor:
        result = extractor.extract()
except Exception as e:
    print(f"Extraction failed: {e}")
```

## Performance Tips

1. **Use page ranges** when you don't need all pages
2. **Disable metadata** if not needed: `include_metadata=False`
3. **Use tolerance mode** for faster processing of well-formed PDFs
4. **Reuse extractor** for multiple extractions from same file

```python
# Efficient: extract multiple ranges
with PDFExtractor("large.pdf") as extractor:
    first_pages = extractor.extract(end_page=5)
    last_pages = extractor.extract(start_page=95)
```

## Testing

See `tests/test_extractor.py`:

```bash
uv run pytest tests/test_extractor.py -v
```

Key test classes:
- `TestPDFExtractor` - Core functionality
- `TestExtractionResult` - Result handling
- `TestPageResult` - Page results
- `TestTextElement` - Element data
- `TestExtractText` - Convenience function
- `TestExtractJson` - JSON output