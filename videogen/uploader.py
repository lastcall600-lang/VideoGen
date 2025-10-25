"""YouTube upload helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Dict
import logging

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import google.oauth2.credentials
import json


logger = logging.getLogger(__name__)


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def load_credentials(client_secret_path: Path, token_path: Path) -> google.oauth2.credentials.Credentials:
    if token_path.exists():
        with open(token_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        credentials = google.oauth2.credentials.Credentials.from_authorized_user_info(data, SCOPES)
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        return credentials
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
    credentials = flow.run_local_server(port=0)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    with open(token_path, "w", encoding="utf-8") as file:
        file.write(credentials.to_json())
    return credentials


def upload_video(video_path: Path, title: str, description: str, client_secret_path: Path, token_path: Path, category_id: str = "22", tags: list[str] | None = None, privacy_status: str = "unlisted") -> Dict:
    credentials = load_credentials(client_secret_path, token_path)
    youtube = build("youtube", "v3", credentials=credentials)
    body = {
        "snippet": {"title": title, "description": description, "categoryId": category_id, "tags": tags or []},
        "status": {"privacyStatus": privacy_status},
    }
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.info("Upload progress: %.2f%%", status.progress() * 100)
    logger.info("Uploaded video id: %s", response.get("id"))
    return response
