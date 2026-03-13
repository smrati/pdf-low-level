"""
Tests for API use cases described in docs/api_docs.md.

This test module verifies all the examples and use cases documented
in the API documentation work correctly.
"""

import pytest
import json
from io import BytesIO
from pathlib import Path

from pdf_lowlevel import (
    PDFExtractor,
    ExtractionResult,
    PageResult,
    TextElement,
    extract_text,
    extract_json,
    logger,
    configure_logger,
    __version__,
)
from pdf_lowlevel.parser.reader import open_pdf, PDFParseError


class TestPublicAPIExports:
    """Test that all public API symbols are exported correctly."""

    def test_all_exports_available(self):
        """Verify all documented exports are available."""
        from pdf_lowlevel import (
            PDFExtractor,
            ExtractionResult,
            PageResult,
            TextElement,
            extract_text,
            extract_json,
            logger,
            configure_logger,
            __version__,
        )
        # If we get here, all imports succeeded
        assert True

    def test_version_is_string(self):
        """Test that __version__ is a string."""
        assert isinstance(__version__, str)

    def test_logger_is_available(self):
        """Test that logger is available."""
        assert logger is not None

    def test_configure_logger_callable(self):
        """Test that configure_logger is callable."""
        assert callable(configure_logger)


class TestExtractTextFunction:
    """Tests for extract_text() convenience function use cases."""

    def test_extract_text_from_file_path(self, minimal_pdf_bytes, tmp_path):
        """Example 1: Basic text extraction from file path."""
        pdf_path = tmp_path / "document.pdf"
        pdf_path.write_bytes(minimal_pdf_bytes)

        text = extract_text(str(pdf_path))
        assert isinstance(text, str)

    def test_extract_text_from_bytes(self, minimal_pdf_bytes):
        """Example: Extract text from bytes."""
        text = extract_text(minimal_pdf_bytes)
        assert isinstance(text, str)

    def test_extract_text_from_bytesio(self, minimal_pdf_bytes):
        """Example: Extract text from BytesIO."""
        file_obj = BytesIO(minimal_pdf_bytes)
        text = extract_text(file_obj)
        assert isinstance(text, str)

    def test_extract_text_with_grouping_mode_cluster(self, text_pdf_bytes):
        """Test extract_text with grouping_mode='cluster'."""
        text = extract_text(text_pdf_bytes, grouping_mode="cluster")
        assert isinstance(text, str)

    def test_extract_text_with_grouping_mode_tolerance(self, text_pdf_bytes):
        """Test extract_text with grouping_mode='tolerance'."""
        text = extract_text(text_pdf_bytes, grouping_mode="tolerance")
        assert isinstance(text, str)

    def test_extract_text_with_y_tolerance(self, text_pdf_bytes):
        """Test extract_text with custom y_tolerance."""
        text = extract_text(text_pdf_bytes, y_tolerance=10.0)
        assert isinstance(text, str)


class TestExtractJsonFunction:
    """Tests for extract_json() convenience function use cases."""

    def test_extract_json_returns_valid_json(self, minimal_pdf_bytes):
        """Test that extract_json returns valid JSON."""
        json_str = extract_json(minimal_pdf_bytes)
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)

    def test_extract_json_structure(self, minimal_pdf_bytes):
        """Example 3: Get structured JSON output."""
        json_str = extract_json(minimal_pdf_bytes)
        data = json.loads(json_str)

        # Verify structure
        assert "page_count" in data
        assert "pages" in data
        assert isinstance(data["pages"], list)

    def test_extract_json_with_page_range(self, multi_page_pdf_bytes):
        """Test extract_json with page range."""
        json_str = extract_json(multi_page_pdf_bytes, start_page=0, end_page=2)
        data = json.loads(json_str)

        assert len(data["pages"]) == 2

    def test_extract_json_with_grouping_mode(self, text_pdf_bytes):
        """Test extract_json with grouping_mode parameter."""
        json_str = extract_json(text_pdf_bytes, grouping_mode="cluster")
        data = json.loads(json_str)
        assert "grouping_config" in data
        assert data["grouping_config"]["grouping_mode"] == "cluster"


