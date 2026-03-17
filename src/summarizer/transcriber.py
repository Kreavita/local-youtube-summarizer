import subprocess
import sys
import tempfile
import torch
from pathlib import Path


def check_cuda() -> str:
    """Check CUDA availability and return device info."""
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        cuda_ver = torch.version.cuda
        return f"cuda ({device_name}, CUDA {cuda_ver})"
    return "cpu"


def get_cache_path(video_id: str) -> Path:
    """Get path for cached transcription."""
    cache_dir = Path.home() / ".cache" / "yt_summarizer"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{video_id}.txt"


def load_cached_transcript(video_id: str) -> str | None:
    """Load cached transcript if exists."""
    cache_path = get_cache_path(video_id)
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8")
    return None


def save_transcript(video_id: str, transcript: str) -> None:
    """Save transcript to cache."""
    cache_path = get_cache_path(video_id)
    cache_path.write_text(transcript, encoding="utf-8")


def transcribe_audio(audio_path: str, model_size: str = "large-v3-turbo") -> str:
    """Transcribe audio file using Faster Whisper via subprocess."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {check_cuda()}")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
        tmp_path = tmp.name

    compute_type = "float16" if device == "cuda" else "int8"

    cli_script = str(Path(__file__).parent / "_transcribe_cli.py")

    cmd = [
        sys.executable, cli_script,
        "--model", model_size,
        "--device", device,
        "--compute_type", compute_type,
        "--output_file", tmp_path,
        "--filename_timestamps",
        audio_path
    ]

    subprocess.run(cmd, check=True, cwd=Path(__file__).parent)

    with open(tmp_path, encoding="utf-8") as f:
        result = f.read()

    Path(tmp_path).unlink()

    print("Whisper model unloaded from VRAM", flush=True)
    return result


def unload_model() -> None:
    """Unload Whisper model from memory/VRAM."""
    pass
