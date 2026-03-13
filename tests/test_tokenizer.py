"""
Unit tests for PDF tokenizer.

Tests tokenization of PDF syntax elements:
- Numbers (integers, reals)
- Strings (literal, hex)
- Names
- Booleans
- Null
- Arrays and dictionaries
- Comments
- Keywords
"""

import pytest
from io import BytesIO

from pdf_lowlevel.parser.tokenizer import (
    PDFTokenizer,
    Token,
    TokenType,
    tokenize_pdf,
)


class TestPDFTokenizer:
    """Tests for PDFTokenizer class."""

    # ========================================================================
    # Number Tokenization
    # ========================================================================

    def test_tokenize_positive_integer(self):
        """Test tokenizing positive integers."""
        tokenizer = PDFTokenizer(b"123")
        token = tokenizer.next_token()
        assert token.type == TokenType.INTEGER
        assert token.value == 123

    def test_tokenize_negative_integer(self):
        """Test tokenizing negative integers."""
        tokenizer = PDFTokenizer(b"-42")
        token = tokenizer.next_token()
        assert token.type == TokenType.INTEGER
        assert token.value == -42

    def test_tokenize_zero(self):
        """Test tokenizing zero."""
        tokenizer = PDFTokenizer(b"0")
        token = tokenizer.next_token()
        assert token.type == TokenType.INTEGER
        assert token.value == 0

    def test_tokenize_positive_with_plus(self):
        """Test tokenizing integer with explicit plus sign."""
        tokenizer = PDFTokenizer(b"+99")
        token = tokenizer.next_token()
        assert token.type == TokenType.INTEGER
        assert token.value == 99

    def test_tokenize_real_number(self):
        """Test tokenizing real numbers."""
        tokenizer = PDFTokenizer(b"3.14")
        token = tokenizer.next_token()
        assert token.type == TokenType.REAL
        assert token.value == 3.14

    def test_tokenize_negative_real(self):
        """Test tokenizing negative real numbers."""
        tokenizer = PDFTokenizer(b"-0.5")
        token = tokenizer.next_token()
        assert token.type == TokenType.REAL
        assert token.value == -0.5

    def test_tokenize_real_with_trailing_dot(self):
        """Test tokenizing real number like 12.0."""
        tokenizer = PDFTokenizer(b"12.0")
        token = tokenizer.next_token()
        assert token.type == TokenType.REAL
        assert token.value == 12.0

    # ========================================================================
    # Name Tokenization
    # ========================================================================

    def test_tokenize_simple_name(self):
        """Test tokenizing simple names."""
        tokenizer = PDFTokenizer(b"/Name")
        token = tokenizer.next_token()
        assert token.type == TokenType.NAME
        assert token.value == "Name"

    def test_tokenize_type_name(self):
        """Test tokenizing /Type name."""
        tokenizer = PDFTokenizer(b"/Type")
        token = tokenizer.next_token()
        assert token.type == TokenType.NAME
        assert token.value == "Type"

    def test_tokenize_name_with_special_chars(self):
        """Test tokenizing names with special characters."""
        tokenizer = PDFTokenizer(b"/A;Name_With-Various***Chars")
        token = tokenizer.next_token()
        assert token.type == TokenType.NAME
        assert token.value == "A;Name_With-Various***Chars"

    def test_tokenize_name_with_hash_escape(self):
        """Test tokenizing names with # escape sequences."""
        tokenizer = PDFTokenizer(b"/Name#20With#20Spaces")
        token = tokenizer.next_token()
        assert token.type == TokenType.NAME
        # #20 is space character
        assert token.value == "Name With Spaces"

    # ========================================================================
    # String Tokenization
    # ========================================================================

    def test_tokenize_simple_string(self):
        """Test tokenizing simple literal strings."""
        tokenizer = PDFTokenizer(b"(Hello)")
        token = tokenizer.next_token()
        assert token.type == TokenType.STRING
        assert token.value == b"Hello"

    def test_tokenize_string_with_spaces(self):
        """Test tokenizing strings with spaces."""
        tokenizer = PDFTokenizer(b"(Hello World)")
        token = tokenizer.next_token()
        assert token.type == TokenType.STRING
        assert token.value == b"Hello World"

    def test_tokenize_empty_string(self):
        """Test tokenizing empty strings."""
        tokenizer = PDFTokenizer(b"()")
        token = tokenizer.next_token()
        assert token.type == TokenType.STRING
        assert token.value == b""

    def test_tokenize_nested_parens(self):
        """Test tokenizing strings with nested parentheses."""
        tokenizer = PDFTokenizer(b"(Hello (World))")
        token = tokenizer.next_token()
        assert token.type == TokenType.STRING
        assert token.value == b"Hello (World)"

    def test_tokenize_escaped_parens(self):
        """Test tokenizing strings with escaped parentheses."""
        tokenizer = PDFTokenizer(b"(Hello \\(World\\))")
        token = tokenizer.next_token()
        assert token.type == TokenType.STRING
        assert token.value == b"Hello (World)"

    def test_tokenize_escaped_newline(self):
        """Test tokenizing strings with escaped newline."""
        tokenizer = PDFTokenizer(b"(Line1\\nLine2)")
        token = tokenizer.next_token()
        assert token.type == TokenType.STRING
        assert token.value == b"Line1\nLine2"

    # ========================================================================
    # Hex String Tokenization
    # ========================================================================

    def test_tokenize_simple_hex_string(self):
        """Test tokenizing simple hex strings."""
        tokenizer = PDFTokenizer(b"<48656C6C6F>")
        token = tokenizer.next_token()
        assert token.type == TokenType.HEX_STRING
        assert token.value == b"Hello"

    def test_tokenize_hex_string_odd_length(self):
        """Test hex string with odd length (should pad with 0)."""
        tokenizer = PDFTokenizer(b"<41>")
        token = tokenizer.next_token()
        assert token.type == TokenType.HEX_STRING
        # 41 -> 41 0 -> b'A\x00' or just b'A' depending on implementation
        # Most implementations pad with 0
        assert token.value[0] == ord("A")

    def test_tokenize_empty_hex_string(self):
        """Test tokenizing empty hex strings."""
        tokenizer = PDFTokenizer(b"<>")
        token = tokenizer.next_token()
        assert token.type == TokenType.HEX_STRING
        assert token.value == b""

    # ========================================================================
    # Boolean and Null Tokenization
    # ========================================================================

    def test_tokenize_true(self):
        """Test tokenizing true boolean."""
        tokenizer = PDFTokenizer(b"true")
        token = tokenizer.next_token()
        assert token.type == TokenType.BOOLEAN
        assert token.value == True

    def test_tokenize_false(self):
        """Test tokenizing false boolean."""
        tokenizer = PDFTokenizer(b"false")
        token = tokenizer.next_token()
        assert token.type == TokenType.BOOLEAN
        assert token.value == False

    def test_tokenize_null(self):
        """Test tokenizing null."""
        tokenizer = PDFTokenizer(b"null")
        token = tokenizer.next_token()
        assert token.type == TokenType.NULL
        assert token.value is None

    # ========================================================================
    # Array Tokenization
    # ========================================================================

    def test_tokenize_array_start(self):
        """Test tokenizing array start."""
        tokenizer = PDFTokenizer(b"[")
        token = tokenizer.next_token()
        assert token.type == TokenType.ARRAY_START

    def test_tokenize_array_end(self):
        """Test tokenizing array end."""
        tokenizer = PDFTokenizer(b"]")
        token = tokenizer.next_token()
        assert token.type == TokenType.ARRAY_END

    def test_tokenize_simple_array(self):
        """Test tokenizing a simple array."""
        tokenizer = PDFTokenizer(b"[1 2 3]")
        tokens = tokenizer.get_all_tokens()
        assert len(tokens) == 5
        assert tokens[0].type == TokenType.ARRAY_START
        assert tokens[1].type == TokenType.INTEGER
        assert tokens[1].value == 1
        assert tokens[4].type == TokenType.ARRAY_END

    # ========================================================================
    # Dictionary Tokenization
    # ========================================================================

    def test_tokenize_dict_start(self):
        """Test tokenizing dictionary start."""
        tokenizer = PDFTokenizer(b"<<")
        token = tokenizer.next_token()
        assert token.type == TokenType.DICT_START

    def test_tokenize_dict_end(self):
        """Test tokenizing dictionary end."""
        tokenizer = PDFTokenizer(b">>")
        token = tokenizer.next_token()
        assert token.type == TokenType.DICT_END

    def test_tokenize_simple_dict(self):
        """Test tokenizing a simple dictionary."""
        tokenizer = PDFTokenizer(b"<< /Name /Value >>")
        tokens = tokenizer.get_all_tokens()
        assert len(tokens) == 4
        assert tokens[0].type == TokenType.DICT_START
        assert tokens[1].type == TokenType.NAME
        assert tokens[2].type == TokenType.NAME
        assert tokens[3].type == TokenType.DICT_END

    # ========================================================================
    # Keyword Tokenization
    # ========================================================================

    def test_tokenize_obj_keyword(self):
        """Test tokenizing obj keyword."""
        tokenizer = PDFTokenizer(b"obj")
        token = tokenizer.next_token()
        assert token.type == TokenType.OBJ_START

    def test_tokenize_endobj_keyword(self):
        """Test tokenizing endobj keyword."""
        tokenizer = PDFTokenizer(b"endobj")
        token = tokenizer.next_token()
        assert token.type == TokenType.OBJ_END

    def test_tokenize_stream_keyword(self):
        """Test tokenizing stream keyword."""
        tokenizer = PDFTokenizer(b"stream")
        token = tokenizer.next_token()
        assert token.type == TokenType.STREAM_START

    def test_tokenize_endstream_keyword(self):
        """Test tokenizing endstream keyword."""
        tokenizer = PDFTokenizer(b"endstream")
        token = tokenizer.next_token()
        assert token.type == TokenType.STREAM_END

    def test_tokenize_trailer_keyword(self):
        """Test tokenizing trailer keyword."""
        tokenizer = PDFTokenizer(b"trailer")
        token = tokenizer.next_token()
        assert token.type == TokenType.TRAILER

    def test_tokenize_xref_keyword(self):
        """Test tokenizing xref keyword."""
        tokenizer = PDFTokenizer(b"xref")
        token = tokenizer.next_token()
        assert token.type == TokenType.XREF

    def test_tokenize_R_keyword(self):
        """Test tokenizing R (indirect reference) keyword."""
        tokenizer = PDFTokenizer(b"R")
        token = tokenizer.next_token()
        assert token.type == TokenType.INDIRECT_REF

    # ========================================================================
    # Comment Tokenization
    # ========================================================================

    def test_tokenize_comment(self):
        """Test tokenizing comments."""
        tokenizer = PDFTokenizer(b"% This is a comment\n")
        token = tokenizer.next_token()
        assert token.type == TokenType.COMMENT
        assert "% This is a comment" in token.value

    def test_tokenize_eof_marker(self):
        """Test tokenizing %%EOF marker."""
        tokenizer = PDFTokenizer(b"%%EOF")
        token = tokenizer.next_token()
        assert token.type == TokenType.ENDOFFILE

    # ========================================================================
    # Indirect Reference Tokenization
    # ========================================================================

    def test_tokenize_indirect_reference(self):
        """Test tokenizing indirect reference (n m R)."""
        tokenizer = PDFTokenizer(b"1 0 R")
        tokens = tokenizer.get_all_tokens()
        assert len(tokens) == 3
        assert tokens[0].type == TokenType.INTEGER
        assert tokens[0].value == 1
        assert tokens[1].type == TokenType.INTEGER
        assert tokens[1].value == 0
        assert tokens[2].type == TokenType.INDIRECT_REF

    # ========================================================================
    # Whitespace Handling
    # ========================================================================

    def test_skip_whitespace_spaces(self):
        """Test that spaces are skipped."""
        tokenizer = PDFTokenizer(b"   123")
        token = tokenizer.next_token()
        assert token.type == TokenType.INTEGER
        assert token.value == 123

    def test_skip_whitespace_tabs(self):
        """Test that tabs are skipped."""
        tokenizer = PDFTokenizer(b"\t\t42")
        token = tokenizer.next_token()
        assert token.type == TokenType.INTEGER
        assert token.value == 42

    def test_skip_whitespace_newlines(self):
        """Test that newlines are skipped."""
        tokenizer = PDFTokenizer(b"\n\n99")
        token = tokenizer.next_token()
        assert token.type == TokenType.INTEGER
        assert token.value == 99

    def test_skip_mixed_whitespace(self):
        """Test that mixed whitespace is skipped."""
        tokenizer = PDFTokenizer(b" \t\n\r 123")
        token = tokenizer.next_token()
        assert token.type == TokenType.INTEGER
        assert token.value == 123

    # ========================================================================
    # Token Position Tracking
    # ========================================================================

    def test_token_offset(self):
        """Test that token offsets are tracked."""
        tokenizer = PDFTokenizer(b"123 456")
        token1 = tokenizer.next_token()
        token2 = tokenizer.next_token()
        assert token1.offset == 0
        assert token2.offset > token1.offset

    # ========================================================================
    # Complex Tokenization
    # ========================================================================

    def test_tokenize_complex_object(self):
        """Test tokenizing a complex PDF object."""
        pdf_bytes = b"""1 0 obj
<< /Type /Catalog /Pages 2 0 R /Metadata 5 0 R >>
endobj"""
        tokenizer = PDFTokenizer(pdf_bytes)
        tokens = tokenizer.get_all_tokens()

        # Should have: 1, 0, obj, <<, /Type, /Catalog, /Pages, 2, 0, R, /Metadata, 5, 0, R, >>, endobj
        assert any(t.type == TokenType.INTEGER and t.value == 1 for t in tokens)
        assert any(t.type == TokenType.OBJ_START for t in tokens)
        assert any(t.type == TokenType.DICT_START for t in tokens)
        assert any(t.type == TokenType.NAME and t.value == "Type" for t in tokens)
        assert any(t.type == TokenType.INDIRECT_REF for t in tokens)
        assert any(t.type == TokenType.OBJ_END for t in tokens)

    def test_tokenize_pdf_header(self):
        """Test tokenizing PDF header."""
        tokenizer = PDFTokenizer(b"%PDF-1.4")
        token = tokenizer.next_token()
        assert token.type == TokenType.COMMENT
        assert "%PDF-1.4" in token.value

    # ========================================================================
    # File-like Object Support
    # ========================================================================

    def test_tokenize_from_file_like(self):
        """Test tokenizing from file-like object."""
        file_obj = BytesIO(b"123 456")
        tokenizer = PDFTokenizer(file_obj)
        token = tokenizer.next_token()
        assert token.type == TokenType.INTEGER
        assert token.value == 123

    # ========================================================================
    # Edge Cases
    # ========================================================================

    def test_empty_input(self):
        """Test tokenizing empty input."""
        tokenizer = PDFTokenizer(b"")
        token = tokenizer.next_token()
        assert token is None

    def test_only_whitespace(self):
        """Test tokenizing only whitespace."""
        tokenizer = PDFTokenizer(b"   \t\n   ")
        token = tokenizer.next_token()
        assert token is None

    def test_seek_and_tell(self):
        """Test seek and tell methods."""
        tokenizer = PDFTokenizer(b"123 456 789")
        tokenizer.next_token()  # 123
        pos = tokenizer.tell()
        tokenizer.next_token()  # 456
        tokenizer.seek(pos)
        token = tokenizer.next_token()
        assert token.value == 456


