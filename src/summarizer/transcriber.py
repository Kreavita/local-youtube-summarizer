import whisper


def transcribe_audio(audio_path: str, model_size: str = "base") -> str:
    """Transcribe audio file using Whisper."""
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path)
    return result["text"]
