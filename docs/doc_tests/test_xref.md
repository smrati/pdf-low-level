# Cross-Reference Table Tests (test_xref.py)

This document describes the **26 tests** for PDF cross-reference table parsing in `tests/test_xref.py`.

## Overview

The xref tests verify parsing of PDF cross-reference tables, trailer dictionaries, and indirect references.

**Source:** `src/pdf_lowlevel/parser/xref.py`

## Test Classes

| Class | Tests | Description |
|-------|-------|-------------|
| TestIndirectRef | 2 | Indirect reference dataclass |
| TestXRefEntry | 4 | XRef entry dataclass |
| TestXRefTable | 8 | XRef table operations |
| TestFindXRefOffset | 3 | Finding xref offset |
| TestXRefParser | 4 | Parsing xref tables |
| TestParseXref | 2 | Convenience function |
| TestIndirectRefParsing | 3 | Regression tests |

---

## TestIndirectRef

Tests for the `IndirectRef` dataclass.

### test_create_indirect_ref
Verifies creating an indirect reference.

```python
def test_create_indirect_ref(self):
    ref = IndirectRef(1, 0)
    assert ref.object_number == 1
    assert ref.generation_number == 0
```

### test_indirect_ref_repr
Verifies string representation.

```python
def test_indirect_ref_repr(self):
    ref = IndirectRef(5, 2)
    repr_str = repr(ref)
    assert "5" in repr_str
    assert "2" in repr_str
```

---

## TestXRefEntry

Tests for the `XRefEntry` dataclass.

### test_create_entry_defaults
Verifies default values.

```python
def test_create_entry_defaults(self):
    entry = XRefEntry()
    assert entry.offset == 0
    assert entry.generation == 0
    assert entry.free == False
    assert entry.entry_type == 1
```

### test_create_entry_in_use
Verifies creating in-use entry.

```python
def test_create_entry_in_use(self):
    entry = XRefEntry(offset=1234, generation=0, free=False)
    assert entry.offset == 1234
    assert entry.free == False
    assert entry.entry_type == 1
```

### test_create_entry_free
Verifies creating free entry.

```python
def test_create_entry_free(self):
    entry = XRefEntry(offset=0, generation=65535, free=True, entry_type=0)
    assert entry.free == True
    assert entry.entry_type == 0
```

### test_create_compressed_entry
Verifies creating compressed object stream entry.

```python
def test_create_compressed_entry(self):
    entry = XRefEntry(
        object_stream_num=10,
        index_in_stream=5,
        entry_type=2
    )
    assert entry.entry_type == 2
    assert entry.object_stream_num == 10
```

---

## TestXRefTable

Tests for the `XRefTable` class.

### test_empty_table
Verifies empty table behavior.

```python
def test_empty_table(self):
    table = XRefTable()
    assert len(table.entries) == 0
    assert table.get_offset(1) is None
```

### test_add_and_get_entry
Verifies adding and retrieving entries.

```python
def test_add_and_get_entry(self):
    table = XRefTable()
    entry = XRefEntry(offset=100, generation=0)
    table.add_entry(1, entry)

    assert table.get_offset(1) == 100
    assert table.get_entry(1) == entry
```

### test_get_offset_free_entry
Verifies free entries return None.

```python
def test_get_offset_free_entry(self):
    table = XRefTable()
    entry = XRefEntry(offset=0, free=True, entry_type=0)
    table.add_entry(0, entry)

    assert table.get_offset(0) is None
```

### test_get_root_ref
Verifies getting root catalog reference.

```python
def test_get_root_ref(self):
    table = XRefTable()
    table.trailer["Root"] = IndirectRef(1, 0)

    root_ref = table.get_root_ref()
    assert root_ref == (1, 0)
```

### test_get_root_ref_missing
Verifies missing root reference.

```python
def test_get_root_ref_missing(self):
    table = XRefTable()
    assert table.get_root_ref() is None
```

### test_get_info_ref
Verifies getting info dictionary reference.

```python
def test_get_info_ref(self):
    table = XRefTable()
    table.trailer["Info"] = IndirectRef(4, 0)

    info_ref = table.get_info_ref()
    assert info_ref == (4, 0)
```

### test_get_size
Verifies getting size from trailer.

```python
def test_get_size(self):
    table = XRefTable()
    table.trailer["Size"] = 10

    assert table.get_size() == 10
```

### test_get_size_default
Verifies default size when not set.

```python
def test_get_size_default(self):
    table = XRefTable()
    assert table.get_size() == 0
```

---

## TestFindXRefOffset

Tests for `find_xref_offset()` function.

### test_find_xref_offset_simple
Verifies finding xref offset in simple PDF.

```python
def test_find_xref_offset_simple(self, minimal_pdf_bytes):
    file_obj = BytesIO(minimal_pdf_bytes)
    offset = find_xref_offset(file_obj)
    assert offset > 0
```

