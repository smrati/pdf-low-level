"""
Graphics State for PDF Content Streams.

This module manages the graphics state machine that tracks
transformations, text state, and positioning during content stream parsing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class Matrix:
    """
    A 3x3 transformation matrix for PDF graphics.

    PDF uses a 3x3 matrix but stores it as [a, b, c, d, e, f]:
    | a b 0 |
    | c d 0 |
    | e f 1 |

    For transformations:
    - Translation: [1, 0, 0, 1, tx, ty]
    - Scaling: [sx, 0, 0, sy, 0, 0]
    - Rotation: [cos(θ), sin(θ), -sin(θ), cos(θ), 0, 0]
    """

    a: float = 1.0
    b: float = 0.0
    c: float = 0.0
    d: float = 1.0
    e: float = 0.0
    f: float = 0.0

    def __mul__(self, other: "Matrix") -> "Matrix":
        """Matrix multiplication (self * other)."""
        return Matrix(
            a=self.a * other.a + self.b * other.c,
            b=self.a * other.b + self.b * other.d,
            c=self.c * other.a + self.d * other.c,
            d=self.c * other.b + self.d * other.d,
            e=self.e * other.a + self.f * other.c + other.e,
            f=self.e * other.b + self.f * other.d + other.f,
        )

    def transform_point(self, x: float, y: float) -> Tuple[float, float]:
        """Transform a point (x, y) through this matrix."""
        new_x = self.a * x + self.c * y + self.e
        new_y = self.b * x + self.d * y + self.f
        return (new_x, new_y)

    def transform_vector(self, dx: float, dy: float) -> Tuple[float, float]:
        """Transform a vector (dx, dy) through this matrix (no translation)."""
        new_dx = self.a * dx + self.c * dy
        new_dy = self.b * dx + self.d * dy
        return (new_dx, new_dy)

    @classmethod
    def identity(cls) -> "Matrix":
        """Return identity matrix."""
        return cls()

    @classmethod
    def translation(cls, tx: float, ty: float) -> "Matrix":
        """Return translation matrix."""
        return cls(e=tx, f=ty)

    @classmethod
    def scaling(cls, sx: float, sy: float) -> "Matrix":
        """Return scaling matrix."""
        return cls(a=sx, d=sy)

    @classmethod
    def rotation(cls, angle: float) -> "Matrix":
        """Return rotation matrix (angle in radians)."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return cls(a=cos_a, b=sin_a, c=-sin_a, d=cos_a)

    def copy(self) -> "Matrix":
        """Return a copy of this matrix."""
        return Matrix(self.a, self.b, self.c, self.d, self.e, self.f)

    def to_list(self) -> List[float]:
        """Convert to [a, b, c, d, e, f] list."""
        return [self.a, self.b, self.c, self.d, self.e, self.f]

    @classmethod
    def from_list(cls, values: List[float]) -> "Matrix":
        """Create matrix from [a, b, c, d, e, f] list."""
        if len(values) != 6:
            raise ValueError(f"Expected 6 values, got {len(values)}")
        return cls(*values)


@dataclass
class TextState:
    """
    PDF Text State parameters.

    These parameters control how text is rendered.
    """

    # Font settings
    font_name: Optional[str] = None
    font_size: float = 0.0
    font_object: Optional[any] = None  # Will hold font dictionary

    # Character spacing (Tc operator)
    char_spacing: float = 0.0

    # Word spacing (Tw operator)
    word_spacing: float = 0.0

    # Horizontal scaling (Tz operator) - percentage (100 = normal)
    horizontal_scaling: float = 100.0

    # Leading (TL operator) - used for line spacing
    leading: float = 0.0

    # Text render mode (Tr operator)
    # 0 = fill, 1 = stroke, 2 = fill then stroke, 3 = invisible,
    # 4 = fill and add to clip, 5 = stroke and add to clip,
    # 6 = fill, stroke, and clip, 7 = add to clip
    render_mode: int = 0

    # Text rise (Ts operator) - vertical offset for superscript/subscript
    text_rise: float = 0.0

    # Text knockout (currently not tracked)
    text_knockout: bool = True

    def copy(self) -> "TextState":
        """Return a copy of this text state."""
        return TextState(
            font_name=self.font_name,
            font_size=self.font_size,
            font_object=self.font_object,
            char_spacing=self.char_spacing,
            word_spacing=self.word_spacing,
            horizontal_scaling=self.horizontal_scaling,
            leading=self.leading,
            render_mode=self.render_mode,
            text_rise=self.text_rise,
            text_knockout=self.text_knockout,
        )


