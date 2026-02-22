"""
Background removal + compositing + final export.

Two modes:
  - chromakey: fast, use when avatar image has a solid-color background
  - rembg:     automatic AI-based removal, works on any background
"""

import subprocess
from pathlib import Path


# ── Chromakey path (fast, uses ffmpeg) ────────────────────────────────────────

def compose_chromakey(
    avatar_video: str,
    audio_path: str,
    background_path: str,
    output_path: str,
    bg_color: str = "00ff00",   # hex color to key out
    similarity: float = 0.3,
    width: int = 1080,
    height: int = 1920,
):
    """Fast background removal using ffmpeg chromakey filter."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    bg_is_video = Path(background_path).suffix.lower() in {".mp4", ".mov", ".avi", ".webm"}

    if bg_is_video:
        bg_input = ["-i", background_path]
        bg_filter = f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}[bg]"
    else:
        bg_input = ["-loop", "1", "-i", background_path]
        bg_filter = f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}[bg]"

    filter_complex = (
        f"{bg_filter};"
        f"[1:v]chromakey=0x{bg_color}:{similarity}:0.1,scale=-1:{height}[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        *bg_input,
        "-i", avatar_video,
        "-i", audio_path,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-map", "2:a:0",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_path,
    ]

    print("\n🎬  Compositing (chromakey)...")
    subprocess.run(cmd, check=True)


# ── rembg path (automatic AI removal) ─────────────────────────────────────────

def compose_rembg(
    avatar_video: str,
    audio_path: str,
    background_path: str,
    output_path: str,
    width: int = 1080,
    height: int = 1920,
):
    """AI background removal frame-by-frame, then composite onto background."""
    import cv2
    import numpy as np
    from PIL import Image
    from rembg import remove, new_session
    import tempfile, os

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print("\n🤖  Removing background with rembg (u2net_human_seg)...")
    session = new_session("u2net_human_seg")

    cap = cv2.VideoCapture(avatar_video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Prepare background
    bg_is_video = Path(background_path).suffix.lower() in {".mp4", ".mov", ".avi", ".webm"}
    bg_cap = None
    if background_path:
        if bg_is_video:
            bg_cap = cv2.VideoCapture(background_path)
        else:
            bg_img = Image.open(background_path).convert("RGB").resize((width, height), Image.LANCZOS)
    else:
        # Default: dark gradient background
        bg_arr = np.zeros((height, width, 3), dtype=np.uint8)
        for y in range(height):
            v = int(20 + (y / height) * 40)
            bg_arr[y, :] = [v, v, v]
        bg_img = Image.fromarray(bg_arr)

    # Write frames to a temp video (no audio)
    tmp_video = output_path.replace(".mp4", "_noaudio.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(tmp_video, fourcc, fps, (width, height))

    frame_idx = 0
    print(f"   Processing {total} frames at {fps:.0f}fps...")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Get background for this frame
        if bg_cap is not None:
            ret_bg, bg_frame = bg_cap.read()
            if not ret_bg:
                bg_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                _, bg_frame = bg_cap.read()
            bg_img = Image.fromarray(cv2.cvtColor(bg_frame, cv2.COLOR_BGR2RGB)).resize(
                (width, height), Image.LANCZOS
            )

        # Remove background
        frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        fg_rgba = remove(frame_pil, session=session)

        # Scale avatar to fit height, keep aspect ratio
        aw, ah = fg_rgba.size
        scale = height / ah
        new_w = int(aw * scale)
        fg_rgba = fg_rgba.resize((new_w, height), Image.LANCZOS)

        # Paste centered on background
        composite = bg_img.copy().convert("RGB")
        x = (width - new_w) // 2
        composite.paste(fg_rgba, (x, 0), fg_rgba)

        out.write(cv2.cvtColor(np.array(composite), cv2.COLOR_RGB2BGR))

        frame_idx += 1
        if frame_idx % 25 == 0:
            pct = frame_idx / max(total, 1) * 100
            print(f"   {frame_idx}/{total} frames ({pct:.0f}%)")

    cap.release()
    out.release()
    if bg_cap:
        bg_cap.release()

    print("✓ Frames composited")

    # Mux audio
    print("🔊  Muxing audio...")
    cmd = [
        "ffmpeg", "-y",
        "-i", tmp_video,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_path,
    ]
    subprocess.run(cmd, check=True)
    Path(tmp_video).unlink(missing_ok=True)
    print(f"✓ Saved: {output_path}")


# ── Public entry point ─────────────────────────────────────────────────────────

def compose_final(
    avatar_video: str,
    audio_path: str,
    background_path: str | None,
    output_path: str,
    remove_bg: bool = True,
    bg_color: str | None = None,
    width: int = 1080,
    height: int = 1920,
):
    bg = background_path or ""

    if not remove_bg:
        # Just reformat to 9:16 and mux audio
        _export_plain(avatar_video, audio_path, output_path, width, height)
        return

    if bg_color:
        if not bg:
            raise ValueError("--bg-color requires --bg to specify a background")
        compose_chromakey(avatar_video, audio_path, bg, output_path, bg_color, width=width, height=height)
    else:
        compose_rembg(avatar_video, audio_path, bg, output_path, width, height)


def _export_plain(video: str, audio: str, output: str, width: int, height: int):
    """Reformat to 9:16 and mux audio, no compositing."""
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", video,
        "-i", audio,
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
               f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        output,
    ]
    subprocess.run(cmd, check=True)
    print(f"✓ Saved: {output}")
