"""
Content Stream Parser.

This module parses PDF content streams and interprets the operators
to extract text and other content with positioning information.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple, Union

from pdf_lowlevel.content.graphics import (
    GraphicsStateStack,
    Matrix,
)


@dataclass
class ContentOperator:
    """
    Represents a parsed content stream operator.

    In PDF content streams, operators come after their operands:
    operand1 operand2 ... operator
    """

    operator: str
    operands: List[Any]
    offset: int = 0  # Position in stream (for debugging)


@dataclass
class TextElement:
    """
    A piece of text extracted from the PDF with position information.

    This is the primary output of the content stream parser for text extraction.
    """

    text: str
    x: float  # Lower-left x in user space
    y: float  # Lower-left y (baseline) in user space
    width: float  # Width of text
    height: float  # Height of text (font size)
    font_name: Optional[str] = None
    font_size: float = 0.0
    page_number: int = 0

    # Additional metadata
    char_spacing: float = 0.0
    word_spacing: float = 0.0
    horizontal_scaling: float = 100.0
    text_render_mode: int = 0

    # Raw bytes (for debugging or re-encoding)
    raw_bytes: bytes = field(default=b"", repr=False)

    # Bounding box (computed)
    @property
    def bbox(self) -> Tuple[float, float, float, float]:
        """Return bounding box as (x0, y0, x1, y1)."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "text": self.text,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "bbox": list(self.bbox),
            "font_name": self.font_name,
            "font_size": self.font_size,
            "page_number": self.page_number,
        }


