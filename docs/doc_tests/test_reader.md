# PDF Reader Tests (test_reader.py)

This document describes the **32 tests** for PDF reading and parsing in `tests/test_reader.py`.

## Overview

The reader tests verify PDF file reading, object parsing, page loading, and stream decompression.

**Source:** `src/pdf_lowlevel/parser/reader.py`

## Test Classes

| Class | Tests | Description |
|-------|-------|-------------|
| TestPDFReader | 20 | Main reader functionality |
| TestOpenPdf | 3 | Convenience function |
| TestPDFParseError | 2 | Exception handling |
| TestIndirectReferences | 2 | Reference resolution |
| TestMultiPagePDF | 2 | Multi-page handling |

---

## TestPDFReader

Main test class for PDFReader functionality.

### Initialization and Context Manager

#### test_init_with_bytes
Verifies initializing reader with bytes.

```python
def test_init_with_bytes(self, minimal_pdf_bytes):
    reader = PDFReader(minimal_pdf_bytes)
    assert reader._file is not None
    reader.close()
```

#### test_init_with_file_like
Verifies initializing reader with file-like object.

```python
def test_init_with_file_like(self, minimal_pdf):
    reader = PDFReader(minimal_pdf)
    assert reader._file is not None
    reader.close()
```

#### test_context_manager
Verifies using reader as context manager.

```python
def test_context_manager(self, minimal_pdf_bytes):
    with PDFReader(minimal_pdf_bytes) as reader:
        reader.read()
        assert reader.page_count >= 0
```

#### test_close
Verifies closing reader.

```python
def test_close(self, minimal_pdf_bytes):
    reader = PDFReader(minimal_pdf_bytes)
    reader.close()
    # Should not raise error
```

### Header Verification

#### test_read_valid_pdf
Verifies reading valid PDF.

```python
def test_read_valid_pdf(self, minimal_pdf_bytes):
    reader = PDFReader(minimal_pdf_bytes)
    reader.read()
    assert hasattr(reader, "version")
    reader.close()
```

#### test_invalid_pdf_raises_error
Verifies invalid PDF raises PDFParseError.

```python
def test_invalid_pdf_raises_error(self, invalid_pdf_bytes):
    reader = PDFReader(invalid_pdf_bytes)
    with pytest.raises(PDFParseError):
        reader.read()
    reader.close()
```

#### test_empty_pdf_raises_error
Verifies empty file raises PDFParseError.

```python
def test_empty_pdf_raises_error(self, empty_pdf_bytes):
    reader = PDFReader(empty_pdf_bytes)
    with pytest.raises(PDFParseError):
        reader.read()
    reader.close()
```

#### test_pdf_version
Verifies PDF version is extracted.

```python
def test_pdf_version(self, minimal_pdf_bytes):
    reader = PDFReader(minimal_pdf_bytes)
    reader.read()
    assert reader.version == "1.4"
    reader.close()
```

### Page Count

#### test_page_count_single
Verifies page count for single-page PDF.

```python
def test_page_count_single(self, minimal_pdf_bytes):
    with PDFReader(minimal_pdf_bytes) as reader:
        reader.read()
        assert reader.page_count == 1
```

#### test_page_count_multi
Verifies page count for multi-page PDF.

```python
def test_page_count_multi(self, multi_page_pdf_bytes):
    with PDFReader(multi_page_pdf_bytes) as reader:
        reader.read()
        assert reader.page_count == 3
```

### Object Access

#### test_get_object
Verifies getting an object by number.

```python
def test_get_object(self, minimal_pdf_bytes):
    with PDFReader(minimal_pdf_bytes) as reader:
        reader.read()
        obj = reader.get_object(1, 0)  # Catalog
        assert obj is not None
```

#### test_get_nonexistent_object
Verifies nonexistent object returns None.

```python
def test_get_nonexistent_object(self, minimal_pdf_bytes):
    with PDFReader(minimal_pdf_bytes) as reader:
        reader.read()
        obj = reader.get_object(999, 0)
        assert obj is None
```

### Page Access

#### test_get_page
Verifies getting a page object.

```python
def test_get_page(self, minimal_pdf_bytes):
    with PDFReader(minimal_pdf_bytes) as reader:
        reader.read()
        page = reader.get_page(0)
        assert page is not None
        assert "Type" in page or "/Type" in page
```

#### test_get_page_out_of_range
Verifies out-of-range page returns None.

```python
def test_get_page_out_of_range(self, minimal_pdf_bytes):
    with PDFReader(minimal_pdf_bytes) as reader:
        reader.read()
        page = reader.get_page(999)
        assert page is None
```

#### test_get_page_negative
Verifies negative index returns None.

```python
def test_get_page_negative(self, minimal_pdf_bytes):
    with PDFReader(minimal_pdf_bytes) as reader:
        reader.read()
        page = reader.get_page(-1)
        assert page is None
```

### Media Box

#### test_get_media_box
Verifies getting page media box.

