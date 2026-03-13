"""
Content stream parsing package.
"""

from pdf_lowlevel.content.graphics import (
    GraphicsState,
    GraphicsStateStack,
    Matrix,
    TextPosition,
    TextState,
)
from pdf_lowlevel.content.stream import (
    ContentOperator,
    ContentStreamParser,
    TextElement,
    parse_content_stream,
)
from pdf_lowlevel.content.grouper import (
    TextGrouper,
    TextLine,
    TextBlock,
    group_text_elements,
)

__all__ = [
    # Graphics
    "Matrix",
    "TextState",
    "TextPosition",
    "GraphicsState",
    "GraphicsStateStack",
    # Stream
    "ContentOperator",
    "ContentStreamParser",
    "TextElement",
    "parse_content_stream",
    # Grouper
    "TextGrouper",
    "TextLine",
    "TextBlock",
    "group_text_elements",
]