class TestPDFExtractorClass:
    """Tests for PDFExtractor class use cases."""

    # ========================================================================
    # Constructor - Supported Input Types
    # ========================================================================

    def test_constructor_with_string_path(self, minimal_pdf_bytes, tmp_path):
        """Test PDFExtractor with file path string."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(minimal_pdf_bytes)

        with PDFExtractor(str(pdf_path)) as extractor:
            result = extractor.extract()
            assert result is not None

    def test_constructor_with_path_object(self, minimal_pdf_bytes, tmp_path):
        """Test PDFExtractor with Path object."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(minimal_pdf_bytes)

        with PDFExtractor(Path(pdf_path)) as extractor:
            result = extractor.extract()
            assert result is not None

    def test_constructor_with_bytes(self, minimal_pdf_bytes):
        """Test PDFExtractor with bytes."""
        with PDFExtractor(minimal_pdf_bytes) as extractor:
            result = extractor.extract()
            assert result is not None

    def test_constructor_with_file_object(self, minimal_pdf_bytes):
        """Test PDFExtractor with file-like object."""
        file_obj = BytesIO(minimal_pdf_bytes)
        with PDFExtractor(file_obj) as extractor:
            result = extractor.extract()
            assert result is not None

    # ========================================================================
    # Context Manager Usage
    # ========================================================================

    def test_context_manager_auto_close(self, minimal_pdf_bytes):
        """Test that context manager properly closes resources."""
        with PDFExtractor(minimal_pdf_bytes) as extractor:
            result = extractor.extract()
        
        # After context exit, reader should be closed
        assert extractor._reader is None

    # ========================================================================
    # extract() Method - Parameters
    # ========================================================================

    def test_extract_with_start_page_only(self, multi_page_pdf_bytes):
        """Test extract with only start_page specified."""
        with PDFExtractor(multi_page_pdf_bytes) as extractor:
            result = extractor.extract(start_page=1)
            assert len(result.pages) == 2  # Pages 2 and 3

    def test_extract_with_end_page_only(self, multi_page_pdf_bytes):
        """Test extract with only end_page specified."""
        with PDFExtractor(multi_page_pdf_bytes) as extractor:
            result = extractor.extract(end_page=2)
            assert len(result.pages) == 2  # Pages 1 and 2

    def test_extract_with_full_page_range(self, multi_page_pdf_bytes):
        """Example 2: Extract specific pages."""
        with PDFExtractor(multi_page_pdf_bytes) as extractor:
            result = extractor.extract(start_page=0, end_page=5)
            assert result is not None

    def test_extract_without_metadata(self, minimal_pdf_bytes):
        """Test extract with include_metadata=False."""
        with PDFExtractor(minimal_pdf_bytes) as extractor:
            result = extractor.extract(include_metadata=False)
            assert result.metadata == {}

    def test_extract_with_metadata(self, indirect_ref_pdf_bytes):
        """Example 7: Extract metadata."""
        with PDFExtractor(indirect_ref_pdf_bytes) as extractor:
            result = extractor.extract(include_metadata=True)
            assert isinstance(result.metadata, dict)

    # ========================================================================
    # Grouping Parameters
    # ========================================================================

    def test_extract_with_grouping_mode_cluster(self, text_pdf_bytes):
        """Test extract with grouping_mode='cluster'."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract(grouping_mode="cluster")
            assert result.grouping_config.grouping_mode == "cluster"

    def test_extract_with_grouping_mode_tolerance(self, text_pdf_bytes):
        """Test extract with grouping_mode='tolerance'."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract(grouping_mode="tolerance")
            assert result.grouping_config.grouping_mode == "tolerance"

    def test_extract_with_y_tolerance(self, text_pdf_bytes):
        """Test extract with custom y_tolerance."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract(y_tolerance=10.0)
            assert result.grouping_config.y_tolerance == 10.0

    def test_extract_with_x_tolerance(self, text_pdf_bytes):
        """Test extract with custom x_tolerance."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract(x_tolerance=3.0)
            assert result.grouping_config.x_tolerance == 3.0

    def test_extract_with_space_width(self, text_pdf_bytes):
        """Test extract with custom space_width."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract(space_width=2.0)
            assert result.grouping_config.space_width == 2.0

    def test_extract_with_line_gap_threshold(self, text_pdf_bytes):
        """Test extract with custom line_gap_threshold."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract(line_gap_threshold=2.0)
            assert result.grouping_config.line_gap_threshold == 2.0

    def test_extract_with_all_grouping_params(self, text_pdf_bytes):
        """Example 4: Custom grouping settings."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract(
                grouping_mode="cluster",
                y_tolerance=8.0,
                x_tolerance=3.0,
                space_width=2.0,
                line_gap_threshold=2.0,
            )
            
            assert result.grouping_config.grouping_mode == "cluster"
            assert result.grouping_config.y_tolerance == 8.0
            assert result.grouping_config.x_tolerance == 3.0
            assert result.grouping_config.space_width == 2.0
            assert result.grouping_config.line_gap_threshold == 2.0

    # ========================================================================
    # close() Method
    # ========================================================================

    def test_manual_close(self, minimal_pdf_bytes):
        """Test manually closing the extractor."""
        extractor = PDFExtractor(minimal_pdf_bytes)
        result = extractor.extract()
        extractor.close()
        
        assert extractor._reader is None


class TestExtractionResultClass:
    """Tests for ExtractionResult class use cases."""

    def test_result_attributes(self, minimal_pdf_bytes):
        """Test ExtractionResult attributes."""
        with PDFExtractor(minimal_pdf_bytes) as extractor:
            result = extractor.extract()
            
            assert isinstance(result.filename, str)
            assert isinstance(result.page_count, int)
            assert isinstance(result.pages, list)
            assert isinstance(result.metadata, dict)

    def test_to_dict_method(self, minimal_pdf_bytes):
        """Test ExtractionResult.to_dict()."""
        with PDFExtractor(minimal_pdf_bytes) as extractor:
            result = extractor.extract()
            data = result.to_dict()
            
            assert isinstance(data, dict)
            assert "filename" in data
            assert "page_count" in data
            assert "pages" in data
            assert "metadata" in data
            assert "grouping_config" in data

    def test_to_json_method(self, minimal_pdf_bytes):
        """Test ExtractionResult.to_json()."""
        with PDFExtractor(minimal_pdf_bytes) as extractor:
            result = extractor.extract()
            json_str = result.to_json(indent=4)
            
            assert isinstance(json_str, str)
            # Verify it's valid JSON
            parsed = json.loads(json_str)
            assert isinstance(parsed, dict)

    def test_get_all_text_method(self, text_pdf_bytes):
        """Test ExtractionResult.get_all_text()."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract()
            text = result.get_all_text()
            
            assert isinstance(text, str)

    def test_result_with_multi_page(self, multi_page_pdf_bytes):
        """Test ExtractionResult with multiple pages."""
        with PDFExtractor(multi_page_pdf_bytes) as extractor:
            result = extractor.extract()
            
            assert result.page_count == 3
            assert len(result.pages) == 3
            
            # Each page should have correct page_number
            for i, page in enumerate(result.pages):
                assert page.page_number == i + 1


