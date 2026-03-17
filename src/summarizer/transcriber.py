import whisper
import torch


def transcribe_audio(audio_path: str, model_size: str = "base") -> str:
    """Transcribe audio file using Whisper."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisper.load_model(model_size, device=device)
    print(f"Using device: {device}")
    result = model.transcribe(audio_path, verbose=False)
    return result["text"]