class TestTokenizePdfFunction:
    """Tests for the tokenize_pdf convenience function."""

    def test_tokenize_pdf_returns_list(self):
        """Test that tokenize_pdf returns a list."""
        tokens = tokenize_pdf(b"1 2 3")
        assert isinstance(tokens, list)

    def test_tokenize_pdf_all_tokens(self):
        """Test that tokenize_pdf returns all tokens."""
        tokens = tokenize_pdf(b"[1 2 3]")
        assert len(tokens) == 5  # [, 1, 2, 3, ]


class TestToken:
    """Tests for Token dataclass."""

    def test_token_repr(self):
        """Test token string representation."""
        token = Token(TokenType.INTEGER, 42, 0)
        repr_str = repr(token)
        assert "INTEGER" in repr_str
        assert "42" in repr_str

    def test_token_with_bytes_value(self):
        """Test token with bytes value."""
        token = Token(TokenType.STRING, b"Hello", 0)
        assert token.value == b"Hello"


class TestTokenType:
    """Tests for TokenType enum."""

    def test_all_token_types_exist(self):
        """Test that all expected token types exist."""
        expected_types = [
            "INTEGER",
            "REAL",
            "STRING",
            "HEX_STRING",
            "NAME",
            "BOOLEAN",
            "NULL",
            "ARRAY_START",
            "ARRAY_END",
            "DICT_START",
            "DICT_END",
            "STREAM_START",
            "STREAM_END",
            "OBJ_START",
            "OBJ_END",
            "XREF",
            "TRAILER",
            "STARTXREF",
            "ENDOFFILE",
            "INDIRECT_REF",
            "COMMENT",
            "UNKNOWN",
        ]
        for type_name in expected_types:
            assert hasattr(TokenType, type_name)