@dataclass
class TextPosition:
    """
    Current text position tracking.

    The text matrix (Tm) combined with the CTM gives the
    text rendering matrix, which determines where text appears.
    """

    # Text matrix - tracks position/orientation of text space
    text_matrix: Matrix = field(default_factory=Matrix.identity)

    # Line matrix - position at start of current line
    line_matrix: Matrix = field(default_factory=Matrix.identity)

    # Current position on the line (for TJ operator tracking)
    current_x: float = 0.0
    current_y: float = 0.0

    def get_render_position(self, ctm: Matrix) -> Tuple[float, float]:
        """
        Get the current rendering position in user space.

        Args:
            ctm: Current Transformation Matrix

        Returns:
            (x, y) in user space coordinates
        """
        # Combine text matrix with CTM
        render_matrix = ctm * self.text_matrix
        return render_matrix.transform_point(0, 0)

    def get_baseline_position(self, ctm: Matrix) -> Tuple[float, float]:
        """Get the baseline position for text rendering."""
        return self.get_render_position(ctm)

    def move_to(self, x: float, y: float) -> None:
        """Move text position to (x, y) in text space."""
        self.text_matrix = Matrix.translation(x, y)
        self.line_matrix = self.text_matrix.copy()
        self.current_x = x
        self.current_y = y

    def move_by(self, dx: float, dy: float) -> None:
        """Move text position by (dx, dy) in text space."""
        new_x = self.text_matrix.e + dx
        new_y = self.text_matrix.f + dy
        self.text_matrix.e = new_x
        self.text_matrix.f = new_y
        self.current_x = new_x
        self.current_y = new_y

    def set_line_offset(self, offset: float) -> None:
        """Move to start of line with vertical offset (for Td/TD operators)."""
        self.text_matrix = Matrix.translation(self.line_matrix.e, self.line_matrix.f + offset)
        self.line_matrix = self.text_matrix.copy()
        self.current_x = self.text_matrix.e
        self.current_y = self.text_matrix.f

    def new_line(self, leading: float) -> None:
        """Move to start of next line (T* operator)."""
        self.text_matrix = Matrix.translation(self.line_matrix.e, self.line_matrix.f - leading)
        self.line_matrix = self.text_matrix.copy()
        self.current_x = self.text_matrix.e
        self.current_y = self.text_matrix.f

    def set_matrix(self, a: float, b: float, c: float, d: float, e: float, f: float) -> None:
        """Set the text matrix directly (Tm operator)."""
        self.text_matrix = Matrix(a, b, c, d, e, f)
        self.line_matrix = self.text_matrix.copy()
        self.current_x = e
        self.current_y = f

    def copy(self) -> "TextPosition":
        """Return a copy of this position state."""
        pos = TextPosition()
        pos.text_matrix = self.text_matrix.copy()
        pos.line_matrix = self.line_matrix.copy()
        pos.current_x = self.current_x
        pos.current_y = self.current_y
        return pos


@dataclass
class GraphicsState:
    """
    Complete graphics state for PDF rendering.

    This is the state that gets saved/restored with q/Q operators.
    """

    # Current Transformation Matrix
    ctm: Matrix = field(default_factory=Matrix.identity)

    # Text state
    text_state: TextState = field(default_factory=TextState)

    # Text position tracking
    text_position: TextPosition = field(default_factory=TextPosition)

    # Clipping path (simplified - not fully implemented)
    clipping_path: Optional[any] = None

    # Color space and color values (simplified)
    fill_color: Tuple[float, ...] = (0.0,)  # Black
    stroke_color: Tuple[float, ...] = (0.0,)

    # Line width
    line_width: float = 1.0

    # Line cap style
    line_cap: int = 0

    # Line join style
    line_join: int = 0

    # Miter limit
    miter_limit: float = 10.0

    # Dash pattern
    dash_pattern: Tuple[List[float], float] = ([], 0.0)

    def copy(self) -> "GraphicsState":
        """Return a copy of this graphics state (for q operator)."""
        return GraphicsState(
            ctm=self.ctm.copy(),
            text_state=self.text_state.copy(),
            text_position=self.text_position.copy(),
            clipping_path=self.clipping_path,
            fill_color=self.fill_color,
            stroke_color=self.stroke_color,
            line_width=self.line_width,
            line_cap=self.line_cap,
            line_join=self.line_join,
            miter_limit=self.miter_limit,
            dash_pattern=(list(self.dash_pattern[0]), self.dash_pattern[1]),
        )


class GraphicsStateStack:
    """
    Stack of graphics states.

    Manages save/restore operations (q/Q operators) and provides
    access to the current graphics state.
    """

    def __init__(self):
        """Initialize the graphics state stack."""
        self._stack: List[GraphicsState] = [GraphicsState()]

    @property
    def current(self) -> GraphicsState:
        """Get the current graphics state."""
        return self._stack[-1]

    def save(self) -> None:
        """Save current state (q operator)."""
        self._stack.append(self.current.copy())

    def restore(self) -> None:
        """Restore previous state (Q operator)."""
        if len(self._stack) > 1:
            self._stack.pop()

    @property
    def ctm(self) -> Matrix:
        """Get current transformation matrix."""
        return self.current.ctm

    def set_ctm(self, matrix: Matrix) -> None:
        """Set current transformation matrix."""
        self.current.ctm = matrix

    def modify_ctm(self, matrix: Matrix) -> None:
        """Modify CTM by concatenating a matrix (cm operator)."""
        self.current.ctm = matrix * self.current.ctm

    @property
    def text_state(self) -> TextState:
        """Get current text state."""
        return self.current.text_state

    @property
    def text_position(self) -> TextPosition:
        """Get current text position."""
        return self.current.text_position

    def reset(self) -> None:
        """Reset to initial state."""
        self._stack = [GraphicsState()]