"""Configuration helpers for the VideoGen project."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass
class VideoGenConfig:
    """Container for API keys and project level paths."""

    openai_api_key: str
    pexels_api_key: str
    youtube_client_secret: Path
    output_dir: Path
    working_dir: Path
    openai_model: str = "gpt-4o-mini"
    openai_tts_model: str = "gpt-4o-mini-tts"
    openai_tts_voice: str = "alloy"

    @classmethod
    def from_environment(cls) -> "VideoGenConfig":
        """Build configuration from environment variables."""
        openai_key = os.environ.get("OPENAI_API_KEY")
        pexels_key = os.environ.get("PEXELS_API_KEY")
        client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET")
        output_dir = Path(os.environ.get("VIDEOGEN_OUTPUT_DIR", "output"))
        working_dir = Path(os.environ.get("VIDEOGEN_WORKING_DIR", "working"))
        if not openai_key:
            raise EnvironmentError("OPENAI_API_KEY must be set")
        if not pexels_key:
            raise EnvironmentError("PEXELS_API_KEY must be set")
        if not client_secret:
            raise EnvironmentError("YOUTUBE_CLIENT_SECRET must be set")

        output_dir.mkdir(parents=True, exist_ok=True)
        working_dir.mkdir(parents=True, exist_ok=True)

        return cls(
            openai_api_key=openai_key,
            pexels_api_key=pexels_key,
            youtube_client_secret=Path(client_secret),
            output_dir=output_dir,
            working_dir=working_dir,
            openai_model=os.environ.get("VIDEOGEN_OPENAI_MODEL", "gpt-4o-mini"),
            openai_tts_model=os.environ.get("VIDEOGEN_OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
            openai_tts_voice=os.environ.get("VIDEOGEN_OPENAI_TTS_VOICE", "alloy"),
        )


def ensure_directory(path: Path) -> Path:
    """Ensure that the directory for the given path exists."""
    path.mkdir(parents=True, exist_ok=True)
    return path
