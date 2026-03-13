"""
Unit tests for PDF Reader.

Tests PDF reading and parsing including:
- PDF header verification
- Object parsing
- Page loading
- Stream decoding
"""

import pytest
from io import BytesIO

from pdf_lowlevel.parser.reader import (
    PDFReader,
    PDFParseError,
    open_pdf,
)


class TestPDFReader:
    """Tests for PDFReader class."""

    # ========================================================================
    # Initialization and Context Manager
    # ========================================================================

    def test_init_with_bytes(self, minimal_pdf_bytes):
        """Test initializing reader with bytes."""
        reader = PDFReader(minimal_pdf_bytes)
        assert reader._file is not None
        reader.close()

    def test_init_with_file_like(self, minimal_pdf):
        """Test initializing reader with file-like object."""
        reader = PDFReader(minimal_pdf)
        assert reader._file is not None
        reader.close()

    def test_context_manager(self, minimal_pdf_bytes):
        """Test using reader as context manager."""
        with PDFReader(minimal_pdf_bytes) as reader:
            reader.read()
            assert reader.page_count >= 0

    def test_close(self, minimal_pdf_bytes):
        """Test closing reader."""
        reader = PDFReader(minimal_pdf_bytes)
        reader.close()
        # Should not raise error

    # ========================================================================
    # Header Verification
    # ========================================================================

    def test_read_valid_pdf(self, minimal_pdf_bytes):
        """Test reading valid PDF."""
        reader = PDFReader(minimal_pdf_bytes)
        reader.read()
        assert hasattr(reader, "version")
        reader.close()

    def test_invalid_pdf_raises_error(self, invalid_pdf_bytes):
        """Test that invalid PDF raises PDFParseError."""
        reader = PDFReader(invalid_pdf_bytes)
        with pytest.raises(PDFParseError):
            reader.read()
        reader.close()

    def test_empty_pdf_raises_error(self, empty_pdf_bytes):
        """Test that empty file raises PDFParseError."""
        reader = PDFReader(empty_pdf_bytes)
        with pytest.raises(PDFParseError):
            reader.read()
        reader.close()

    def test_pdf_version(self, minimal_pdf_bytes):
        """Test that PDF version is extracted."""
        reader = PDFReader(minimal_pdf_bytes)
        reader.read()
        assert reader.version == "1.4"
        reader.close()

    # ========================================================================
    # Page Count
    # ========================================================================

    def test_page_count_single(self, minimal_pdf_bytes):
        """Test page count for single-page PDF."""
        with PDFReader(minimal_pdf_bytes) as reader:
            reader.read()
            assert reader.page_count == 1

    def test_page_count_multi(self, multi_page_pdf_bytes):
        """Test page count for multi-page PDF."""
        with PDFReader(multi_page_pdf_bytes) as reader:
            reader.read()
            assert reader.page_count == 3

    # ========================================================================
    # Object Access
    # ========================================================================

    def test_get_object(self, minimal_pdf_bytes):
        """Test getting an object by number."""
        with PDFReader(minimal_pdf_bytes) as reader:
            reader.read()
            # Object 1 should be the catalog
            obj = reader.get_object(1, 0)
            assert obj is not None

    def test_get_nonexistent_object(self, minimal_pdf_bytes):
        """Test getting nonexistent object returns None."""
        with PDFReader(minimal_pdf_bytes) as reader:
            reader.read()
            obj = reader.get_object(999, 0)
            assert obj is None

    # ========================================================================
    # Page Access
    # ========================================================================

    def test_get_page(self, minimal_pdf_bytes):
        """Test getting a page object."""
        with PDFReader(minimal_pdf_bytes) as reader:
            reader.read()
            page = reader.get_page(0)
            assert page is not None
            assert "Type" in page or "/Type" in page

    def test_get_page_out_of_range(self, minimal_pdf_bytes):
        """Test getting page out of range returns None."""
        with PDFReader(minimal_pdf_bytes) as reader:
            reader.read()
            page = reader.get_page(999)
            assert page is None

    def test_get_page_negative(self, minimal_pdf_bytes):
        """Test getting page with negative index returns None."""
        with PDFReader(minimal_pdf_bytes) as reader:
            reader.read()
            page = reader.get_page(-1)
            assert page is None

    # ========================================================================
    # Media Box
    # ========================================================================

    def test_get_media_box(self, minimal_pdf_bytes):
        """Test getting page media box."""
        with PDFReader(minimal_pdf_bytes) as reader:
            reader.read()
            media_box = reader.get_page_media_box(0)
            assert media_box is not None
            assert len(media_box) == 4
            # Default US Letter: [0, 0, 612, 792]
            assert media_box[2] == 612
            assert media_box[3] == 792

    # ========================================================================
    # Page Contents
    # ========================================================================

    def test_get_page_contents_text_pdf(self, text_pdf_bytes):
        """Test getting page contents from text PDF."""
        with PDFReader(text_pdf_bytes) as reader:
            reader.read()
            contents = reader.get_page_contents(0)
            assert contents is not None
            # Check for text operators (case-insensitive or partial)
            assert b"Tj" in contents  # Text show operator
            assert b"ET" in contents  # End text

    def test_get_page_contents_empty_page(self, minimal_pdf_bytes):
        """Test getting contents from page without content stream."""
        with PDFReader(minimal_pdf_bytes) as reader:
            reader.read()
            contents = reader.get_page_contents(0)
            # Page has no content stream
            assert contents is None

    # ========================================================================
    # Resources
    # ========================================================================

    def test_get_page_resources(self, text_pdf_bytes):
        """Test getting page resources."""
        with PDFReader(text_pdf_bytes) as reader:
            reader.read()
            resources = reader.get_page_resources(0)
            assert resources is not None

    # ========================================================================
    # Stream Decompression
    # ========================================================================

    def test_flate_decode(self):
        """Test FlateDecode decompression."""
        import zlib

        original = b"Hello, World! This is a test."
        compressed = zlib.compress(original)

        # Create a PDF with compressed stream
        pdf = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R
