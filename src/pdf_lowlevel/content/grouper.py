"""
Text Grouping Module.

This module provides functionality to group individual text fragments
into lines and blocks based on their positions, improving readability
of extracted PDF text.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Optional


class GroupingMode(Enum):
    """Algorithm to use for grouping text into lines."""
    
    TOLERANCE = "tolerance"
    """
    Quantization-based grouping (bucket by Y).
    Fast but may misorder characters with slightly different Y values.
    
    Elements are grouped by rounding Y to nearest tolerance value.
    """
    
    CLUSTER = "cluster"
    """
    Clustering-based grouping (nearest-neighbor).
    More accurate for documents with variable character positioning.
    
    Elements are clustered if their Y values are within tolerance
    of any element already in the cluster.
    """


@dataclass
class TextLine:
    """
    A line of text composed of grouped text fragments.
    
    All fragments in a line share approximately the same Y coordinate.
    """
    
    text: str
    y: float  # Y coordinate of the line
    x_start: float  # Leftmost X coordinate
    x_end: float  # Rightmost X coordinate
    fragments: List[dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "text": self.text,
            "y": self.y,
            "x_start": self.x_start,
            "x_end": self.x_end,
            "fragment_count": len(self.fragments),
        }


@dataclass  
class TextBlock:
    """
    A block of text lines that form a paragraph or column.
    
    Lines in a block are vertically adjacent with consistent spacing.
    """
    
    lines: List[TextLine] = field(default_factory=list)
    x_start: float = 0
    x_end: float = 0
    y_start: float = 0
    y_end: float = 0
    
    @property
    def text(self) -> str:
        """Get all text in the block as a string."""
        return "\n".join(line.text for line in self.lines)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "text": self.text,
            "line_count": len(self.lines),
            "x_start": self.x_start,
            "x_end": self.x_end,
            "y_start": self.y_start,
            "y_end": self.y_end,
            "lines": [line.to_dict() for line in self.lines],
        }


class TextGrouper:
    """
    Groups individual text elements into lines and blocks.
    
    PDF content streams often split text into small fragments (even
    individual characters). This class groups them back into readable
    text based on spatial proximity.
    
    Two grouping algorithms are available:
    
    1. **Tolerance mode** (default): Groups by quantizing Y coordinates
       - Fast and simple
       - May misorder characters with slightly different Y values
       
    2. **Cluster mode**: Uses nearest-neighbor clustering
       - More accurate for variable character positioning
       - Better handles sub-pixel Y variations
    
    Example:
        grouper = TextGrouper(
            elements,
            grouping_mode="cluster",
            y_tolerance=5.0,
        )
        lines = grouper.group_into_lines()
        blocks = grouper.group_into_blocks()
    """
    
    def __init__(
        self,
        elements: List,
        y_tolerance: float = 5.0,
        x_tolerance: float = 5.0,
        space_width: float = 3.0,
        line_gap_threshold: float = 1.5,
        grouping_mode: str = "cluster",
    ):
        """
        Initialize the text grouper.
        
        Args:
            elements: List of TextElement objects from content stream parser
            y_tolerance: Vertical tolerance for grouping into lines (points)
            x_tolerance: Horizontal tolerance for merging fragments (points)
            space_width: Minimum gap to insert a space between fragments
            line_gap_threshold: Multiplier of avg line height to detect paragraph breaks
            grouping_mode: "tolerance" (quantization) or "cluster" (nearest-neighbor)
        """
        self.elements = elements
        self.y_tolerance = y_tolerance
        self.x_tolerance = x_tolerance
        self.space_width = space_width
        self.line_gap_threshold = line_gap_threshold
        
        # Parse grouping mode
        if isinstance(grouping_mode, str):
            grouping_mode = GroupingMode(grouping_mode.lower())
        self.grouping_mode = grouping_mode
        
    def group_into_lines(self) -> List[TextLine]:
        """
        Group text elements into lines based on Y coordinate.
        
        Uses the configured grouping mode (tolerance or cluster).
        
        Returns:
            List of TextLine objects, sorted from top to bottom
        """
        if not self.elements:
            return []
        
        if self.grouping_mode == GroupingMode.CLUSTER:
            return self._group_lines_cluster()
        else:
            return self._group_lines_tolerance()
    
    def _group_lines_tolerance(self) -> List[TextLine]:
        """
        Group lines using Y quantization (bucket approach).
        
        Elements are grouped by rounding their Y coordinate to the
        nearest tolerance value.
        """
        # Group by Y coordinate (with tolerance)
        y_groups: dict[int, List] = {}
        
        for elem in self.elements:
            # Quantize Y to group nearby elements
            y_key = round(elem.y / self.y_tolerance) * self.y_tolerance
            
            if y_key not in y_groups:
                y_groups[y_key] = []
            y_groups[y_key].append(elem)
        
        # Process each group into a line
        lines = []
        
        for y_key in sorted(y_groups.keys(), reverse=True):  # Top to bottom
            group = y_groups[y_key]
            line = self._create_line_from_group(group, y_key)
            lines.append(line)
        
        return lines
    
    def _group_lines_cluster(self) -> List[TextLine]:
        """
        Group lines using nearest-neighbor clustering.
        
        Elements are clustered if their Y values are within tolerance
        of any element already in the cluster. This handles cases where
        characters on the same line have slightly different Y values.
        """
        # Sort elements by Y (descending, top to bottom)
        sorted_elems = sorted(self.elements, key=lambda e: (-e.y, e.x))
        
        # Build clusters using nearest-neighbor approach
        clusters: List[List] = []
        cluster_y_values: List[float] = []  # Representative Y for each cluster
        
        for elem in sorted_elems:
            # Find a cluster this element belongs to
            found_cluster = False
            
            for i, cluster_y in enumerate(cluster_y_values):
                # Check if element Y is within tolerance of cluster Y
                if abs(elem.y - cluster_y) <= self.y_tolerance:
                    clusters[i].append(elem)
                    # Update cluster Y to be average of all elements
                    cluster_y_values[i] = sum(e.y for e in clusters[i]) / len(clusters[i])
                    found_cluster = True
                    break
            
            if not found_cluster:
                # Start a new cluster
                clusters.append([elem])
                cluster_y_values.append(elem.y)
        
        # Process each cluster into a line
        lines = []
        
        # Sort clusters by Y (descending, top to bottom)
        cluster_pairs = sorted(zip(cluster_y_values, clusters), key=lambda p: -p[0])
        
        for cluster_y, cluster in cluster_pairs:
            line = self._create_line_from_group(cluster, cluster_y)
            lines.append(line)
        
        return lines
    
    def _create_line_from_group(self, group: List, y_coord: float) -> TextLine:
        """
        Create a TextLine from a group of elements.
        
        Args:
            group: List of TextElement objects on the same line
            y_coord: Y coordinate for the line
            
        Returns:
            TextLine object with merged text
        """
        # Sort by X coordinate (left to right)
        sorted_elems = sorted(group, key=lambda e: e.x)
        
        # Merge fragments into text
        fragments = []
        text_parts = []
        prev_x_end = None
        
        for elem in sorted_elems:
            elem_dict = {
                "text": elem.text,
                "x": elem.x,
                "y": elem.y,
                "width": elem.width,
                "height": elem.height,
            }
            fragments.append(elem_dict)
            
            # Check if we need to add space
            if prev_x_end is not None:
                gap = elem.x - prev_x_end
                if gap > self.space_width:
                    text_parts.append(" ")
                elif gap < -self.x_tolerance:
                    # Overlapping or very close - might be kerning
                    pass
            
            text_parts.append(elem.text)
            prev_x_end = elem.x + elem.width
        
        return TextLine(
            text="".join(text_parts),
            y=y_coord,
            x_start=min(e.x for e in group),
            x_end=max(e.x + e.width for e in group),
            fragments=fragments,
        )
    
    def group_into_blocks(self) -> List[TextBlock]:
        """
        Group lines into blocks (paragraphs/columns) based on spacing.
        
        Returns:
            List of TextBlock objects
        """
        lines = self.group_into_lines()
        
        if not lines:
            return []
        
        blocks = []
        current_block = TextBlock()
        prev_y = None
        avg_line_height = None
        
        for line in lines:
            if prev_y is not None:
                gap = prev_y - line.y  # Positive since we go top to bottom
                
                # Calculate running average line height
                if avg_line_height is None:
                    avg_line_height = gap
                else:
                    avg_line_height = 0.9 * avg_line_height + 0.1 * gap
                
                # Check if this is a paragraph break
                if gap > avg_line_height * self.line_gap_threshold:
                    # Start a new block
                    if current_block.lines:
                        blocks.append(current_block)
                    current_block = TextBlock()
            
            # Add line to current block
            current_block.lines.append(line)
            
            # Update block bounds
            if not current_block.lines or len(current_block.lines) == 1:
                current_block.y_start = line.y
            current_block.y_end = line.y
            current_block.x_start = min(current_block.x_start, line.x_start) if current_block.x_start else line.x_start
            current_block.x_end = max(current_block.x_end, line.x_end) if current_block.x_end else line.x_end
            
            prev_y = line.y
        
        # Don't forget the last block
        if current_block.lines:
            blocks.append(current_block)
        
        return blocks
    
    def get_plain_text(self, line_separator: str = "\n", block_separator: str = "\n\n") -> str:
        """
        Get all text as a plain string.
        
        Args:
            line_separator: String to join lines within a block
            block_separator: String to separate blocks
            
        Returns:
            Plain text string
        """
        blocks = self.group_into_blocks()
        texts = []
        
        for block in blocks:
            block_text = line_separator.join(line.text for line in block.lines)
            texts.append(block_text)
        
        return block_separator.join(texts)


def group_text_elements(
    elements: List,
    y_tolerance: float = 5.0,
    x_tolerance: float = 5.0,
    grouping_mode: str = "cluster",
) -> List[TextLine]:
    """
    Convenience function to group text elements into lines.
    
    Args:
        elements: List of TextElement objects
        y_tolerance: Vertical tolerance for line grouping
        x_tolerance: Horizontal tolerance for fragment merging
        grouping_mode: "tolerance" or "cluster"
        
    Returns:
        List of TextLine objects
    """
    grouper = TextGrouper(
        elements,
        y_tolerance=y_tolerance,
        x_tolerance=x_tolerance,
        grouping_mode=grouping_mode,
    )
    return grouper.group_into_lines()