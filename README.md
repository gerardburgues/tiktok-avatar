# TikTok Avatar Pipeline

Record your voice → animate a **fully synthetic avatar** → swap background → export 9:16 for TikTok/Instagram.

No face on camera. Your real voice. Clean professional result.

```
Voice recording
      ↓
AI talking-head animation (SadTalker / LivePortrait)
      ↓
Background removal (rembg / chromakey)
      ↓
Composite on clean background
      ↓
Export 1080×1920 for TikTok
```

Runs locally on **Apple Silicon M-series** (MPS acceleration).

---

## Requirements

- macOS with Apple Silicon (M1/M2/M3/M4) — or Linux with CUDA GPU
- Python 3.10+
- ffmpeg (`brew install ffmpeg`)
- ~2GB disk for SadTalker models

---

## Setup (one time)

```bash
git clone https://github.com/gerardburgues/tiktok-avatar
cd tiktok-avatar
bash setup.sh
```

For LivePortrait support (more natural motion):
```bash
bash setup.sh --with-liveportrait
```

---

## Prepare your avatar

1. Generate a portrait with **Midjourney**, **FLUX**, or any AI image tool
2. Use a **solid-color background** (green `#00FF00` is fastest, any plain color works)
3. Save as `assets/avatar.png`

Add a background scene image to `assets/backgrounds/` — a clean studio, café, gradient, etc.

---

## Usage

### Record audio now → animate → swap background
```bash
python pipeline.py \
  --avatar assets/avatar.png \
  --record-audio \
  --bg assets/backgrounds/studio.jpg
```

### Use an existing audio file
```bash
python pipeline.py \
  --avatar assets/avatar.png \
  --audio my_voice.wav \
  --bg assets/backgrounds/studio.jpg
```

### LivePortrait mode (most natural head movement)
Record yourself on webcam to drive the avatar's motion. Your face is replaced, voice kept.
```bash
python pipeline.py \
  --avatar assets/avatar.png \
  --record-audio \
  --record-webcam \
  --engine liveportrait \
  --bg assets/backgrounds/studio.jpg
```

### Fast mode (avatar on green background)
Skips AI background removal — use ffmpeg chromakey instead. Much faster.
```bash
python pipeline.py \
  --avatar assets/avatar_green.png \
  --audio my_voice.wav \
  --bg assets/backgrounds/studio.jpg \
  --bg-color 00ff00
```

### All options
```
--avatar          Avatar image (.png) — required
--audio           Existing audio file (.wav/.mp3)
--record-audio    Record from mic now
--duration        Recording length in seconds (default: 30)
--bg              Background image or video
--engine          sadtalker (default) | liveportrait
--bg-color        Hex color to chromakey out (e.g. 00ff00) — fast path
--no-bg-removal   Skip background removal entirely
--device          mps / cuda / cpu (auto-detected)
--output          Output path (default: output/tiktok_TIMESTAMP.mp4)
```

---

## How it works

| Step | Tool | Notes |
|------|------|-------|
| Audio recording | `sounddevice` | Mic input, saved as WAV |
| Talking head animation | **SadTalker** or **LivePortrait** | MPS-accelerated |
| Background removal | **rembg** (u2net_human_seg) | Frame-by-frame AI masking |
| Compositing | `Pillow` + `ffmpeg` | Avatar centered on background |
| Export | `ffmpeg` | H.264, 1080×1920, AAC audio |

### SadTalker vs LivePortrait

| | SadTalker | LivePortrait |
|---|---|---|
| Input | Still image + audio | Still image + driving video |
| Motion source | Audio-driven lip sync | Your webcam movements |
| Head movement | Minimal (stable) | Full, natural |
| Setup | Easier | Needs webcam recording |
| Best for | Clean talking head | Natural presenter style |

---

## Output

Videos saved to `output/tiktok_YYYYMMDD_HHMMSS.mp4` — ready to upload as TikTok/Instagram photo carousel or video.
