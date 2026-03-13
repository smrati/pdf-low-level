# API Use Cases Tests (test_api_usecases.py)

This document describes the **68 tests** for API use cases described in `docs/api_docs.md`.

## Overview

These tests verify all examples and use cases documented in the API documentation work correctly.

**Source:** `tests/test_api_usecases.py`

## Test Classes

| Class | Tests | Description |
|-------|-------|-------------|
| TestPublicAPIExports | 4 | Public API symbol exports |
| TestExtractTextFunction | 6 | extract_text() use cases |
| TestExtractJsonFunction | 4 | extract_json() use cases |
| TestPDFExtractorClass | 19 | PDFExtractor class use cases |
| TestExtractionResultClass | 5 | ExtractionResult use cases |
| TestPageResultClass | 4 | PageResult use cases |
| TestTextElementFiltering | 4 | Text filtering examples |
| TestTextElementProperties | 2 | TextElement properties |
| TestJSONOutputFormat | 3 | JSON structure tests |
| TestLowLevelReader | 3 | Low-level API access |
| TestErrorHandling | 3 | Error handling examples |
| TestLogging | 3 | Logging configuration |
| TestPerformanceTips | 4 | Performance optimization |
| TestGroupingModes | 3 | Grouping mode tests |
| TestGroupingConfig | 2 | GroupingConfig tests |

---

## TestPublicAPIExports

Tests that all public API symbols are exported correctly.

### test_all_exports_available
Verifies all documented exports can be imported.

```python
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
```

### test_version_is_string
Verifies `__version__` is a string.

### test_logger_is_available
Verifies logger instance is available.

### test_configure_logger_callable
Verifies `configure_logger` is callable.

---

## TestExtractTextFunction

Tests for `extract_text()` convenience function use cases.

### test_extract_text_from_file_path
Example 1: Basic text extraction from file path.

```python
pdf_path = tmp_path / "document.pdf"
pdf_path.write_bytes(minimal_pdf_bytes)
text = extract_text(str(pdf_path))
assert isinstance(text, str)
```

### test_extract_text_from_bytes
Example: Extract text from bytes.

```python
text = extract_text(minimal_pdf_bytes)
assert isinstance(text, str)
```

### test_extract_text_from_bytesio
Example: Extract text from BytesIO.

```python
file_obj = BytesIO(minimal_pdf_bytes)
text = extract_text(file_obj)
```

### test_extract_text_with_grouping_mode_cluster
Test with `grouping_mode="cluster"`.

### test_extract_text_with_grouping_mode_tolerance
Test with `grouping_mode="tolerance"`.

### test_extract_text_with_y_tolerance
Test with custom `y_tolerance`.

---

## TestExtractJsonFunction

Tests for `extract_json()` convenience function use cases.

### test_extract_json_returns_valid_json
Verifies extract_json returns valid JSON.

### test_extract_json_structure
Example 3: Get structured JSON output.

```python
json_str = extract_json(minimal_pdf_bytes)
data = json.loads(json_str)

assert "page_count" in data
assert "pages" in data
```

### test_extract_json_with_page_range
Test extract_json with page range.

### test_extract_json_with_grouping_mode
Test extract_json with grouping_mode parameter.

---

## TestPDFExtractorClass

Tests for PDFExtractor class use cases (19 tests).

### Constructor Input Types

- `test_constructor_with_string_path` - File path string
- `test_constructor_with_path_object` - Path object
- `test_constructor_with_bytes` - Bytes
- `test_constructor_with_file_object` - File-like object

### Context Manager

- `test_context_manager_auto_close` - Verifies resources are cleaned up

### extract() Method Parameters

- `test_extract_with_start_page_only` - Only start_page specified
- `test_extract_with_end_page_only` - Only end_page specified
- `test_extract_with_full_page_range` - Example 2: Extract specific pages
- `test_extract_without_metadata` - With `include_metadata=False`
- `test_extract_with_metadata` - Example 7: Extract metadata

### Grouping Parameters

- `test_extract_with_grouping_mode_cluster` - cluster mode
- `test_extract_with_grouping_mode_tolerance` - tolerance mode
- `test_extract_with_y_tolerance` - custom y_tolerance
- `test_extract_with_x_tolerance` - custom x_tolerance
- `test_extract_with_space_width` - custom space_width
- `test_extract_with_line_gap_threshold` - custom line_gap_threshold
- `test_extract_with_all_grouping_params` - Example 4: Custom grouping settings

### close() Method

- `test_manual_close` - Test manually closing the extractor

---

## TestExtractionResultClass

Tests for ExtractionResult class use cases.

### test_result_attributes
Verifies ExtractionResult attributes.

```python
result = extractor.extract()
assert isinstance(result.filename, str)
assert isinstance(result.page_count, int)
assert isinstance(result.pages, list)
assert isinstance(result.metadata, dict)
```

