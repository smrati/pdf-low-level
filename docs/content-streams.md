# Content Stream Processing

Content streams contain the actual page content - text, graphics, and images.

## Overview

**Source:** `src/pdf_lowlevel/content/stream.py`

The `ContentStreamParser` interprets PDF content stream operators to extract text with positioning information.

## What is a Content Stream?

A content stream is a sequence of PDF operators that describe what to render:

```
BT
/F1 12 Tf
100 700 Td
(Hello World) Tj
ET
```

This means:
1. `BT` - Begin text object
2. `/F1 12 Tf` - Set font F1 at 12pt
3. `100 700 Td` - Move to position (100, 700)
4. `(Hello World) Tj` - Draw text
5. `ET` - End text object

## Usage

### Basic Parsing

```python
from pdf_lowlevel.content.stream import ContentStreamParser, parse_content_stream

# Parse stream data
parser = ContentStreamParser(stream_data)
elements = parser.parse()

for elem in elements:
    print(f"'{elem.text}' at ({elem.x}, {elem.y})")
```

### With Font Resolution

```python
def resolve_font(font_name: str) -> dict:
    # Return font info (widths, encoding, etc.)
    return {"widths": {65: 700, 66: 660, ...}}

parser = ContentStreamParser(stream_data)
parser.font_resolver = resolve_font
elements = parser.parse()
```

### Within PDFReader

```python
from pdf_lowlevel.parser.reader import open_pdf

with open_pdf("document.pdf") as pdf:
    content = pdf.get_page_contents(0)  # Decoded stream
    parser = ContentStreamParser(content)
    elements = parser.parse()
```

## TextElement Output

The parser outputs `TextElement` objects:

```python
@dataclass
class TextElement:
    text: str           # Decoded text
    x: float            # Lower-left x in user space
    y: float            # Baseline y in user space
    width: float        # Width of text
    height: float       # Height (font size)
    
    font_name: str      # Font name from Tf
    font_size: float    # Font size from Tf
    page_number: int    # Set externally
    
    # Text state
    char_spacing: float         # Tc
    word_spacing: float         # Tw
    horizontal_scaling: float   # Tz
    text_render_mode: int       # Tr
    
    raw_bytes: bytes    # Original bytes (for debugging)
```

## PDF Text Operators

### Text Object Operators

| Operator | Description |
|----------|-------------|
| `BT` | Begin text object |
| `ET` | End text object |

```python
def _op_bt(self, operands):
    self.in_text_object = True
    self.graphics_stack.text_position.move_to(0, 0)

def _op_et(self, operands):
    self.in_text_object = False
```

### Text State Operators

| Operator | Operands | Description |
|----------|----------|-------------|
| `Tf` | font_name size | Set font and size |
| `Tc` | charSpacing | Set character spacing |
| `Tw` | wordSpacing | Set word spacing |
| `Tz` | scaling | Set horizontal scaling (%) |
| `TL` | leading | Set text leading |
| `Tr` | render | Set render mode |
| `Ts` | rise | Set text rise |

```python
def _op_tf(self, operands):
    font_name = operands[0]
    font_size = float(operands[1])
    self.graphics_stack.text_state.font_name = font_name
    self.graphics_stack.text_state.font_size = font_size
```

### Text Positioning Operators

| Operator | Operands | Description |
|----------|----------|-------------|
| `Td` | tx ty | Move text position |
| `TD` | tx ty | Move and set leading |
| `T*` | - | Move to next line |
| `Tm` | a b c d e f | Set text matrix |

```python
def _op_td(self, operands):
    tx, ty = float(operands[0]), float(operands[1])
    self.graphics_stack.text_position.move_by(tx, ty)

def _op_tm(self, operands):
    self.graphics_stack.text_position.set_matrix(
        float(operands[0]), float(operands[1]),
        float(operands[2]), float(operands[3]),
        float(operands[4]), float(operands[5]),
    )
```

### Text Showing Operators

| Operator | Operands | Description |
|----------|----------|-------------|
| `Tj` | string | Show text |
| `TJ` | [array] | Show text with positioning |
| `'` | string | Next line + show text |
| `"` | aw ac string | Set spacing + next line + show |

```python
def _op_tj(self, operands):
    text_bytes = operands[0]
    self._emit_text(text_bytes)

def _op_TJ(self, operands):
    array = operands[0]
    for item in array:
        if isinstance(item, bytes):
            self._emit_text(item, adjust_position=False)
        elif isinstance(item, (int, float)):
            # Position adjustment in 1/1000ths of em
            adjustment = -float(item) / 1000.0 * font_size
            self.graphics_stack.text_position.move_by(adjustment, 0)
```

## Graphics State Operators

| Operator | Description |
|----------|-------------|
| `q` | Save graphics state |
| `Q` | Restore graphics state |
| `cm` | Concatenate matrix |

```python
def _op_q(self, operands):
    self.graphics_stack.save()

def _op_Q(self, operands):
    self.graphics_stack.restore()

def _op_cm(self, operands):
    matrix = Matrix(*operands)
    self.graphics_stack.modify_ctm(matrix)
```

## Parsing Algorithm

### Operator Iteration

