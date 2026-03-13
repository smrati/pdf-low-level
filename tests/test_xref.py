"""
Unit tests for PDF cross-reference table parsing.

Tests xref table parsing including:
- Traditional xref tables
- Trailer dictionary parsing
- Indirect reference handling
- XRefEntry and XRefTable classes
"""

import pytest
from io import BytesIO

from pdf_lowlevel.parser.xref import (
    IndirectRef,
    XRefEntry,
    XRefTable,
    XRefParser,
    find_xref_offset,
    parse_xref,
)


class TestIndirectRef:
    """Tests for IndirectRef dataclass."""

    def test_create_indirect_ref(self):
        """Test creating an indirect reference."""
        ref = IndirectRef(1, 0)
        assert ref.object_number == 1
        assert ref.generation_number == 0

    def test_indirect_ref_repr(self):
        """Test string representation of indirect reference."""
        ref = IndirectRef(5, 2)
        repr_str = repr(ref)
        assert "5" in repr_str
        assert "2" in repr_str


class TestXRefEntry:
    """Tests for XRefEntry dataclass."""

    def test_create_entry_defaults(self):
        """Test creating xref entry with defaults."""
        entry = XRefEntry()
        assert entry.offset == 0
        assert entry.generation == 0
        assert entry.free == False
        assert entry.entry_type == 1

    def test_create_entry_in_use(self):
        """Test creating in-use entry."""
        entry = XRefEntry(offset=1234, generation=0, free=False)
        assert entry.offset == 1234
        assert entry.free == False
        assert entry.entry_type == 1

    def test_create_entry_free(self):
        """Test creating free entry."""
        entry = XRefEntry(offset=0, generation=65535, free=True, entry_type=0)
        assert entry.free == True
        assert entry.entry_type == 0

    def test_create_compressed_entry(self):
        """Test creating compressed object stream entry."""
        entry = XRefEntry(
            object_stream_num=10,
            index_in_stream=5,
            entry_type=2
        )
        assert entry.entry_type == 2
        assert entry.object_stream_num == 10


class TestXRefTable:
    """Tests for XRefTable class."""

    def test_empty_table(self):
        """Test empty xref table."""
        table = XRefTable()
        assert len(table.entries) == 0
        assert table.get_offset(1) is None

    def test_add_and_get_entry(self):
        """Test adding and retrieving entries."""
        table = XRefTable()
        entry = XRefEntry(offset=100, generation=0)
        table.add_entry(1, entry)

        assert table.get_offset(1) == 100
        assert table.get_entry(1) == entry

    def test_get_offset_free_entry(self):
        """Test that free entries return None."""
        table = XRefTable()
        entry = XRefEntry(offset=0, free=True, entry_type=0)
        table.add_entry(0, entry)

        assert table.get_offset(0) is None

    def test_get_root_ref(self):
        """Test getting root catalog reference."""
        table = XRefTable()
        table.trailer["Root"] = IndirectRef(1, 0)

        root_ref = table.get_root_ref()
        assert root_ref == (1, 0)

    def test_get_root_ref_missing(self):
        """Test getting root reference when missing."""
        table = XRefTable()
        assert table.get_root_ref() is None

    def test_get_info_ref(self):
        """Test getting info dictionary reference."""
        table = XRefTable()
        table.trailer["Info"] = IndirectRef(4, 0)

        info_ref = table.get_info_ref()
        assert info_ref == (4, 0)

    def test_get_size(self):
        """Test getting size from trailer."""
        table = XRefTable()
        table.trailer["Size"] = 10

        assert table.get_size() == 10

    def test_get_size_default(self):
        """Test getting size when not set."""
        table = XRefTable()
        assert table.get_size() == 0


class TestFindXRefOffset:
    """Tests for find_xref_offset function."""

    def test_find_xref_offset_simple(self, minimal_pdf_bytes):
        """Test finding xref offset in simple PDF."""
        file_obj = BytesIO(minimal_pdf_bytes)
        offset = find_xref_offset(file_obj)
        assert offset > 0

    def test_find_xref_offset_multi_page(self, multi_page_pdf_bytes):
        """Test finding xref offset in multi-page PDF."""
        file_obj = BytesIO(multi_page_pdf_bytes)
        offset = find_xref_offset(file_obj)
        assert offset > 0

    def test_find_xref_offset_no_startxref(self):
        """Test error when startxref is missing."""
        file_obj = BytesIO(b"%PDF-1.4\n%EOF")
        with pytest.raises(ValueError, match="startxref"):
            find_xref_offset(file_obj)


