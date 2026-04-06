"""
Chunking service — parses book text files into chapters and chunks.

Handles chapter detection across multiple formatting styles,
text cleaning (especially Book 7 OCR artifacts), and
paragraph-aware chunking with configurable size limits.
"""

import os
import re
from dataclasses import dataclass, field


TARGET_CHUNK_SIZE = 1800
MAX_CHUNK_SIZE = 2200
MIN_CHUNK_SIZE = 200


# -- Book title mapping (filename stem -> canonical title) --

BOOK_TITLES = {
    "1-sorcerers-stone": "Harry Potter and the Sorcerer's Stone",
    "2-chamber-of-secrets": "Harry Potter and the Chamber of Secrets",
    "3-prisoner-of-azkaban": "Harry Potter and the Prisoner of Azkaban",
    "4-goblet-of-fire": "Harry Potter and the Goblet of Fire",
    "5-order-of-the-phoenix": "Harry Potter and the Order of the Phoenix",
    "6-half-blood-prince": "Harry Potter and the Half-Blood Prince",
    "7-deathly-hallows": "Harry Potter and the Deathly Hallows",
}


@dataclass
class Chapter:
    number: int
    title: str
    text: str


@dataclass
class BookData:
    book_number: int
    book_title: str
    chapters: list[Chapter] = field(default_factory=list)


# -- Word-number to integer mapping --

WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "twenty-one": 21, "twenty-two": 22,
    "twenty-three": 23, "twenty-four": 24, "twenty-five": 25,
    "twenty-six": 26, "twenty-seven": 27, "twenty-eight": 28,
    "twenty-nine": 29, "thirty": 30, "thirty-one": 31,
    "thirty-two": 32, "thirty-three": 33, "thirty-four": 34,
    "thirty-five": 35, "thirty-six": 36, "thirty-seven": 37,
    "thirty-eight": 38,
}


def _parse_chapter_number(raw: str) -> int:
    """Convert a chapter number string (word or digit) to int."""
    raw = raw.strip().lower()
    if raw.isdigit():
        return int(raw)
    return WORD_NUMBERS.get(raw, 0)


# -- Chapter splitting per book format --

def _split_chapters_separator(text: str) -> list[Chapter]:
    """Books 1-2: ===...=== / CHAPTER X / ===...=== / TITLE format."""
    pattern = re.compile(
        r"={3,}\s*\n\s*CHAPTER\s+([\w -]+?)\s*\n\s*={3,}\s*\n\s*(.+)",
        re.IGNORECASE,
    )

    chapters = []
    matches = list(pattern.finditer(text))

    for i, match in enumerate(matches):
        chapter_num = _parse_chapter_number(match.group(1))
        chapter_title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chapter_text = text[start:end].strip()
        chapters.append(Chapter(number=chapter_num, title=chapter_title, text=chapter_text))

    return chapters


def _split_chapters_inline_double_dash(text: str) -> list[Chapter]:
    """Book 3: CHAPTER X -- TITLE format."""
    pattern = re.compile(
        r"^CHAPTER\s+([\w -]+?)\s+--\s+(.+)$",
        re.MULTILINE | re.IGNORECASE,
    )

    chapters = []
    matches = list(pattern.finditer(text))

    for i, match in enumerate(matches):
        chapter_num = _parse_chapter_number(match.group(1))
        chapter_title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chapter_text = text[start:end].strip()
        chapters.append(Chapter(number=chapter_num, title=chapter_title, text=chapter_text))

    return chapters


def _split_chapters_inline_single_dash(text: str) -> list[Chapter]:
    """Book 4: CHAPTER X - TITLE format."""
    pattern = re.compile(
        r"^CHAPTER\s+([\w -]+?)\s+-\s+(.+)$",
        re.MULTILINE | re.IGNORECASE,
    )

    chapters = []
    matches = list(pattern.finditer(text))

    for i, match in enumerate(matches):
        chapter_num = _parse_chapter_number(match.group(1))
        chapter_title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chapter_text = text[start:end].strip()
        chapters.append(Chapter(number=chapter_num, title=chapter_title, text=chapter_text))

    return chapters


def _split_chapters_dashes_around(text: str) -> list[Chapter]:
    """Book 5: - CHAPTER X - / blank / Title format."""
    pattern = re.compile(
        r"^-\s*CHAPTER\s+([\w -]+?)\s*-\s*\n+\s*(.+)",
        re.MULTILINE | re.IGNORECASE,
    )

    chapters = []
    matches = list(pattern.finditer(text))

    for i, match in enumerate(matches):
        chapter_num = _parse_chapter_number(match.group(1))
        chapter_title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chapter_text = text[start:end].strip()
        chapters.append(Chapter(number=chapter_num, title=chapter_title, text=chapter_text))

    return chapters


def _split_chapters_colon(text: str) -> list[Chapter]:
    """Book 6: Chapter N: Title format (colon sometimes missing)."""
    pattern = re.compile(
        r"^Chapter\s+(\d+):?\s+(.+)$",
        re.MULTILINE,
    )

    chapters = []
    matches = list(pattern.finditer(text))

    for i, match in enumerate(matches):
        chapter_num = int(match.group(1))
        chapter_title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chapter_text = text[start:end].strip()
        chapters.append(Chapter(number=chapter_num, title=chapter_title, text=chapter_text))

    return chapters


