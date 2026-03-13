# Tokenizer Tests (test_tokenizer.py)

This document describes the **47 tests** for PDF tokenization in `tests/test_tokenizer.py`.

## Overview

The tokenizer tests verify that `PDFTokenizer` correctly converts raw PDF bytes into `Token` objects.

**Source:** `src/pdf_lowlevel/parser/tokenizer.py`

## Test Classes

### TestPDFTokenizer (47 tests)

Main test class for tokenizer functionality.

---

## Number Tokenization

### test_tokenize_positive_integer
Verifies positive integer tokenization.

```python
def test_tokenize_positive_integer(self):
    tokenizer = PDFTokenizer(b"123")
    token = tokenizer.next_token()
    assert token.type == TokenType.INTEGER
    assert token.value == 123
```

### test_tokenize_negative_integer
Verifies negative integer tokenization.

```python
def test_tokenize_negative_integer(self):
    tokenizer = PDFTokenizer(b"-42")
    token = tokenizer.next_token()
    assert token.type == TokenType.INTEGER
    assert token.value == -42
```

### test_tokenize_zero
Verifies zero tokenization.

```python
def test_tokenize_zero(self):
    tokenizer = PDFTokenizer(b"0")
    token = tokenizer.next_token()
    assert token.type == TokenType.INTEGER
    assert token.value == 0
```

### test_tokenize_positive_with_plus
Verifies integer with explicit plus sign.

```python
def test_tokenize_positive_with_plus(self):
    tokenizer = PDFTokenizer(b"+99")
    token = tokenizer.next_token()
    assert token.type == TokenType.INTEGER
    assert token.value == 99
```

### test_tokenize_real_number
Verifies real number tokenization.

```python
def test_tokenize_real_number(self):
    tokenizer = PDFTokenizer(b"3.14")
    token = tokenizer.next_token()
    assert token.type == TokenType.REAL
    assert token.value == 3.14
```

### test_tokenize_negative_real
Verifies negative real number tokenization.

```python
def test_tokenize_negative_real(self):
    tokenizer = PDFTokenizer(b"-0.5")
    token = tokenizer.next_token()
    assert token.type == TokenType.REAL
    assert token.value == -0.5
```

### test_tokenize_real_with_trailing_dot
Verifies real number like 12.0.

```python
def test_tokenize_real_with_trailing_dot(self):
    tokenizer = PDFTokenizer(b"12.0")
    token = tokenizer.next_token()
    assert token.type == TokenType.REAL
    assert token.value == 12.0
```

---

## Name Tokenization

### test_tokenize_simple_name
Verifies simple name tokenization.

```python
def test_tokenize_simple_name(self):
    tokenizer = PDFTokenizer(b"/Name")
    token = tokenizer.next_token()
    assert token.type == TokenType.NAME
    assert token.value == "Name"
```

### test_tokenize_type_name
Verifies /Type name tokenization.

```python
def test_tokenize_type_name(self):
    tokenizer = PDFTokenizer(b"/Type")
    token = tokenizer.next_token()
    assert token.type == TokenType.NAME
    assert token.value == "Type"
```

### test_tokenize_name_with_special_chars
Verifies names with special characters.

```python
def test_tokenize_name_with_special_chars(self):
    tokenizer = PDFTokenizer(b"/A;Name_With-Various***Chars")
    token = tokenizer.next_token()
    assert token.type == TokenType.NAME
    assert token.value == "A;Name_With-Various***Chars"
```

### test_tokenize_name_with_hash_escape
Verifies names with # escape sequences.

```python
def test_tokenize_name_with_hash_escape(self):
    tokenizer = PDFTokenizer(b"/Name#20With#20Spaces")
    token = tokenizer.next_token()
    assert token.type == TokenType.NAME
    assert token.value == "Name With Spaces"  # #20 is space
```

---

## String Tokenization

### test_tokenize_simple_string
Verifies simple literal string tokenization.

```python
def test_tokenize_simple_string(self):
    tokenizer = PDFTokenizer(b"(Hello)")
    token = tokenizer.next_token()
    assert token.type == TokenType.STRING
    assert token.value == b"Hello"
```

### test_tokenize_string_with_spaces
Verifies strings with spaces.

```python
def test_tokenize_string_with_spaces(self):
    tokenizer = PDFTokenizer(b"(Hello World)")
    token = tokenizer.next_token()
    assert token.type == TokenType.STRING
    assert token.value == b"Hello World"
```

### test_tokenize_empty_string
Verifies empty string tokenization.

