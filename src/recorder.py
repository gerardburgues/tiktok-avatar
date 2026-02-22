import time
import numpy as np
from pathlib import Path


def record_audio(output_path: str, duration: int = 30, sample_rate: int = 44100) -> str:
    """Record audio from the default microphone. Ctrl+C stops early and saves cleanly."""
    import sounddevice as sd
    from scipy.io import wavfile

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"\n🎙  Recording audio for up to {duration}s — speak now!")
    print("   Press Ctrl+C when you're done.\n")
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    print("   GO!\n")

    chunks = []

    def _callback(indata, frames, time_info, status):
        chunks.append(indata.copy())

    try:
        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
            callback=_callback,
        ):
            sd.sleep(duration * 1000)
    except KeyboardInterrupt:
        print("\n   (stopped early — saving...)")

    if not chunks:
        raise RuntimeError("No audio was recorded")

    audio = np.concatenate(chunks, axis=0)
    wavfile.write(output_path, sample_rate, audio)
    print(f"✓ Audio saved: {output_path}  ({len(audio) / sample_rate:.1f}s)")
    return output_path


def record_webcam(output_path: str, duration: int = 30) -> str:
    """Record from the default webcam (used as driving video for LivePortrait)."""
    import cv2

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam")

    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    print(f"\n📹  Recording webcam for {duration}s — press Q to stop early.\n")
    start = time.time()
    while time.time() - start < duration:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        cv2.imshow("Recording (Q to stop)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()
    print(f"✓ Webcam video saved: {output_path}")
    return output_path