### test_to_dict_method
Test `ExtractionResult.to_dict()`.

### test_to_json_method
Test `ExtractionResult.to_json()`.

### test_get_all_text_method
Test `ExtractionResult.get_all_text()`.

### test_result_with_multi_page
Test ExtractionResult with multiple pages.

---

## TestPageResultClass

Tests for PageResult class use cases.

### test_page_result_attributes
Verifies PageResult attributes.

```python
page = result.pages[0]
assert page.page_number == 1
assert page.width == 612
assert page.height == 792
assert isinstance(page.elements, list)
```

### test_get_text_method
Test `PageResult.get_text()`.

### test_get_text_with_blocks_method
Test `PageResult.get_text_with_blocks()`.

### test_to_dict_method
Test `PageResult.to_dict()`.

---

## TestTextElementFiltering

Tests for TextElement filtering use cases (Example 5, 6).

### test_element_has_position_attributes
Example 5: Extract with positions.

```python
for page in result.pages:
    for elem in page.elements:
        assert hasattr(elem, 'text')
        assert hasattr(elem, 'x')
        assert hasattr(elem, 'y')
        assert hasattr(elem, 'font_name')
        assert hasattr(elem, 'font_size')
```

### test_filter_by_region
Example 6: Filter by region.

```python
x1, y1, x2, y2 = 0, 0, 500, 792
region_elements = [
    elem for elem in page.elements
    if x1 <= elem.x <= x2 and y1 <= elem.y <= y2
]
```

### test_filter_by_font_size
Example: Filter by font size (find headers).

### test_filter_left_column
Example: Filter by position (left column).

---

## TestTextElementProperties

Tests for TextElement properties.

### test_bbox_property
Test `TextElement.bbox` property.

### test_to_dict_method
Test `TextElement.to_dict()`.

---

## TestJSONOutputFormat

Tests for JSON output format (Example 9).

### test_json_structure_complete
Verifies JSON output has complete structure.

```python
data = json.loads(result.to_json())
assert "filename" in data
assert "page_count" in data
assert "pages" in data
assert "metadata" in data
assert "grouping_config" in data
```

### test_json_page_structure
Verifies each page in JSON has correct structure.

### test_json_grouping_config_structure
Verifies grouping_config in JSON has correct structure.

---

## TestLowLevelReader

Tests for low-level reader access (Example 10).

### test_open_pdf_context_manager
Example 10: Access low-level reader.

```python
with open_pdf(minimal_pdf_bytes) as pdf:
    assert pdf.version == "1.4"
    assert pdf.page_count == 1
```

### test_low_level_page_contents
Test getting page contents via low-level API.

### test_low_level_media_box
Test getting media box via low-level API.

---

## TestErrorHandling

Tests for error handling use cases.

### test_file_not_found
Test FileNotFoundError for non-existent file.

```python
with pytest.raises(FileNotFoundError):
    with PDFExtractor("/nonexistent/path/file.pdf") as extractor:
        extractor.extract()
```

### test_invalid_pdf_error
Test PDFParseError for invalid PDF.

### test_empty_file_error
Test error for empty file.

---

## TestLogging

Tests for logging functionality.

### test_configure_logger_debug
Test configuring logger to DEBUG level.

### test_configure_logger_info
Test configuring logger to INFO level.

### test_extraction_with_debug_logging
Test extraction with debug logging enabled.

---

## TestPerformanceTips

Tests demonstrating performance-related use cases.

### test_use_page_ranges
Performance tip 1: Use page ranges.

### test_disable_metadata
Performance tip 2: Disable metadata if not needed.

### test_tolerance_mode_faster
Performance tip 3: Use tolerance mode for well-formed PDFs.

### test_reuse_extractor
Performance tip 4: Reuse extractor for multiple extractions.

```python
with PDFExtractor(multi_page_pdf_bytes) as extractor:
    first = extractor.extract(end_page=2)
    last = extractor.extract(start_page=1)
```

---

## TestGroupingModes

Tests for different grouping modes.

### test_cluster_mode
Test cluster grouping mode.

### test_tolerance_mode
Test tolerance grouping mode.

### test_small_y_tolerance_more_lines
Test that smaller y_tolerance creates more lines.

---

## TestGroupingConfig

Tests for GroupingConfig class.

### test_grouping_config_in_result
Test that GroupingConfig is included in result.

### test_grouping_config_to_dict
Test `GroupingConfig.to_dict()`.

---

## Skipped Tests

6 tests are skipped when text extraction is not fully implemented:
- `test_element_has_position_attributes`
- `test_filter_by_region`
- `test_filter_by_font_size`
- `test_filter_left_column`
- `test_bbox_property`
- `test_to_dict_method` (TextElement)

These tests will automatically pass once text extraction is fully implemented.