# PDF File Format Basics

Understanding the PDF file format is essential for working with this library. This document covers the fundamental structure of PDF files.

## PDF File Structure

A PDF file consists of four main sections:

```
┌─────────────────────────────────────────┐
│              Header                      │
│  %PDF-1.7                                │
│  %binary junk (optional)                 │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│              Body                        │
│  Indirect objects                        │
│  1 0 obj ... endobj                      │
│  2 0 obj ... endobj                      │
│  ...                                     │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│         Cross-Reference Table            │
│  xref                                    │
│  0 3                                     │
│  0000000000 65535 f                      │
│  0000000015 00000 n                      │
│  0000000074 00000 n                      │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│              Trailer                     │
│  trailer                                 │
│  << /Size 3 /Root 1 0 R >>              │
│  startxref                               │
│  143                                     │
│  %%EOF                                   │
└─────────────────────────────────────────┘
```

## Header

The header identifies the file as PDF and specifies the version:

```
%PDF-1.7
%âãÏÓ  (binary marker to identify as binary file)
```

Common versions:
- PDF 1.4 (Acrobat 5)
- PDF 1.5 (Acrobat 6) - Introduced xref streams
- PDF 1.7 (Acrobat 8) - Current standard
- PDF 2.0 - Latest ISO standard

## Body - Indirect Objects

The body contains **indirect objects**, the fundamental storage units:

```
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
```

Format: `object_number generation_number obj ... endobj`

### Object Types

#### 1. Numbers
```
42        % Integer
3.14      % Real
-5        % Negative
+10       % Positive (rare)
```

#### 2. Strings
```
(Hello World)           % Literal string
<48656C6C6F>           % Hex string
```

Literal strings support escape sequences:
- `\n` - Newline
- `\r` - Carriage return
- `\t` - Tab
- `\b` - Backspace
- `\f` - Form feed
- `\(` `\)` `\\` - Literal parentheses/backslash
- `\ddd` - Octal code

#### 3. Names
```
/Name
/Type
/SomeNameWithSpaces
/#20Name  (escaped space - #20 is hex for space)
```

Names start with `/` and are used as dictionary keys.

#### 4. Booleans
```
true
false
```

#### 5. Null
```
null
```

#### 6. Arrays
```
[1 2 3]
[(Hello) (World)]
[/Name1 /Name2]
```

#### 7. Dictionaries
```
<< /Key1 /Value1
   /Key2 42
   /Key3 [1 2 3]
>>
```

#### 8. Streams
```
5 0 obj
<< /Length 12 >>
stream
Hello World!
endstream
endobj
```

Streams contain binary data (images, content, fonts). They're usually compressed:
```
<< /Length 100 /Filter /FlateDecode >>
```

#### 9. Indirect References
```
1 0 R    % Reference to object 1, generation 0
```

This is how objects link to each other.

## Cross-Reference Table (xref)

The xref table maps object numbers to byte offsets:

```
xref
0 3              % First object number, count
0000000000 65535 f   % Object 0: always free
0000000015 00000 n   % Object 1: at byte 15, generation 0
0000000074 00000 n   % Object 2: at byte 74
```

Format per entry: `nnnnnnnnnn ggggg n|f`
- `n` = 10-digit byte offset
- `g` = 5-digit generation number
- `n` = in-use, `f` = free

### XRef Streams (PDF 1.5+)

Modern PDFs may use xref streams instead of tables:

```
15 0 obj
<< /Type /XRef /Size 3 /W [1 2 1] /Root 1 0 R >>
stream
...binary data...
endstream
endobj
```

## Trailer

The trailer provides key document information:

```
trailer
<< /Size 3           % Number of entries in xref
   /Root 1 0 R       % Reference to catalog
   /Info 4 0 R       % Reference to info dict (optional)
   /Encrypt ...      % Encryption info (optional)
>>
startxref
143                  % Byte offset to xref
%%EOF
```

## Document Structure

### Catalog

The root object (catalog) defines the document structure:

```
1 0 obj
<< /Type /Catalog
   /Pages 2 0 R      % Page tree root
   /Outlines 10 0 R  % Outline/bookmarks (optional)
   /Metadata 11 0 R  % XMP metadata (optional)
>>
endobj
```

### Page Tree

Pages are organized in a tree structure:

```
2 0 obj
<< /Type /Pages
   /Kids [3 0 R 4 0 R 5 0 R]
   /Count 3
>>
endobj

3 0 obj
<< /Type /Page
   /Parent 2 0 R
   /MediaBox [0 0 612 792]
   /Contents 6 0 R
   /Resources << /Font << /F1 7 0 R >> >>
>>
endobj
```

**MediaBox**: Page dimensions `[x0 y0 x1 y1]` in points (1/72 inch)
- US Letter: `[0 0 612 792]`
- A4: `[0 0 595 842]`

### Resources

Page resources define fonts, images, etc.:

```
<< /Font << /F1 7 0 R /F2 8 0 R >>
   /XObject << /Im1 9 0 R >>
   /ColorSpace << ... >>
   /Pattern << ... >>
   /Shading << ... >>
>>
```

### Content Streams

Page content is a stream of operators:

```
6 0 obj
<< /Length 44 >>
stream
BT
/F1 12 Tf
100 700 Td
(Hello World) Tj
ET
endstream
endobj
```

## Incremental Updates

PDFs can be updated incrementally - changes are appended:

```
[Original PDF]
...
%%EOF

[Update 1]
... new objects ...
xref
... updated xref ...
trailer
<< /Size N /Prev offset_of_old_xref >>
startxref
...
%%EOF
```

The `/Prev` chain links to previous xref tables.

## Compression Filters

Streams can be compressed:

| Filter | Description |
|--------|-------------|
| `/FlateDecode` | zlib/deflate (most common) |
| `/LZWDecode` | LZW compression |
| `/ASCII85Decode` | ASCII85 encoding |
| `/ASCIIHexDecode` | ASCII hex encoding |
| `/RunLengthDecode` | RLE compression |
| `/DCTDecode` | JPEG |
| `/CCITTFaxDecode` | Fax/CCITT |
| `/JBIG2Decode` | JBIG2 |
| `/JPXDecode` | JPEG2000 |

Multiple filters are applied in order:
```
<< /Filter [/ASCII85Decode /FlateDecode] >>
```

## Text Encoding

PDF uses several encodings:

1. **Standard encodings**: WinAnsiEncoding, MacRomanEncoding
2. **Custom encodings**: Via /Encoding dictionary
3. **ToUnicode CMap**: Maps glyph IDs to Unicode

Font dictionaries:
```
<< /Type /Font
   /Subtype /Type1
   /BaseFont /Helvetica
   /Encoding /WinAnsiEncoding
   /ToUnicode 10 0 R    % CMap for Unicode mapping
>>
```

## Common Gotchas

1. **Byte offsets must be exact** - Offsets in xref must point to the exact byte
2. **Line endings** - CR, LF, or CRLF are all valid
3. **Name escaping** - Special chars in names use `#XX` hex
4. **String encoding** - Literal strings are not UTF-8 by default
5. **Generation numbers** - Usually 0, increments when objects are updated
6. **Object streams** (PDF 1.5+) - Objects can be inside compressed streams

## Further Reading

- [PDF 1.7 Reference (ISO 32000-1)](https://www.adobe.com/content/dam/acom/en/devnet/pdf/pdfs/PDF32000_2008.pdf)
- [PDF 2.0 (ISO 32000-2)](https://www.iso.org/standard/63534.html)