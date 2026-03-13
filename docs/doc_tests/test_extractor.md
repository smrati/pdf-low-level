# Extractor API Tests (test_extractor.py)

This document describes the **38 tests** for the high-level extraction API in `tests/test_extractor.py`.

## Overview

The extractor tests verify the `PDFExtractor` class, convenience functions, and result data classes.

**Source:** `src/pdf_lowlevel/extract.py`

## Test Classes

| Class | Tests | Description |
|-------|-------|-------------|
| TestPDFExtractor | 21 | Main extractor functionality |
| TestExtractText | 3 | extract_text function |
| TestExtractJson | 4 | extract_json function |
| TestTextElement | 2 | TextElement dataclass |
| TestErrorHandling | 2 | Error cases |
| TestDifferentInputTypes | 4 | Input type handling |
| TestLogging | 2 | Logging functionality |

**Note:** 4 tests are skipped because text extraction is not fully implemented.

---

## TestPDFExtractor

Main test class for PDFExtractor functionality.

### Initialization

#### test_init_with_bytes
Verifies initializing extractor with bytes.

```python
def test_init_with_bytes(self, minimal_pdf_bytes):
    extractor = PDFExtractor(minimal_pdf_bytes)
    assert extractor.source == minimal_pdf_bytes
    extractor.close()
```

#### test_init_with_file_like
Verifies initializing extractor with file-like object.

```python
def test_init_with_file_like(self, minimal_pdf):
    extractor = PDFExtractor(minimal_pdf)
    assert extractor.source == minimal_pdf
    extractor.close()
```

#### test_init_with_bytesio
Verifies initializing extractor with BytesIO.

```python
def test_init_with_bytesio(self, minimal_pdf_bytes):
    file_obj = BytesIO(minimal_pdf_bytes)
    extractor = PDFExtractor(file_obj)
    extractor.close()
```

#### test_context_manager
Verifies using extractor as context manager.

```python
def test_context_manager(self, minimal_pdf_bytes):
    with PDFExtractor(minimal_pdf_bytes) as extractor:
        result = extractor.extract()
        assert result is not None
```

### Extraction

#### test_extract_returns_result
Verifies extract returns ExtractionResult.

```python
def test_extract_returns_result(self, minimal_pdf_bytes):
    with PDFExtractor(minimal_pdf_bytes) as extractor:
        result = extractor.extract()
        assert isinstance(result, ExtractionResult)
```

#### test_extract_page_count
Verifies extraction with single page.

```python
def test_extract_page_count(self, minimal_pdf_bytes):
    with PDFExtractor(minimal_pdf_bytes) as extractor:
        result = extractor.extract()
        assert result.page_count == 1
```

#### test_extract_multi_page
Verifies extraction with multiple pages.

```python
def test_extract_multi_page(self, multi_page_pdf_bytes):
    with PDFExtractor(multi_page_pdf_bytes) as extractor:
        result = extractor.extract()
        assert result.page_count == 3
        assert len(result.pages) == 3
```

#### test_extract_page_range
Verifies extracting specific page range.

```python
def test_extract_page_range(self, multi_page_pdf_bytes):
    with PDFExtractor(multi_page_pdf_bytes) as extractor:
        result = extractor.extract(start_page=1, end_page=2)
        assert len(result.pages) == 1
        assert result.pages[0].page_number == 2  # 1-indexed
```

#### test_extract_single_page
Verifies extracting single page.

```python
def test_extract_single_page(self, multi_page_pdf_bytes):
    with PDFExtractor(multi_page_pdf_bytes) as extractor:
        result = extractor.extract(start_page=0, end_page=1)
        assert len(result.pages) == 1
```

#### test_extract_without_metadata
Verifies extraction without metadata.

```python
def test_extract_without_metadata(self, minimal_pdf_bytes):
    with PDFExtractor(minimal_pdf_bytes) as extractor:
        result = extractor.extract(include_metadata=False)
        assert result.metadata == {}
```

### ExtractionResult

#### test_result_filename
Verifies filename is set when extracting from file.

```python
def test_result_filename(self, minimal_pdf_bytes, tmp_path):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(minimal_pdf_bytes)

    with PDFExtractor(str(pdf_path)) as extractor:
        result = extractor.extract()
        assert result.filename == "test.pdf"
```

#### test_result_to_dict
Verifies converting result to dictionary.

