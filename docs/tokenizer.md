# PDF Tokenizer

The tokenizer is the first stage of PDF parsing, converting raw bytes into meaningful tokens.

## Overview

**Source:** `src/pdf_lowlevel/parser/tokenizer.py`

The `PDFTokenizer` class performs lexical analysis of PDF syntax, producing a stream of `Token` objects.

## Usage

### Basic Usage

```python
from pdf_lowlevel.parser.tokenizer import PDFTokenizer, tokenize_pdf

# From bytes
tokenizer = PDFTokenizer(pdf_bytes)
for token in tokenizer.tokenize():
    print(f"{token.type.name}: {token.value}")

# Convenience function
tokens = tokenize_pdf(pdf_bytes)
```

### Random Access

```python
tokenizer = PDFTokenizer(pdf_bytes)

# Get current position
pos = tokenizer.tell()

# Seek to specific offset
tokenizer.seek(100)

# Read token at that position
token = tokenizer.next_token()
```

### Within PDF Reader

```python
from pdf_lowlevel.parser.reader import open_pdf

with open_pdf("document.pdf") as pdf:
    # Tokenizer is used internally
    # Access via pdf._tokenizer if needed
    pass
```

## Token Types

The `TokenType` enum defines all token types:

### Literals
| Type | Example | Python Value |
|------|---------|--------------|
| `INTEGER` | `42` | `int(42)` |
| `REAL` | `3.14` | `float(3.14)` |
| `STRING` | `(Hello)` | `bytes(b'Hello')` |
| `HEX_STRING` | `<48656C6C6F>` | `bytes(b'Hello')` |
| `NAME` | `/Type` | `str('Type')` |
| `BOOLEAN` | `true` | `bool(True)` |
| `NULL` | `null` | `None` |

### Structures
| Type | PDF Syntax |
|------|------------|
| `ARRAY_START` | `[` |
| `ARRAY_END` | `]` |
| `DICT_START` | `<<` |
| `DICT_END` | `>>` |

### Objects
| Type | PDF Syntax |
|------|------------|
| `OBJ_START` | `obj` |
| `OBJ_END` | `endobj` |
| `STREAM_START` | `stream` |
| `STREAM_END` | `endstream` |

### Keywords
| Type | PDF Syntax |
|------|------------|
| `XREF` | `xref` |
| `TRAILER` | `trailer` |
| `STARTXREF` | `startxref` |
| `ENDOFFILE` | `%%EOF` |
| `INDIRECT_REF` | `R` |

### Special
| Type | Description |
|------|-------------|
| `COMMENT` | `%...` (comments) |
| `UNKNOWN` | Unrecognized token |

## Token Dataclass

Each token is a `Token` dataclass:

```python
@dataclass
class Token:
    type: TokenType      # Type of token
    value: Union[str, int, float, bytes, None]  # Parsed value
    offset: int          # Byte position in file
    line: int = 0        # Line number (for debugging)
    column: int = 0      # Column number (for debugging)
```

## Implementation Details

### Character Classes

The tokenizer recognizes PDF character classes:

```python
# Whitespace (ignored between tokens)
WHITESPACE = b" \t\r\n\x00\x0c"

# Delimiters (separate tokens)
DELIMITERS = b"()<>[]{}/%"
```

### Number Parsing

Numbers are parsed as integers or reals:

```python
def _read_number(self, first_byte: int) -> Token:
    # Reads digits, sign, and decimal point
    # Returns INTEGER if no decimal, REAL otherwise
```

Examples:
- `42` → `Token(INTEGER, 42)`
- `3.14` → `Token(REAL, 3.14)`
- `-5` → `Token(INTEGER, -5)`
- `+1.5` → `Token(REAL, 1.5)`

### Name Parsing

Names start with `/` and may contain `#` escapes:

```python
def _read_name(self) -> Token:
    # Handles #XX hex escapes
```