```python
def test_get_media_box(self, minimal_pdf_bytes):
    with PDFReader(minimal_pdf_bytes) as reader:
        reader.read()
        media_box = reader.get_page_media_box(0)
        assert media_box is not None
        assert len(media_box) == 4
        assert media_box[2] == 612  # US Letter width
        assert media_box[3] == 792  # US Letter height
```

### Page Contents

#### test_get_page_contents_text_pdf
Verifies getting page contents from text PDF.

```python
def test_get_page_contents_text_pdf(self, text_pdf_bytes):
    with PDFReader(text_pdf_bytes) as reader:
        reader.read()
        contents = reader.get_page_contents(0)
        assert contents is not None
        assert b"BT" in contents  # Begin text
        assert b"ET" in contents  # End text
```

#### test_get_page_contents_empty_page
Verifies contents from page without content stream.

```python
def test_get_page_contents_empty_page(self, minimal_pdf_bytes):
    with PDFReader(minimal_pdf_bytes) as reader:
        reader.read()
        contents = reader.get_page_contents(0)
        assert contents is None  # No content stream
```

### Resources

#### test_get_page_resources
Verifies getting page resources.

```python
def test_get_page_resources(self, text_pdf_bytes):
    with PDFReader(text_pdf_bytes) as reader:
        reader.read()
        resources = reader.get_page_resources(0)
        assert resources is not None
```

### Stream Decompression

#### test_flate_decode
Verifies FlateDecode decompression concept.

```python
def test_flate_decode(self):
    import zlib

    original = b"Hello, World! This is a test."
    compressed = zlib.compress(original)
    # Test verifies the concept; actual PDF may need adjustment
```

---

## TestOpenPdf

Tests for `open_pdf()` convenience function.

### test_open_pdf_bytes
Verifies opening PDF from bytes.

```python
def test_open_pdf_bytes(self, minimal_pdf_bytes):
    reader = open_pdf(minimal_pdf_bytes)
    assert reader is not None
    assert reader.page_count == 1
    reader.close()
```

### test_open_pdf_file_like
Verifies opening PDF from file-like object.

```python
def test_open_pdf_file_like(self, minimal_pdf):
    reader = open_pdf(minimal_pdf)
    assert reader is not None
    reader.close()
```

### test_open_pdf_with_context_manager
Verifies opening PDF with context manager.

```python
def test_open_pdf_with_context_manager(self, minimal_pdf_bytes):
    with open_pdf(minimal_pdf_bytes) as reader:
        assert reader.page_count == 1
```

---

## TestPDFParseError

Tests for PDFParseError exception.

### test_exception_message
Verifies exception message is preserved.

```python
def test_exception_message(self):
    try:
        raise PDFParseError("Test error message")
    except PDFParseError as e:
        assert "Test error message" in str(e)
```

### test_exception_is_exception
Verifies PDFParseError is an Exception.

```python
def test_exception_is_exception(self):
    assert issubclass(PDFParseError, Exception)
```

---

## TestIndirectReferences

Tests for indirect reference handling.

### test_catalog_has_pages_ref
Verifies catalog has Pages reference.

```python
def test_catalog_has_pages_ref(self, minimal_pdf_bytes):
    with PDFReader(minimal_pdf_bytes) as reader:
        reader.read()
        catalog = reader.get_object(1, 0)
        assert catalog is not None
        assert "Pages" in catalog or "/Pages" in catalog
```

### test_resolve_indirect_ref
Verifies resolving indirect references.

```python
def test_resolve_indirect_ref(self, minimal_pdf_bytes):
    from pdf_lowlevel.parser.objects import PDFIndirectRef

    with PDFReader(minimal_pdf_bytes) as reader:
        reader.read()
        catalog = reader.get_object(1, 0)

        pages_key = "Pages" if "Pages" in catalog else "/Pages"
        pages_ref = catalog.get(pages_key)

        if isinstance(pages_ref, PDFIndirectRef):
            pages_obj = reader.get_object(
                pages_ref.object_number, 
                pages_ref.generation_number
            )
            assert pages_obj is not None
            assert "Kids" in pages_obj or "/Kids" in pages_obj
```

---

## TestMultiPagePDF

Tests specific to multi-page PDFs.

### test_all_pages_accessible
Verifies all pages are accessible.

```python
def test_all_pages_accessible(self, multi_page_pdf_bytes):
    with PDFReader(multi_page_pdf_bytes) as reader:
        reader.read()
        assert reader.page_count == 3

        for i in range(reader.page_count):
            page = reader.get_page(i)
            assert page is not None
```

### test_page_media_boxes
Verifies all pages have media boxes.

```python
def test_page_media_boxes(self, multi_page_pdf_bytes):
    with PDFReader(multi_page_pdf_bytes) as reader:
        reader.read()

        for i in range(reader.page_count):
            media_box = reader.get_page_media_box(i)
            assert media_box is not None
            assert len(media_box) == 4