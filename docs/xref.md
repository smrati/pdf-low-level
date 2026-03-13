# Cross-Reference Table Parser

The cross-reference (xref) table is crucial for locating objects within a PDF file.

## Overview

**Source:** `src/pdf_lowlevel/parser/xref.py`

The xref parser locates and parses the cross-reference table, which maps object numbers to byte offsets in the file.

## Usage

### Basic Usage

```python
from pdf_lowlevel.parser.xref import parse_xref, find_xref_offset

# Find xref offset from end of file
xref_offset = find_xref_offset(file_handle)

# Parse xref table
file_handle.seek(xref_offset)
xref_table = parse_xref(file_handle)

# Get object offset
offset = xref_table.get_offset(5)  # Object 5
print(f"Object 5 is at byte {offset}")
```

### Getting Document Info

```python
# Get root catalog reference
root_ref = xref_table.get_root_ref()  # Returns (obj_num, gen_num)

# Get info dictionary reference
info_ref = xref_table.get_info_ref()

# Get total object count
size = xref_table.get_size()
```

## Data Structures

### XRefEntry

Represents a single entry in the table:

```python
@dataclass
class XRefEntry:
    offset: int = 0           # Byte position in file
    generation: int = 0       # Generation number
    free: bool = False        # True if entry is free
    
    # For xref stream type 2 (compressed objects)
    object_stream_num: int = 0
    index_in_stream: int = 0
    
    entry_type: int = 1  # 0=free, 1=normal, 2=compressed
```

Entry types:
| Type | Description |
|------|-------------|
| 0 | Free entry (deleted object) |
| 1 | Normal entry (offset points to `n m obj`) |
| 2 | Compressed entry (in object stream) |

### XRefTable

Collection of entries with trailer info:

```python
@dataclass
class XRefTable:
    entries: Dict[int, XRefEntry]  # obj_num -> entry
    trailer: Dict[str, any]        # Trailer dictionary
```

Methods:
```python
# Get offset for object
table.get_offset(obj_num, gen_num=0) -> Optional[int]

# Get full entry
table.get_entry(obj_num) -> Optional[XRefEntry]

# Add/update entry
table.add_entry(obj_num, entry)

# Get root catalog reference
table.get_root_ref() -> Optional[Tuple[int, int]]

# Get info dict reference
table.get_info_ref() -> Optional[Tuple[int, int]]

# Get size from trailer
table.get_size() -> int
```

### IndirectRef

Represents an indirect reference (`n m R`):

```python
@dataclass
class IndirectRef:
    object_number: int
    generation_number: int
```

## Finding the XRef Offset

The `find_xref_offset()` function locates the table:

```python
def find_xref_offset(source: BinaryIO) -> int:
    # Searches backwards from EOF for 'startxref'
    # Returns the offset specified after 'startxref'
```

Example PDF trailer:
```
trailer
<< /Size 10 /Root 1 0 R >>
startxref
1234
%%EOF
```

The function finds `startxref` and returns `1234`.

## Parsing Traditional XRef Tables

The `XRefParser` class handles traditional xref tables:

```python
class XRefParser:
    def __init__(self, source: BinaryIO):
        self.source = source
        self.tokenizer = PDFTokenizer(source)
    
    def parse(self) -> XRefTable:
        # Detects format (traditional vs stream)
        # Parses entries and trailer
```

### Traditional Format

```
xref
0 5
0000000000 65535 f 
0000000015 00000 n 
0000000079 00000 n 
0000000143 00000 n 
0000000207 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
```

Format per entry:
- 10-digit offset (zero-padded)
- Space
- 5-digit generation (zero-padded)
- Space
- `f` (free) or `n` (in-use)
- End-of-line (CR, LF, or CRLF)

### Parsing Algorithm

```python
def _parse_traditional_xref(self) -> XRefTable:
    # 1. Expect 'xref' keyword
    # 2. Parse subsections: "start count"
    # 3. For each entry, parse: offset generation type
    # 4. Parse trailer dictionary
```

## Parsing XRef Streams (PDF 1.5+)

Modern PDFs may use xref streams instead:

```python
def _parse_xref_stream(self) -> XRefTable:
    # Parses stream objects that combine xref and trailer
    # Currently returns empty table (partial implementation)
```

XRef streams use binary encoding with field widths specified in `/W`.

## Handling Incremental Updates

PDFs can have multiple xref tables (incremental updates):

```python
def parse_xref(source: BinaryIO) -> XRefTable:
    # 1. Parse main xref
    # 2. Follow /Prev chain
    # 3. Merge entries (don't overwrite newer)
```

Example:
```
[Original PDF]
xref
0 5
...
trailer << /Size 5 /Root 1 0 R >>
%%EOF

[Update]
xref
0 5
...  (updated offsets)
trailer << /Size 5 /Root 1 0 R /Prev 1234 >>
%%EOF
```

## Trailer Parsing

The trailer dictionary contains essential info:

```python
def _parse_trailer(self) -> Dict[str, any]:
    # Parses << /Key value ... >>
    # Resolves indirect references
```

Standard trailer keys:
| Key | Description |
|-----|-------------|
| `/Size` | Total entries in xref |
| `/Root` | Reference to catalog |
| `/Info` | Reference to info dict |
| `/Encrypt` | Encryption dictionary |
| `/Prev` | Previous xref offset |
| `/ID` | File identifiers |

## Indirect Reference Resolution

The parser resolves indirect references in trailer:

```python
def _parse_value(self) -> any:
    # Detects pattern: INTEGER INTEGER R
    # Returns IndirectRef instead of raw integers
```

Example:
```
trailer
<< /Root 1 0 R >>    # Returns IndirectRef(1, 0)
```

## Common Issues

### 1. Incorrect Offsets

If xref offsets are wrong, objects can't be found:

```python
offset = xref_table.get_offset(5)
if offset is None:
    print("Object not found or is free")
```

### 2. Compressed Objects

Type 2 entries need special handling:

```python
entry = xref_table.get_entry(5)
if entry.entry_type == 2:
    # Object is in object stream
    stream_num = entry.object_stream_num
    index = entry.index_in_stream
    # Need to parse object stream
```

### 3. Hybrid Files

Some PDFs have both xref table and xref stream:

```python
# Parser tries traditional first, then stream
byte = self.source.read(1)
if byte == b"x":
    return self._parse_traditional_xref()
elif byte.isdigit():
    return self._parse_xref_stream()
```

## Integration with PDFReader

The PDFReader uses xref for object resolution:

```python
class PDFReader:
    def read(self):
        self._xref_table = parse_xref(self._file)
    
    def get_object(self, obj_num, gen_num=0):
        offset = self._xref_table.get_offset(obj_num)
        self._file.seek(offset)
        return self._parse_indirect_object(offset)
```

## Debugging

Enable debug logging to trace xref parsing:

```python
from pdf_lowlevel import configure_logger
configure_logger(level="DEBUG")
```

## Testing

See `tests/test_xref.py`:

```bash
uv run pytest tests/test_xref.py -v
```

Key test classes:
- `TestXRefEntry` - Entry creation
- `TestXRefTable` - Table operations
- `TestFindXRefOffset` - Offset finding
- `TestXRefParser` - Parsing logic
- `TestIndirectRefParsing` - Reference resolution