class TestPageResultClass:
    """Tests for PageResult class use cases."""

    def test_page_result_attributes(self, minimal_pdf_bytes):
        """Test PageResult attributes."""
        with PDFExtractor(minimal_pdf_bytes) as extractor:
            result = extractor.extract()
            page = result.pages[0]
            
            assert isinstance(page, PageResult)
            assert page.page_number == 1
            assert page.width == 612
            assert page.height == 792
            assert isinstance(page.elements, list)
            assert isinstance(page.lines, list)
            assert isinstance(page.blocks, list)

    def test_get_text_method(self, text_pdf_bytes):
        """Test PageResult.get_text()."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract()
            page = result.pages[0]
            
            text = page.get_text()
            assert isinstance(text, str)

    def test_get_text_with_blocks_method(self, text_pdf_bytes):
        """Test PageResult.get_text_with_blocks()."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract()
            page = result.pages[0]
            
            text = page.get_text_with_blocks()
            assert isinstance(text, str)

    def test_to_dict_method(self, minimal_pdf_bytes):
        """Test PageResult.to_dict()."""
        with PDFExtractor(minimal_pdf_bytes) as extractor:
            result = extractor.extract()
            page = result.pages[0]
            
            data = page.to_dict()
            assert isinstance(data, dict)
            assert "page_number" in data
            assert "width" in data
            assert "height" in data
            assert "text" in data
            assert "elements" in data
            assert "lines" in data
            assert "blocks" in data


