#!/usr/bin/env bash
# TikTok Avatar Pipeline — one-time setup
set -e

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║    TikTok Avatar Pipeline — Setup        ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── System deps ──────────────────────────────────────────────────────────────
if ! command -v ffmpeg &>/dev/null; then
    echo "Installing ffmpeg..."
    brew install ffmpeg
fi

if ! command -v git-lfs &>/dev/null; then
    echo "Installing git-lfs (needed for model downloads)..."
    brew install git-lfs
    git lfs install
fi

# ── Python deps ───────────────────────────────────────────────────────────────
echo "Installing Python dependencies..."

# On Apple Silicon: use onnxruntime with CoreML for faster rembg
if [[ $(uname -m) == "arm64" ]]; then
    pip install onnxruntime-silicon 2>/dev/null || pip install onnxruntime
else
    pip install onnxruntime
fi

pip install -r requirements.txt

# ── SadTalker ─────────────────────────────────────────────────────────────────
if [ ! -d "engines/SadTalker" ]; then
    echo ""
    echo "Cloning SadTalker..."
    git clone https://github.com/OpenTalker/SadTalker engines/SadTalker
fi

echo "Installing SadTalker dependencies..."
pip install -r engines/SadTalker/requirements.txt

echo "Downloading SadTalker checkpoints (~300MB)..."
cd engines/SadTalker
bash scripts/download_models.sh
cd ../..

# ── LivePortrait (optional) ───────────────────────────────────────────────────
if [[ "$1" == "--with-liveportrait" ]]; then
    if [ ! -d "engines/LivePortrait" ]; then
        echo ""
        echo "Cloning LivePortrait..."
        git clone https://github.com/KwaiVGI/LivePortrait engines/LivePortrait
    fi
    echo "Installing LivePortrait dependencies..."
    pip install -r engines/LivePortrait/requirements.txt
    echo "Downloading LivePortrait models..."
    cd engines/LivePortrait
    python scripts/download_models.py
    cd ../..
fi

# ── Sample assets ─────────────────────────────────────────────────────────────
echo ""
echo "Creating sample background placeholders..."
mkdir -p assets/backgrounds

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Setup complete!                        ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Add your avatar image:  assets/avatar.png"
echo "     Tip: generate with FLUX/Midjourney, use a plain colored background"
echo ""
echo "  2. Add a background image: assets/backgrounds/studio.jpg"
echo "     (or any image/video you want behind the avatar)"
echo ""
echo "  3. Run the pipeline:"
echo "     python pipeline.py --avatar assets/avatar.png --record-audio --bg assets/backgrounds/studio.jpg"
echo ""
echo "For natural head movement (LivePortrait mode), also run:"
echo "  bash setup.sh --with-liveportrait"
echo ""
