import subprocess
import sys
from pathlib import Path


def run_sadtalker(
    avatar_path: str,
    audio_path: str,
    output_dir: str,
    sadtalker_dir: str = "engines/SadTalker",
    device: str = "mps",
) -> str:
    """
    Animate a still avatar image with audio using SadTalker.
    Returns path to the output video.
    """
    from src.utils import check_engine

    sadtalker = Path(sadtalker_dir).resolve()
    check_engine(str(sadtalker), "SadTalker")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(sadtalker / "inference.py"),
        "--driven_audio", str(Path(audio_path).resolve()),
        "--source_image", str(Path(avatar_path).resolve()),
        "--result_dir",   str(Path(output_dir).resolve()),
        "--still",             # minimal head movement — good for avatars
        "--preprocess", "full",
        "--enhancer", "gfpgan",  # face enhancement
        "--device", device,
    ]

    print(f"\n🎭  Animating avatar with SadTalker (device={device})...")
    subprocess.run(cmd, cwd=str(sadtalker), check=True)

    videos = sorted(Path(output_dir).rglob("*.mp4"))
    if not videos:
        raise RuntimeError("SadTalker produced no output video")
    return str(videos[-1])


def run_liveportrait(
    avatar_path: str,
    driving_path: str,
    output_dir: str,
    liveportrait_dir: str = "engines/LivePortrait",
    device: str = "mps",
) -> str:
    """
    Animate avatar using LivePortrait driven by a reference video.
    Returns path to the output video.
    """
    from src.utils import check_engine

    liveportrait = Path(liveportrait_dir).resolve()
    check_engine(str(liveportrait), "LivePortrait")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(liveportrait / "inference.py"),
        "-s", str(Path(avatar_path).resolve()),
        "-d", str(Path(driving_path).resolve()),
        "--output-dir", str(Path(output_dir).resolve()),
    ]

    print(f"\n🎭  Animating avatar with LivePortrait (device={device})...")
    subprocess.run(cmd, cwd=str(liveportrait), check=True)

    videos = sorted(Path(output_dir).rglob("*.mp4"))
    if not videos:
        raise RuntimeError("LivePortrait produced no output video")
    return str(videos[-1])