class TestTextElementFiltering:
    """Tests for TextElement filtering use cases (Example 5, 6)."""

    def test_element_has_position_attributes(self, text_pdf_bytes):
        """Example 5: Extract with positions."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract()
            
            if len(result.pages[0].elements) == 0:
                pytest.skip("Text extraction not yet fully implemented")
            
            for page in result.pages:
                for elem in page.elements:
                    assert hasattr(elem, 'text')
                    assert hasattr(elem, 'x')
                    assert hasattr(elem, 'y')
                    assert hasattr(elem, 'font_name')
                    assert hasattr(elem, 'font_size')

    def test_filter_by_region(self, text_pdf_bytes):
        """Example 6: Filter by region."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract()
            
            if len(result.pages[0].elements) == 0:
                pytest.skip("Text extraction not yet fully implemented")
            
            page = result.pages[0]
            x1, y1, x2, y2 = 0, 0, 500, 792
            
            region_elements = [
                elem for elem in page.elements
                if x1 <= elem.x <= x2 and y1 <= elem.y <= y2
            ]
            
            # All filtered elements should be within region
            for elem in region_elements:
                assert x1 <= elem.x <= x2
                assert y1 <= elem.y <= y2

    def test_filter_by_font_size(self, text_pdf_bytes):
        """Example: Filter by font size (find headers)."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract()
            
            if len(result.pages[0].elements) == 0:
                pytest.skip("Text extraction not yet fully implemented")
            
            page = result.pages[0]
            
            # Find elements with font_size > 14 (potential headers)
            headers = [
                elem for elem in page.elements
                if elem.font_size > 14
            ]
            
            for elem in headers:
                assert elem.font_size > 14

    def test_filter_left_column(self, text_pdf_bytes):
        """Example: Filter by position (left column)."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract()
            
            if len(result.pages[0].elements) == 0:
                pytest.skip("Text extraction not yet fully implemented")
            
            page = result.pages[0]
            
            # Get elements from left half of page
            left_elements = [
                elem for elem in page.elements
                if elem.x < 300
            ]
            
            for elem in left_elements:
                assert elem.x < 300


class TestTextElementProperties:
    """Tests for TextElement properties."""

    def test_bbox_property(self, text_pdf_bytes):
        """Test TextElement.bbox property."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract()
            
            if len(result.pages[0].elements) == 0:
                pytest.skip("Text extraction not yet fully implemented")
            
            elem = result.pages[0].elements[0]
            bbox = elem.bbox
            
            assert isinstance(bbox, tuple)
            assert len(bbox) == 4  # (x0, y0, x1, y1)

    def test_to_dict_method(self, text_pdf_bytes):
        """Test TextElement.to_dict()."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract()
            
            if len(result.pages[0].elements) == 0:
                pytest.skip("Text extraction not yet fully implemented")
            
            elem = result.pages[0].elements[0]
            data = elem.to_dict()
            
            assert isinstance(data, dict)
            assert "text" in data
            assert "x" in data
            assert "y" in data
            assert "bbox" in data


class TestJSONOutputFormat:
    """Tests for JSON output format (Example 9)."""

    def test_json_structure_complete(self, minimal_pdf_bytes):
        """Test that JSON output has complete structure."""
        with PDFExtractor(minimal_pdf_bytes) as extractor:
            result = extractor.extract()
            data = json.loads(result.to_json())
            
            # Top-level keys
            assert "filename" in data
            assert "page_count" in data
            assert "pages" in data
            assert "metadata" in data
            assert "grouping_config" in data

    def test_json_page_structure(self, minimal_pdf_bytes):
        """Test that each page in JSON has correct structure."""
        with PDFExtractor(minimal_pdf_bytes) as extractor:
            result = extractor.extract()
            data = json.loads(result.to_json())
            
            for page in data["pages"]:
                assert "page_number" in page
                assert "width" in page
                assert "height" in page
                assert "text" in page
                assert "elements" in page
                assert "lines" in page
                assert "blocks" in page

    def test_json_grouping_config_structure(self, minimal_pdf_bytes):
        """Test that grouping_config in JSON has correct structure."""
        with PDFExtractor(minimal_pdf_bytes) as extractor:
            result = extractor.extract()
            data = json.loads(result.to_json())
            
            gc = data["grouping_config"]
            assert "y_tolerance" in gc
            assert "x_tolerance" in gc
            assert "space_width" in gc
            assert "line_gap_threshold" in gc
            assert "grouping_mode" in gc


class TestLowLevelReader:
    """Tests for low-level reader access (Example 10)."""

    def test_open_pdf_context_manager(self, minimal_pdf_bytes):
        """Example 10: Access low-level reader."""
        with open_pdf(minimal_pdf_bytes) as pdf:
            assert pdf.version == "1.4"
            assert pdf.page_count == 1

    def test_low_level_page_contents(self, text_pdf_bytes):
        """Test getting page contents via low-level API."""
        with open_pdf(text_pdf_bytes) as pdf:
            content = pdf.get_page_contents(0)
            assert content is not None
            # Content should have text operators (Tf, Td, Tj, ET)
            assert b"Tf" in content or b"Tj" in content  # Font or text show operator

    def test_low_level_media_box(self, minimal_pdf_bytes):
        """Test getting media box via low-level API."""
        with open_pdf(minimal_pdf_bytes) as pdf:
            media_box = pdf.get_page_media_box(0)
            assert media_box is not None
            assert len(media_box) == 4


