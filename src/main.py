import base64
import os
import uuid
from typing import Literal, Optional

import httpx
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field

app = FastAPI(title="Voice Tool Gateway", version="0.2.0")


class TtsRequest(BaseModel):
    provider: Literal["elevenlabs", "minimax"]
    text: str = Field(min_length=1)
    voice_id: str = Field(min_length=1)
    model: Optional[str] = None


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/tts")
async def text_to_speech(payload: TtsRequest, request: Request):
    request_id = _request_id(request)
    if payload.provider == "elevenlabs":
        return await _tts_elevenlabs(payload, request_id)
    return await _tts_minimax(payload, request_id)


@app.post("/clone/elevenlabs")
async def clone_voice_elevenlabs(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    files: list[UploadFile] = File(...),
):
    request_id = _request_id(request)
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing ELEVENLABS_API_KEY")

    data = {"name": name, "description": description}
    multipart = []
    for f in files:
        content = await f.read()
        multipart.append(("files", (f.filename, content, f.content_type or "audio/mpeg")))

    headers = {"xi-api-key": api_key}
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.elevenlabs.io/v1/voices/add",
            data=data,
            files=multipart,
            headers=headers,
        )
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return {"request_id": request_id, "provider": "elevenlabs", "result": resp.json()}


async def _tts_elevenlabs(payload: TtsRequest, request_id: str):
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing ELEVENLABS_API_KEY")

    body = {
        "text": payload.text,
        "model_id": payload.model or "eleven_multilingual_v2",
    }
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{payload.voice_id}"

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, json=body, headers=headers)
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    audio_base64 = base64.b64encode(resp.content).decode("utf-8")
    return {"request_id": request_id, "audio_base64": audio_base64, "format": "mp3", "provider": "elevenlabs"}


async def _tts_minimax(payload: TtsRequest, request_id: str):
    api_key = os.getenv("MINIMAX_API_KEY")
    group_id = os.getenv("MINIMAX_GROUP_ID")
    if not api_key or not group_id:
        raise HTTPException(status_code=500, detail="Missing MINIMAX_API_KEY or MINIMAX_GROUP_ID")

    body = {
        "model": payload.model or "speech-01-hd",
        "text": payload.text,
        "voice_id": payload.voice_id,
        "audio_setting": {"sample_rate": 32000, "bitrate": 128000, "format": "mp3"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    url = f"https://api.minimax.chat/v1/t2a_v2?GroupId={group_id}"
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, json=body, headers=headers)

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return {"request_id": request_id, "provider": "minimax", "result": resp.json()}


def _request_id(request: Request) -> str:
    return request.headers.get("X-Request-ID", str(uuid.uuid4()))