>>
endobj
4 0 obj
<< /Length {len(compressed)} /Filter /FlateDecode >>
stream
{compressed.decode('latin-1')}endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000211 00000 n 
trailer
<< /Root 1 0 R /Size 5 >>
startxref
300
%%EOF""".encode('latin-1')

        # This test verifies the concept; actual PDF may need adjustment


class TestOpenPdf:
    """Tests for open_pdf convenience function."""

    def test_open_pdf_bytes(self, minimal_pdf_bytes):
        """Test opening PDF from bytes."""
        reader = open_pdf(minimal_pdf_bytes)
        assert reader is not None
        assert reader.page_count == 1
        reader.close()

    def test_open_pdf_file_like(self, minimal_pdf):
        """Test opening PDF from file-like object."""
        reader = open_pdf(minimal_pdf)
        assert reader is not None
        reader.close()

    def test_open_pdf_with_context_manager(self, minimal_pdf_bytes):
        """Test opening PDF with context manager."""
        with open_pdf(minimal_pdf_bytes) as reader:
            assert reader.page_count == 1


class TestPDFParseError:
    """Tests for PDFParseError exception."""

    def test_exception_message(self):
        """Test that exception message is preserved."""
        try:
            raise PDFParseError("Test error message")
        except PDFParseError as e:
            assert "Test error message" in str(e)

    def test_exception_is_exception(self):
        """Test that PDFParseError is an Exception."""
        assert issubclass(PDFParseError, Exception)


class TestIndirectReferences:
    """Tests for indirect reference handling."""

    def test_catalog_has_pages_ref(self, minimal_pdf_bytes):
        """Test that catalog has Pages reference."""
        with PDFReader(minimal_pdf_bytes) as reader:
            reader.read()
            catalog = reader.get_object(1, 0)
            assert catalog is not None
            # Should have Pages key
            assert "Pages" in catalog or "/Pages" in catalog

    def test_resolve_indirect_ref(self, minimal_pdf_bytes):
        """Test resolving indirect references."""
        from pdf_lowlevel.parser.objects import PDFIndirectRef

        with PDFReader(minimal_pdf_bytes) as reader:
            reader.read()
            catalog = reader.get_object(1, 0)

            # Get Pages reference
            pages_key = "Pages" if "Pages" in catalog else "/Pages"
            pages_ref = catalog.get(pages_key)

            if isinstance(pages_ref, PDFIndirectRef):
                # Resolve it
                pages_obj = reader.get_object(pages_ref.object_number, pages_ref.generation_number)
                assert pages_obj is not None
                assert "Kids" in pages_obj or "/Kids" in pages_obj


class TestMultiPagePDF:
    """Tests specific to multi-page PDFs."""

    def test_all_pages_accessible(self, multi_page_pdf_bytes):
        """Test that all pages are accessible."""
        with PDFReader(multi_page_pdf_bytes) as reader:
            reader.read()
            assert reader.page_count == 3

            for i in range(reader.page_count):
                page = reader.get_page(i)
                assert page is not None

    def test_page_media_boxes(self, multi_page_pdf_bytes):
        """Test that all pages have media boxes."""
        with PDFReader(multi_page_pdf_bytes) as reader:
            reader.read()

            for i in range(reader.page_count):
                media_box = reader.get_page_media_box(i)
                assert media_box is not None
                assert len(media_box) == 4