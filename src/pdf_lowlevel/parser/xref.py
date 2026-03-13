"""
PDF Cross-Reference Table Parser.

This module handles parsing of PDF cross-reference tables and streams,
which map object numbers to their positions in the file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import BinaryIO, Dict, List, Optional, Tuple

from pdf_lowlevel.parser.tokenizer import PDFTokenizer, Token, TokenType


@dataclass
class IndirectRef:
    """Represents an indirect object reference (e.g., '1 0 R')."""

    object_number: int
    generation_number: int

    def __repr__(self) -> str:
        return f"IndirectRef({self.object_number}, {self.generation_number})"


@dataclass
class XRefEntry:
    """
    A single entry in the cross-reference table.

    For traditional xref tables:
    - offset: byte position in file (type 0: in-use)
    - generation: generation number
    - free: True if entry is free (type 1), False if in-use (type 0)

    For xref streams:
    - Additional fields may be populated based on entry type
    """

    offset: int = 0
    generation: int = 0
    free: bool = False
    # For xref stream type 2 entries
    object_stream_num: int = 0  # Object number of containing object stream
    index_in_stream: int = 0  # Index within the object stream

    # Entry type for xref streams
    # 0 = free, 1 = in-use (normal), 2 = in-use (compressed in object stream)
    entry_type: int = 1


@dataclass
class XRefTable:
    """
    Cross-reference table for a PDF file.

    Maps (object_number, generation_number) to file positions.
    """

    entries: Dict[int, XRefEntry] = field(default_factory=dict)
    trailer: Dict[str, any] = field(default_factory=dict)

    def get_offset(self, obj_num: int, gen_num: int = 0) -> Optional[int]:
        """
        Get the file offset for an object.

        Args:
            obj_num: Object number
            gen_num: Generation number (usually 0)

        Returns:
            File offset, or None if object not found
        """
        entry = self.entries.get(obj_num)
        if entry is None or entry.free:
            return None

        # For compressed objects (type 2), return None
        # They need to be extracted from object streams
        if entry.entry_type == 2:
            return None

        return entry.offset

    def get_entry(self, obj_num: int) -> Optional[XRefEntry]:
        """Get the xref entry for an object number."""
        return self.entries.get(obj_num)

    def add_entry(self, obj_num: int, entry: XRefEntry) -> None:
        """Add or update an entry."""
        self.entries[obj_num] = entry

    def get_root_ref(self) -> Optional[Tuple[int, int]]:
        """
        Get the root catalog object reference from trailer.

        Returns:
            (object_number, generation_number) or None
        """
        root = self.trailer.get("Root")
        if root is not None:
            return (root.object_number, root.generation_number)
        return None

    def get_info_ref(self) -> Optional[Tuple[int, int]]:
        """Get the info dictionary object reference from trailer."""
        info = self.trailer.get("Info")
        if info is not None:
            return (info.object_number, info.generation_number)
        return None

    def get_size(self) -> int:
        """Get the total number of entries (from Size in trailer)."""
        return self.trailer.get("Size", 0)


class XRefParser:
    """
    Parser for PDF cross-reference tables.

    Handles both traditional xref tables and xref streams (PDF 1.5+).
    """

    def __init__(self, source: BinaryIO):
        """
        Initialize the xref parser.

        Args:
            source: Binary file-like object positioned at start of xref
        """
        self.source = source
        self.tokenizer = PDFTokenizer(source)
        self._pending_tokens: List[Token] = []

    def _next_token(self) -> Optional[Token]:
        """Get next token, checking pending tokens first."""
        if self._pending_tokens:
            return self._pending_tokens.pop(0)
        return self.tokenizer.next_token()

    def parse(self) -> XRefTable:
        """
        Parse the cross-reference table.

        Returns:
            XRefTable with entries and trailer info
        """
        # Check if this is a traditional xref or xref stream
        pos = self.source.tell()

        # Read first non-whitespace byte
        byte = self.source.read(1)
        while byte and byte in b" \t\r\n":
            byte = self.source.read(1)

        print(f"DEBUG xref: First byte at pos {pos}: {byte!r}")
        
        self.source.seek(pos)

        if byte == b"x":
            # Traditional xref table
            print("DEBUG xref: Parsing traditional xref table")
            return self._parse_traditional_xref()
        elif byte and byte.isdigit():
            # Likely an xref stream (starts with object number)
            print("DEBUG xref: Parsing xref stream")
            return self._parse_xref_stream()
        else:
            # Try to find trailer anyway
            print("DEBUG xref: Parsing trailer only")
            return self._parse_trailer_only()

    def _parse_traditional_xref(self) -> XRefTable:
        """Parse a traditional xref table."""
        xref_table = XRefTable()

        # Expect 'xref' keyword
        token = self.tokenizer.next_token()
        if token is None or token.type != TokenType.XREF:
            raise ValueError(f"Expected 'xref' keyword, got {token}")

        print(f"DEBUG xref: Got xref keyword, token={token}")

        # Parse subsections
        while True:
            token = self.tokenizer.next_token()

            print(f"DEBUG xref: Next token in loop: {token}")

            if token is None:
                print("DEBUG xref: Token is None, breaking")
                break

            # Check for trailer keyword
            if token.type == TokenType.TRAILER:
                print("DEBUG xref: Found trailer, parsing trailer dict")
                # Parse trailer dictionary
                trailer_dict = self._parse_trailer()
                xref_table.trailer.update(trailer_dict)
                print(f"DEBUG xref: Trailer dict: {trailer_dict}")
                break

            # Should be start object number
            if token.type != TokenType.INTEGER:
                # Unknown token, might be at trailer
                print(f"DEBUG xref: Non-integer token: {token.type}")
                if token.type == TokenType.TRAILER:
                    trailer_dict = self._parse_trailer()
                    xref_table.trailer.update(trailer_dict)
                break

            start_obj = token.value
            print(f"DEBUG xref: Start obj: {start_obj}")

            # Get count
            token = self.tokenizer.next_token()
            if token is None or token.type != TokenType.INTEGER:
                raise ValueError(f"Expected count after start object, got {token}")

            count = token.value
            print(f"DEBUG xref: Count: {count}")

            # Parse entries
            for i in range(count):
                obj_num = start_obj + i
                entry = self._parse_xref_entry()
                if entry is not None:
                    xref_table.add_entry(obj_num, entry)
                    print(f"DEBUG xref: Added entry for obj {obj_num}: offset={entry.offset}")

        print(f"DEBUG xref: Total entries parsed: {len(xref_table.entries)}")
        return xref_table

    def _parse_xref_entry(self) -> Optional[XRefEntry]:
        """
        Parse a single xref entry.

        Format: nnnnnnnnnn ggggg n\r\n
        - n: 10-digit byte offset
        - g: 5-digit generation number
        - n or f: in-use or free
        - End of line: SP CR NL, SP NL, or CR NL
        """
        entry = XRefEntry()

        # Get offset (10 digits)
        offset_bytes = []
        for _ in range(10):
            byte = self.source.read(1)
            if not byte:
                return None
            offset_bytes.append(byte)

        try:
            entry.offset = int(b"".join(offset_bytes))
        except ValueError:
            return None

        # Skip space
        self.source.read(1)

        # Get generation (5 digits)
        gen_bytes = []
        for _ in range(5):
            byte = self.source.read(1)
            if not byte:
                return None
            gen_bytes.append(byte)

        try:
            entry.generation = int(b"".join(gen_bytes))
        except ValueError:
            return None

        # Skip space
        self.source.read(1)

        # Get type (f or n)
        type_byte = self.source.read(1)
        if type_byte == b"f":
            entry.free = True
            entry.entry_type = 0
        elif type_byte == b"n":
            entry.free = False
            entry.entry_type = 1
        else:
            return None

        # Skip end of line (could be SP CR NL, SP NL, or CR NL)
        eol1 = self.source.read(1)
        if eol1 == b"\r":
            eol2 = self.source.read(1)
            if eol2 != b"\n":
                # Put back if not NL
                self.source.seek(-1, 1)
        elif eol1 == b" ":
            # Could be SP CR NL or SP NL
            eol2 = self.source.read(1)
            if eol2 == b"\r":
                eol3 = self.source.read(1)
                if eol3 != b"\n":
                    self.source.seek(-1, 1)

        return entry

    def _parse_trailer(self) -> Dict[str, any]:
        """Parse the trailer dictionary."""
        trailer = {}

        # Expect 'trailer' keyword was just consumed
        # Next should be '<<'
        token = self._next_token()
        if token is None or token.type != TokenType.DICT_START:
            raise ValueError(f"Expected '<<' after trailer, got {token}")

        # Parse dictionary contents
        while True:
            token = self._next_token()
            if token is None:
                break

            if token.type == TokenType.DICT_END:
                break

            if token.type == TokenType.NAME:
                key = token.value
                value = self._parse_value()
                if value is not None:
                    trailer[key] = value

        return trailer

    def _parse_value(self) -> any:
        """
        Parse a value from the trailer, handling indirect references.

        Indirect references are: INTEGER INTEGER R
        """
        token = self._next_token()
        if token is None:
            return None

        # Check if this could be start of an indirect reference
        if token.type == TokenType.INTEGER:
            # Peek at next token
            next_token = self._next_token()

            if next_token is None:
                return token.value

            if next_token.type == TokenType.INTEGER:
                # Could be indirect reference, check for 'R'
                third_token = self._next_token()

                if third_token is not None and third_token.type == TokenType.INDIRECT_REF:
                    # It's an indirect reference: obj_num gen_num R
                    return IndirectRef(token.value, next_token.value)
                else:
                    # Not an indirect reference, put back tokens and return first value
                    self._pending_tokens.append(next_token)
                    if third_token is not None:
                        self._pending_tokens.append(third_token)
                    return token.value
            else:
                # Not an indirect reference
                # Store the next token for re-reading
                self._pending_tokens.append(next_token)
                return token.value

        return self._token_to_value(token)

    def _token_to_value(self, token: Token) -> any:
        """Convert a token to its Python value."""
        if token.type == TokenType.INTEGER:
            return token.value
        elif token.type == TokenType.REAL:
            return token.value
        elif token.type == TokenType.STRING:
            return token.value
        elif token.type == TokenType.HEX_STRING:
            return token.value
        elif token.type == TokenType.NAME:
            return token.value
        elif token.type == TokenType.BOOLEAN:
            return token.value
        elif token.type == TokenType.NULL:
            return None
        elif token.type == TokenType.INDIRECT_REF:
            return token.value
        else:
            return token.value

    def _parse_xref_stream(self) -> XRefTable:
        """
        Parse an xref stream (PDF 1.5+).

        XRef streams combine the xref table and trailer into a stream object.
        """
        # This requires full object parsing, which we'll implement
        # after the object parser is complete
        # For now, return empty table
        return XRefTable()

    def _parse_trailer_only(self) -> XRefTable:
        """
        Parse just the trailer when no xref is found.

        This is used for incremental updates or linearized PDFs.
        """
        xref_table = XRefTable()

        # Search for trailer
        while True:
            token = self.tokenizer.next_token()
            if token is None:
                break

            if token.type == TokenType.TRAILER:
                trailer_dict = self._parse_trailer()
                xref_table.trailer.update(trailer_dict)
                break

        return xref_table


def find_xref_offset(source: BinaryIO) -> int:
    """
    Find the offset of the main xref table from the end of the file.

    The offset is specified in the 'startxref' section near EOF.

    Args:
        source: Binary file-like object

    Returns:
        Byte offset to the xref table
    """
    # Seek to near end of file
    source.seek(0, 2)  # End of file
    file_size = source.tell()

    # Search backwards for 'startxref'
    # Usually within last 1024 bytes
    search_start = max(0, file_size - 1024)
    source.seek(search_start)

    data = source.read()

    # Find 'startxref'
    startxref_pos = data.rfind(b"startxref")
    if startxref_pos == -1:
        raise ValueError("Could not find 'startxref' in file")

    # Read the offset after 'startxref'
    pos = startxref_pos + len(b"startxref")

    # Skip whitespace
    while pos < len(data) and data[pos : pos + 1] in b" \t\r\n":
        pos += 1

    # Read the number
    offset_bytes = []
    while pos < len(data) and data[pos : pos + 1].isdigit():
        offset_bytes.append(data[pos : pos + 1])
        pos += 1

    if not offset_bytes:
        raise ValueError("Could not read xref offset")

    return int(b"".join(offset_bytes))


def parse_xref(source: BinaryIO) -> XRefTable:
    """
    Parse the cross-reference table from a PDF file.

    Args:
        source: Binary file-like object opened in binary mode

    Returns:
        XRefTable with entries and trailer info
    """
    # Find the xref offset
    xref_offset = find_xref_offset(source)

    # Seek to xref position
    source.seek(xref_offset)

    # Parse the xref
    parser = XRefParser(source)
    return parser.parse()