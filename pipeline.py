#!/usr/bin/env python3
"""
TikTok Avatar Pipeline
======================
Record your voice → animate a synthetic avatar → swap background → export 9:16.

QUICK START
-----------
# 1. Run setup (first time only)
bash setup.sh

# 2. Generate or find an avatar image (plain-color background recommended)
#    Save it as: assets/avatar.png

# 3. Run the pipeline

  # Record audio now, SadTalker animates it:
  python pipeline.py --avatar assets/avatar.png --record-audio --bg assets/backgrounds/studio.jpg

  # Use an existing audio file:
  python pipeline.py --avatar assets/avatar.png --audio voice.wav --bg assets/backgrounds/studio.jpg

  # LivePortrait mode (most natural motion — record yourself to drive the avatar):
  python pipeline.py --avatar assets/avatar.png --record-audio --record-webcam \\
      --engine liveportrait --bg assets/backgrounds/studio.jpg

  # Fast background removal (avatar on green background):
  python pipeline.py --avatar assets/avatar_greenscreen.png --audio voice.wav \\
      --bg assets/backgrounds/studio.jpg --bg-color 00ff00

ENGINES
-------
  sadtalker    Audio → talking head from a still image. Easy, no webcam needed.
  liveportrait Webcam recording drives the avatar's full head motion. More natural.
"""

import argparse
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser(
        description="TikTok Avatar Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Inputs
    p.add_argument("--avatar",    required=True, help="Avatar image (.png)")
    p.add_argument("--audio",     help="Existing audio file (.wav/.mp3)")
    p.add_argument("--driving",   help="Existing driving video for LivePortrait (.mp4)")
    p.add_argument("--bg",        help="Background image or video file")

    # Recording
    p.add_argument("--record-audio",  action="store_true", help="Record audio from mic")
    p.add_argument("--record-webcam", action="store_true", help="Record webcam (LivePortrait driving video)")
    p.add_argument("--duration",  type=int, default=25, help="Recording duration in seconds (default: 25)")

    # Engine
    p.add_argument("--engine", choices=["sadtalker", "liveportrait"], default="sadtalker")
    p.add_argument("--sadtalker-dir",    default="engines/SadTalker")
    p.add_argument("--liveportrait-dir", default="engines/LivePortrait")
    p.add_argument("--device", default=None, help="mps / cuda / cpu (auto-detected)")

    # Background removal
    p.add_argument("--bg-color",    default=None, help="Chromakey hex color to remove (e.g. 00ff00)")
    p.add_argument("--no-bg-removal", action="store_true", help="Skip background removal")

    # Output
    p.add_argument("--output", help="Output path (default: output/tiktok_TIMESTAMP.mp4)")

    return p.parse_args()


def main():
    args = parse_args()

    from src.utils import get_device, banner, check_requirements
    from src.recorder import record_audio, record_webcam
    from src.animator import run_sadtalker, run_liveportrait
    from src.composer import compose_final

    banner()
    check_requirements()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    workdir = Path(tempfile.mkdtemp(prefix=f"tiktok_{ts}_"))
    output_path = args.output or f"output/tiktok_{ts}.mp4"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    device = args.device or get_device()
    print(f"Device : {device}")
    print(f"Engine : {args.engine}")
    print(f"Output : {output_path}\n")

    try:
        # ── Step 1: Audio ────────────────────────────────────────────────────
        audio_path = args.audio
        if args.record_audio:
            audio_path = str(workdir / "voice.wav")
            record_audio(audio_path, duration=args.duration)

        if not audio_path:
            print("ERROR: Provide --audio <file> or use --record-audio")
            sys.exit(1)

        if not Path(audio_path).exists():
            print(f"ERROR: Audio file not found: {audio_path}")
            sys.exit(1)

        # ── Step 2: Animate ──────────────────────────────────────────────────
        if args.engine == "liveportrait":
            driving_path = args.driving
            if args.record_webcam:
                driving_path = str(workdir / "driving.mp4")
                record_webcam(driving_path, duration=args.duration)
            if not driving_path:
                print("ERROR: LivePortrait needs --driving <file> or --record-webcam")
                sys.exit(1)
            animated = run_liveportrait(
                avatar_path=args.avatar,
                driving_path=driving_path,
                output_dir=str(workdir / "animated"),
                liveportrait_dir=args.liveportrait_dir,
                device=device,
            )
        else:
            animated = run_sadtalker(
                avatar_path=args.avatar,
                audio_path=audio_path,
                output_dir=str(workdir / "animated"),
                sadtalker_dir=args.sadtalker_dir,
                device=device,
            )

        # ── Step 3: Compose ──────────────────────────────────────────────────
        compose_final(
            avatar_video=animated,
            audio_path=audio_path,
            background_path=args.bg,
            output_path=output_path,
            remove_bg=not args.no_bg_removal,
            bg_color=args.bg_color,
        )

        print(f"\n✅  Done!  →  {output_path}")

    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()
