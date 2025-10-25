"""Utilities for working with YouTube videos and captions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List
import logging
import re

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled


logger = logging.getLogger(__name__)


_VIDEO_ID_RE = re.compile(r"(?:v=|youtu\.be/|youtube\.com/embed/)([\w-]{11})")


@dataclass
class VideoTranscript:
    """Container for a transcript and metadata."""

    video_id: str
    title: str
    text: str


def extract_video_id(url: str) -> str:
    """Extract the video identifier from a YouTube url."""
    match = _VIDEO_ID_RE.search(url)
    if not match:
        raise ValueError(f"Could not determine video id for url: {url}")
    return match.group(1)


def download_transcript(video_id: str, languages: Iterable[str] | None = None) -> str:
    """Download transcript text for the supplied video."""
    languages = list(languages or ("tr", "en"))
    try:
        segments = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
    except TranscriptsDisabled as exc:  # pragma: no cover - network failure case
        raise RuntimeError(f"Transcripts disabled for video {video_id}") from exc
    combined = " ".join(entry["text"].strip() for entry in segments if entry["text"].strip())
    return combined


def gather_transcripts(urls: Iterable[str]) -> List[VideoTranscript]:
    """Collect transcripts for each supplied URL."""
    transcripts: List[VideoTranscript] = []
    for url in urls:
        video_id = extract_video_id(url)
        text = download_transcript(video_id)
        transcripts.append(VideoTranscript(video_id=video_id, title=video_id, text=text))
        logger.info("Downloaded transcript for %s", video_id)
    return transcripts
