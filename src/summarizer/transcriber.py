import torch
from pathlib import Path
from faster_whisper import WhisperModel


_model = None


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
    """Transcribe audio file using Faster Whisper."""
    global _model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {check_cuda()}")
    _model = WhisperModel(model_size, device=device, compute_type="float16" if device == "cuda" else "int8")
    segments, _ = _model.transcribe(audio_path, log_progress=True)
    return " ".join([seg.text for seg in segments])


def unload_model() -> None:
    """Unload Whisper model from memory/VRAM."""
    global _model
    if _model is not None:
        del _model
        _model = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