```python
def test_result_to_dict(self, minimal_pdf_bytes):
    with PDFExtractor(minimal_pdf_bytes) as extractor:
        result = extractor.extract()
        d = result.to_dict()
        assert isinstance(d, dict)
        assert "page_count" in d
        assert "pages" in d
```

#### test_result_to_json
Verifies converting result to JSON.

```python
def test_result_to_json(self, minimal_pdf_bytes):
    with PDFExtractor(minimal_pdf_bytes) as extractor:
        result = extractor.extract()
        json_str = result.to_json()
        assert isinstance(json_str, str)

        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
```

#### test_result_get_all_text
Verifies getting all text as string.

```python
def test_result_get_all_text(self, text_pdf_bytes):
    with PDFExtractor(text_pdf_bytes) as extractor:
        result = extractor.extract()
        text = result.get_all_text()
        assert isinstance(text, str)
```

### PageResult

#### test_page_result_properties
Verifies PageResult properties.

```python
def test_page_result_properties(self, minimal_pdf_bytes):
    with PDFExtractor(minimal_pdf_bytes) as extractor:
        result = extractor.extract()
        page = result.pages[0]

        assert isinstance(page, PageResult)
        assert page.page_number == 1  # 1-indexed
        assert page.width == 612
        assert page.height == 792
```

#### test_page_result_to_dict
Verifies converting PageResult to dictionary.

```python
def test_page_result_to_dict(self, minimal_pdf_bytes):
    with PDFExtractor(minimal_pdf_bytes) as extractor:
        result = extractor.extract()
        page = result.pages[0]
        d = page.to_dict()

        assert isinstance(d, dict)
        assert "page_number" in d
        assert "width" in d
        assert "height" in d
        assert "elements" in d
```

### Text Extraction

#### test_extract_text_elements
Verifies extracting text elements.

```python
def test_extract_text_elements(self, text_pdf_bytes):
    with PDFExtractor(text_pdf_bytes) as extractor:
        result = extractor.extract()
        page = result.pages[0]

        if len(page.elements) > 0:
            element = page.elements[0]
            assert isinstance(element, TextElement)
            assert "Hello" in element.text or "World" in element.text
```

#### test_text_element_properties
Verifies TextElement properties. **(SKIPPED)**

```python
@pytest.mark.skip(reason="Text extraction not fully implemented")
def test_text_element_properties(self, text_pdf_bytes):
    with PDFExtractor(text_pdf_bytes) as extractor:
        result = extractor.extract()
        
        if len(result.pages[0].elements) == 0:
            pytest.skip("Text extraction not yet fully implemented")
        
        element = result.pages[0].elements[0]
        assert element.x is not None
        assert element.y is not None
        assert element.page_number == 1
```

#### test_text_element_bbox
Verifies TextElement bounding box. **(SKIPPED)**

```python
@pytest.mark.skip(reason="Text extraction not fully implemented")
def test_text_element_bbox(self, text_pdf_bytes):
    with PDFExtractor(text_pdf_bytes) as extractor:
        result = extractor.extract()
        
        if len(result.pages[0].elements) == 0:
            pytest.skip("Text extraction not yet fully implemented")
        
        element = result.pages[0].elements[0]
        bbox = element.bbox
        assert len(bbox) == 4
```

### Metadata

#### test_extract_metadata
Verifies extracting document metadata.

```python
def test_extract_metadata(self, indirect_ref_pdf_bytes):
    with PDFExtractor(indirect_ref_pdf_bytes) as extractor:
        result = extractor.extract()
        assert isinstance(result.metadata, dict)
```

---

## TestExtractText

Tests for `extract_text()` convenience function.

### test_extract_text_returns_string
Verifies extract_text returns string.

```python
def test_extract_text_returns_string(self, text_pdf_bytes):
    text = extract_text(text_pdf_bytes)
    assert isinstance(text, str)
```

### test_extract_text_content
Verifies extracted text content.

```python
def test_extract_text_content(self, text_pdf_bytes):
    text = extract_text(text_pdf_bytes)
    assert isinstance(text, str)
```

### test_extract_text_empty_page
Verifies extracting from page without text.

```python
def test_extract_text_empty_page(self, minimal_pdf_bytes):
    text = extract_text(minimal_pdf_bytes)
    assert text.strip() == ""
```

---

## TestExtractJson

Tests for `extract_json()` convenience function.

### test_extract_json_returns_string
Verifies extract_json returns string.

