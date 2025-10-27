"""Command line entry point for the VideoGen pipeline."""
from __future__ import annotations

from pathlib import Path
from typing import List
import argparse
import logging

from moviepy.editor import AudioFileClip

from .config import VideoGenConfig
from .youtube import gather_transcripts
from .openai_utils import OpenAIWorkflow, SegmentPlan
from .pexels import PexelsClient
from .project import VideoProject, create_project_segments
from .render import render_project
from .uploader import upload_video
from .script_utils import build_plans_from_script


logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def build_project_from_plans(
    plans: List[SegmentPlan],
    brief: str,
    workflow: OpenAIWorkflow,
    config: VideoGenConfig,
    project_name: str,
    render: bool,
    upload: bool,
    upload_title: str | None,
    upload_description: str | None,
    privacy_status: str,
) -> VideoProject:

    speech_dir = config.working_dir / "speech"
    video_dir = config.working_dir / "video"
    speech_paths: List[Path] = []
    video_paths: List[Path | None] = []
    durations: List[float] = []

    pexels_client = PexelsClient(config.pexels_api_key, video_dir)

    for index, plan in enumerate(plans):
        speech_path = speech_dir / f"segment_{index:02d}.mp3"
        workflow.generate_speech(plan.script, speech_path)
        with AudioFileClip(str(speech_path)) as audio_clip:
            duration = float(audio_clip.duration)
        query = " ".join(plan.keywords) or plan.title
        pexels_video = pexels_client.search_and_download(query)
        video_path = pexels_video.filepath if pexels_video else None
        speech_paths.append(speech_path)
        video_paths.append(video_path)
        durations.append(duration)
        logger.info("Prepared segment %d with duration %.2fs", index + 1, duration)

    segments = create_project_segments(plans, speech_paths, video_paths, durations)

    render_path = config.output_dir / f"{project_name}.mp4"
    project = VideoProject(name=project_name, segments=segments, render_path=render_path)
    project_file = config.output_dir / f"{project_name}.json"
    project.save(project_file)

    if render:
        render_project(project.segments, render_path)

    if upload:
        upload_title = upload_title or project_name
        upload_description = upload_description or brief or project_name
        token_path = config.working_dir / "youtube_token.json"
        upload_video(render_path, upload_title, upload_description, config.youtube_client_secret, token_path, privacy_status=privacy_status)

    return project


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Generate AI-assisted videos from YouTube transcripts or custom scripts."
    )
    parser.add_argument("urls", nargs="*", help="YouTube video URLs")
    parser.add_argument("--prompt", default="", help="Creative brief for the new video")
    parser.add_argument("--project", default="videogen_project", help="Name of the project")
    parser.add_argument("--render", action="store_true", help="Render the final video")
    parser.add_argument("--upload", action="store_true", help="Upload the rendered video to YouTube")
    parser.add_argument("--privacy", default="unlisted", help="YouTube privacy status")
    parser.add_argument("--upload-title", help="Title for the YouTube upload")
    parser.add_argument("--upload-description", help="Description for the YouTube upload")
    parser.add_argument("--script-file", help="Path to a text file that will be used as the narration script")

    args = parser.parse_args(argv)

    if not args.urls and not args.script_file:
        parser.error("Provide at least one YouTube URL or a --script-file")

    if args.urls and not args.prompt:
        parser.error("--prompt is required when using YouTube URLs")

    config = VideoGenConfig.from_environment()

    workflow = OpenAIWorkflow(
        api_key=config.openai_api_key,
        model=config.openai_model,
        tts_model=config.openai_tts_model,
        tts_voice=config.openai_tts_voice,
    )

    if args.script_file:
        script_path = Path(args.script_file)
        script_text = script_path.read_text(encoding="utf-8")
        plans = build_plans_from_script(script_text)
        brief = args.prompt or "Video generated from provided script."
    else:
        transcripts = gather_transcripts(args.urls)
        plans = workflow.generate_script_outline([transcript.text for transcript in transcripts], args.prompt)
        brief = args.prompt

    if not plans:
        raise SystemExit("No segments could be generated. Provide a longer script or additional context.")

    build_project_from_plans(
        plans=plans,
        brief=brief,
        workflow=workflow,
        config=config,
        project_name=args.project,
        render=args.render,
        upload=args.upload,
        upload_title=args.upload_title,
        upload_description=args.upload_description,
        privacy_status=args.privacy,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
