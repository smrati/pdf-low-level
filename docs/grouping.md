# Text Grouping Algorithms

Text grouping is the process of organizing individual text fragments into lines and blocks based on their spatial positions.

## Overview

**Source:** `src/pdf_lowlevel/content/grouper.py`

PDF content streams often split text into small fragments - sometimes even individual characters. The `TextGrouper` class groups these fragments back into readable text based on spatial proximity.

## The Problem

When a PDF content stream draws text like "Hello World", it might be split into multiple fragments:

```
BT
/F1 12 Tf
100 700 Td
(Hello) Tj
55 0 Td
(World) Tj
ET
```

This produces two separate `TextElement` objects:
- `"Hello"` at (100, 700)
- `"World"` at (155, 700)

The grouper combines these into a single line: `"Hello World"`

## Usage

### Basic Usage

```python
from pdf_lowlevel.content.grouper import TextGrouper, group_text_elements

# Using the class
grouper = TextGrouper(
    elements,
    grouping_mode="cluster",
    y_tolerance=5.0,
)
lines = grouper.group_into_lines()
blocks = grouper.group_into_blocks()

# Convenience function
lines = group_text_elements(elements, y_tolerance=5.0)
```

### Within PDFExtractor

```python
from pdf_lowlevel import PDFExtractor

with PDFExtractor("document.pdf") as extractor:
    result = extractor.extract(
        grouping_mode="cluster",
        y_tolerance=5.0,
        x_tolerance=5.0,
        space_width=3.0,
        line_gap_threshold=1.5,
    )
```

## Grouping Algorithms

### Tolerance Mode (Quantization)

```python
grouper = TextGrouper(elements, grouping_mode="tolerance", y_tolerance=5.0)
```

**How it works:**
1. Quantize Y coordinates to buckets: `y_key = round(y / tolerance) * tolerance`
2. Group all elements with the same `y_key`
3. Sort groups top-to-bottom
4. Within each group, sort left-to-right

**Example:**
```
Element A: y = 700.2  → y_key = 700
Element B: y = 702.8  → y_key = 700  (same bucket!)
Element C: y = 699.9  → y_key = 700  (same bucket!)
Element D: y = 710.0  → y_key = 710  (different line)
```

**Pros:**
- Fast O(n) grouping
- Simple to understand

**Cons:**
- May misorder characters near bucket boundaries
- Example: y=697.49 → 695, but y=697.51 → 700

### Cluster Mode (Nearest-Neighbor)

```python
grouper = TextGrouper(elements, grouping_mode="cluster", y_tolerance=5.0)
```

**How it works:**
1. Sort elements by Y (descending, top-to-bottom)
2. For each element, find a cluster where `|elem.y - cluster_y| <= tolerance`
3. If found, add to cluster and update `cluster_y` to average
4. If not found, create new cluster

**Example:**
```
Elements sorted by Y: [710, 702, 700, 699, 650]

1. y=710: No clusters → create cluster A (y=710)
2. y=702: |702-710|=8 > 5 → create cluster B (y=702)
3. y=700: |700-702|=2 ≤ 5 → join cluster B (avg y=701)
4. y=699: |699-701|=2 ≤ 5 → join cluster B (avg y=700.33)
5. y=650: |650-700|=50 > 5 → create cluster C (y=650)

Result: 3 lines at y=710, y=700.33, y=650
```

**Pros:**
- Handles variable Y positions better
- No boundary artifacts
- More accurate for generated PDFs with sub-pixel variations

**Cons:**
- Slightly slower O(n²) worst case (usually O(n log n) with sorting)

## Configuration Parameters

### y_tolerance

Vertical tolerance for grouping into lines (in points).

```python
grouper = TextGrouper(elements, y_tolerance=5.0)
```

- **Smaller** (e.g., 2.0): More lines, stricter grouping
- **Larger** (e.g., 10.0): Fewer lines, more aggressive grouping

Choose based on:
- Font size (larger fonts need larger tolerance)
- PDF quality (generated PDFs may need larger tolerance)

### x_tolerance

Horizontal tolerance for merging overlapping fragments.

```python
grouper = TextGrouper(elements, x_tolerance=5.0)
```

Used to detect when fragments overlap or are very close (kerning).

### space_width

Minimum gap to insert a space between fragments.