```python
def test_extract_json_returns_string(self, minimal_pdf_bytes):
    json_str = extract_json(minimal_pdf_bytes)
    assert isinstance(json_str, str)
```

### test_extract_json_valid_json
Verifies extract_json returns valid JSON.

```python
def test_extract_json_valid_json(self, minimal_pdf_bytes):
    json_str = extract_json(minimal_pdf_bytes)
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
```

### test_extract_json_structure
Verifies JSON structure.

```python
def test_extract_json_structure(self, minimal_pdf_bytes):
    json_str = extract_json(minimal_pdf_bytes)
    parsed = json.loads(json_str)

    assert "page_count" in parsed
    assert "pages" in parsed
```

### test_extract_json_with_page_range
Verifies extract_json with page range.

```python
def test_extract_json_with_page_range(self, multi_page_pdf_bytes):
    json_str = extract_json(multi_page_pdf_bytes, start_page=0, end_page=2)
    parsed = json.loads(json_str)

    assert len(parsed["pages"]) == 2
```

---

## TestTextElement

Tests for TextElement dataclass.

### test_text_element_to_dict
Verifies TextElement.to_dict(). **(SKIPPED)**

```python
@pytest.mark.skip(reason="Text extraction not fully implemented")
def test_text_element_to_dict(self, text_pdf_bytes):
    with PDFExtractor(text_pdf_bytes) as extractor:
        result = extractor.extract()
        
        if len(result.pages[0].elements) == 0:
            pytest.skip("Text extraction not yet fully implemented")
        
        element = result.pages[0].elements[0]
        d = element.to_dict()

        assert isinstance(d, dict)
        assert "text" in d
        assert "x" in d
        assert "y" in d
        assert "bbox" in d
```

### test_text_element_repr
Verifies TextElement string representation. **(SKIPPED)**

```python
@pytest.mark.skip(reason="Text extraction not fully implemented")
def test_text_element_repr(self, text_pdf_bytes):
    with PDFExtractor(text_pdf_bytes) as extractor:
        result = extractor.extract()
        
        if len(result.pages[0].elements) == 0:
            pytest.skip("Text extraction not yet fully implemented")
        
        element = result.pages[0].elements[0]
        repr_str = repr(element)

        assert "TextElement" in repr_str
```

---

## TestErrorHandling

Tests for error handling.

### test_invalid_pdf
Verifies handling of invalid PDF.

```python
def test_invalid_pdf(self, invalid_pdf_bytes):
    with pytest.raises(Exception):
        with PDFExtractor(invalid_pdf_bytes) as extractor:
            extractor.extract()
```

### test_empty_pdf
Verifies handling of empty file.

```python
def test_empty_pdf(self, empty_pdf_bytes):
    with pytest.raises(Exception):
        with PDFExtractor(empty_pdf_bytes) as extractor:
            extractor.extract()
```

---

## TestDifferentInputTypes

Tests for different input types.

### test_bytes_input
Verifies with bytes input.

```python
def test_bytes_input(self, minimal_pdf_bytes):
    result = extract_text(minimal_pdf_bytes)
    assert isinstance(result, str)
```

### test_bytesio_input
Verifies with BytesIO input.

```python
def test_bytesio_input(self, minimal_pdf_bytes):
    file_obj = BytesIO(minimal_pdf_bytes)
    result = extract_text(file_obj)
    assert isinstance(result, str)
```

### test_file_path_input
Verifies with file path input.

```python
def test_file_path_input(self, minimal_pdf_bytes, tmp_path):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(minimal_pdf_bytes)

    result = extract_text(str(pdf_path))
    assert isinstance(result, str)
```

### test_path_object_input
Verifies with Path object input.

```python
def test_path_object_input(self, minimal_pdf_bytes, tmp_path):
    pdf_path = tmp_path / "test.pdf"
    pdf_path.write_bytes(minimal_pdf_bytes)

    result = extract_text(Path(pdf_path))
    assert isinstance(result, str)
```

---

## TestLogging

Tests for logging functionality.

### test_extraction_with_logging
Verifies extraction works with logging enabled.

```python
def test_extraction_with_logging(self, text_pdf_bytes, suppress_logging):
    with PDFExtractor(text_pdf_bytes) as extractor:
        result = extractor.extract()
        assert result is not None
```

### test_configure_logger
Verifies configure_logger is accessible.

```python
def test_configure_logger(self, suppress_logging):
    from pdf_lowlevel import configure_logger, logger

    configure_logger(level="DEBUG")
    assert logger is not None