# Công cụ Voice (MiniMax + ElevenLabs)

Tool API đơn giản để:
- Gọi TTS với **ElevenLabs** hoặc **MiniMax**.
- Clone voice trên **ElevenLabs**.
- Gắn API key qua biến môi trường.

## Cài đặt

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Cấu hình API

```bash
cp .env.example .env
# sửa key trong .env
```

Xuất biến môi trường:

```bash
export ELEVENLABS_API_KEY=...
export MINIMAX_API_KEY=...
export MINIMAX_GROUP_ID=...
```

## Chạy server

```bash
uvicorn src.main:app --reload --port 8000
```

## API endpoints

### 1) Kiểm tra trạng thái

`GET /health`

### 2) Chuyển văn bản thành giọng nói (TTS)

`POST /tts`

Body JSON:

```json
{
  "provider": "elevenlabs",
  "text": "Xin chào",
  "voice_id": "VOICE_ID",
  "model": "eleven_multilingual_v2"
}
```

- `provider`: `elevenlabs` hoặc `minimax`
- `model`: optional
- Mọi response sẽ có `request_id` để trace; bạn có thể truyền `X-Request-ID` (ví dụ: `2399e9d8-7c9b-4c69-b610-2aa3b23b6fee`).

### 3) Clone giọng nói ElevenLabs

`POST /clone/elevenlabs` (multipart/form-data)
- `name` (text)
- `description` (text)
- `files` (1 hoặc nhiều audio file)

Ví dụ curl:

```bash
curl -X POST http://localhost:8000/clone/elevenlabs \
  -H "accept: application/json" \
  -F "name=My Clone" \
  -F "description=voice clone test" \
  -F "files=@sample1.mp3" \
  -F "files=@sample2.wav"
```

## Lưu ý

- Endpoint `/tts` trả về:
  - ElevenLabs: `audio_base64` (chuỗi Base64 chuẩn của mp3) để dễ truyền tiếp qua API nội bộ.
  - MiniMax: trả raw JSON từ MiniMax.
- Bạn có thể đổi sang trả stream/file nếu muốn.
