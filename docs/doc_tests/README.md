# Test Suite Documentation

This directory contains comprehensive documentation for the pdf-lowlevel test suite.

## Overview

The test suite uses **pytest** and consists of **143 tests** across 4 test modules, with 4 tests skipped (text extraction features not fully implemented).

```
tests/
├── __init__.py         # Package marker
├── conftest.py         # Shared fixtures and test utilities
├── test_tokenizer.py   # 47 tests for PDF tokenization
├── test_xref.py        # 26 tests for cross-reference table parsing
├── test_reader.py      # 32 tests for PDF reading
└── test_extractor.py   # 38 tests for high-level extraction API
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_tokenizer.py

# Run specific test class
uv run pytest tests/test_tokenizer.py::TestPDFTokenizer

# Run specific test
uv run pytest tests/test_tokenizer.py::TestPDFTokenizer::test_tokenize_positive_integer

# Run with coverage
uv run pytest --cov=pdf_lowlevel

# Run quietly (only show failures)
uv run pytest -q
```

## Test Documentation Index

| Document | Description | Tests |
|----------|-------------|-------|
| [conftest.md](conftest.md) | Shared fixtures and test PDF generation | N/A |
| [test_tokenizer.md](test_tokenizer.md) | Tokenization tests | 47 |
| [test_xref.md](test_xref.md) | Cross-reference table tests | 26 |
| [test_reader.md](test_reader.md) | PDF reader tests | 32 |
| [test_extractor.md](test_extractor.md) | Extraction API tests | 38 |

## Test Categories

### Unit Tests
Test individual functions and classes in isolation:
- Token parsing (integers, reals, strings, names, etc.)
- XRef entry and table operations
- Object parsing

### Integration Tests
Test module interactions:
- PDF reading with xref parsing
- Extraction with content stream parsing
- Full workflow tests

### Edge Case Tests
Test boundary conditions and error handling:
- Invalid PDF content
- Empty files
- Malformed structures
- Out-of-range values

## Test Fixtures

The test suite uses dynamically generated PDFs created in `conftest.py`:

| Fixture | Description |
|---------|-------------|
| `minimal_pdf_bytes` | Minimal valid PDF (1 page, no content) |
| `text_pdf_bytes` | PDF with "Hello, World!" text |
| `multi_page_pdf_bytes` | PDF with 3 pages |
| `indirect_ref_pdf_bytes` | PDF with Info dictionary |
| `invalid_pdf_bytes` | Invalid PDF content |
| `empty_pdf_bytes` | Empty file |
| `truncated_pdf_bytes` | Truncated PDF |

## Test Results Summary

```
=================================== 143 passed, 4 skipped in 0.11s ===================================
```

### Skipped Tests
4 tests are skipped because text extraction is not fully implemented:
- `test_text_element_properties`
- `test_text_element_bbox`
- `test_text_element_to_dict`
- `test_text_element_repr`

## Contributing Tests

When adding new features:

1. **Create test file** if new module: `tests/test_new_module.py`
2. **Add fixtures** to `conftest.py` if needed
3. **Follow naming convention**: `test_<functionality>_<scenario>`
4. **Use descriptive test names**: `test_tokenize_negative_integer`
5. **Add docstrings** explaining what is being tested

### Test Template

```python
class TestNewFeature:
    """Tests for NewFeature class."""
    
    def test_basic_functionality(self, fixture_name):
        """Test basic functionality works."""
        # Arrange
        input_data = ...
        
        # Act
        result = function_under_test(input_data)
        
        # Assert
        assert result == expected_value
    
    def test_edge_case(self):
        """Test edge case handling."""
        with pytest.raises(ExpectedException):
            function_under_test(invalid_input)