```python
def test_tokenize_empty_string(self):
    tokenizer = PDFTokenizer(b"()")
    token = tokenizer.next_token()
    assert token.type == TokenType.STRING
    assert token.value == b""
```

### test_tokenize_nested_parens
Verifies strings with nested parentheses.

```python
def test_tokenize_nested_parens(self):
    tokenizer = PDFTokenizer(b"(Hello (World))")
    token = tokenizer.next_token()
    assert token.type == TokenType.STRING
    assert token.value == b"Hello (World)"
```

### test_tokenize_escaped_parens
Verifies strings with escaped parentheses.

```python
def test_tokenize_escaped_parens(self):
    tokenizer = PDFTokenizer(b"(Hello \\(World\\))")
    token = tokenizer.next_token()
    assert token.type == TokenType.STRING
    assert token.value == b"Hello (World)"
```

### test_tokenize_escaped_newline
Verifies strings with escaped newline.

```python
def test_tokenize_escaped_newline(self):
    tokenizer = PDFTokenizer(b"(Line1\\nLine2)")
    token = tokenizer.next_token()
    assert token.type == TokenType.STRING
    assert token.value == b"Line1\nLine2"
```

---

## Hex String Tokenization

### test_tokenize_simple_hex_string
Verifies simple hex string tokenization.

```python
def test_tokenize_simple_hex_string(self):
    tokenizer = PDFTokenizer(b"<48656C6C6F>")
    token = tokenizer.next_token()
    assert token.type == TokenType.HEX_STRING
    assert token.value == b"Hello"
```

### test_tokenize_hex_string_odd_length
Verifies hex string with odd length (pads with 0).

```python
def test_tokenize_hex_string_odd_length(self):
    tokenizer = PDFTokenizer(b"<41>")
    token = tokenizer.next_token()
    assert token.type == TokenType.HEX_STRING
    assert token.value[0] == ord("A")
```

### test_tokenize_empty_hex_string
Verifies empty hex string tokenization.

```python
def test_tokenize_empty_hex_string(self):
    tokenizer = PDFTokenizer(b"<>")
    token = tokenizer.next_token()
    assert token.type == TokenType.HEX_STRING
    assert token.value == b""
```

---

## Boolean and Null Tokenization

### test_tokenize_true
Verifies true boolean tokenization.

```python
def test_tokenize_true(self):
    tokenizer = PDFTokenizer(b"true")
    token = tokenizer.next_token()
    assert token.type == TokenType.BOOLEAN
    assert token.value == True
```

### test_tokenize_false
Verifies false boolean tokenization.

```python
def test_tokenize_false(self):
    tokenizer = PDFTokenizer(b"false")
    token = tokenizer.next_token()
    assert token.type == TokenType.BOOLEAN
    assert token.value == False
```

### test_tokenize_null
Verifies null tokenization.

```python
def test_tokenize_null(self):
    tokenizer = PDFTokenizer(b"null")
    token = tokenizer.next_token()
    assert token.type == TokenType.NULL
    assert token.value is None
```

---

## Array Tokenization

### test_tokenize_array_start
Verifies array start delimiter.

```python
def test_tokenize_array_start(self):
    tokenizer = PDFTokenizer(b"[")
    token = tokenizer.next_token()
    assert token.type == TokenType.ARRAY_START
```

### test_tokenize_array_end
Verifies array end delimiter.

```python
def test_tokenize_array_end(self):
    tokenizer = PDFTokenizer(b"]")
    token = tokenizer.next_token()
    assert token.type == TokenType.ARRAY_END
```

### test_tokenize_simple_array
Verifies complete array tokenization.

```python
def test_tokenize_simple_array(self):
    tokenizer = PDFTokenizer(b"[1 2 3]")
    tokens = tokenizer.get_all_tokens()
    assert len(tokens) == 5
    assert tokens[0].type == TokenType.ARRAY_START
    assert tokens[1].value == 1
    assert tokens[4].type == TokenType.ARRAY_END
```

---

## Dictionary Tokenization

### test_tokenize_dict_start
Verifies dictionary start delimiter.

```python
def test_tokenize_dict_start(self):
    tokenizer = PDFTokenizer(b"<<")
    token = tokenizer.next_token()
    assert token.type == TokenType.DICT_START
```

### test_tokenize_dict_end
Verifies dictionary end delimiter.

```python
def test_tokenize_dict_end(self):
    tokenizer = PDFTokenizer(b">>")
    token = tokenizer.next_token()
    assert token.type == TokenType.DICT_END
```

### test_tokenize_simple_dict
Verifies complete dictionary tokenization.