```python
grouper = TextGrouper(elements, space_width=3.0)
```

When the gap between two fragments exceeds this value, a space is inserted.

**Example:**
```
Fragment 1: "Hello" at x=100, width=30 (ends at x=130)
Fragment 2: "World" at x=145

Gap = 145 - 130 = 15 points

If space_width=3.0: gap(15) > 3 → insert space → "Hello World"
If space_width=20: gap(15) < 20 → no space → "HelloWorld"
```

### line_gap_threshold

Multiplier for detecting paragraph breaks.

```python
grouper = TextGrouper(elements, line_gap_threshold=1.5)
```

If the gap between lines exceeds `avg_line_height * threshold`, a new paragraph is started.

**Example:**
```
Line 1 at y=700
Line 2 at y=680  (gap=20)
Line 3 at y=660  (gap=20)
Line 4 at y=620  (gap=40)

avg_line_height ≈ 20
threshold = 1.5
break_threshold = 20 * 1.5 = 30

Gap between Line 3 and Line 4 is 40 > 30 → paragraph break
```

## Data Structures

### TextLine

```python
@dataclass
class TextLine:
    text: str              # Merged text content
    y: float               # Y coordinate of the line
    x_start: float         # Leftmost X coordinate
    x_end: float           # Rightmost X coordinate
    fragments: List[dict]  # Original fragments
```

### TextBlock

```python
@dataclass
class TextBlock:
    lines: List[TextLine]  # Lines in this block
    x_start: float         # Block bounds
    x_end: float
    y_start: float
    y_end: float
    
    @property
    def text(self) -> str:
        return "\n".join(line.text for line in self.lines)
```

## Algorithm Details

### Line Creation

```python
def _create_line_from_group(self, group, y_coord):
    # 1. Sort elements by X (left to right)
    sorted_elems = sorted(group, key=lambda e: e.x)
    
    # 2. Merge fragments, adding spaces where needed
    text_parts = []
    prev_x_end = None
    
    for elem in sorted_elems:
        if prev_x_end is not None:
            gap = elem.x - prev_x_end
            if gap > self.space_width:
                text_parts.append(" ")
        
        text_parts.append(elem.text)
        prev_x_end = elem.x + elem.width
    
    return TextLine(text="".join(text_parts), ...)
```

### Block Detection

```python
def group_into_blocks(self):
    lines = self.group_into_lines()
    blocks = []
    current_block = TextBlock()
    avg_line_height = None
    
    for line in lines:
        if prev_y is not None:
            gap = prev_y - line.y
            
            # Update running average
            if avg_line_height is None:
                avg_line_height = gap
            else:
                avg_line_height = 0.9 * avg_line_height + 0.1 * gap
            
            # Check for paragraph break
            if gap > avg_line_height * self.line_gap_threshold:
                blocks.append(current_block)
                current_block = TextBlock()
        
        current_block.lines.append(line)
    
    return blocks
```

## Choosing an Algorithm

| Scenario | Recommended Mode | Tolerance |
|----------|-----------------|-----------|
| Well-formed PDFs | tolerance | 3-5 points |
| Generated PDFs | cluster | 5-10 points |
| Scanned/OCR PDFs | cluster | 10-15 points |
| Multi-column layouts | cluster | 3-5 points |
| Tables | tolerance | 2-3 points |

## Common Issues

### 1. Text on Same Line Split

**Symptom:** "Hello World" becomes two lines

**Solution:** Increase `y_tolerance`

```python
grouper = TextGrouper(elements, y_tolerance=10.0)
```

### 2. Different Lines Merged

**Symptom:** Lines that should be separate are combined

**Solution:** Decrease `y_tolerance`

```python
grouper = TextGrouper(elements, y_tolerance=2.0)
```

### 3. Missing Spaces

**Symptom:** "HelloWorld" instead of "Hello World"

**Solution:** Decrease `space_width`

```python
grouper = TextGrouper(elements, space_width=1.0)
```

### 4. Extra Spaces

**Symptom:** "H e l l o" with spaces between letters

**Solution:** Increase `space_width`

```python
grouper = TextGrouper(elements, space_width=5.0)
```

## Testing

The text grouper is tested via `test_extractor.py`:

```bash
uv run pytest tests/test_extractor.py -v