from dataclasses import dataclass

from pypdf import PdfReader

from . import config


@dataclass
class Chunk:
    text: str
    index: int
    source: str
    page: int


def extract_pdf_text_by_page(path: str) -> list[str]:
    reader = PdfReader(path)
    return [page.extract_text() or "" for page in reader.pages]


def extract_txt_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    step = max(chunk_size - chunk_overlap, 1)
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        start += step
    return chunks


def chunk_pdf(path: str, source: str) -> list[Chunk]:
    pages = extract_pdf_text_by_page(path)
    chunks: list[Chunk] = []
    idx = 0
    for page_num, page_text in enumerate(pages, start=1):
        for piece in split_text(page_text, config.CHUNK_SIZE, config.CHUNK_OVERLAP):
            chunks.append(Chunk(text=piece, index=idx, source=source, page=page_num))
            idx += 1
    return chunks


def chunk_text_file(path: str, source: str) -> list[Chunk]:
    text = extract_txt_text(path)
    chunks: list[Chunk] = []
    for idx, piece in enumerate(split_text(text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)):
        chunks.append(Chunk(text=piece, index=idx, source=source, page=1))
    return chunks


def chunk_file(path: str, source: str) -> list[Chunk]:
    if path.lower().endswith(".pdf"):
        return chunk_pdf(path, source)
    return chunk_text_file(path, source)