Examples:
- `/Name` → `Token(NAME, 'Name')`
- `/Type1` → `Token(NAME, 'Type1')`
- `/#20Name` → `Token(NAME, ' Name')` (space)

### String Parsing

#### Literal Strings

```python
def _read_literal_string(self) -> Token:
    # Handles nested parentheses
    # Processes escape sequences
```

Escape handling:
| Escape | Result |
|--------|--------|
| `\n` | newline |
| `\r` | carriage return |
| `\t` | tab |
| `\b` | backspace |
| `\f` | form feed |
| `\(` | literal `(` |
| `\)` | literal `)` |
| `\\` | literal `\` |
| `\ddd` | octal byte |

#### Hex Strings

```python
def _read_hex_string(self) -> Token:
    # Reads hex digits, ignores whitespace
    # Pads with 0 if odd length
```

### Comment Handling

Comments start with `%` and end at line break:

```python
def _skip_comment(self) -> Token:
    # Returns comment as token
    # Special case: %%EOF is tokenized separately
```

### Keyword Recognition

Keywords are recognized from a predefined set:

```python
KEYWORDS = {
    b"true": (TokenType.BOOLEAN, True),
    b"false": (TokenType.BOOLEAN, False),
    b"null": (TokenType.NULL, None),
    b"obj": (TokenType.OBJ_START, "obj"),
    b"endobj": (TokenType.OBJ_END, "endobj"),
    # ... etc
}
```

## Indirect Reference Detection

The tokenizer handles the ambiguity of indirect references (`n m R`):

```python
# When we see INTEGER, peek ahead
if token.type == TokenType.INTEGER:
    next_token = self._next_token()
    if next_token.type == TokenType.INTEGER:
        third_token = self._next_token()
        if third_token.type == TokenType.INDIRECT_REF:
            return PDFIndirectRef(token.value, next_token.value)
```

This is because `42` alone is an integer, but `42 0 R` is an indirect reference.

## Buffering and Lookahead

The tokenizer uses a buffer for lookahead:

```python
def _peek_byte(self, count: int = 1) -> Tuple[int, ...]:
    # Peek at bytes without consuming

def _unread_byte(self, byte: int) -> None:
    # Put byte back into buffer
```

This is essential for:
1. Detecting `<<` vs `<`
2. Detecting `>>` vs `>`
3. Indirect reference detection

## Common Patterns

### Parsing a Dictionary

```python
tokens = tokenize_pdf(pdf_bytes)
i = 0
while i < len(tokens):
    token = tokens[i]
    if token.type == TokenType.DICT_START:
        # Parse dictionary
        d = {}
        i += 1
        while tokens[i].type != TokenType.DICT_END:
            key = tokens[i].value
            i += 1
            value = tokens[i].value
            i += 1
            d[key] = value
    i += 1
```

### Finding an Object

```python
def find_object(tokens, obj_num, gen_num):
    for i, token in enumerate(tokens):
        if (token.type == TokenType.INTEGER and 
            token.value == obj_num):
            if (tokens[i+1].type == TokenType.INTEGER and
                tokens[i+1].value == gen_num and
                tokens[i+2].type == TokenType.OBJ_START):
                # Found object, parse until endobj
                return parse_object(tokens, i+3)
    return None
```

## Error Handling

The tokenizer is permissive - it returns `UNKNOWN` tokens rather than raising errors:

```python
# Unknown token
return Token(TokenType.UNKNOWN, token_str, start_offset)
```

This allows higher-level parsers to handle errors contextually.

## Performance Considerations

1. **Lazy iteration**: `tokenize()` is a generator, not a list
2. **Position tracking**: `tell()` and `seek()` allow random access
3. **Minimal copying**: Strings are decoded only when needed

## Testing

See `tests/test_tokenizer.py` for comprehensive tests:

```bash
uv run pytest tests/test_tokenizer.py -v
```

Key test classes:
- `TestPDFTokenizer` - Basic tokenization
- `TestToken` - Token dataclass
- `TestTokenType` - Enum coverage