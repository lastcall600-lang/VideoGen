"""Pexels API integration for stock video retrieval."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import logging
import requests

from .config import ensure_directory


logger = logging.getLogger(__name__)


PEXELS_SEARCH_URL = "https://api.pexels.com/videos/search"


@dataclass
class PexelsVideo:
    """Representation of a downloaded Pexels video."""

    title: str
    filepath: Path
    duration: float


class PexelsClient:
    """Simple wrapper around the Pexels API."""

    def __init__(self, api_key: str, download_dir: Path) -> None:
        self.api_key = api_key
        self.download_dir = ensure_directory(download_dir)

    def search_video(self, query: str, min_duration: int = 5, max_duration: int = 90) -> Optional[dict]:
        headers = {"Authorization": self.api_key}
        params = {"query": query, "per_page": 1, "orientation": "landscape"}
        response = requests.get(PEXELS_SEARCH_URL, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        for video in data.get("videos", []):
            duration = video.get("duration") or 0
            if min_duration <= duration <= max_duration:
                return video
        return None

    def download_video(self, video: dict, filename_hint: str) -> PexelsVideo:
        video_files = video.get("video_files", [])
        if not video_files:
            raise ValueError("Video has no downloadable files")
        # Choose the highest resolution file with reasonable size
        chosen = max(video_files, key=lambda item: item.get("width", 0))
        url = chosen["link"]
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        safe_name = "_".join(filename_hint.lower().split()) or "segment"
        filepath = self.download_dir / f"{safe_name}.mp4"
        with open(filepath, "wb") as file:
            file.write(response.content)
        logger.info("Downloaded Pexels video to %s", filepath)
        return PexelsVideo(title=video.get("url", "Pexels Video"), filepath=filepath, duration=video.get("duration", 0.0))

    def search_and_download(self, query: str) -> Optional[PexelsVideo]:
        video = self.search_video(query)
        if not video:
            logger.warning("No Pexels video found for query '%s'", query)
            return None
        return self.download_video(video, query)
