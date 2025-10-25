"""Integration helpers for the OpenAI APIs."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List
import json
import logging

from openai import OpenAI


logger = logging.getLogger(__name__)


@dataclass
class SegmentPlan:
    """Structured representation of a generated segment."""

    title: str
    summary: str
    script: str
    keywords: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SegmentPlan":
        return cls(
            title=data.get("title", "Unnamed"),
            summary=data.get("summary", ""),
            script=data.get("script", ""),
            keywords=list(data.get("keywords", [])),
        )


class OpenAIWorkflow:
    """Wrapper around the OpenAI API calls needed for the pipeline."""

    def __init__(self, api_key: str, model: str, tts_model: str, tts_voice: str) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.tts_model = tts_model
        self.tts_voice = tts_voice

    def generate_script_outline(self, transcripts: Iterable[str], prompt: str) -> List[SegmentPlan]:
        """Generate a structured plan for the new video using GPT."""
        combined_text = "\n".join(transcripts)
        system_prompt = (
            "You are an assistant that creates structured video scripts. "
            "Return valid JSON with a list of segments under a 'segments' key. "
            "Each segment must include title, summary, script, and keywords array."
        )
        user_prompt = (
            f"Original transcripts:\n{combined_text}\n\n"
            f"Creative brief:\n{prompt}\n\n"
            "Respond with JSON only."
        )
        response = self.client.responses.create(
            model=self.model,
            input=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=0.7,
        )
        content = response.output[0].content[0].text  # type: ignore[index]
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            logger.exception("Failed to parse response: %s", content)
            raise ValueError("OpenAI response was not valid JSON") from exc
        segments = [SegmentPlan.from_dict(item) for item in parsed.get("segments", [])]
        if not segments:
            raise ValueError("OpenAI returned no segments")
        logger.info("Generated %d segments", len(segments))
        return segments

    def generate_speech(self, text: str, destination: Path) -> Path:
        """Generate narration audio for the provided text."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        with self.client.audio.speech.with_streaming_response.create(
            model=self.tts_model,
            voice=self.tts_voice,
            input=text,
            format="mp3",
        ) as response:
            response.stream_to_file(destination)
        logger.info("Generated speech at %s", destination)
        return destination
