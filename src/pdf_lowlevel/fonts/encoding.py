"""
Font Encoding Support.

This module handles font encoding and character mapping for text extraction.
PDF fonts can use various encodings: standard encodings, custom encodings,
or ToUnicode CMaps for mapping character codes to Unicode values.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

# Standard PDF encodings
WIN_ANSI_ENCODING: Dict[int, str] = {
    0: '\x00', 1: '\x01', 2: '\x02', 3: '\x03', 4: '\x04', 5: '\x05', 6: '\x06', 7: '\x07',
    8: '\x08', 9: '\t', 10: '\n', 11: '\x0b', 12: '\x0c', 13: '\r', 14: '\x0e', 15: '\x0f',
    16: '\x10', 17: '\x11', 18: '\x12', 19: '\x13', 20: '\x14', 21: '\x15', 22: '\x16', 23: '\x17',
    24: '\x18', 25: '\x19', 26: '\x1a', 27: '\x1b', 28: '\x1c', 29: '\x1d', 30: '\x1e', 31: '\x1f',
    32: ' ', 33: '!', 34: '"', 35: '#', 36: '$', 37: '%', 38: '&', 39: "'",
    40: '(', 41: ')', 42: '*', 43: '+', 44: ',', 45: '-', 46: '.', 47: '/',
    48: '0', 49: '1', 50: '2', 51: '3', 52: '4', 53: '5', 54: '6', 55: '7',
    56: '8', 57: '9', 58: ':', 59: ';', 60: '<', 61: '=', 62: '>', 63: '?',
    64: '@', 65: 'A', 66: 'B', 67: 'C', 68: 'D', 69: 'E', 70: 'F', 71: 'G',
    72: 'H', 73: 'I', 74: 'J', 75: 'K', 76: 'L', 77: 'M', 78: 'N', 79: 'O',
    80: 'P', 81: 'Q', 82: 'R', 83: 'S', 84: 'T', 85: 'U', 86: 'V', 87: 'W',
    88: 'X', 89: 'Y', 90: 'Z', 91: '[', 92: '\\', 93: ']', 94: '^', 95: '_',
    96: '`', 97: 'a', 98: 'b', 99: 'c', 100: 'd', 101: 'e', 102: 'f', 103: 'g',
    104: 'h', 105: 'i', 106: 'j', 107: 'k', 108: 'l', 109: 'm', 110: 'n', 111: 'o',
    112: 'p', 113: 'q', 114: 'r', 115: 's', 116: 't', 117: 'u', 118: 'v', 119: 'w',
    120: 'x', 121: 'y', 122: 'z', 123: '{', 124: '|', 125: '}', 126: '~', 127: '\x7f',
    128: '\u20ac', 129: '\x81', 130: '\u201a', 131: '\u0192', 132: '\u201e', 133: '\u2026', 134: '\u2020', 135: '\u2021',
    136: '\u02c6', 137: '\u2030', 138: '\u0160', 139: '\u2039', 140: '\u0152', 141: '\x8d', 142: '\u017d', 143: '\x8f',
    144: '\x90', 145: '\u2018', 146: '\u2019', 147: '\u201c', 148: '\u201d', 149: '\u2022', 150: '\u2013', 151: '\u2014',
    152: '\u02dc', 153: '\u2122', 154: '\u0161', 155: '\u203a', 156: '\u0153', 157: '\x9d', 158: '\u017e', 159: '\u0178',
    160: '\xa0', 161: '\xa1', 162: '\xa2', 163: '\xa3', 164: '\xa4', 165: '\xa5', 166: '\xa6', 167: '\xa7',
    168: '\xa8', 169: '\xa9', 170: '\xaa', 171: '\xab', 172: '\xac', 173: '\xad', 174: '\xae', 175: '\xaf',
    176: '\xb0', 177: '\xb1', 178: '\xb2', 179: '\xb3', 180: '\xb4', 181: '\xb5', 182: '\xb6', 183: '\xb7',
    184: '\xb8', 185: '\xb9', 186: '\xba', 187: '\xbb', 188: '\xbc', 189: '\xbd', 190: '\xbe', 191: '\xbf',
    192: '\xc0', 193: '\xc1', 194: '\xc2', 195: '\xc3', 196: '\xc4', 197: '\xc5', 198: '\xc6', 199: '\xc7',
    200: '\xc8', 201: '\xc9', 202: '\xca', 203: '\xcb', 204: '\xcc', 205: '\xcd', 206: '\xce', 207: '\xcf',
    208: '\xd0', 209: '\xd1', 210: '\xd2', 211: '\xd3', 212: '\xd4', 213: '\xd5', 214: '\xd6', 215: '\xd7',
    216: '\xd8', 217: '\xd9', 218: '\xda', 219: '\xdb', 220: '\xdc', 221: '\xdd', 222: '\xde', 223: '\xdf',
    224: '\xe0', 225: '\xe1', 226: '\xe2', 227: '\xe3', 228: '\xe4', 229: '\xe5', 230: '\xe6', 231: '\xe7',
    232: '\xe8', 233: '\xe9', 234: '\xea', 235: '\xeb', 236: '\xec', 237: '\xed', 238: '\xee', 239: '\xef',
    240: '\xf0', 241: '\xf1', 242: '\xf2', 243: '\xf3', 244: '\xf4', 245: '\xf5', 246: '\xf6', 247: '\xf7',
    248: '\xf8', 249: '\xf9', 250: '\xfa', 251: '\xfb', 252: '\xfc', 253: '\xfd', 254: '\xfe', 255: '\xff',
}

# MacRomanEncoding (simplified - covers most common characters)
MAC_ROMAN_ENCODING: Dict[int, str] = {
    **{i: chr(i) for i in range(128)},  # ASCII is same
    128: '\xc4', 129: '\xc5', 130: '\xc7', 131: '\xc9', 132: '\xd1', 133: '\xd6', 134: '\xdc', 135: '\xe1',
    136: '\xe0', 137: '\xe2', 138: '\xe4', 139: '\xe3', 140: '\xe5', 141: '\xe7', 142: '\xe9', 143: '\xe8',
    144: '\xea', 145: '\xeb', 146: '\xed', 147: '\xec', 148: '\xee', 149: '\xef', 150: '\xf1', 151: '\xf3',
    152: '\xf2', 153: '\xf4', 154: '\xf6', 155: '\xf5', 156: '\xfa', 157: '\xf9', 158: '\xfb', 159: '\xfc',
    160: '\u2020', 161: '\xb0', 162: '\xa2', 163: '\xa3', 164: '\xa7', 165: '\u2022', 166: '\xb6', 167: '\xdf',
    168: '\xae', 169: '\xa9', 170: '\u2122', 171: '\xb4', 172: '\xa8', 173: '\u2260', 174: '\xc6', 175: '\xd8',
    176: '\u221e', 177: '\xb1', 178: '\u2264', 179: '\u2265', 180: '\xa5', 181: '\xb5', 182: '\u2202', 183: '\u2211',
    184: '\u220f', 185: '\u03c0', 186: '\u222b', 187: '\xaa', 188: '\xba', 189: '\u03a9', 190: '\xe6', 191: '\xf8',
    192: '\xbf', 193: '\xa1', 194: '\xac', 195: '\u221a', 196: '\u0192', 197: '\u2248', 198: '\u2206', 199: '\xab',
    200: '\xbb', 201: '\u2026', 202: '\xa0', 203: '\xc0', 204: '\xc3', 205: '\xd5', 206: '\u0152', 207: '\u0153',
    208: '\u2013', 209: '\u2014', 210: '\u201c', 211: '\u201d', 212: '\u2018', 213: '\u2019', 214: '\xf7', 215: '\u25ca',
    216: '\xff', 217: '\u0178', 218: '\u2044', 219: '\u20ac', 220: '\u2039', 221: '\u203a', 222: '\ufb01', 223: '\ufb02',
    224: '\u2021', 225: '\xb7', 226: '\u201a', 227: '\u201e', 228: '\u2030', 229: '\xc2', 230: '\xca', 231: '\xc1',
    232: '\xcb', 233: '\xc8', 234: '\xcd', 235: '\xce', 236: '\xcf', 237: '\xcc', 238: '\xd3', 239: '\xd4',
    240: '\uf8ff', 241: '\xd2', 242: '\xda', 243: '\xdb', 244: '\xd9', 245: '\u0131', 246: '\u02c6', 247: '\u02dc',
    248: '\xaf', 249: '\u02d8', 250: '\u02d9', 251: '\u02da', 252: '\xb8', 253: '\u02dd', 254: '\u02db', 255: '\u02c7',
}

# Standard Type1 font glyph names to Unicode
GLYPH_TO_UNICODE: Dict[str, str] = {
    'space': ' ', 'exclam': '!', 'quotedbl': '"', 'numbersign': '#', 'dollar': '$',
    'percent': '%', 'ampersand': '&', 'quoteright': "'", 'parenleft': '(', 'parenright': ')',
    'asterisk': '*', 'plus': '+', 'comma': ',', 'hyphen': '-', 'period': '.', 'slash': '/',
    'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
    'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'colon': ':', 'semicolon': ';',
    'less': '<', 'equal': '=', 'greater': '>', 'question': '?', 'at': '@',
    'A': 'A', 'B': 'B', 'C': 'C', 'D': 'D', 'E': 'E', 'F': 'F', 'G': 'G', 'H': 'H',
    'I': 'I', 'J': 'J', 'K': 'K', 'L': 'L', 'M': 'M', 'N': 'N', 'O': 'O', 'P': 'P',
    'Q': 'Q', 'R': 'R', 'S': 'S', 'T': 'T', 'U': 'U', 'V': 'V', 'W': 'W', 'X': 'X',
    'Y': 'Y', 'Z': 'Z', 'bracketleft': '[', 'backslash': '\\', 'bracketright': ']',
    'asciicircum': '^', 'underscore': '_', 'quoteleft': '`',
    'a': 'a', 'b': 'b', 'c': 'c', 'd': 'd', 'e': 'e', 'f': 'f', 'g': 'g', 'h': 'h',
    'i': 'i', 'j': 'j', 'k': 'k', 'l': 'l', 'm': 'm', 'n': 'n', 'o': 'o', 'p': 'p',
    'q': 'q', 'r': 'r', 's': 's', 't': 't', 'u': 'u', 'v': 'v', 'w': 'w', 'x': 'x',
    'y': 'y', 'z': 'z', 'braceleft': '{', 'bar': '|', 'braceright': '}', 'asciitilde': '~',
    'bullet': '\u2022', 'emdash': '\u2014', 'endash': '\u2013', 'ellipsis': '\u2026',
    'fi': 'fi', 'fl': 'fl', 'ffi': 'ffi', 'ffl': 'ffl', 'ff': 'ff',
}


class CMapParser:
    """
    Parser for ToUnicode CMap streams.

    CMaps define mappings from character codes to Unicode values.
    They use a postfix notation with specific operators.
    """

    def __init__(self, cmap_data: bytes):
        """
        Initialize the CMap parser.

        Args:
            cmap_data: Raw CMap stream data
        """
        self.data = cmap_data
        self.pos = 0
        self.cmap: Dict[int, str] = {}
        self.codespaceranges: List[Tuple[int, int]] = []

    def parse(self) -> Dict[int, str]:
        """
        Parse the CMap and return the character mapping.

        Returns:
            Dictionary mapping character codes to Unicode strings
        """
        self.pos = 0
        self.cmap = {}
        self.codespaceranges = []

        while self.pos < len(self.data):
            self._skip_whitespace()
            if self.pos >= len(self.data):
                break

            # Read token
            token = self._read_token()

            if token == b'begincodespacerange':
                self._parse_codespacerange()
            elif token == b'beginbfchar':
                self._parse_bfchar()
            elif token == b'beginbfrange':
                self._parse_bfrange()

        return self.cmap

    def _skip_whitespace(self) -> None:
        """Skip whitespace and comments."""
        while self.pos < len(self.data):
            byte = self.data[self.pos:self.pos + 1]
            if byte in b' \t\r\n\x00\x0c':
                self.pos += 1
            elif byte == b'%':
                # Skip comment
                while self.pos < len(self.data) and self.data[self.pos:self.pos + 1] not in b'\r\n':
                    self.pos += 1
            else:
                break

    def _read_token(self) -> bytes:
        """Read the next token."""
        self._skip_whitespace()

        if self.pos >= len(self.data):
            return b''

        byte = self.data[self.pos:self.pos + 1]

        # String
        if byte == b'(':
            return self._read_string()
        # Hex string
        elif byte == b'<':
            return self._read_hex()
        # Number or name
        else:
            start = self.pos
            while self.pos < len(self.data):
                b = self.data[self.pos:self.pos + 1]
                if b in b' \t\r\n\x00\x0c[]{}()<>':
                    break
                self.pos += 1
            return self.data[start:self.pos]

    def _read_string(self) -> bytes:
        """Read a literal string (...)."""
        self.pos += 1  # Skip (
        result = bytearray()
        depth = 1

        while self.pos < len(self.data) and depth > 0:
            byte = self.data[self.pos:self.pos + 1]
            self.pos += 1

            if byte == b'(':
                depth += 1
                result.append(ord('('))
            elif byte == b')':
                depth -= 1
                if depth > 0:
                    result.append(ord(')'))
            elif byte == b'\\':
                if self.pos < len(self.data):
                    result.append(self.data[self.pos])
                    self.pos += 1
            else:
                result.extend(byte)

        return bytes(result)

    def _read_hex(self) -> bytes:
        """Read a hex string <...>."""
        self.pos += 1  # Skip <
        hex_chars = []

        while self.pos < len(self.data) and self.data[self.pos:self.pos + 1] != b'>':
            byte = self.data[self.pos:self.pos + 1]
            self.pos += 1
            if byte not in b' \t\r\n':
                hex_chars.append(chr(byte[0]))

        self.pos += 1  # Skip >

        if len(hex_chars) % 2 == 1:
            hex_chars.append('0')

        try:
            return bytes.fromhex(''.join(hex_chars))
        except ValueError:
            return b''

    def _read_number(self) -> int:
        """Read an integer."""
        self._skip_whitespace()
        start = self.pos

        if self.pos < len(self.data) and self.data[self.pos:self.pos + 1] in b'+-':
            self.pos += 1

        while self.pos < len(self.data) and self.data[self.pos:self.pos + 1].isdigit():
            self.pos += 1

        return int(self.data[start:self.pos])

    def _parse_codespacerange(self) -> None:
        """Parse codespacerange section."""
        count = self._read_number()
        self._skip_whitespace()

        for _ in range(count):
            start_code = self._read_token()
            end_code = self._read_token()

            if start_code and end_code:
                start = int.from_bytes(start_code, 'big')
                end = int.from_bytes(end_code, 'big')
                self.codespaceranges.append((start, end))

    def _parse_bfchar(self) -> None:
        """Parse bfchar section (single character mappings)."""
        count = self._read_number()
        self._skip_whitespace()

        for _ in range(count):
            src_code = self._read_token()
            dst_value = self._read_token()

            if src_code:
                code = int.from_bytes(src_code, 'big')
                if dst_value:
                    # Destination is Unicode value
                    unicode_val = self._hex_to_unicode(dst_value)
                    self.cmap[code] = unicode_val

    def _parse_bfrange(self) -> None:
        """Parse bfrange section (range mappings)."""
        count = self._read_number()
        self._skip_whitespace()

        for _ in range(count):
            src_start = self._read_token()
            src_end = self._read_token()
            dst_start = self._read_token()

            if src_start and src_end and dst_start:
                start_code = int.from_bytes(src_start, 'big')
                end_code = int.from_bytes(src_end, 'big')
                unicode_start = int.from_bytes(dst_start, 'big')

                for code in range(start_code, end_code + 1):
                    unicode_val = chr(unicode_start + (code - start_code))
                    self.cmap[code] = unicode_val

    def _hex_to_unicode(self, hex_bytes: bytes) -> str:
        """Convert hex bytes to Unicode string."""
        if not hex_bytes:
            return ''

        # UTF-16BE encoded
        if len(hex_bytes) >= 2 and hex_bytes[0:2] == b'\xfe\xff':
            try:
                return hex_bytes.decode('utf-16-be')
            except UnicodeDecodeError:
                pass

        # Try as UTF-16BE without BOM
        if len(hex_bytes) % 2 == 0:
            try:
                return hex_bytes.decode('utf-16-be')
            except UnicodeDecodeError:
                pass

        # Fall back to individual bytes
        return ''.join(chr(b) for b in hex_bytes)


class FontEncoder:
    """
    Handles character encoding for a PDF font.

    Supports standard encodings and ToUnicode CMaps.
    """

    def __init__(self):
        """Initialize the font encoder."""
        self.encoding: Optional[str] = None
        self.to_unicode: Optional[Dict[int, str]] = None
        self.differences: Dict[int, str] = {}
        self.widths: Dict[int, float] = {}

    def set_encoding(self, encoding_name: str) -> None:
        """
        Set the font encoding.

        Args:
            encoding_name: Name of the encoding (WinAnsiEncoding, MacRomanEncoding, etc.)
        """
        self.encoding = encoding_name

    def set_to_unicode(self, cmap_data: bytes) -> None:
        """
        Set the ToUnicode CMap for this font.

        Args:
            cmap_data: Raw CMap stream data
        """
        parser = CMapParser(cmap_data)
        self.to_unicode = parser.parse()

    def set_differences(self, differences: Dict[int, str]) -> None:
        """
        Set encoding differences.

        Args:
            differences: Dictionary mapping character codes to glyph names
        """
        self.differences = differences

    def set_widths(self, widths: Dict[int, float]) -> None:
        """
        Set character widths.

        Args:
            widths: Dictionary mapping character codes to widths
        """
        self.widths = widths

    def decode(self, char_code: int) -> str:
        """
        Decode a character code to Unicode.

        Args:
            char_code: Character code to decode

        Returns:
            Unicode character(s)
        """
        # Try ToUnicode CMap first
        if self.to_unicode and char_code in self.to_unicode:
            return self.to_unicode[char_code]

        # Try encoding differences
        if char_code in self.differences:
            glyph_name = self.differences[char_code]
            if glyph_name in GLYPH_TO_UNICODE:
                return GLYPH_TO_UNICODE[glyph_name]

        # Try standard encoding
        if self.encoding == 'WinAnsiEncoding':
            return WIN_ANSI_ENCODING.get(char_code, chr(char_code) if char_code < 256 else '\ufffd')
        elif self.encoding == 'MacRomanEncoding':
            return MAC_ROMAN_ENCODING.get(char_code, chr(char_code) if char_code < 256 else '\ufffd')

        # Fall back to Latin-1
        if char_code < 256:
            return chr(char_code)

        return '\ufffd'  # Replacement character

    def decode_string(self, data: bytes) -> str:
        """
        Decode a byte string to Unicode.

        Args:
            data: Byte string to decode

        Returns:
            Unicode string
        """
        return ''.join(self.decode(b) for b in data)

    def get_width(self, char_code: int) -> float:
        """
        Get the width of a character.

        Args:
            char_code: Character code

        Returns:
            Width in 1/1000ths of em
        """
        if char_code in self.widths:
            return self.widths[char_code]

        # Default width
        return 500


def parse_encoding(encoding_dict: Dict) -> Tuple[str, Dict[int, str]]:
    """
    Parse a font encoding dictionary.

    Args:
        encoding_dict: PDF encoding dictionary

    Returns:
        Tuple of (base_encoding, differences)
    """
    base_encoding = 'WinAnsiEncoding'  # Default
    differences = {}

    if isinstance(encoding_dict, dict):
        base = encoding_dict.get('BaseEncoding')
        if base:
            if hasattr(base, 'value'):
                base_encoding = base.value
            else:
                base_encoding = str(base)

        diffs = encoding_dict.get('Differences')
        if diffs and isinstance(diffs, list):
            current_code = 0
            for item in diffs:
                if isinstance(item, int):
                    current_code = item
                elif hasattr(item, 'value'):
                    differences[current_code] = item.value
                    current_code += 1
                else:
                    differences[current_code] = str(item)
                    current_code += 1

    return base_encoding, differences