```python
def test_tokenize_simple_dict(self):
    tokenizer = PDFTokenizer(b"<< /Name /Value >>")
    tokens = tokenizer.get_all_tokens()
    assert len(tokens) == 4
    assert tokens[0].type == TokenType.DICT_START
    assert tokens[1].type == TokenType.NAME
    assert tokens[3].type == TokenType.DICT_END
```

---

## Keyword Tokenization

### test_tokenize_obj_keyword
Verifies `obj` keyword.

```python
def test_tokenize_obj_keyword(self):
    tokenizer = PDFTokenizer(b"obj")
    token = tokenizer.next_token()
    assert token.type == TokenType.OBJ_START
```

### test_tokenize_endobj_keyword
Verifies `endobj` keyword.

```python
def test_tokenize_endobj_keyword(self):
    tokenizer = PDFTokenizer(b"endobj")
    token = tokenizer.next_token()
    assert token.type == TokenType.OBJ_END
```

### test_tokenize_stream_keyword
Verifies `stream` keyword.

```python
def test_tokenize_stream_keyword(self):
    tokenizer = PDFTokenizer(b"stream")
    token = tokenizer.next_token()
    assert token.type == TokenType.STREAM_START
```

### test_tokenize_endstream_keyword
Verifies `endstream` keyword.

```python
def test_tokenize_endstream_keyword(self):
    tokenizer = PDFTokenizer(b"endstream")
    token = tokenizer.next_token()
    assert token.type == TokenType.STREAM_END
```

### test_tokenize_trailer_keyword
Verifies `trailer` keyword.

```python
def test_tokenize_trailer_keyword(self):
    tokenizer = PDFTokenizer(b"trailer")
    token = tokenizer.next_token()
    assert token.type == TokenType.TRAILER
```

### test_tokenize_xref_keyword
Verifies `xref` keyword.

```python
def test_tokenize_xref_keyword(self):
    tokenizer = PDFTokenizer(b"xref")
    token = tokenizer.next_token()
    assert token.type == TokenType.XREF
```

### test_tokenize_R_keyword
Verifies `R` (indirect reference) keyword.

```python
def test_tokenize_R_keyword(self):
    tokenizer = PDFTokenizer(b"R")
    token = tokenizer.next_token()
    assert token.type == TokenType.INDIRECT_REF
```

---

## Comment Tokenization

### test_tokenize_comment
Verifies comment tokenization.

```python
def test_tokenize_comment(self):
    tokenizer = PDFTokenizer(b"% This is a comment\n")
    token = tokenizer.next_token()
    assert token.type == TokenType.COMMENT
    assert "% This is a comment" in token.value
```

### test_tokenize_eof_marker
Verifies `%%EOF` marker tokenization.

```python
def test_tokenize_eof_marker(self):
    tokenizer = PDFTokenizer(b"%%EOF")
    token = tokenizer.next_token()
    assert token.type == TokenType.ENDOFFILE
```

---

## Indirect Reference Tokenization

### test_tokenize_indirect_reference
Verifies indirect reference pattern (`n m R`).

```python
def test_tokenize_indirect_reference(self):
    tokenizer = PDFTokenizer(b"1 0 R")
    tokens = tokenizer.get_all_tokens()
    assert len(tokens) == 3
    assert tokens[0].type == TokenType.INTEGER
    assert tokens[0].value == 1
    assert tokens[1].type == TokenType.INTEGER
    assert tokens[1].value == 0
    assert tokens[2].type == TokenType.INDIRECT_REF
```

---

## Whitespace Handling

### test_skip_whitespace_spaces
Verifies spaces are skipped.

```python
def test_skip_whitespace_spaces(self):
    tokenizer = PDFTokenizer(b"   123")
    token = tokenizer.next_token()
    assert token.type == TokenType.INTEGER
    assert token.value == 123
```

### test_skip_whitespace_tabs
Verifies tabs are skipped.

```python
def test_skip_whitespace_tabs(self):
    tokenizer = PDFTokenizer(b"\t\t42")
    token = tokenizer.next_token()
    assert token.type == TokenType.INTEGER
    assert token.value == 42
```

### test_skip_whitespace_newlines
Verifies newlines are skipped.

```python
def test_skip_whitespace_newlines(self):
    tokenizer = PDFTokenizer(b"\n\n99")
    token = tokenizer.next_token()
    assert token.type == TokenType.INTEGER
    assert token.value == 99
```

### test_skip_mixed_whitespace
Verifies mixed whitespace is skipped.

