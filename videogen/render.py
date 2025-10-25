"""Rendering helpers using moviepy."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable
import logging

from moviepy.editor import AudioFileClip, VideoFileClip, concatenate_videoclips

from .project import ProjectSegment


logger = logging.getLogger(__name__)


def prepare_clip(segment: ProjectSegment) -> VideoFileClip:
    """Load and align a video clip with its narration audio."""
    audio_clip = AudioFileClip(str(segment.speech_path))
    if segment.video_path:
        video_clip = VideoFileClip(str(segment.video_path))
    else:  # fallback to a blank color clip if no video is available
        from moviepy.editor import ColorClip

        video_clip = ColorClip(size=(1920, 1080), color=(0, 0, 0), duration=audio_clip.duration)
    if video_clip.duration < audio_clip.duration:
        loops = int(audio_clip.duration // video_clip.duration) + 1
        clips = [video_clip] * loops
        video_clip = concatenate_videoclips(clips)
    video_clip = video_clip.subclip(0, audio_clip.duration)
    video_clip = video_clip.set_audio(audio_clip)
    return video_clip


def render_project(segments: Iterable[ProjectSegment], destination: Path, fps: int = 30) -> Path:
    """Render the list of segments into a single video file."""
    clips = [prepare_clip(segment) for segment in segments]
    final_clip = concatenate_videoclips(clips, method="compose")
    destination.parent.mkdir(parents=True, exist_ok=True)
    final_clip.write_videofile(str(destination), fps=fps)
    final_clip.close()
    for clip in clips:
        clip.close()
    logger.info("Rendered video to %s", destination)
    return destination
