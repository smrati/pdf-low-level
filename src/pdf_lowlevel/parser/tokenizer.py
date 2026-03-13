"""
PDF Tokenizer.

This module handles low-level tokenization of PDF file syntax.
It converts raw bytes into meaningful tokens for the parser.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from io import BytesIO
from typing import BinaryIO, Generator, List, Optional, Tuple, Union


class TokenType(Enum):
    """Types of tokens in PDF syntax."""

    # Literals
    INTEGER = auto()
    REAL = auto()
    STRING = auto()  # Literal string (...)
    HEX_STRING = auto()  # Hex string (<...>)
    NAME = auto()  # Name (/Name)
    BOOLEAN = auto()  # true or false
    NULL = auto()

    # Structures
    ARRAY_START = auto()  # [
    ARRAY_END = auto()  # ]
    DICT_START = auto()  # <<
    DICT_END = auto()  # >>
    STREAM_START = auto()  # stream
    STREAM_END = auto()  # endstream
    OBJ_START = auto()  # obj
    OBJ_END = auto()  # endobj
    XREF = auto()  # xref
    TRAILER = auto()  # trailer
    STARTXREF = auto()  # startxref
    ENDOFFILE = auto()  # %%EOF

    # Indirect reference
    INDIRECT_REF = auto()  # R (after two numbers)

    # Special
    COMMENT = auto()  # %...
    UNKNOWN = auto()


@dataclass
class Token:
    """A token from PDF source."""

    type: TokenType
    value: Union[str, int, float, bytes, None]
    offset: int  # Position in file
    line: int = 0
    column: int = 0

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, offset={self.offset})"


class PDFTokenizer:
    """
    Tokenizer for PDF files.

    Converts raw PDF bytes into a stream of tokens. Handles:
    - Comments (%...)
    - Numbers (integers and reals)
    - Strings (literal and hex)
    - Names (/Name)
    - Booleans (true, false)
    - Null (null)
    - Arrays ([...])
    - Dictionaries (<<...>>)
    - Streams (stream...endstream)
    - Indirect objects (n m obj...endobj)
    - Keywords (xref, trailer, startxref, %%EOF)
    """

    # PDF whitespace characters
    WHITESPACE = b" \t\r\n\x00\x0c"

    # PDF delimiter characters
    DELIMITERS = b"()<>[]{}/%"

    # Keywords
    KEYWORDS = {
        b"true": (TokenType.BOOLEAN, True),
        b"false": (TokenType.BOOLEAN, False),
        b"null": (TokenType.NULL, None),
        b"obj": (TokenType.OBJ_START, "obj"),
        b"endobj": (TokenType.OBJ_END, "endobj"),
        b"stream": (TokenType.STREAM_START, "stream"),
        b"endstream": (TokenType.STREAM_END, "endstream"),
        b"xref": (TokenType.XREF, "xref"),
        b"trailer": (TokenType.TRAILER, "trailer"),
        b"startxref": (TokenType.STARTXREF, "startxref"),
        b"R": (TokenType.INDIRECT_REF, "R"),
    }

    def __init__(self, source: Union[bytes, BinaryIO]):
        """
        Initialize the tokenizer.

        Args:
            source: PDF source as bytes or a file-like object.
        """
        if isinstance(source, bytes):
            self.source: BinaryIO = BytesIO(source)
        else:
            self.source = source

        self.offset = 0
        self.line = 1
        self.column = 1

        # Buffer for peeking
        self._buffer: List[int] = []

    def tell(self) -> int:
        """Return current position in the source."""
        return self.offset

    def seek(self, pos: int) -> None:
        """Seek to a position in the source."""
        self.source.seek(pos)
        self.offset = pos
        self._buffer.clear()

    def _read_byte(self) -> int:
        """Read a single byte from the source."""
        if self._buffer:
            byte = self._buffer.pop(0)
        else:
            byte = self.source.read(1)
            if not byte:
                return -1
            byte = byte[0]

        self.offset += 1
        if byte == ord("\n"):
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return byte

    def _peek_byte(self, count: int = 1) -> Tuple[int, ...]:
        """Peek at the next byte(s) without consuming them."""
        while len(self._buffer) < count:
            byte = self.source.read(1)
            if not byte:
                self._buffer.append(-1)
                break
            self._buffer.append(byte[0])

        return tuple(self._buffer[:count])

    def _unread_byte(self, byte: int) -> None:
        """Put a byte back into the buffer."""
        self._buffer.append(byte)
        self.offset -= 1

    def _skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while True:
            byte = self._read_byte()
            if byte == -1:
                break
            if byte not in self.WHITESPACE:
                self._unread_byte(byte)
                break

    def _skip_comment(self) -> Token:
        """Skip a comment and return it as a token."""
        start_offset = self.offset - 1  # Include the %
        comment_bytes = [ord("%")]

        while True:
            byte = self._read_byte()
            if byte == -1 or byte == ord("\n") or byte == ord("\r"):
                break
            comment_bytes.append(byte)

        # Handle \r\n
        if byte == ord("\r"):
            next_byte = self._peek_byte()[0]
            if next_byte == ord("\n"):
                self._read_byte()

        comment_str = bytes(comment_bytes).decode("latin-1", errors="replace")
        return Token(TokenType.COMMENT, comment_str, start_offset)

    def _read_number(self, first_byte: int) -> Token:
        """Read a number (integer or real)."""
        start_offset = self.offset - 1
        num_bytes = [first_byte]

        while True:
            byte = self._read_byte()
            if byte == -1:
                break

            char = chr(byte)
            if char.isdigit() or char in "+-.":
                num_bytes.append(byte)
            else:
                self._unread_byte(byte)
                break

        num_str = bytes(num_bytes).decode("ascii")

        # Determine if integer or real
        if "." in num_str:
            return Token(TokenType.REAL, float(num_str), start_offset)
        else:
            return Token(TokenType.INTEGER, int(num_str), start_offset)

    def _read_name(self) -> Token:
        """Read a name object (/Name)."""
        start_offset = self.offset - 1  # Include the /
        name_bytes = []

        while True:
            byte = self._read_byte()
            if byte == -1:
                break

            # Check for delimiter or whitespace
            if byte in self.WHITESPACE or byte in self.DELIMITERS:
                self._unread_byte(byte)
                break

            # Handle # escape sequences
            if byte == ord("#"):
                hex_bytes = []
                for _ in range(2):
                    hex_byte = self._read_byte()
                    if hex_byte == -1:
                        break
                    hex_bytes.append(chr(hex_byte))
                if len(hex_bytes) == 2:
                    try:
                        name_bytes.append(int("".join(hex_bytes), 16))
                    except ValueError:
                        name_bytes.extend([ord("#")] + [ord(c) for c in hex_bytes])
                else:
                    name_bytes.append(ord("#"))
                    for c in hex_bytes:
                        name_bytes.append(ord(c))
            else:
                name_bytes.append(byte)

        name_str = bytes(name_bytes).decode("utf-8", errors="replace")
        return Token(TokenType.NAME, name_str, start_offset)

    def _read_literal_string(self) -> Token:
        """Read a literal string (...)."""
        start_offset = self.offset - 1  # Include the (
        string_bytes = []
        paren_depth = 1

        while True:
            byte = self._read_byte()
            if byte == -1:
                break

            if byte == ord("("):
                paren_depth += 1
                string_bytes.append(byte)
            elif byte == ord(")"):
                paren_depth -= 1
                if paren_depth == 0:
                    break
                string_bytes.append(byte)
            elif byte == ord("\\"):
                # Escape sequence
                next_byte = self._read_byte()
                if next_byte == -1:
                    break

                escape_map = {
                    ord("n"): ord("\n"),
                    ord("r"): ord("\r"),
                    ord("t"): ord("\t"),
                    ord("b"): ord("\b"),
                    ord("f"): ord("\f"),
                    ord("("): ord("("),
                    ord(")"): ord(")"),
                    ord("\\"): ord("\\"),
                }

                if next_byte in escape_map:
                    string_bytes.append(escape_map[next_byte])
                elif next_byte == ord("\n"):
                    # Line continuation
                    pass
                elif next_byte == ord("\r"):
                    # Line continuation (handle \r\n)
                    peek = self._peek_byte()[0]
                    if peek == ord("\n"):
                        self._read_byte()
                elif chr(next_byte).isdigit():
                    # Octal escape (1-3 digits)
                    octal_str = chr(next_byte)
                    for _ in range(2):
                        peek = self._peek_byte()[0]
                        if peek != -1 and chr(peek).isdigit():
                            octal_str += chr(self._read_byte())
                        else:
                            break
                    try:
                        string_bytes.append(int(octal_str, 8) & 0xFF)
                    except ValueError:
                        string_bytes.extend([ord("\\"), next_byte])
                else:
                    # Unknown escape, just include the character
                    string_bytes.append(next_byte)
            else:
                string_bytes.append(byte)

        return Token(TokenType.STRING, bytes(string_bytes), start_offset)

    def _read_hex_string(self) -> Token:
        """Read a hexadecimal string (<...>)."""
        start_offset = self.offset - 1  # Include the <
        hex_bytes = []

        while True:
            byte = self._read_byte()
            if byte == -1:
                break

            if byte == ord(">"):
                break

            if byte not in self.WHITESPACE:
                hex_bytes.append(chr(byte))

        hex_str = "".join(hex_bytes)

        # Pad with 0 if odd length
        if len(hex_str) % 2 == 1:
            hex_str += "0"

        try:
            decoded = bytes.fromhex(hex_str)
        except ValueError:
            decoded = hex_str.encode("latin-1")

        return Token(TokenType.HEX_STRING, decoded, start_offset)

    def _read_keyword_or_number(self, first_byte: int) -> Token:
        """Read a keyword, number, or identifier."""
        start_offset = self.offset - 1
        token_bytes = [first_byte]

        while True:
            byte = self._read_byte()
            if byte == -1:
                break

            # Check for delimiter or whitespace
            if byte in self.WHITESPACE or byte in self.DELIMITERS:
                self._unread_byte(byte)
                break

            token_bytes.append(byte)

        token_str_bytes = bytes(token_bytes)

        # Check if it's a keyword
        if token_str_bytes in self.KEYWORDS:
            token_type, value = self.KEYWORDS[token_str_bytes]
            return Token(token_type, value, start_offset)

        # Check if it's a number
        token_str = token_str_bytes.decode("ascii", errors="replace")
        if re.match(r"^[+-]?\d*\.?\d+$", token_str):
            if "." in token_str:
                return Token(TokenType.REAL, float(token_str), start_offset)
            else:
                return Token(TokenType.INTEGER, int(token_str), start_offset)

        # Unknown token
        return Token(TokenType.UNKNOWN, token_str, start_offset)

    def next_token(self) -> Optional[Token]:
        """
        Get the next token from the source.

        Returns:
            The next token, or None if at end of file.
        """
        while True:
            byte = self._read_byte()
            if byte == -1:
                return None

            # Skip whitespace
            if byte in self.WHITESPACE:
                continue

            # Comment
            if byte == ord("%"):
                # Check for %%EOF
                remaining = bytes([byte]) + self.source.read(4)
                self.source.seek(-4, 1)  # Seek back

                if remaining == b"%%EOF":
                    # Consume the rest
                    self.source.read(4)
                    self.offset += 4
                    return Token(TokenType.ENDOFFILE, "%%EOF", self.offset - 5)

                return self._skip_comment()

            # Number (starts with digit or +/-)
            if chr(byte).isdigit() or byte in (ord("+"), ord("-")):
                # Need to check if it's a number or just starting chars
                next_bytes = self._peek_byte(2)
                if byte in (ord("+"), ord("-")) and (
                    not next_bytes[0] != -1 and not chr(next_bytes[0]).isdigit()
                ):
                    # It's a keyword starting with +/-
                    return self._read_keyword_or_number(byte)
                return self._read_number(byte)

            # Name
            if byte == ord("/"):
                return self._read_name()

            # Literal string
            if byte == ord("("):
                return self._read_literal_string()

            # Hex string or dictionary
            if byte == ord("<"):
                next_byte = self._peek_byte()[0]
                if next_byte == ord("<"):
                    self._read_byte()  # Consume second <
                    return Token(TokenType.DICT_START, "<<", self.offset - 2)
                else:
                    return self._read_hex_string()

            # Dictionary end
            if byte == ord(">"):
                next_byte = self._peek_byte()[0]
                if next_byte == ord(">"):
                    self._read_byte()  # Consume second >
                    return Token(TokenType.DICT_END, ">>", self.offset - 2)
                else:
                    # Stray >, treat as unknown
                    return Token(TokenType.UNKNOWN, ">", self.offset - 1)

            # Array
            if byte == ord("["):
                return Token(TokenType.ARRAY_START, "[", self.offset - 1)

            if byte == ord("]"):
                return Token(TokenType.ARRAY_END, "]", self.offset - 1)

            # Keyword or identifier
            return self._read_keyword_or_number(byte)

    def tokenize(self) -> Generator[Token, None, None]:
        """
        Generate all tokens from the source.

        Yields:
            Tokens until end of file.
        """
        while True:
            token = self.next_token()
            if token is None:
                break
            yield token

    def get_all_tokens(self) -> List[Token]:
        """Get all tokens as a list."""
        return list(self.tokenize())


def tokenize_pdf(source: Union[bytes, BinaryIO]) -> List[Token]:
    """
    Convenience function to tokenize PDF source.

    Args:
        source: PDF source as bytes or file-like object.

    Returns:
        List of all tokens.
    """
    tokenizer = PDFTokenizer(source)
    return tokenizer.get_all_tokens()