```python
def test_skip_mixed_whitespace(self):
    tokenizer = PDFTokenizer(b" \t\n\r 123")
    token = tokenizer.next_token()
    assert token.type == TokenType.INTEGER
    assert token.value == 123
```

---

## Token Position Tracking

### test_token_offset
Verifies token offsets are tracked.

```python
def test_token_offset(self):
    tokenizer = PDFTokenizer(b"123 456")
    token1 = tokenizer.next_token()
    token2 = tokenizer.next_token()
    assert token1.offset == 0
    assert token2.offset > token1.offset
```

---

## Complex Tokenization

### test_tokenize_complex_object
Verifies tokenizing a complex PDF object.

```python
def test_tokenize_complex_object(self):
    pdf_bytes = b"""1 0 obj
<< /Type /Catalog /Pages 2 0 R /Metadata 5 0 R >>
endobj"""
    tokenizer = PDFTokenizer(pdf_bytes)
    tokens = tokenizer.get_all_tokens()

    assert any(t.type == TokenType.INTEGER and t.value == 1 for t in tokens)
    assert any(t.type == TokenType.OBJ_START for t in tokens)
    assert any(t.type == TokenType.DICT_START for t in tokens)
    assert any(t.type == TokenType.NAME and t.value == "Type" for t in tokens)
    assert any(t.type == TokenType.INDIRECT_REF for t in tokens)
    assert any(t.type == TokenType.OBJ_END for t in tokens)
```

### test_tokenize_pdf_header
Verifies PDF header tokenization.

```python
def test_tokenize_pdf_header(self):
    tokenizer = PDFTokenizer(b"%PDF-1.4")
    token = tokenizer.next_token()
    assert token.type == TokenType.COMMENT
    assert "%PDF-1.4" in token.value
```

---

## Edge Cases

### test_empty_input
Verifies empty input handling.

```python
def test_empty_input(self):
    tokenizer = PDFTokenizer(b"")
    token = tokenizer.next_token()
    assert token is None
```

### test_only_whitespace
Verifies whitespace-only input.

```python
def test_only_whitespace(self):
    tokenizer = PDFTokenizer(b"   \t\n   ")
    token = tokenizer.next_token()
    assert token is None
```

### test_seek_and_tell
Verifies seek and tell methods.

```python
def test_seek_and_tell(self):
    tokenizer = PDFTokenizer(b"123 456 789")
    tokenizer.next_token()  # 123
    pos = tokenizer.tell()
    tokenizer.next_token()  # 456
    tokenizer.seek(pos)
    token = tokenizer.next_token()
    assert token.value == 456
```

### test_tokenize_from_file_like
Verifies tokenizing from file-like object.

```python
def test_tokenize_from_file_like(self):
    file_obj = BytesIO(b"123 456")
    tokenizer = PDFTokenizer(file_obj)
    token = tokenizer.next_token()
    assert token.type == TokenType.INTEGER
    assert token.value == 123
```

---

## TestTokenizePdfFunction

### test_tokenize_pdf_returns_list
Verifies `tokenize_pdf` returns a list.

```python
def test_tokenize_pdf_returns_list(self):
    tokens = tokenize_pdf(b"1 2 3")
    assert isinstance(tokens, list)
```

### test_tokenize_pdf_all_tokens
Verifies `tokenize_pdf` returns all tokens.

```python
def test_tokenize_pdf_all_tokens(self):
    tokens = tokenize_pdf(b"[1 2 3]")
    assert len(tokens) == 5  # [, 1, 2, 3, ]
```

---

## TestToken

### test_token_repr
Verifies token string representation.

```python
def test_token_repr(self):
    token = Token(TokenType.INTEGER, 42, 0)
    repr_str = repr(token)
    assert "INTEGER" in repr_str
    assert "42" in repr_str
```

### test_token_with_bytes_value
Verifies token with bytes value.

```python
def test_token_with_bytes_value(self):
    token = Token(TokenType.STRING, b"Hello", 0)
    assert token.value == b"Hello"
```

---

## TestTokenType

### test_all_token_types_exist
Verifies all expected token types exist.

```python
def test_all_token_types_exist(self):
    expected_types = [
        "INTEGER", "REAL", "STRING", "HEX_STRING", "NAME",
        "BOOLEAN", "NULL", "ARRAY_START", "ARRAY_END",
        "DICT_START", "DICT_END", "STREAM_START", "STREAM_END",
        "OBJ_START", "OBJ_END", "XREF", "TRAILER", "STARTXREF",
        "ENDOFFILE", "INDIRECT_REF", "COMMENT", "UNKNOWN",
    ]
    for type_name in expected_types:
        assert hasattr(TokenType, type_name)