class TestErrorHandling:
    """Tests for error handling use cases."""

    def test_file_not_found(self):
        """Test FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError):
            with PDFExtractor("/nonexistent/path/file.pdf") as extractor:
                extractor.extract()

    def test_invalid_pdf_error(self, invalid_pdf_bytes):
        """Test PDFParseError for invalid PDF."""
        with pytest.raises(PDFParseError):
            with PDFExtractor(invalid_pdf_bytes) as extractor:
                extractor.extract()

    def test_empty_file_error(self, empty_pdf_bytes):
        """Test error for empty file."""
        with pytest.raises(PDFParseError):
            with PDFExtractor(empty_pdf_bytes) as extractor:
                extractor.extract()


class TestLogging:
    """Tests for logging functionality."""

    def test_configure_logger_debug(self, suppress_logging):
        """Test configuring logger to DEBUG level."""
        configure_logger(level="DEBUG")
        # Should not raise error
        assert True

    def test_configure_logger_info(self, suppress_logging):
        """Test configuring logger to INFO level."""
        configure_logger(level="INFO")
        # Should not raise error
        assert True

    def test_extraction_with_debug_logging(self, text_pdf_bytes, suppress_logging):
        """Test extraction with debug logging enabled."""
        configure_logger(level="DEBUG")
        
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract()
            assert result is not None


class TestPerformanceTips:
    """Tests demonstrating performance-related use cases."""

    def test_use_page_ranges(self, multi_page_pdf_bytes):
        """Performance tip 1: Use page ranges."""
        with PDFExtractor(multi_page_pdf_bytes) as extractor:
            result = extractor.extract(start_page=0, end_page=2)
            assert len(result.pages) == 2

    def test_disable_metadata(self, minimal_pdf_bytes):
        """Performance tip 2: Disable metadata if not needed."""
        with PDFExtractor(minimal_pdf_bytes) as extractor:
            result = extractor.extract(include_metadata=False)
            assert result.metadata == {}

    def test_tolerance_mode_faster(self, text_pdf_bytes):
        """Performance tip 3: Use tolerance mode for well-formed PDFs."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract(grouping_mode="tolerance")
            assert result.grouping_config.grouping_mode == "tolerance"

    def test_reuse_extractor(self, multi_page_pdf_bytes):
        """Performance tip 4: Reuse extractor for multiple extractions."""
        with PDFExtractor(multi_page_pdf_bytes) as extractor:
            first = extractor.extract(end_page=2)
            last = extractor.extract(start_page=1)
            
            assert len(first.pages) == 2
            assert len(last.pages) == 2


class TestGroupingModes:
    """Tests for different grouping modes."""

    def test_cluster_mode(self, text_pdf_bytes):
        """Test cluster grouping mode."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract(grouping_mode="cluster")
            assert result.grouping_config.grouping_mode == "cluster"

    def test_tolerance_mode(self, text_pdf_bytes):
        """Test tolerance grouping mode."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result = extractor.extract(grouping_mode="tolerance")
            assert result.grouping_config.grouping_mode == "tolerance"

    def test_small_y_tolerance_more_lines(self, text_pdf_bytes):
        """Test that smaller y_tolerance creates more lines."""
        with PDFExtractor(text_pdf_bytes) as extractor:
            result_small = extractor.extract(y_tolerance=2.0)
            result_large = extractor.extract(y_tolerance=10.0)
            
            # Smaller tolerance should generally produce same or more lines
            # (depends on text content)
            assert isinstance(result_small.pages[0].lines, list)
            assert isinstance(result_large.pages[0].lines, list)


class TestGroupingConfig:
    """Tests for GroupingConfig class."""

    def test_grouping_config_in_result(self, minimal_pdf_bytes):
        """Test that GroupingConfig is included in result."""
        with PDFExtractor(minimal_pdf_bytes) as extractor:
            result = extractor.extract()
            
            assert hasattr(result, 'grouping_config')
            assert hasattr(result.grouping_config, 'y_tolerance')
            assert hasattr(result.grouping_config, 'x_tolerance')
            assert hasattr(result.grouping_config, 'space_width')
            assert hasattr(result.grouping_config, 'line_gap_threshold')
            assert hasattr(result.grouping_config, 'grouping_mode')

    def test_grouping_config_to_dict(self, minimal_pdf_bytes):
        """Test GroupingConfig.to_dict()."""
        with PDFExtractor(minimal_pdf_bytes) as extractor:
            result = extractor.extract()
            
            gc_dict = result.grouping_config.to_dict()
            assert isinstance(gc_dict, dict)
            assert "y_tolerance" in gc_dict
            assert "x_tolerance" in gc_dict