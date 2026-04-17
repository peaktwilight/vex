"""Naive substring + token-overlap retriever.

Intentionally crude: no embeddings, no vector store, no dependencies beyond
the standard library. Replace with a real RAG pipeline (`sentence-transformers`
+ `chromadb`, or `bm25s`) without touching `agent.py`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parents[2] / "docs"
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]+")
MIN_TOKEN_LEN = 3
# Hand-rolled stoplist so ultra-common terms don't dominate scoring. Good
# enough for a 5-doc tutorial corpus; swap for real IDF when you grow out of it.
STOPWORDS = frozenset(
    "the and for with that this from into are was were has have had its vex".split()
)
FILENAME_BONUS = 3.0


@dataclass(frozen=True)
class Hit:
    doc: str
    score: float
    text: str


def _tokenize(text: str) -> list[str]:
    return [
        m.group(0).lower()
        for m in TOKEN_RE.finditer(text)
        if len(m.group(0)) >= MIN_TOKEN_LEN and m.group(0).lower() not in STOPWORDS
    ]


def _chunk_paragraphs(text: str) -> list[str]:
    raw = [block.strip() for block in re.split(r"\n\s*\n", text)]
    return [block for block in raw if block]


def _score(tokens: list[str], chunk: str, doc_stem: str) -> float:
    chunk_lower = chunk.lower()
    doc_lower = doc_stem.lower()
    score = 0.0
    for token in tokens:
        score += chunk_lower.count(token)
        if token in doc_lower:
            score += FILENAME_BONUS
    return score


def search(query: str, k: int = 3) -> list[Hit]:
    """Return up to k highest-scoring chunks across the docs corpus."""
    tokens = _tokenize(query)
    if not tokens:
        return []
    hits: list[Hit] = []
    for md in sorted(DOCS_DIR.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        for chunk in _chunk_paragraphs(text):
            s = _score(tokens, chunk, md.stem)
            if s > 0:
                hits.append(Hit(doc=md.name, score=s, text=chunk))
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:k]


def format_hits(hits: list[Hit]) -> str:
    if not hits:
        return "NO_RESULTS"
    return "\n\n".join(
        f"[{hit.doc} score={hit.score:.1f}]\n{hit.text}" for hit in hits
    )