```python
def _iter_operators(self) -> Generator[ContentOperator, None, None]:
    operands = []
    
    while self.pos < len(self.data):
        # Skip whitespace and comments
        self._skip_whitespace()
        
        # Parse value
        value = self._parse_value()
        
        if is_operator(value):
            yield ContentOperator(value, operands)
            operands = []
        else:
            operands.append(value)
```

### Value Parsing

```python
def _parse_value(self) -> Any:
    byte = self.data[self.pos]
    
    if byte == ord('('):
        return self._parse_literal_string()
    elif byte == ord('<'):
        return self._parse_hex_string()
    elif byte == ord('['):
        return self._parse_array()
    elif byte == ord('/'):
        return self._parse_name()
    elif byte.isdigit() or byte in b'+-.':
        return self._parse_number()
    else:
        return self._parse_operator()
```

## Text Position Calculation

### Coordinate Transformation

Text position is computed by combining:
1. **Text Matrix** (Tm) - Text space to user space
2. **CTM** (Current Transformation Matrix) - User space to device space

```python
def _emit_text(self, text_bytes, adjust_position=True):
    text_pos = self.graphics_stack.text_position
    ctm = self.graphics_stack.ctm
    
    # Combine matrices
    render_matrix = ctm * text_pos.text_matrix
    
    # Get position in user space
    x, y = render_matrix.transform_point(0, 0)
    
    # Create element
    element = TextElement(text=text, x=x, y=y, ...)
    
    # Update position for next text
    if adjust_position:
        width = self._get_text_width(text_bytes)
        self.graphics_stack.text_position.move_by(width, 0)
```

## Text Decoding

### Decoding Process

```python
def _decode_text(self, text_bytes: bytes) -> str:
    # 1. Try UTF-16BE (BOM detection)
    if text_bytes.startswith(b'\xfe\xff'):
        return text_bytes.decode('utf-16-be')
    
    # 2. Try UTF-8
    try:
        return text_bytes.decode('utf-8')
    except UnicodeDecodeError:
        pass
    
    # 3. Fall back to Latin-1
    result = []
    for byte in text_bytes:
        if 32 <= byte <= 126:
            result.append(chr(byte))
        else:
            result.append(chr(byte))  # Latin-1 mapping
    
    return ''.join(result)
```

### Font Encoding

For proper decoding, font encoding is needed:

```python
def _decode_with_font(self, text_bytes, font_info):
    encoding = font_info.get('encoding')
    to_unicode = font_info.get('to_unicode')
    
    if to_unicode:
        # Use ToUnicode CMap
        return self._apply_cmap(text_bytes, to_unicode)
    elif encoding == 'WinAnsiEncoding':
        return self._apply_win_ansi(text_bytes)
    else:
        return self._decode_text(text_bytes)
```

## Text Width Calculation

```python
def _get_text_width(self, text_bytes: bytes) -> float:
    text_state = self.graphics_stack.text_state
    
    widths = self._get_font_widths()
    width = 0.0
    
    for byte in text_bytes:
        # Width in 1/1000ths of em
        char_width = widths.get(byte, 500)
        
        # Convert to text space
        w = char_width / 1000.0 * text_state.font_size
        width += w
        
        # Add spacing
        width += text_state.char_spacing
        if byte == 32:  # Space
            width += text_state.word_spacing
    
    return width
```

## Operator Handler Mapping

```python
_operator_handlers = {
    # Text object
    "BT": _op_bt,
    "ET": _op_et,
    
    # Graphics state
    "q": _op_q,
    "Q": _op_Q,
    "cm": _op_cm,
    
    # Text state
    "Tf": _op_tf,
    "Tc": _op_tc,
    "Tw": _op_tw,
    "Tz": _op_tz,
    "TL": _op_tl,
    "Tr": _op_tr,
    "Ts": _op_ts,
    
    # Text positioning
    "Td": _op_td,
    "TD": _op_TD,
    "T*": _op_t_star,
    "Tm": _op_tm,
    
    # Text showing
    "Tj": _op_tj,
    "TJ": _op_TJ,
    "'": _op_quote,
    '"': _op_double_quote,
}
```

## Extending the Parser

### Adding New Operators

```python
# Custom handler
def _op_custom(self, operands):
    # Handle custom operator
    pass

# Register handler
parser._operator_handlers["Custom"] = _op_custom
```

### Custom Font Resolution

```python
class FontResolver:
    def __call__(self, font_name: str) -> dict:
        # Return font info
        return {
            "widths": self._load_widths(font_name),
            "encoding": self._get_encoding(font_name),
        }

parser.font_resolver = FontResolver()
```

## Common Issues

### 1. Missing Text

- Font not in resources
- Text in Form XObjects (not yet supported)
- Text rendered as paths (Type 3 fonts)

### 2. Incorrect Positions

- CTM not properly tracked
- Nested q/Q state saves
- Text matrix not reset

### 3. Garbled Text

- Font encoding not resolved
- ToUnicode CMap not parsed
- Non-standard encoding

## Testing

The content stream parser is tested indirectly via `test_extractor.py`:

```bash
uv run pytest tests/test_extractor.py -v