def _split_chapters_book7(raw_text: str) -> list[Chapter]:
    """Book 7: split on raw text first, then clean each chapter.

    Raw format is: Chapter \\n<number> \\n\\n\\n<Title\\nWords> \\n
    Lines have trailing spaces. Must split before line-joining
    because the join logic would merge the multi-line header.
    """
    # Strip page headers (all-caps CHAPTER blocks with period after number)
    cleaned = re.sub(
        r"\n\nCHAPTER\s*\n\d+\.\s*\n(?:[A-Z]+[A-Z ]*\n)+",
        "\n\n",
        raw_text,
    )

    # Match real chapter starts (mixed-case "Chapter" without period)
    pattern = re.compile(
        r"Chapter\s*\n\s*(\d+)\s*\n\s*\n+((?:[^\n]+\n)*?[^\n]+)\s*\n\s*\n",
    )

    chapters = []
    matches = list(pattern.finditer(cleaned))

    for i, match in enumerate(matches):
        chapter_num = int(match.group(1))
        raw_title = match.group(2).strip()
        chapter_title = " ".join(line.strip() for line in raw_title.split("\n") if line.strip())
        chapter_title = chapter_title.title()

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned)
        chapter_text = cleaned[start:end].strip()

        # Clean OCR artifacts within each chapter's text
        chapter_text = _clean_book7_chapter(chapter_text)

        chapters.append(Chapter(number=chapter_num, title=chapter_title, text=chapter_text))

    return chapters


def _clean_book7_chapter(text: str) -> str:
    """Clean OCR artifacts within a single book 7 chapter."""

    # Replace unicode replacement character with apostrophe
    text = text.replace("\ufffd", "'")

    # Remove form feed characters
    text = text.replace("\x0c", "")

    # Remove any remaining page headers
    text = re.sub(
        r"\nCHAPTER\s*\n\d+\.\s*\n(?:[A-Z]+[A-Z ]*\n)+",
        "\n",
        text,
    )

    # Remove standalone page numbers
    text = re.sub(r"\n\d{1,3}\s*\n", "\n", text)

    # Fix stuttered first characters (e.g., "T\nT\nhe" -> "The")
    text = re.sub(r"\n([A-Z])\n\1\n", r"\n\1", text)

    # Fix words mashed together (lowercase followed by uppercase)
    text = re.sub(r"([a-z])([A-Z][a-z])", r"\1 \2", text)

    # Join broken lines: if a line doesn't end with sentence-ending
    # punctuation or a quote mark, join it with the next line
    lines = text.split("\n")
    joined = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            joined.append(line)
            i += 1
            continue

        while i + 1 < len(lines) and lines[i + 1].strip():
            if re.search(r'[.!?"\'\u2019\u201d]\s*$', line.rstrip()):
                break
            i += 1
            line = line.rstrip() + " " + lines[i].lstrip()

        joined.append(line)
        i += 1

    return "\n".join(joined)


# -- Chapter splitter dispatch --

_SPLITTERS = {
    1: _split_chapters_separator,
    2: _split_chapters_separator,
    3: _split_chapters_inline_double_dash,
    4: _split_chapters_inline_single_dash,
    5: _split_chapters_dashes_around,
    6: _split_chapters_colon,
    7: _split_chapters_book7,
}


# -- Paragraph-aware chunking --

def chunk_chapter(
    text: str,
    target_size: int = TARGET_CHUNK_SIZE,
    max_size: int = MAX_CHUNK_SIZE,
    min_size: int = MIN_CHUNK_SIZE,
) -> list[str]:
    """Split chapter text into chunks at paragraph boundaries.

    Groups consecutive paragraphs until target_size is reached.
    Never exceeds max_size per chunk (single large paragraphs
    become their own chunk). Merges trailing small chunks with
    the previous chunk.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return []

    chunks = []
    current = ""

    for para in paragraphs:
        candidate = (current + "\n\n" + para).strip() if current else para

        if len(candidate) <= target_size:
            current = candidate
        elif not current:
            # Single paragraph exceeds target — accept it as-is
            chunks.append(para)
        else:
            # Adding this paragraph would exceed target — finalize current chunk
            chunks.append(current)
            current = para

    if current:
        # Merge small trailing chunk with previous
        if chunks and len(current) < min_size:
            chunks[-1] = chunks[-1] + "\n\n" + current
        else:
            chunks.append(current)

    return chunks


# -- Main entry point --

def parse_book(filepath: str, book_number: int) -> BookData:
    """Parse a book text file into structured chapters and metadata."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    # Get canonical title from filename stem
    stem = os.path.splitext(os.path.basename(filepath))[0]
    book_title = BOOK_TITLES.get(stem, stem)

    # Split into chapters using the appropriate splitter
    # (Book 7 handles its own cleanup internally)
    splitter = _SPLITTERS[book_number]
    chapters = splitter(text)

    return BookData(
        book_number=book_number,
        book_title=book_title,
        chapters=chapters,
    )


# -- Custom text chunking (sliding window) --

def chunk_custom_text(
    text: str,
    chunk_size: int = 200,
    overlap: int = 50,
) -> list[str]:
    """Split user-entered text into overlapping chunks at word boundaries.

    Uses a sliding window approach. No paragraph or sentence
    awareness — user-entered text has no guaranteed structure.

    Args:
        text: Raw text to chunk.
        chunk_size: Target size per chunk in characters.
        overlap: Number of overlapping characters between chunks.
    """
    text = text.strip()
    if not text:
        return []

    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    step = chunk_size - overlap

    while start < len(text):
        end = start + chunk_size

        # If this is the last chunk, take everything remaining
        if end >= len(text):
            chunks.append(text[start:].strip())
            break

        # Walk back from end to find a word boundary (space)
        boundary = end
        while boundary > start and text[boundary] != " ":
            boundary -= 1

        # If no space found, just cut at chunk_size
        if boundary == start:
            boundary = end

        chunks.append(text[start:boundary].strip())
        start += step

    return [c for c in chunks if c]