class TestXRefParser:
    """Tests for XRefParser class."""

    def test_parse_minimal_pdf(self, minimal_pdf):
        """Test parsing xref from minimal PDF."""
        # Find xref offset first
        minimal_pdf.seek(0)
        offset = find_xref_offset(minimal_pdf)
        minimal_pdf.seek(offset)

        parser = XRefParser(minimal_pdf)
        table = parser.parse()

        assert table is not None
        assert len(table.entries) > 0

    def test_parse_trailer_root_ref(self, minimal_pdf):
        """Test that trailer has Root reference."""
        minimal_pdf.seek(0)
        offset = find_xref_offset(minimal_pdf)
        minimal_pdf.seek(offset)

        parser = XRefParser(minimal_pdf)
        table = parser.parse()

        root_ref = table.get_root_ref()
        assert root_ref is not None
        assert isinstance(root_ref, tuple)
        assert len(root_ref) == 2

    def test_parse_indirect_ref_in_trailer(self, indirect_ref_pdf):
        """Test parsing indirect references in trailer (regression test)."""
        indirect_ref_pdf.seek(0)
        offset = find_xref_offset(indirect_ref_pdf)
        indirect_ref_pdf.seek(offset)

        parser = XRefParser(indirect_ref_pdf)
        table = parser.parse()

        # This was the bug: Root was being stored as int instead of IndirectRef
        root_ref = table.get_root_ref()
        assert root_ref is not None
        assert isinstance(root_ref, tuple)
        assert root_ref[0] == 1  # object number
        assert root_ref[1] == 0  # generation number

        # Also check Info reference
        info_ref = table.get_info_ref()
        assert info_ref is not None
        assert info_ref[0] == 4  # object number
        assert info_ref[1] == 0  # generation number

    def test_parse_entries_offsets(self, minimal_pdf):
        """Test that entry offsets are parsed correctly."""
        minimal_pdf.seek(0)
        offset = find_xref_offset(minimal_pdf)
        minimal_pdf.seek(offset)

        parser = XRefParser(minimal_pdf)
        table = parser.parse()

        # Object 1 should have an offset
        entry = table.get_entry(1)
        assert entry is not None
        assert entry.offset > 0
        assert entry.free == False


class TestParseXref:
    """Tests for parse_xref convenience function."""

    def test_parse_xref_minimal(self, minimal_pdf):
        """Test parse_xref with minimal PDF."""
        minimal_pdf.seek(0)
        table = parse_xref(minimal_pdf)
        assert table is not None
        assert len(table.entries) > 0

    def test_parse_xref_text_pdf(self, text_pdf):
        """Test parse_xref with text PDF."""
        text_pdf.seek(0)
        table = parse_xref(text_pdf)
        assert table is not None


class TestIndirectRefParsing:
    """Regression tests for IndirectRef parsing bug."""

    def test_root_is_indirect_ref(self, minimal_pdf):
        """Test that Root in trailer is parsed as IndirectRef, not int."""
        minimal_pdf.seek(0)
        table = parse_xref(minimal_pdf)

        root = table.trailer.get("Root")
        assert isinstance(root, IndirectRef), f"Root should be IndirectRef, got {type(root)}"

    def test_info_is_indirect_ref(self, indirect_ref_pdf):
        """Test that Info in trailer is parsed as IndirectRef."""
        indirect_ref_pdf.seek(0)
        table = parse_xref(indirect_ref_pdf)

        info = table.trailer.get("Info")
        assert isinstance(info, IndirectRef), f"Info should be IndirectRef, got {type(info)}"

    def test_multiple_indirect_refs(self, indirect_ref_pdf):
        """Test parsing multiple indirect references in trailer."""
        indirect_ref_pdf.seek(0)
        table = parse_xref(indirect_ref_pdf)

        # Both Root and Info should be IndirectRef
        root = table.trailer.get("Root")
        info = table.trailer.get("Info")

        assert isinstance(root, IndirectRef)
        assert isinstance(info, IndirectRef)
        assert root.object_number == 1
        assert info.object_number == 4