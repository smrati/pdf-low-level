"""
High-level PDF Text Extraction.

This module provides the main API for extracting text from PDFs
with position information and layout analysis.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

from pdf_lowlevel.content.stream import ContentStreamParser, TextElement
from pdf_lowlevel.content.grouper import TextGrouper, TextLine, TextBlock, GroupingMode
from pdf_lowlevel.logger import logger
from pdf_lowlevel.parser.objects import PDFIndirectRef, PDFName, PDFStream
from pdf_lowlevel.parser.reader import PDFReader, open_pdf


# Default grouping configuration
DEFAULT_Y_TOLERANCE = 5.0
DEFAULT_X_TOLERANCE = 5.0
DEFAULT_SPACE_WIDTH = 3.0
DEFAULT_GROUPING_MODE = "cluster"


@dataclass
class GroupingConfig:
    """
    Configuration for text grouping behavior.
    
    Attributes:
        y_tolerance: Vertical tolerance for grouping into lines (points)
        x_tolerance: Horizontal tolerance for merging fragments (points)
        space_width: Minimum gap to insert a space between fragments
        line_gap_threshold: Multiplier of avg line height to detect paragraph breaks
        grouping_mode: "tolerance" (quantization) or "cluster" (nearest-neighbor)
    """
    y_tolerance: float = DEFAULT_Y_TOLERANCE
    x_tolerance: float = DEFAULT_X_TOLERANCE
    space_width: float = DEFAULT_SPACE_WIDTH
    line_gap_threshold: float = 1.5
    grouping_mode: str = DEFAULT_GROUPING_MODE
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "y_tolerance": self.y_tolerance,
            "x_tolerance": self.x_tolerance,
            "space_width": self.space_width,
            "line_gap_threshold": self.line_gap_threshold,
            "grouping_mode": self.grouping_mode,
        }


@dataclass
class PageResult:
    """Result of extracting text from a single page."""

    page_number: int
    width: float
    height: float
    elements: List[TextElement] = field(default_factory=list)
    lines: List[TextLine] = field(default_factory=list)
    blocks: List[TextBlock] = field(default_factory=list)
    
    # Grouping configuration
    _grouping_config: GroupingConfig = field(
        default_factory=GroupingConfig,
        repr=False,
        compare=False,
    )

    def _ensure_grouped(self) -> None:
        """Ensure lines and blocks are computed."""
        if not self.lines and self.elements:
            grouper = TextGrouper(
                self.elements,
                y_tolerance=self._grouping_config.y_tolerance,
                x_tolerance=self._grouping_config.x_tolerance,
                space_width=self._grouping_config.space_width,
                line_gap_threshold=self._grouping_config.line_gap_threshold,
                grouping_mode=self._grouping_config.grouping_mode,
            )
            self.lines = grouper.group_into_lines()
            self.blocks = grouper.group_into_blocks()

    def get_text(self) -> str:
        """Get page text as a string (lines joined by newline)."""
        self._ensure_grouped()
        return "\n".join(line.text for line in self.lines)

    def get_text_with_blocks(self) -> str:
        """Get page text with paragraph separation."""
        self._ensure_grouped()
        return "\n\n".join(block.text for block in self.blocks)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        self._ensure_grouped()
        return {
            "page_number": self.page_number,
            "width": self.width,
            "height": self.height,
            "text": self.get_text(),
            "elements": [e.to_dict() for e in self.elements],
            "lines": [line.to_dict() for line in self.lines],
            "blocks": [block.to_dict() for block in self.blocks],
        }


@dataclass
class ExtractionResult:
    """Result of extracting text from a PDF."""

    filename: str = ""
    page_count: int = 0
    pages: List[PageResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    grouping_config: GroupingConfig = field(default_factory=GroupingConfig)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "filename": self.filename,
            "page_count": self.page_count,
            "pages": [p.to_dict() for p in self.pages],
            "metadata": self.metadata,
            "grouping_config": self.grouping_config.to_dict(),
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def get_all_text(self) -> str:
        """Get all text as a single string (uses grouped lines)."""
        texts = []
        for page in self.pages:
            texts.append(page.get_text())
        return "\n\n".join(texts)


class PDFExtractor:
    """
    High-level PDF text extractor.

    Provides methods to extract text with positions from PDF files.
    Supports font encoding, layout analysis, and multiple output formats.

    Text Grouping:
        Two algorithms are available for grouping text into lines:
        
        - "cluster" (default): Uses nearest-neighbor clustering. More accurate
          for documents with variable character positioning (sub-pixel Y variations).
        
        - "tolerance": Uses Y quantization (bucket approach). Faster but may
          misorder characters with slightly different Y values.

    Example:
        # Basic usage with defaults
        extractor = PDFExtractor("document.pdf")
        result = extractor.extract()
        print(result.to_json())
        
        # With custom grouping settings
        result = extractor.extract(
            grouping_mode="cluster",
            y_tolerance=5.0,
            x_tolerance=5.0,
        )
    """

    def __init__(self, source: Union[str, Path, BinaryIO, bytes]):
        """
        Initialize the extractor.

        Args:
            source: PDF source - file path, file-like object, or bytes
        """
        self.source = source
        self._reader: Optional[PDFReader] = None
        self._fonts: Dict[str, Any] = {}
        self._grouping_config: GroupingConfig = GroupingConfig()
        logger.debug(f"Initialized PDFExtractor with source type: {type(source).__name__}")

    def _ensure_reader(self) -> PDFReader:
        """Ensure the PDF reader is initialized."""
        if self._reader is None:
            self._reader = open_pdf(self.source)
        return self._reader

    def extract(
        self,
        start_page: int = 0,
        end_page: Optional[int] = None,
        include_metadata: bool = True,
        *,
        # Grouping parameters
        grouping_mode: str = DEFAULT_GROUPING_MODE,
        y_tolerance: float = DEFAULT_Y_TOLERANCE,
        x_tolerance: float = DEFAULT_X_TOLERANCE,
        space_width: float = DEFAULT_SPACE_WIDTH,
        line_gap_threshold: float = 1.5,
    ) -> ExtractionResult:
        """
        Extract text from the PDF.

        Args:
            start_page: First page to extract (0-indexed)
            end_page: Last page to extract (exclusive). None = all pages
            include_metadata: Whether to include document metadata
            
            grouping_mode: Algorithm for grouping text into lines.
                "cluster" (default) - nearest-neighbor clustering, more accurate
                "tolerance" - Y quantization, faster but may misorder chars
            y_tolerance: Vertical tolerance for grouping into lines (points).
                Larger values group more aggressively.
            x_tolerance: Horizontal tolerance for merging fragments (points)
            space_width: Minimum gap to insert a space between fragments (points)
            line_gap_threshold: Multiplier of avg line height to detect paragraph breaks

        Returns:
            ExtractionResult with text elements and metadata
        """
        reader = self._ensure_reader()

        # Store grouping config
        self._grouping_config = GroupingConfig(
            y_tolerance=y_tolerance,
            x_tolerance=x_tolerance,
            space_width=space_width,
            line_gap_threshold=line_gap_threshold,
            grouping_mode=grouping_mode,
        )

        result = ExtractionResult(grouping_config=self._grouping_config)

        # Get filename
        if isinstance(self.source, (str, Path)):
            result.filename = str(Path(self.source).name)

        result.page_count = reader.page_count
        logger.info(f"Extracting from '{result.filename}' ({reader.page_count} pages)")
        logger.debug(f"Grouping config: mode={grouping_mode}, y_tol={y_tolerance}, x_tol={x_tolerance}")

        # Set page range
        if end_page is None:
            end_page = reader.page_count
        end_page = min(end_page, reader.page_count)

        # Load fonts from first page resources
        logger.debug("Loading fonts from page resources")
        self._load_fonts(0)

        # Extract each page
        for page_num in range(start_page, end_page):
            logger.debug(f"Extracting page {page_num + 1}")
            page_result = self._extract_page(page_num)
            result.pages.append(page_result)
            logger.debug(f"Page {page_num + 1}: {len(page_result.elements)} text elements")

        # Add metadata
        if include_metadata:
            result.metadata = self._get_metadata()

        logger.info(f"Extraction complete: {sum(len(p.elements) for p in result.pages)} total elements")
        return result

    def _extract_page(self, page_num: int) -> PageResult:
        """
        Extract text from a single page.

        Args:
            page_num: Page number (0-indexed)

        Returns:
            PageResult with text elements
        """
        reader = self._ensure_reader()

        # Get page dimensions
        media_box = reader.get_page_media_box(page_num)
        width = media_box[2] - media_box[0] if media_box else 612
        height = media_box[3] - media_box[1] if media_box else 792

        page_result = PageResult(
            page_number=page_num + 1,  # 1-indexed for output
            width=width,
            height=height,
            _grouping_config=self._grouping_config,
        )

        # Get content stream
        content = reader.get_page_contents(page_num)
        if content is None:
            return page_result

        # Parse content stream
        parser = ContentStreamParser(content)
        parser.font_resolver = self._resolve_font
        elements = parser.parse()

        # Set page number on elements
        for element in elements:
            element.page_number = page_num + 1

        page_result.elements = elements

        return page_result

    def _load_fonts(self, page_num: int) -> None:
        """Load font information from page resources."""
        reader = self._ensure_reader()
        resources = reader.get_page_resources(page_num)

        if resources is None:
            return

        fonts = resources.get("Font", {})
        if isinstance(fonts, dict):
            for font_name, font_ref in fonts.items():
                if isinstance(font_ref, PDFIndirectRef):
                    font_obj = reader.get_object(font_ref.object_number, font_ref.generation_number)
                    if font_obj:
                        self._fonts[font_name] = font_obj

    def _resolve_font(self, font_name: str) -> Optional[Dict[str, Any]]:
        """
        Resolve font information for the content stream parser.

        Args:
            font_name: Name of the font in the resource dictionary

        Returns:
            Font information dictionary or None
        """
        if font_name not in self._fonts:
            return None

        font_obj = self._fonts[font_name]
        if not isinstance(font_obj, dict):
            return None

        result = {}

        # Get widths
        widths = self._get_font_widths(font_obj)
        if widths:
            result["widths"] = widths

        return result

    def _get_font_widths(self, font_obj: Dict) -> Dict[int, float]:
        """Extract character widths from font object."""
        widths = {}

        # Check for Widths array
        if "Widths" in font_obj:
            widths_array = font_obj["Widths"]
            first_char = font_obj.get("FirstChar", 0)

            if isinstance(widths_array, list):
                for i, w in enumerate(widths_array):
                    char_code = first_char + i
                    if isinstance(w, (int, float)):
                        widths[char_code] = float(w)

        return widths

    def _get_metadata(self) -> Dict[str, Any]:
        """Get document metadata."""
        metadata = {}

        if self._reader is None:
            return metadata

        # Get from trailer
        xref = self._reader._xref_table
        if xref:
            info_ref = xref.get_info_ref()
            if info_ref:
                info = self._reader.get_object(info_ref[0], info_ref[1])
                if info and isinstance(info, dict):
                    for key, value in info.items():
                        if isinstance(value, bytes):
                            try:
                                metadata[key] = value.decode("utf-8")
                            except UnicodeDecodeError:
                                metadata[key] = value.decode("latin-1")
                        elif isinstance(value, str):
                            metadata[key] = value
                        else:
                            metadata[key] = str(value)

        return metadata

    def close(self) -> None:
        """Close the PDF reader."""
        if self._reader:
            self._reader.close()
            self._reader = None

    def __enter__(self) -> "PDFExtractor":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()


def extract_text(
    source: Union[str, Path, BinaryIO, bytes],
    *,
    grouping_mode: str = DEFAULT_GROUPING_MODE,
    y_tolerance: float = DEFAULT_Y_TOLERANCE,
) -> str:
    """
    Extract plain text from a PDF.

    Args:
        source: PDF source
        grouping_mode: "cluster" (default) or "tolerance"
        y_tolerance: Vertical tolerance for line grouping

    Returns:
        Plain text string
    """
    with PDFExtractor(source) as extractor:
        result = extractor.extract(
            grouping_mode=grouping_mode,
            y_tolerance=y_tolerance,
        )
        return result.get_all_text()


def extract_json(
    source: Union[str, Path, BinaryIO, bytes],
    start_page: int = 0,
    end_page: Optional[int] = None,
    *,
    grouping_mode: str = DEFAULT_GROUPING_MODE,
    y_tolerance: float = DEFAULT_Y_TOLERANCE,
) -> str:
    """
    Extract text from a PDF as JSON.

    Args:
        source: PDF source
        start_page: First page to extract
        end_page: Last page to extract
        grouping_mode: "cluster" (default) or "tolerance"
        y_tolerance: Vertical tolerance for line grouping

    Returns:
        JSON string with extraction results
    """
    with PDFExtractor(source) as extractor:
        result = extractor.extract(
            start_page=start_page,
            end_page=end_page,
            grouping_mode=grouping_mode,
            y_tolerance=y_tolerance,
        )
        return result.to_json()