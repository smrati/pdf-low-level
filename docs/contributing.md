# Contributing to pdf-lowlevel

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/pdf-lowlevel.git
cd pdf-lowlevel

# Install dependencies
uv sync

# Run tests to verify setup
uv run pytest
```

### Project Structure

```
pdf-lowlevel/
├── src/pdf_lowlevel/
│   ├── __init__.py          # Public API
│   ├── extract.py           # High-level API
│   ├── logger.py            # Logging config
│   ├── parser/              # Low-level parsing
│   │   ├── tokenizer.py     # Lexical analysis
│   │   ├── xref.py          # Cross-reference
│   │   ├── reader.py        # PDF reader
│   │   └── objects.py       # Object model
│   ├── content/             # Content processing
│   │   ├── stream.py        # Content streams
│   │   ├── graphics.py      # Graphics state
│   │   └── grouper.py       # Text grouping
│   └── fonts/               # Font handling
│       └── encoding.py      # Character encoding
├── tests/                   # Test suite
│   ├── conftest.py          # Fixtures
│   ├── test_tokenizer.py
│   ├── test_xref.py
│   ├── test_reader.py
│   └── test_extractor.py
└── docs/                    # Documentation
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code following existing patterns
- Add tests for new functionality
- Update documentation if needed

### 3. Run Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_tokenizer.py

# Run with coverage
uv run pytest --cov=pdf_lowlevel

# Run with verbose output
uv run pytest -v
```

### 4. Check Code Quality

```bash
# Format code
uv run ruff format .

# Check linting
uv run ruff check .

# Type checking (if configured)
uv run mypy src/
```

### 5. Commit Changes

```bash
git add .
git commit -m "Description of changes"
```

Follow conventional commit format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring

## Coding Standards

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for public APIs
- Keep functions focused and small

### Example

```python
from typing import Optional, List

def parse_object(data: bytes, offset: int) -> Optional[PDFObject]:
    """
    Parse a PDF object from bytes.
    
    Args:
        data: PDF source bytes
        offset: Starting position
        
    Returns:
        Parsed object or None if invalid
    """
    if offset >= len(data):
        return None
    
    # Implementation...
    return result
```

### Logging

Use loguru for logging:

```python
from pdf_lowlevel.logger import logger

def some_function():
    logger.debug("Processing started")
    logger.info(f"Found {count} objects")
    logger.warning("Unexpected format")
    logger.error("Failed to parse")
```

## Testing

### Test Structure

Tests are organized by module:

```python
# tests/test_tokenizer.py
class TestPDFTokenizer:
    def test_tokenize_integer(self):
        """Test tokenizing an integer."""
        tokenizer = PDFTokenizer(b"42")
        token = tokenizer.next_token()
        assert token.type == TokenType.INTEGER
        assert token.value == 42
```

### Fixtures

Shared fixtures are in `conftest.py`:

```python
# tests/conftest.py
@pytest.fixture
def minimal_pdf_bytes():
    """Minimal valid PDF for testing."""
    return b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
...
%%EOF"""
```

### Creating Test PDFs

For testing, create minimal PDFs:

```python
def create_test_pdf(content: str) -> bytes:
    """Create a minimal PDF with text content."""
    # Calculate byte offsets carefully!
    # See conftest.py for examples
```

### Test Categories

- **Unit tests**: Test individual functions/classes
- **Integration tests**: Test module interactions
- **Edge cases**: Boundary conditions, errors

## Adding New Features

### 1. Content Stream Operators

Add to `content/stream.py`:

```python
def _op_new_operator(self, operands):
    """Handle NEW operator."""
    # Implementation

# Register in _operator_handlers
_operator_handlers["NEW"] = _op_new_operator
```

### 2. Stream Filters

Add to `parser/reader.py`:

```python
def _apply_new_filter(self, data: bytes, params: Dict) -> bytes:
    """Apply NewDecode filter."""
    # Implementation

# Add to _apply_filter method
if filter_name == "NewDecode":
    return self._apply_new_filter(data, params)
```

### 3. Text Grouping Algorithms

Add to `content/grouper.py`:

```python
class NewGrouper:
    def group_into_lines(self, elements):
        # Implementation
```

## Documentation

### Updating Docs

Documentation is in `docs/`:

- Update relevant `.md` files
- Add examples for new features
- Keep API reference current

### Docstrings

Use Google-style docstrings:

```python
def extract_text(source: Union[str, bytes]) -> str:
    """
    Extract text from a PDF.
    
    Args:
        source: PDF file path or bytes
        
    Returns:
        Extracted text as string
        
    Raises:
        PDFParseError: If PDF is invalid
        
    Example:
        >>> text = extract_text("document.pdf")
        >>> print(text)
    """
```

## Reporting Issues

### Bug Reports

Include:
1. Python version
2. Library version
3. Minimal reproducible example
4. Expected vs actual behavior
5. Sample PDF (if possible)

### Feature Requests

Include:
1. Use case description
2. Proposed API (if any)
3. Alternative solutions considered

## Pull Request Process

1. **Fork and branch** from `main`
2. **Make changes** following standards
3. **Add tests** for new functionality
4. **Update docs** if needed
5. **Run tests** to verify
6. **Submit PR** with description

### PR Checklist

- [ ] Tests pass
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] CHANGELOG updated (if applicable)
- [ ] No breaking changes (or documented)

## Getting Help

- Open an issue for bugs/features
- Check existing issues first
- Read the documentation in `docs/`

## License

By contributing, you agree your contributions are licensed under the MIT License.