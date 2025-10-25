"""Project data structures and serialization."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any
import json
import logging

from .openai_utils import SegmentPlan


logger = logging.getLogger(__name__)


@dataclass
class ProjectSegment:
    """Represents a segment within a video project."""

    index: int
    title: str
    summary: str
    script: str
    keywords: List[str]
    speech_path: Path
    video_path: Path | None
    duration: float

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["speech_path"] = str(self.speech_path)
        data["video_path"] = str(self.video_path) if self.video_path else None
        return data


@dataclass
class VideoProject:
    """Container for the full project state."""

    name: str
    segments: List[ProjectSegment]
    render_path: Path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "render_path": str(self.render_path),
            "segments": [segment.to_dict() for segment in self.segments],
        }

    def save(self, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, "w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, indent=2, ensure_ascii=False)
        logger.info("Project saved to %s", destination)
        return destination


def create_project_segments(plans: List[SegmentPlan], speech_paths: List[Path], video_paths: List[Path | None], durations: List[float]) -> List[ProjectSegment]:
    segments: List[ProjectSegment] = []
    for index, plan in enumerate(plans):
        segments.append(
            ProjectSegment(
                index=index,
                title=plan.title,
                summary=plan.summary,
                script=plan.script,
                keywords=plan.keywords,
                speech_path=speech_paths[index],
                video_path=video_paths[index],
                duration=durations[index],
            )
        )
    return segments