class ContentStreamParser:
    """
    Parser for PDF content streams.

    Content streams contain sequences of operators that describe
    what to render on a page. This parser tokenizes and interprets
    these operators.

    Key text operators:
    - BT/ET: Begin/End text object
    - Tf: Set font and size
    - Td/TD/T*: Move text position
    - Tm: Set text matrix
    - Tj/': Show text
    - TJ: Show text with individual glyph positioning
    - Tc/Tw/Tz/TL/Tr/Ts: Text state parameters
    """

    def __init__(self, stream_data: bytes):
        """
        Initialize the content stream parser.

        Args:
            stream_data: Decoded content stream bytes
        """
        self.data = stream_data
        self.pos = 0
        self.graphics_stack = GraphicsStateStack()
        self.in_text_object = False

        # Extracted elements
        self.text_elements: List[TextElement] = []

        # Font resolver callback (set externally)
        self.font_resolver: Optional[Callable[[str], Dict]] = None

        # Default font widths (for width calculation)
        self._default_char_width = 0.5  # Fraction of font size

    def parse(self) -> List[TextElement]:
        """
        Parse the content stream and extract text elements.

        Returns:
            List of TextElement objects
        """
        self.text_elements = []
        self.pos = 0
        self.graphics_stack.reset()

        for op in self._iter_operators():
            self._handle_operator(op)

        return self.text_elements

    def _iter_operators(self) -> Generator[ContentOperator, None, None]:
        """
        Iterate over operators in the content stream.

        Yields:
            ContentOperator objects
        """
        operands = []

        while self.pos < len(self.data):
            offset = self.pos

            # Skip whitespace
            self._skip_whitespace()

            if self.pos >= len(self.data):
                break

            # Check for comment
            if self.data[self.pos : self.pos + 1] == b"%":
                self._skip_comment()
                continue

            # Try to parse a value
            value = self._parse_value()

            if value is None:
                continue

            # Check if it's an operator (starts with letter)
            if isinstance(value, bytes) and len(value) > 0:
                first_byte = value[0:1]
                if first_byte.isalpha() or first_byte in (b"'", b'"'):
                    # It's an operator
                    operator = value.decode("latin-1", errors="replace")
                    yield ContentOperator(operator, operands, offset)
                    operands = []
                else:
                    operands.append(value)
            elif isinstance(value, (int, float, str)):
                operands.append(value)
            elif isinstance(value, list):
                operands.append(value)

    def _skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.pos < len(self.data) and self.data[self.pos : self.pos + 1] in b" \t\r\n\x00\x0c":
            self.pos += 1

    def _skip_comment(self) -> None:
        """Skip a comment (from % to end of line)."""
        while self.pos < len(self.data) and self.data[self.pos : self.pos + 1] not in b"\r\n":
            self.pos += 1

    def _parse_value(self) -> Any:
        """
        Parse a value from the content stream.

        Returns:
            Parsed value (int, float, bytes, list, or None)
        """
        if self.pos >= len(self.data):
            return None

        byte = self.data[self.pos : self.pos + 1]

        # String
        if byte == b"(":
            return self._parse_literal_string()
        elif byte == b"<":
            if self.pos + 1 < len(self.data) and self.data[self.pos + 1 : self.pos + 2] == b"<":
                return self._parse_dict()
            return self._parse_hex_string()

        # Array
        elif byte == b"[":
            return self._parse_array()

        # Name
        elif byte == b"/":
            return self._parse_name()

        # Number
        elif byte.isdigit() or byte in b"+-.":
            return self._parse_number()

        # Operator or keyword
        else:
            return self._parse_operator_or_name()

    def _parse_number(self) -> Union[int, float]:
        """Parse a number (integer or real)."""
        start = self.pos
        has_dot = False

        if self.data[self.pos : self.pos + 1] in b"+-":
            self.pos += 1

        while self.pos < len(self.data):
            byte = self.data[self.pos : self.pos + 1]
            if byte.isdigit():
                self.pos += 1
            elif byte == b"." and not has_dot:
                has_dot = True
                self.pos += 1
            else:
                break

        num_str = self.data[start : self.pos].decode("ascii")

        if has_dot:
            return float(num_str)
        else:
            return int(num_str)

    def _parse_literal_string(self) -> bytes:
        """Parse a literal string (...)."""
        self.pos += 1  # Skip (
        result = bytearray()
        paren_depth = 1

        while self.pos < len(self.data) and paren_depth > 0:
            byte = self.data[self.pos : self.pos + 1]
            self.pos += 1

            if byte == b"(":
                paren_depth += 1
                result.append(ord("("))
            elif byte == b")":
                paren_depth -= 1
                if paren_depth > 0:
                    result.append(ord(")"))
            elif byte == b"\\":
                if self.pos < len(self.data):
                    next_byte = self.data[self.pos : self.pos + 1]
                    self.pos += 1

                    escape_map = {
                        b"n": b"\n",
                        b"r": b"\r",
                        b"t": b"\t",
                        b"b": b"\b",
                        b"f": b"\f",
                        b"(": b"(",
                        b")": b")",
                        b"\\": b"\\",
                    }

                    if next_byte in escape_map:
                        result.extend(escape_map[next_byte])
                    elif next_byte.isdigit():
                        # Octal escape
                        octal = next_byte.decode()
                        for _ in range(2):
                            if self.pos < len(self.data) and self.data[self.pos : self.pos + 1].isdigit():
                                octal += chr(self.data[self.pos])
                                self.pos += 1
                            else:
                                break
                        result.append(int(octal, 8) & 0xFF)
                    elif next_byte in b"\r\n":
                        # Line continuation
                        if next_byte == b"\r" and self.pos < len(self.data) and self.data[self.pos : self.pos + 1] == b"\n":
                            self.pos += 1
                    else:
                        # Unknown escape, include as-is
                        result.extend(next_byte)
            else:
                result.extend(byte)

        return bytes(result)

    def _parse_hex_string(self) -> bytes:
        """Parse a hex string (<...>)."""
        self.pos += 1  # Skip <
        hex_chars = []

        while self.pos < len(self.data) and self.data[self.pos : self.pos + 1] != b">":
            byte = self.data[self.pos : self.pos + 1]
            self.pos += 1

            if byte not in b" \t\r\n":
                hex_chars.append(chr(byte[0]))

        # Skip >
        if self.pos < len(self.data):
            self.pos += 1

        # Pad with 0 if odd length
        if len(hex_chars) % 2 == 1:
            hex_chars.append("0")

        try:
            return bytes.fromhex("".join(hex_chars))
        except ValueError:
            return "".join(hex_chars).encode("latin-1")

    def _parse_array(self) -> List[Any]:
        """Parse an array [...]."""
        self.pos += 1  # Skip [
        items = []

        while self.pos < len(self.data):
            self._skip_whitespace()

            if self.pos >= len(self.data):
                break

            if self.data[self.pos : self.pos + 1] == b"]":
                self.pos += 1
                break

            value = self._parse_value()
            if value is not None:
                items.append(value)

        return items

    def _parse_dict(self) -> Dict[str, Any]:
        """Parse a dictionary <<...>>."""
        self.pos += 2  # Skip <<
        result = {}

        while self.pos < len(self.data):
            self._skip_whitespace()

            if self.pos + 1 < len(self.data) and self.data[self.pos : self.pos + 2] == b">>":
                self.pos += 2
                break

            key = self._parse_value()
            value = self._parse_value()

            if key is not None:
                result[str(key)] = value

        return result

    def _parse_name(self) -> str:
        """Parse a name (/Name)."""
        self.pos += 1  # Skip /
        start = self.pos

        while self.pos < len(self.data):
            byte = self.data[self.pos : self.pos + 1]
            if byte in b" \t\r\n[]<>()/%":
                break
            self.pos += 1

        return self.data[start : self.pos].decode("utf-8", errors="replace")

    def _parse_operator_or_name(self) -> bytes:
        """Parse an operator or keyword."""
        start = self.pos

        while self.pos < len(self.data):
            byte = self.data[self.pos : self.pos + 1]
            if byte in b" \t\r\n[]<>()/%":
                break
            self.pos += 1

        return self.data[start : self.pos]

    def _handle_operator(self, op: ContentOperator) -> None:
        """
        Handle a content stream operator.

        Args:
            op: The operator to handle
        """
        handler = self._operator_handlers.get(op.operator)
        if handler:
            handler(self, op.operands)

    # Operator handlers
    def _op_bt(self, operands: List) -> None:
        """Begin text object."""
        self.in_text_object = True
        self.graphics_stack.text_position.move_to(0, 0)

    def _op_et(self, operands: List) -> None:
        """End text object."""
        self.in_text_object = False

    def _op_q(self, operands: List) -> None:
        """Save graphics state."""
        self.graphics_stack.save()

    def _op_Q(self, operands: List) -> None:
        """Restore graphics state."""
        self.graphics_stack.restore()

    def _op_cm(self, operands: List) -> None:
        """Concatenate matrix to CTM."""
        if len(operands) == 6:
            matrix = Matrix(
                float(operands[0]),
                float(operands[1]),
                float(operands[2]),
                float(operands[3]),
                float(operands[4]),
                float(operands[5]),
            )
            self.graphics_stack.modify_ctm(matrix)

    def _op_tf(self, operands: List) -> None:
        """Set font (Tf operator)."""
        if len(operands) >= 2:
            font_name = operands[0]
            if isinstance(font_name, bytes):
                font_name = font_name.decode("latin-1", errors="replace")
            font_size = float(operands[1])

            text_state = self.graphics_stack.text_state
            text_state.font_name = font_name
            text_state.font_size = font_size

    def _op_tc(self, operands: List) -> None:
        """Set character spacing (Tc)."""
        if operands:
            self.graphics_stack.text_state.char_spacing = float(operands[0])

    def _op_tw(self, operands: List) -> None:
        """Set word spacing (Tw)."""
        if operands:
            self.graphics_stack.text_state.word_spacing = float(operands[0])

    def _op_tz(self, operands: List) -> None:
        """Set horizontal scaling (Tz)."""
        if operands:
            self.graphics_stack.text_state.horizontal_scaling = float(operands[0])

    def _op_tl(self, operands: List) -> None:
        """Set text leading (TL)."""
        if operands:
            self.graphics_stack.text_state.leading = float(operands[0])

    def _op_tr(self, operands: List) -> None:
        """Set text rendering mode (Tr)."""
        if operands:
            self.graphics_stack.text_state.render_mode = int(operands[0])

    def _op_ts(self, operands: List) -> None:
        """Set text rise (Ts)."""
        if operands:
            self.graphics_stack.text_state.text_rise = float(operands[0])

    def _op_td(self, operands: List) -> None:
        """Move text position (Td)."""
        if len(operands) >= 2:
            tx = float(operands[0])
            ty = float(operands[1])
            self.graphics_stack.text_position.move_by(tx, ty)

    def _op_TD(self, operands: List) -> None:
        """Move text position and set leading (TD)."""
        if len(operands) >= 2:
            tx = float(operands[0])
            ty = float(operands[1])
            self.graphics_stack.text_state.leading = -ty
            self.graphics_stack.text_position.move_by(tx, ty)

    def _op_t_star(self, operands: List) -> None:
        """Move to start of next line (T*)."""
        leading = self.graphics_stack.text_state.leading
        self.graphics_stack.text_position.new_line(leading)

    def _op_tm(self, operands: List) -> None:
        """Set text matrix (Tm)."""
        if len(operands) == 6:
            self.graphics_stack.text_position.set_matrix(
                float(operands[0]),
                float(operands[1]),
                float(operands[2]),
                float(operands[3]),
                float(operands[4]),
                float(operands[5]),
            )

    def _op_tj(self, operands: List) -> None:
        """Show text (Tj)."""
        if not operands:
            return

        text_bytes = operands[0]
        if isinstance(text_bytes, str):
            text_bytes = text_bytes.encode("latin-1", errors="replace")

        self._emit_text(text_bytes)

    def _op_quote(self, operands: List) -> None:
        """Move to next line and show text (')."""
        self._op_t_star([])
        self._op_tj(operands)

    def _op_double_quote(self, operands: List) -> None:
        """Set spacing, move to next line, and show text (\")."""
        if len(operands) >= 3:
            self._op_tw([operands[0]])
            self._op_tc([operands[1]])
            self._op_t_star([])
            self._op_tj([operands[2]])

    def _op_TJ(self, operands: List) -> None:
        """Show text with individual glyph positioning (TJ)."""
        if not operands or not isinstance(operands[0], list):
            return

        array = operands[0]

        for item in array:
            if isinstance(item, (bytes, str)):
                # Text string
                if isinstance(item, str):
                    item = item.encode("latin-1", errors="replace")
                self._emit_text(item, adjust_position=False)

                # Update position based on text width
                width = self._get_text_width(item)
                self.graphics_stack.text_position.move_by(width, 0)

            elif isinstance(item, (int, float)):
                # Position adjustment (in 1/1000ths of em)
                adjustment = -float(item) / 1000.0 * self.graphics_stack.text_state.font_size
                # Apply horizontal scaling
                scaling = self.graphics_stack.text_state.horizontal_scaling / 100.0
                self.graphics_stack.text_position.move_by(adjustment * scaling, 0)

    def _emit_text(self, text_bytes: bytes, adjust_position: bool = True) -> None:
        """
        Emit a text element with position information.

        Args:
            text_bytes: Raw text bytes
            adjust_position: Whether to update text position after emitting
        """
        text_state = self.graphics_stack.text_state
        text_pos = self.graphics_stack.text_position
        ctm = self.graphics_stack.ctm

        # Decode text to string
        text = self._decode_text(text_bytes)

        # Get position in user space
        render_matrix = ctm * text_pos.text_matrix
        x, y = render_matrix.transform_point(0, 0)

        # Calculate text dimensions
        font_size = text_state.font_size
        width = self._get_text_width(text_bytes)
        height = font_size

        # Apply transformation to get actual rendered size
        dx, dy = ctm.transform_vector(width, 0)
        rendered_width = dx
        rendered_height = height

        # Create text element
        element = TextElement(
            text=text,
            x=x,
            y=y,
            width=rendered_width,
            height=rendered_height,
            font_name=text_state.font_name,
            font_size=font_size,
            char_spacing=text_state.char_spacing,
            word_spacing=text_state.word_spacing,
            horizontal_scaling=text_state.horizontal_scaling,
            text_render_mode=text_state.render_mode,
            raw_bytes=text_bytes,
        )

        self.text_elements.append(element)

        # Update position
        if adjust_position:
            self.graphics_stack.text_position.move_by(width, 0)

    def _decode_text(self, text_bytes: bytes) -> str:
        """
        Decode text bytes to a string.

        This is a simplified decoder. For proper decoding, we need
        font encoding information (ToUnicode CMap or standard encoding).

        Args:
            text_bytes: Raw text bytes

        Returns:
            Decoded string
        """
        # Try UTF-16BE first (for Unicode strings starting with BOM)
        if len(text_bytes) >= 2 and text_bytes[0:2] == b'\xfe\xff':
            try:
                return text_bytes.decode('utf-16-be')
            except UnicodeDecodeError:
                pass

        # Try UTF-8
        try:
            return text_bytes.decode('utf-8')
        except UnicodeDecodeError:
            pass

        # Fall back to Latin-1 (maps all bytes to Unicode)
        # This handles WinAnsiEncoding and MacRomanEncoding for ASCII range
        result = []
        for byte in text_bytes:
            if 32 <= byte <= 126:
                # ASCII printable range
                result.append(chr(byte))
            elif byte == 0x0A:
                result.append('\n')
            elif byte == 0x0D:
                result.append('\r')
            elif byte == 0x09:
                result.append('\t')
            else:
                # Use Latin-1 mapping for now
                # In a full implementation, we'd use font's ToUnicode map
                result.append(chr(byte))

        return ''.join(result)

    def _get_text_width(self, text_bytes: bytes) -> float:
        """
        Calculate the width of text in text space units.

        Args:
            text_bytes: Raw text bytes

        Returns:
            Width in text space units
        """
        text_state = self.graphics_stack.text_state
        font_size = text_state.font_size
        char_spacing = text_state.char_spacing
        word_spacing = text_state.word_spacing
        scaling = text_state.horizontal_scaling / 100.0

        # Get font widths if available
        widths = self._get_font_widths()

        width = 0.0
        for byte in text_bytes:
            # Get character width (in 1/1000ths of em)
            char_width = widths.get(byte, self._default_char_width * 1000)

            # Convert to text space units
            w = char_width / 1000.0 * font_size
            width += w

            # Add character spacing
            width += char_spacing * scaling

            # Add word spacing for space character
            if byte == 32:  # Space
                width += word_spacing * scaling

        return width

    def _get_font_widths(self) -> Dict[int, float]:
        """
        Get character widths for the current font.

        Returns:
            Dictionary mapping character codes to widths (in 1/1000ths of em)
        """
        # Try to get widths from font resolver
        if self.font_resolver:
            font_name = self.graphics_stack.text_state.font_name
            if font_name:
                font_info = self.font_resolver(font_name)
                if font_info and 'widths' in font_info:
                    return font_info['widths']

        # Default widths (approximate)
        # For most Latin fonts, average width is around 500 (in 1/1000ths)
        default_widths = {}
        for i in range(256):
            # Simple proportional width approximation
            if i == 32:  # Space
                default_widths[i] = 250
            elif 65 <= i <= 90:  # Uppercase
                default_widths[i] = 700
            elif 97 <= i <= 122:  # Lowercase
                default_widths[i] = 500
            elif 48 <= i <= 57:  # Digits
                default_widths[i] = 500
            else:
                default_widths[i] = 500

        return default_widths

    # Operator handler mapping
    _operator_handlers: Dict[str, Callable] = {
        # Text object operators
        "BT": _op_bt,
        "ET": _op_et,

        # Graphics state operators
        "q": _op_q,
        "Q": _op_Q,
        "cm": _op_cm,

        # Text state operators
        "Tf": _op_tf,
        "Tc": _op_tc,
        "Tw": _op_tw,
        "Tz": _op_tz,
        "TL": _op_tl,
        "Tr": _op_tr,
        "Ts": _op_ts,

        # Text positioning operators
        "Td": _op_td,
        "TD": _op_TD,
        "T*": _op_t_star,
        "Tm": _op_tm,

        # Text showing operators
        "Tj": _op_tj,
        "TJ": _op_TJ,
        "'": _op_quote,
        '"': _op_double_quote,
    }


def parse_content_stream(stream_data: bytes) -> List[TextElement]:
    """
    Parse a content stream and extract text elements.

    Args:
        stream_data: Decoded content stream bytes

    Returns:
        List of TextElement objects
    """
    parser = ContentStreamParser(stream_data)
    return parser.parse()