### test_find_xref_offset_multi_page
Verifies finding xref offset in multi-page PDF.

```python
def test_find_xref_offset_multi_page(self, multi_page_pdf_bytes):
    file_obj = BytesIO(multi_page_pdf_bytes)
    offset = find_xref_offset(file_obj)
    assert offset > 0
```

### test_find_xref_offset_no_startxref
Verifies error when startxref is missing.

```python
def test_find_xref_offset_no_startxref(self):
    file_obj = BytesIO(b"%PDF-1.4\n%EOF")
    with pytest.raises(ValueError, match="startxref"):
        find_xref_offset(file_obj)
```

---

## TestXRefParser

Tests for `XRefParser` class.

### test_parse_minimal_pdf
Verifies parsing xref from minimal PDF.

```python
def test_parse_minimal_pdf(self, minimal_pdf):
    minimal_pdf.seek(0)
    offset = find_xref_offset(minimal_pdf)
    minimal_pdf.seek(offset)

    parser = XRefParser(minimal_pdf)
    table = parser.parse()

    assert table is not None
    assert len(table.entries) > 0
```

### test_parse_trailer_root_ref
Verifies trailer has Root reference.

```python
def test_parse_trailer_root_ref(self, minimal_pdf):
    minimal_pdf.seek(0)
    offset = find_xref_offset(minimal_pdf)
    minimal_pdf.seek(offset)

    parser = XRefParser(minimal_pdf)
    table = parser.parse()

    root_ref = table.get_root_ref()
    assert root_ref is not None
    assert isinstance(root_ref, tuple)
    assert len(root_ref) == 2
```

### test_parse_indirect_ref_in_trailer
Verifies parsing indirect references in trailer.

```python
def test_parse_indirect_ref_in_trailer(self, indirect_ref_pdf):
    indirect_ref_pdf.seek(0)
    offset = find_xref_offset(indirect_ref_pdf)
    indirect_ref_pdf.seek(offset)

    parser = XRefParser(indirect_ref_pdf)
    table = parser.parse()

    root_ref = table.get_root_ref()
    assert root_ref is not None
    assert isinstance(root_ref, tuple)
    assert root_ref[0] == 1
    assert root_ref[1] == 0

    info_ref = table.get_info_ref()
    assert info_ref is not None
    assert info_ref[0] == 4
    assert info_ref[1] == 0
```

### test_parse_entries_offsets
Verifies entry offsets are parsed correctly.

```python
def test_parse_entries_offsets(self, minimal_pdf):
    minimal_pdf.seek(0)
    offset = find_xref_offset(minimal_pdf)
    minimal_pdf.seek(offset)

    parser = XRefParser(minimal_pdf)
    table = parser.parse()

    entry = table.get_entry(1)
    assert entry is not None
    assert entry.offset > 0
    assert entry.free == False
```

---

## TestParseXref

Tests for `parse_xref()` convenience function.

### test_parse_xref_minimal
Verifies parse_xref with minimal PDF.

```python
def test_parse_xref_minimal(self, minimal_pdf):
    minimal_pdf.seek(0)
    table = parse_xref(minimal_pdf)
    assert table is not None
    assert len(table.entries) > 0
```

### test_parse_xref_text_pdf
Verifies parse_xref with text PDF.

```python
def test_parse_xref_text_pdf(self, text_pdf):
    text_pdf.seek(0)
    table = parse_xref(text_pdf)
    assert table is not None
```

---

## TestIndirectRefParsing

Regression tests for IndirectRef parsing bug.

### test_root_is_indirect_ref
Verifies Root in trailer is parsed as IndirectRef, not int.

```python
def test_root_is_indirect_ref(self, minimal_pdf):
    minimal_pdf.seek(0)
    table = parse_xref(minimal_pdf)

    root = table.trailer.get("Root")
    assert isinstance(root, IndirectRef)
```

### test_info_is_indirect_ref
Verifies Info in trailer is parsed as IndirectRef.

```python
def test_info_is_indirect_ref(self, indirect_ref_pdf):
    indirect_ref_pdf.seek(0)
    table = parse_xref(indirect_ref_pdf)

    info = table.trailer.get("Info")
    assert isinstance(info, IndirectRef)
```

### test_multiple_indirect_refs
Verifies parsing multiple indirect references in trailer.

```python
def test_multiple_indirect_refs(self, indirect_ref_pdf):
    indirect_ref_pdf.seek(0)
    table = parse_xref(indirect_ref_pdf)

    root = table.trailer.get("Root")
    info = table.trailer.get("Info")

    assert isinstance(root, IndirectRef)
    assert isinstance(info, IndirectRef)
    assert root.object_number == 1
    assert info.object_number == 4