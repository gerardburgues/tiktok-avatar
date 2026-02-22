import platform
import subprocess
import sys


def get_device() -> str:
    """Auto-detect best available device."""
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        return "mps"
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


def banner():
    print("""
╔══════════════════════════════════════════╗
║       TikTok Avatar Pipeline             ║
║  voice + synthetic avatar + background   ║
╚══════════════════════════════════════════╝
""")


def check_requirements():
    missing = []
    for pkg in ["sounddevice", "cv2", "rembg", "PIL", "numpy", "scipy"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"Missing packages: {missing}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)

    result = subprocess.run(["ffmpeg", "-version"], capture_output=True)
    if result.returncode != 0:
        print("ffmpeg not found. Install: brew install ffmpeg")
        sys.exit(1)


def check_engine(engine_dir: str, name: str):
    from pathlib import Path
    if not Path(engine_dir).exists():
        print(f"\nERROR: {name} not found at {engine_dir}")
        print("Run: bash setup.sh")
        sys.exit(1)
