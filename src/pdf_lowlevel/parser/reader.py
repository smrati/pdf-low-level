"""
PDF Reader.

Main module for reading PDF files and parsing their structure.
"""

from __future__ import annotations

import zlib
from io import BytesIO
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

from pdf_lowlevel.parser.objects import (
    PDFIndirectObject,
    PDFIndirectRef,
    PDFName,
    PDFObject,
    PDFStream,
    PDFNames,
)
from pdf_lowlevel.parser.tokenizer import PDFTokenizer, Token, TokenType
from pdf_lowlevel.parser.xref import XRefEntry, XRefTable, find_xref_offset, parse_xref


class PDFParseError(Exception):
    """Exception raised when PDF parsing fails."""
    pass


class PDFReader:
    """
    Main PDF reader class.

    Reads a PDF file and provides access to its objects and structure.
    """

    def __init__(self, source: Union[str, Path, BinaryIO, bytes]):
        """
        Initialize the PDF reader.

        Args:
            source: PDF source - file path, file-like object, or bytes
        """
        self._owns_file = False
        self._file: Optional[BinaryIO] = None
        self._tokenizer: Optional[PDFTokenizer] = None
        self._xref_table: Optional[XRefTable] = None
        self._object_cache: Dict[int, PDFIndirectObject] = {}
        self._pages: List[Dict[str, Any]] = []
        self._page_count = 0

        # Handle different source types
        if isinstance(source, (str, Path)):
            self._file = open(source, "rb")
            self._owns_file = True
        elif isinstance(source, bytes):
            self._file = BytesIO(source)
            self._owns_file = True
        else:
            self._file = source

        self._tokenizer = PDFTokenizer(self._file)
        self._pending_tokens: List[Token] = []

    def close(self) -> None:
        """Close the PDF file if we own it."""
        if self._owns_file and self._file:
            self._file.close()
            self._file = None

    def __enter__(self) -> "PDFReader":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def read(self) -> None:
        """
        Read and parse the PDF file.

        Must be called before accessing objects.
        """
        # Verify PDF header
        self._verify_header()

        # Parse xref table
        self._xref_table = parse_xref(self._file)

        # Load page tree
        self._load_pages()

    def _verify_header(self) -> None:
        """Verify the PDF file header."""
        self._file.seek(0)
        header = self._file.read(8)

        if not header.startswith(b"%PDF-"):
            raise PDFParseError("Not a valid PDF file (missing %PDF- header)")

        # Extract version
        version_str = header[5:8].decode("ascii", errors="replace")
        self.version = version_str

    def get_object(self, obj_num: int, gen_num: int = 0) -> Optional[PDFObject]:
        """
        Get an object by its number.

        Args:
            obj_num: Object number
            gen_num: Generation number (usually 0)

        Returns:
            The PDF object value, or None if not found
        """
        # Check cache
        cache_key = (obj_num, gen_num)
        if cache_key in self._object_cache:
            return self._object_cache[cache_key].value

        # Get offset from xref
        entry = self._xref_table.get_entry(obj_num)
        if entry is None:
            return None

        offset = entry.offset
        if offset is None or offset == 0:
            return None

        # Parse the object at that offset
        obj = self._parse_indirect_object(offset)
        if obj:
            self._object_cache[cache_key] = obj
            return obj.value

        return None

    def _parse_indirect_object(self, offset: int) -> Optional[PDFIndirectObject]:
        """
        Parse an indirect object at a specific offset.

        Args:
            offset: Byte offset in file

        Returns:
            PDFIndirectObject or None
        """
        # Use tokenizer's seek to properly sync the buffer
        self._tokenizer.seek(offset)
        # Clear any pending tokens from previous parsing
        self._pending_tokens.clear()

        # Read object header: n m obj
        obj_num = None
        gen_num = None

        token = self._tokenizer.next_token()
        if token is None or token.type != TokenType.INTEGER:
            return None
        obj_num = token.value

        token = self._tokenizer.next_token()
        if token is None or token.type != TokenType.INTEGER:
            return None
        gen_num = token.value

        token = self._tokenizer.next_token()
        if token is None or token.type != TokenType.OBJ_START:
            return None

        # Parse the object value
        value = self._parse_object_value()

        return PDFIndirectObject(obj_num, gen_num, value)

    def _next_token(self) -> Optional[Token]:
        """Get next token, checking pending tokens first."""
        if self._pending_tokens:
            return self._pending_tokens.pop(0)
        return self._tokenizer.next_token()

    def _parse_object_value(self) -> PDFObject:
        """
        Parse an object value from the current position.

        Returns:
            Parsed PDF object
        """
        token = self._next_token()
        if token is None:
            raise PDFParseError("Unexpected end of file while parsing object")

        # Handle different token types
        if token.type == TokenType.INTEGER:
            # Could be an indirect reference: n m R
            next_token = self._next_token()
            if next_token and next_token.type == TokenType.INTEGER:
                third_token = self._next_token()
                if third_token and third_token.type == TokenType.INDIRECT_REF:
                    return PDFIndirectRef(token.value, next_token.value)
                else:
                    # Not an indirect reference - we need to return the first integer
                    # and push back the other two tokens for later parsing
                    # We'll use a pending token mechanism
                    if third_token:
                        self._pending_tokens.insert(0, third_token)
                    self._pending_tokens.insert(0, next_token)
                    return token.value
            elif next_token:
                # Not an indirect reference, push back and return the integer
                self._pending_tokens.insert(0, next_token)
                return token.value
            else:
                return token.value

        elif token.type == TokenType.REAL:
            return token.value

        elif token.type == TokenType.STRING:
            return token.value

        elif token.type == TokenType.HEX_STRING:
            return token.value

        elif token.type == TokenType.NAME:
            return PDFName(token.value)

        elif token.type == TokenType.BOOLEAN:
            return token.value

        elif token.type == TokenType.NULL:
            return None

        elif token.type == TokenType.ARRAY_START:
            return self._parse_array()

        elif token.type == TokenType.DICT_START:
            return self._parse_dictionary()

        elif token.type == TokenType.OBJ_END:
            # Empty object
            return None

        else:
            raise PDFParseError(f"Unexpected token: {token}")

    def _parse_array(self) -> List[PDFObject]:
        """Parse an array object."""
        array = []

        while True:
            token = self._next_token()
            if token is None:
                break

            if token.type == TokenType.ARRAY_END:
                break

            # Put back and parse as object
            self._pending_tokens.insert(0, token)
            value = self._parse_object_value()
            array.append(value)

        return array

    def _parse_dictionary(self) -> Dict[str, PDFObject]:
        """Parse a dictionary object."""
        dictionary = {}

        while True:
            token = self._next_token()
            if token is None:
                break

            if token.type == TokenType.DICT_END:
                # Could be a stream
                next_token = self._next_token()
                if next_token and next_token.type == TokenType.STREAM_START:
                    # It's a stream, parse stream data
                    return self._parse_stream(dictionary)
                else:
                    # Not a stream, put back
                    if next_token:
                        self._pending_tokens.insert(0, next_token)
                break

            if token.type == TokenType.NAME:
                key = token.value
                value = self._parse_object_value()
                dictionary[key] = value

        return dictionary

    def _parse_stream(self, dictionary: Dict[str, PDFObject]) -> PDFStream:
        """
        Parse a stream object.

        Args:
            dictionary: The stream dictionary already parsed

        Returns:
            PDFStream object
        """
        # Get stream length
        length = dictionary.get("Length", 0)
        if isinstance(length, PDFIndirectRef):
            length = self.get_object(length.object_number, length.generation_number)
        length = int(length) if length else 0

        # Skip whitespace after 'stream' keyword
        # According to PDF spec, there should be LF or CR LF after 'stream'
        byte = self._file.read(1)
        if byte == b"\r":
            byte = self._file.read(1)  # Skip LF if CR LF

        # Read stream data
        stream_data = self._file.read(length)

        # Skip to 'endstream'
        # Some PDFs have inaccurate length, so we may need to search
        while True:
            pos = self._file.tell()
            line = self._file.readline()
            if not line:
                break
            if b"endstream" in line:
                # Seek back to start of line
                self._file.seek(pos)
                # Tokenize to consume endstream properly
                self._tokenizer.next_token()  # endstream
                break

        return PDFStream(dictionary, stream_data, file_offset=self._file.tell())

    def _load_pages(self) -> None:
        """Load the page tree from the PDF."""
        # Get root catalog
        root_ref = self._xref_table.get_root_ref()
        if root_ref is None:
            raise PDFParseError("Could not find Root catalog in trailer")

        root = self.get_object(root_ref[0], root_ref[1])
        if root is None:
            raise PDFParseError("Could not read Root catalog object")

        # Get pages reference
        pages_ref = root.get("Pages")
        if pages_ref is None:
            raise PDFParseError("Could not find Pages in Root catalog")

        if isinstance(pages_ref, PDFIndirectRef):
            pages_obj = self.get_object(pages_ref.object_number, pages_ref.generation_number)
        else:
            pages_obj = pages_ref

        # Recursively load pages
        self._load_page_tree(pages_obj)

    def _load_page_tree(self, node: Dict[str, Any]) -> None:
        """
        Recursively load pages from the page tree.

        Args:
            node: A page tree node (Pages or Page)
        """
        if node is None:
            return

        node_type = node.get("Type")
        if isinstance(node_type, PDFName):
            node_type = node_type.value

        if node_type == "Page":
            # It's a leaf page
            self._pages.append(node)
        elif node_type == "Pages":
            # It's an intermediate node
            kids = node.get("Kids", [])
            for kid_ref in kids:
                if isinstance(kid_ref, PDFIndirectRef):
                    kid = self.get_object(kid_ref.object_number, kid_ref.generation_number)
                else:
                    kid = kid_ref
                self._load_page_tree(kid)

    @property
    def page_count(self) -> int:
        """Get the number of pages in the PDF."""
        return len(self._pages)

    def get_page(self, page_num: int) -> Optional[Dict[str, Any]]:
        """
        Get a page object by page number (0-indexed).

        Args:
            page_num: Page number (0-indexed)

        Returns:
            Page dictionary or None
        """
        if 0 <= page_num < len(self._pages):
            return self._pages[page_num]
        return None

    def get_page_contents(self, page_num: int) -> Optional[bytes]:
        """
        Get the content stream(s) for a page.

        Args:
            page_num: Page number (0-indexed)

        Returns:
            Combined content stream bytes or None
        """
        page = self.get_page(page_num)
        if page is None:
            return None

        contents = page.get("Contents")
        if contents is None:
            return None

        # Contents can be a single stream or an array of streams
        if isinstance(contents, list):
            streams = []
            for content_ref in contents:
                if isinstance(content_ref, PDFIndirectRef):
                    stream = self.get_object(content_ref.object_number, content_ref.generation_number)
                else:
                    stream = content_ref
                if isinstance(stream, PDFStream):
                    streams.append(stream)
            return self._combine_streams(streams)
        else:
            if isinstance(contents, PDFIndirectRef):
                stream = self.get_object(contents.object_number, contents.generation_number)
            else:
                stream = contents
            if isinstance(stream, PDFStream):
                return self._decode_stream(stream)

        return None

    def _combine_streams(self, streams: List[PDFStream]) -> bytes:
        """Combine multiple content streams into one."""
        combined = b""
        for stream in streams:
            decoded = self._decode_stream(stream)
            if decoded:
                combined += decoded
                # Add newline if not present
                if not combined.endswith(b"\n"):
                    combined += b"\n"
        return combined

    def _decode_stream(self, stream: PDFStream) -> Optional[bytes]:
        """
        Decode a stream based on its filters.

        Args:
            stream: PDFStream object

        Returns:
            Decoded bytes or None
        """
        data = stream.data
        if data is None:
            return None

        # Get filter(s)
        filter_obj = stream.dictionary.get("Filter")
        filters = []

        if filter_obj is None:
            return data
        elif isinstance(filter_obj, PDFName):
            filters = [filter_obj.value]
        elif isinstance(filter_obj, list):
            filters = [f.value if isinstance(f, PDFName) else str(f) for f in filter_obj]

        # Apply each filter
        for filter_name in filters:
            data = self._apply_filter(data, filter_name, stream.dictionary)

        return data

    def _apply_filter(self, data: bytes, filter_name: str, params: Dict) -> bytes:
        """
        Apply a decompression filter.

        Args:
            data: Compressed data
            filter_name: Name of the filter
            params: Decode parameters

        Returns:
            Decompressed data
        """
        if filter_name == "FlateDecode":
            return self._apply_flate_decode(data, params)
        elif filter_name == "LZWDecode":
            return self._apply_lzw_decode(data, params)
        elif filter_name == "ASCII85Decode":
            return self._apply_ascii85_decode(data, params)
        elif filter_name == "ASCIIHexDecode":
            return self._apply_ascii_hex_decode(data, params)
        elif filter_name == "RunLengthDecode":
            return self._apply_runlength_decode(data, params)
        else:
            # Unknown filter, return data as-is
            return data

    def _apply_flate_decode(self, data: bytes, params: Dict) -> bytes:
        """Apply Flate (zlib) decompression."""
        try:
            return zlib.decompress(data)
        except zlib.error:
            # Try with raw deflate
            try:
                return zlib.decompress(data, -15)
            except zlib.error:
                return data

    def _apply_lzw_decode(self, data: bytes, params: Dict) -> bytes:
        """Apply LZW decompression."""
        # Simplified LZW implementation
        # For full implementation, see PDF spec
        return self._lzw_decompress(data)

    def _lzw_decompress(self, data: bytes) -> bytes:
        """
        LZW decompression implementation.

        Initial dictionary size is 9 bits (codes 0-255 for bytes,
        256 = clear table, 257 = end of data).
        """
        # Initialize dictionary
        table = {i: bytes([i]) for i in range(256)}
        table[256] = None  # Clear code
        table[257] = None  # EOD code

        next_code = 258
        code_size = 9
        max_code = (1 << code_size) - 1

        # Bit buffer
        bit_buffer = 0
        bits_in_buffer = 0
        byte_pos = 0

        def read_code():
            nonlocal bit_buffer, bits_in_buffer, byte_pos

            while bits_in_buffer < code_size:
                if byte_pos >= len(data):
                    return None
                bit_buffer = (bit_buffer << 8) | data[byte_pos]
                bits_in_buffer += 8
                byte_pos += 1

            code = (bit_buffer >> (bits_in_buffer - code_size)) & ((1 << code_size) - 1)
            bits_in_buffer -= code_size
            return code

        output = bytearray()
        prev_string = None

        while True:
            code = read_code()
            if code is None or code == 257:
                break

            if code == 256:
                # Clear table
                table = {i: bytes([i]) for i in range(256)}
                table[256] = None
                table[257] = None
                next_code = 258
                code_size = 9
                max_code = (1 << code_size) - 1
                prev_string = None
                continue

            if code in table:
                current_string = table[code]
            elif code == next_code and prev_string:
                # Special case: code not yet in table
                current_string = prev_string + bytes([prev_string[0]])
            else:
                # Invalid code
                break

            if current_string:
                output.extend(current_string)

            # Add new entry to table
            if prev_string is not None and next_code <= 4095:
                table[next_code] = prev_string + bytes([current_string[0]])
                next_code += 1

                # Increase code size if needed
                if next_code > max_code and code_size < 12:
                    code_size += 1
                    max_code = (1 << code_size) - 1

            prev_string = current_string

        return bytes(output)

    def _apply_ascii85_decode(self, data: bytes, params: Dict) -> bytes:
        """Apply ASCII85 (Base85) decompression."""
        output = bytearray()
        group = []

        for byte in data:
            if byte == ord("~"):
                # Check for end marker
                break
            if byte == ord("z"):
                # Zero group
                if group:
                    # Incomplete group before z
                    pass
                output.extend([0, 0, 0, 0])
                continue
            if byte in b" \t\r\n":
                continue

            group.append(byte)

            if len(group) == 5:
                # Decode group
                value = 0
                for b in group:
                    value = value * 85 + (b - 33)

                # Convert to 4 bytes
                output.extend([
                    (value >> 24) & 0xFF,
                    (value >> 16) & 0xFF,
                    (value >> 8) & 0xFF,
                    value & 0xFF,
                ])
                group = []

        # Handle remaining bytes
        if group:
            # Pad with 'u' (84)
            while len(group) < 5:
                group.append(ord("u"))

            value = 0
            for b in group:
                value = value * 85 + (b - 33)

            # Output only the needed bytes
            n = len(group)
            for i in range(n - 1):
                output.append((value >> (24 - i * 8)) & 0xFF)

        return bytes(output)

    def _apply_ascii_hex_decode(self, data: bytes, params: Dict) -> bytes:
        """Apply ASCII Hex decompression."""
        output = bytearray()
        hex_chars = []

        for byte in data:
            if byte == ord(">"):
                break
            if byte in b" \t\r\n":
                continue

            hex_chars.append(chr(byte))

            if len(hex_chars) == 2:
                try:
                    output.append(int("".join(hex_chars), 16))
                except ValueError:
                    pass
                hex_chars = []

        # Handle odd length
        if hex_chars:
            try:
                output.append(int(hex_chars[0] + "0", 16))
            except ValueError:
                pass

        return bytes(output)

    def _apply_runlength_decode(self, data: bytes, params: Dict) -> bytes:
        """Apply Run-Length decompression."""
        output = bytearray()
        i = 0

        while i < len(data):
            length = data[i]
            i += 1

            if length == 128:
                # EOD
                break
            elif length < 128:
                # Copy next (length + 1) bytes
                for _ in range(length + 1):
                    if i < len(data):
                        output.append(data[i])
                        i += 1
            else:
                # Repeat next byte (257 - length) times
                if i < len(data):
                    byte = data[i]
                    i += 1
                    for _ in range(257 - length):
                        output.append(byte)

        return bytes(output)

    def get_page_media_box(self, page_num: int) -> Optional[List[float]]:
        """
        Get the media box (page dimensions) for a page.

        Args:
            page_num: Page number (0-indexed)

        Returns:
            [x0, y0, x1, y1] or None
        """
        page = self.get_page(page_num)
        if page is None:
            return None

        media_box = page.get("MediaBox")
        if media_box is None:
            # Inherit from parent
            parent = page.get("Parent")
            if parent:
                # This is simplified; proper implementation would walk up the tree
                pass
            return [0, 0, 612, 792]  # Default US Letter

        # Convert to list of floats
        return [float(x) for x in media_box]

    def get_page_resources(self, page_num: int) -> Optional[Dict[str, Any]]:
        """
        Get the resources dictionary for a page.

        Args:
            page_num: Page number (0-indexed)

        Returns:
            Resources dictionary or None
        """
        page = self.get_page(page_num)
        if page is None:
            return None

        resources = page.get("Resources")
        if resources is None:
            # Inherit from parent
            return None

        if isinstance(resources, PDFIndirectRef):
            return self.get_object(resources.object_number, resources.generation_number)

        return resources


def open_pdf(source: Union[str, Path, BinaryIO, bytes]) -> PDFReader:
    """
    Open a PDF file for reading.

    Args:
        source: PDF source - file path, file-like object, or bytes

    Returns:
        PDFReader instance

    Example:
        with open_pdf("document.pdf") as pdf:
            pdf.read()
            print(f"Pages: {pdf.page_count}")
    """
    reader = PDFReader(source)
    reader.read()
    return reader