"""
PDF Object Model.

This module defines the Python classes that represent PDF objects.
PDF supports 8 basic object types: boolean, integer, real, string, name,
array, dictionary, and stream. There are also indirect object references.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, BinaryIO, Dict, List, Optional, Union


class PDFObjectType(Enum):
    """Enumeration of all PDF object types."""

    BOOLEAN = auto()
    INTEGER = auto()
    REAL = auto()
    STRING = auto()
    HEX_STRING = auto()
    NAME = auto()
    ARRAY = auto()
    DICTIONARY = auto()
    STREAM = auto()
    NULL = auto()
    INDIRECT_REF = auto()
    INDIRECT_OBJ = auto()


@dataclass
class PDFIndirectRef:
    """
    Reference to an indirect object.
    Format: n m R (e.g., "5 0 R")
    """

    object_number: int
    generation_number: int

    def __repr__(self) -> str:
        return f"PDFIndirectRef({self.object_number}, {self.generation_number})"

    def __hash__(self) -> int:
        return hash((self.object_number, self.generation_number))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PDFIndirectRef):
            return False
        return (
            self.object_number == other.object_number
            and self.generation_number == other.generation_number
        )


@dataclass
class PDFIndirectObject:
    """
    An indirect object definition.
    Format: n m obj ... endobj
    """

    object_number: int
    generation_number: int
    value: PDFObject

    def __repr__(self) -> str:
        return f"PDFIndirectObject({self.object_number}, {self.generation_number}, {self.value!r})"


@dataclass
class PDFStream:
    """
    A PDF stream object.
    Streams contain binary data and have a dictionary with metadata.
    """

    dictionary: Dict[str, PDFObject]
    data: bytes = field(repr=False)
    file_offset: int = 0  # Offset in file (for debugging)
    file: Optional[BinaryIO] = field(default=None, repr=False, compare=False)

    def get(self, key: str, default: Optional[PDFObject] = None) -> Optional[PDFObject]:
        """Get a value from the stream dictionary."""
        return self.dictionary.get(key, default)

    def __repr__(self) -> str:
        length = len(self.data) if self.data else 0
        return f"PDFStream(dict={self.dictionary}, length={length})"


# Type alias for all PDF objects
PDFObject = Union[
    bool,  # Boolean
    int,  # Integer
    float,  # Real
    str,  # String (text or hex)
    bytes,  # Raw string data
    List[Any],  # Array
    Dict[str, Any],  # Dictionary
    PDFStream,  # Stream
    None,  # Null
    PDFIndirectRef,  # Indirect reference
    PDFIndirectObject,  # Indirect object
]


# Name object representation
@dataclass(frozen=True)
class PDFName:
    """
    A PDF name object.
    Names start with '/' in PDF syntax.
    Stored without the leading '/'.
    """

    value: str

    def __repr__(self) -> str:
        return f"/{self.value}"

    def __str__(self) -> str:
        return self.value

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PDFName):
            return self.value == other.value
        if isinstance(other, str):
            return self.value == other
        return False


# Common PDF names as constants
class PDFNames:
    """Common PDF name constants."""

    TYPE = PDFName("Type")
    PAGE = PDFName("Page")
    PAGES = PDFName("Pages")
    CATALOG = PDFName("Catalog")
    PARENT = PDFName("Parent")
    KIDS = PDFName("Kids")
    COUNT = PDFName("Count")
    MEDIABOX = PDFName("MediaBox")
    CONTENTS = PDFName("Contents")
    RESOURCES = PDFName("Resources")
    FONT = PDFName("Font")
    LENGTH = PDFName("Length")
    FILTER = PDFName("Filter")
    FLATE_DECODE = PDFName("FlateDecode")
    LZW_DECODE = PDFName("LZWDecode")
    ASCII_HEX_DECODE = PDFName("ASCIIHexDecode")
    ASCII_85_DECODE = PDFName("ASCII85Decode")
    RUN_LENGTH_DECODE = PDFName("RunLengthDecode")
    SUBTYPE = PDFName("Subtype")
    XOBJECT = PDFName("XObject")
    FORM = PDFName("Form")
    IMAGE = PDFName("Image")
    WIDTH = PDFName("Width")
    HEIGHT = PDFName("Height")
    COLORSPACE = PDFName("ColorSpace")
    BITS_PER_COMPONENT = PDFName("BitsPerComponent")
    ENCODING = PDFName("Encoding")
    TO_UNICODE = PDFName("ToUnicode")
    BASE_FONT = PDFName("BaseFont")
    FIRST_CHAR = PDFName("FirstChar")
    LAST_CHAR = PDFName("LastChar")
    DESCENDANT_FONTS = PDFName("DescendantFonts")
    CID_FONT_TYPE0 = PDFName("CIDFontType0")
    CID_FONT_TYPE2 = PDFName("CIDFontType2")