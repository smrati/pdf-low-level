# PDF Reader

The PDF Reader is the main orchestrator for parsing PDF files.

## Overview

**Source:** `src/pdf_lowlevel/parser/reader.py`

The `PDFReader` class coordinates all parsing activities: header validation, xref parsing, object resolution, and page tree loading.

## Usage

### Basic Usage

```python
from pdf_lowlevel.parser.reader import PDFReader, open_pdf

# Using context manager (recommended)
with open_pdf("document.pdf") as pdf:
    print(f"Pages: {pdf.page_count}")
    print(f"Version: {pdf.version}")
    
    # Get page content
    content = pdf.get_page_contents(0)
    
    # Get page dimensions
    media_box = pdf.get_page_media_box(0)
```

### Manual Lifecycle

```python
reader = PDFReader("document.pdf")
reader.read()

# Use reader...
print(reader.page_count)

reader.close()
```

### From Different Sources

```python
# From file path
reader = PDFReader("/path/to/document.pdf")

# From bytes
with open("document.pdf", "rb") as f:
    pdf_bytes = f.read()
reader = PDFReader(pdf_bytes)

# From file-like object
file_obj = open("document.pdf", "rb")
reader = PDFReader(file_obj)
```

## Main Methods

### Reading

```python
def read(self) -> None:
    """Parse the PDF file. Must be called before accessing objects."""
```

### Object Access

```python
def get_object(self, obj_num: int, gen_num: int = 0) -> Optional[PDFObject]:
    """Get an object by its number."""
```

Example:
```python
# Get object 5
obj = pdf.get_object(5)

# Get object with generation 1
obj = pdf.get_object(5, 1)
```

### Page Access

```python
@property
def page_count(self) -> int:
    """Number of pages in the document."""

def get_page(self, page_num: int) -> Optional[Dict[str, Any]]:
    """Get page dictionary (0-indexed)."""

def get_page_contents(self, page_num: int) -> Optional[bytes]:
    """Get decoded content stream for a page."""

def get_page_media_box(self, page_num: int) -> Optional[List[float]]:
    """Get page dimensions [x0, y0, x1, y1]."""

def get_page_resources(self, page_num: int) -> Optional[Dict[str, Any]]:
    """Get page resources dictionary."""
```

## Parsing Process

### 1. Header Validation

```python
def _verify_header(self) -> None:
    # Checks for %PDF-x.y header
    # Extracts version string
```

Raises `PDFParseError` if header is invalid.

### 2. XRef Parsing

```python
def read(self):
    self._xref_table = parse_xref(self._file)
```

See [xref.md](xref.md) for details.

### 3. Page Tree Loading

```python
def _load_pages(self) -> None:
    # Get root catalog
    # Navigate to Pages
    # Recursively load page tree
```

Page tree structure:
```
Catalog
  └── Pages (intermediate node)
        ├── Page (leaf)
        ├── Page (leaf)
        └── Pages (intermediate)
              ├── Page (leaf)
              └── Page (leaf)
```

## Object Parsing

### Indirect Objects

```python
def _parse_indirect_object(self, offset: int) -> Optional[PDFIndirectObject]:
    # Seek to offset
    # Parse: n m obj ... endobj
    # Return object with value
```

### Object Values

```python
def _parse_object_value(self) -> PDFObject:
    # Dispatch based on token type
    # Handles integers, reals, strings, names, arrays, dicts
    # Resolves indirect references
```

### Arrays

```python
def _parse_array(self) -> List[PDFObject]:
    # Parse until ]
    # Recursively parse values
```

### Dictionaries

```python
def _parse_dictionary(self) -> Dict[str, PDFObject]:
    # Parse until >>
    # Handle key-value pairs
    # Check for stream keyword
```

### Streams

```python
def _parse_stream(self, dictionary: Dict[str, PDFObject]) -> PDFStream:
    # Get Length from dictionary
    # Read stream data
    # Find endstream
```

## Stream Decompression

The reader handles multiple compression filters:

### FlateDecode (zlib)

```python
def _apply_flate_decode(self, data: bytes, params: Dict) -> bytes:
    try:
        return zlib.decompress(data)
    except zlib.error:
        # Try raw deflate
        return zlib.decompress(data, -15)
```

### LZWDecode

```python
def _lzw_decompress(self, data: bytes) -> bytes:
    # Full LZW implementation
    # Initial code size: 9 bits
    # Max code size: 12 bits
```

### ASCII85Decode

```python
def _apply_ascii85_decode(self, data: bytes, params: Dict) -> bytes:
    # Base85 decoding
    # Handle 'z' zero groups
    # Handle partial final groups
```

### ASCIIHexDecode

```python
def _apply_ascii_hex_decode(self, data: bytes, params: Dict) -> bytes:
    # Hex decoding
    # Ignore whitespace
    # Handle odd-length with padding
```

### RunLengthDecode

```python
def _apply_runlength_decode(self, data: bytes, params: Dict) -> bytes:
    # Length-byte < 128: copy next n+1 bytes
    # Length-byte > 128: repeat next byte 257-n times
    # Length-byte = 128: end of data
```

## Error Handling

```python
class PDFParseError(Exception):
    """Exception raised when PDF parsing fails."""
```

Common errors:
```python
# Invalid header
raise PDFParseError("Not a valid PDF file (missing %PDF- header)")

# Missing catalog
raise PDFParseError("Could not find Root catalog in trailer")

# Missing pages
raise PDFParseError("Could not find Pages in Root catalog")
```

## Object Caching

Objects are cached to avoid re-parsing:

```python
self._object_cache: Dict[int, PDFIndirectObject] = {}

def get_object(self, obj_num, gen_num=0):
    cache_key = (obj_num, gen_num)
    if cache_key in self._object_cache:
        return self._object_cache[cache_key].value
    # ... parse and cache
```

## Page Tree Navigation

```python
def _load_page_tree(self, node: Dict[str, Any]) -> None:
    node_type = node.get("Type")
    
    if node_type == "Page":
        # Leaf: add to pages list
        self._pages.append(node)
    elif node_type == "Pages":
        # Intermediate: recurse into Kids
        for kid_ref in node.get("Kids", []):
            kid = self.get_object(kid_ref.object_number, ...)
            self._load_page_tree(kid)
```

## Combining Content Streams

Pages can have multiple content streams:

```python
def get_page_contents(self, page_num: int) -> Optional[bytes]:
    contents = page.get("Contents")
    
    if isinstance(contents, list):
        # Multiple streams
        streams = [self.get_object(ref) for ref in contents]
        return self._combine_streams(streams)
    else:
        # Single stream
        stream = self.get_object(contents)
        return self._decode_stream(stream)
```

## Indirect Reference Resolution

The reader resolves references using xref:

```python
# In _parse_object_value
if third_token.type == TokenType.INDIRECT_REF:
    return PDFIndirectRef(token.value, next_token.value)

# Later, when accessing
if isinstance(value, PDFIndirectRef):
    return self.get_object(value.object_number, value.generation_number)
```

## Testing

See `tests/test_reader.py`:

```bash
uv run pytest tests/test_reader.py -v
```

Key test classes:
- `TestPDFReader` - Basic functionality
- `TestObjectParsing` - Object resolution
- `TestPageAccess` - Page tree navigation
- `TestStreamDecompression` - Filter handling