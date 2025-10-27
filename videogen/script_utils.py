"""Utilities for building segment plans from plain text scripts."""
from __future__ import annotations

from collections import Counter
from typing import List
import re

from .openai_utils import SegmentPlan


_STOPWORDS = {
    "and",
    "the",
    "for",
    "with",
    "that",
    "from",
    "this",
    "have",
    "your",
    "into",
    "about",
    "when",
    "where",
    "while",
    "then",
    "over",
    "such",
    "very",
    "just",
    "because",
    "however",
    "also",
    "like",
    "but",
    "are",
    "was",
    "were",
    "you",
    "they",
    "them",
    "our",
    "their",
    "not",
    "bir",
    "ile",
    "ama",
    "gibi",
    "ve",
    "de",
    "da",
    "bu",
    "olan",
    "kadar",
    "çok",
    "daha",
    "için",
    "icin",
    "henüz",
}


def _clean_sentence(text: str) -> str:
    sentence = text.strip().replace("\n", " ")
    return re.sub(r"\s+", " ", sentence)


def _extract_summary(text: str) -> str:
    cleaned = _clean_sentence(text)
    for delimiter in [".", "!", "?"]:
        index = cleaned.find(delimiter)
        if index != -1:
            return cleaned[: index + 1]
    return cleaned[:200]


def _keyword_candidates(text: str) -> List[str]:
    words = re.findall(r"[\wçğıöşüÇĞİÖŞÜ]+", text.lower())
    return [word for word in words if len(word) > 2 and word not in _STOPWORDS]


def _extract_keywords(text: str, limit: int = 5) -> List[str]:
    candidates = _keyword_candidates(text)
    if not candidates:
        return []
    counts = Counter(candidates)
    return [word for word, _ in counts.most_common(limit)]


def _title_from_text(text: str, fallback_index: int) -> str:
    cleaned = _clean_sentence(text)
    if not cleaned:
        return f"Segment {fallback_index}"
    words = cleaned.split()
    snippet = " ".join(words[:6]).strip()
    return snippet if snippet else f"Segment {fallback_index}"


def build_plans_from_script(script_text: str) -> List[SegmentPlan]:
    """Create a list of :class:`SegmentPlan` objects from raw script text."""

    chunks = [chunk.strip() for chunk in re.split(r"\n{2,}", script_text) if chunk.strip()]
    if not chunks:
        return []

    plans: List[SegmentPlan] = []
    for index, chunk in enumerate(chunks, start=1):
        summary = _extract_summary(chunk)
        keywords = _extract_keywords(chunk)
        title = _title_from_text(summary, index)
        plans.append(
            SegmentPlan(
                title=title,
                summary=summary,
                script=_clean_sentence(chunk),
                keywords=keywords,
            )
        )
    return plans

