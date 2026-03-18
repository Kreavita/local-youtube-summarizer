import subprocess
import sys
import tempfile
import torch
import re
from pathlib import Path
from typing import Generator


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

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
    if result.returncode != 0:
        if device == "cuda":
            print("CUDA subprocess failed, retrying with CPU...", flush=True)
            cmd[cmd.index("cuda")] = "cpu"
            cmd[cmd.index("float16")] = "int8"
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
            if result.returncode != 0:
                print(f"STDERR: {result.stderr}", flush=True)
                raise RuntimeError(f"Transcription failed: {result.stderr}")
        else:
            print(f"STDERR: {result.stderr}", flush=True)
            raise RuntimeError(f"Transcription failed: {result.stderr}")

    with open(tmp_path, encoding="utf-8") as f:
        result = f.read()

    Path(tmp_path).unlink()

    return result


def transcribe_audio_progress(audio_path: str, model_size: str = "large-v3-turbo") -> tuple[str, Generator[dict, None, None]]:
    """Transcribe audio file with progress updates."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    video_id = Path(audio_path).stem

    compute_type = "float16" if device == "cuda" else "int8"

    cli_script = str(Path(__file__).parent / "_transcribe_cli.py")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
        tmp_path = tmp.name

    cmd = [
        sys.executable, cli_script,
        "--model", model_size,
        "--device", device,
        "--compute_type", compute_type,
        "--output_file", tmp_path,
        "--filename_timestamps",
        audio_path
    ]

    def run_with_progress():
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=Path(__file__).parent,
            bufsize=1
        )

        tqdm_pattern = re.compile(r'(\d+)%\|')
        transcript_lines: list[str] = []

        for line in process.stdout:
            print(line, end='', flush=True)
            transcript_lines.append(line)
            
            match = tqdm_pattern.search(line)
            if match:
                pct = int(match.group(1))
                yield {"progress": pct / 100.0, "text": f"Transcribing... {match.group(1)}%"}

        process.wait()

        if process.returncode != 0:
            if device == "cuda":
                print("CUDA subprocess failed, retrying with CPU...", flush=True)
                cmd[cmd.index("cuda")] = "cpu"
                cmd[cmd.index("float16")] = "int8"
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=Path(__file__).parent,
                    bufsize=1
                )
                transcript_lines = []
                for line in process.stdout:
                    print(line, end='', flush=True)
                    transcript_lines.append(line)
                    match = tqdm_pattern.search(line)
                    if match:
                        pct = int(match.group(1))
                        yield {"progress": pct / 100.0, "text": f"Transcribing... {match.group(1)}%"}
                process.wait()
                if process.returncode != 0:
                    raise RuntimeError("Transcription failed")
            else:
                raise RuntimeError("Transcription failed")

        with open(tmp_path, encoding="utf-8") as f:
            result = f.read()

        Path(tmp_path).unlink()
        save_transcript(video_id, result)
        yield {"progress": 1.0, "text": "Complete"}

    progress_gen = run_with_progress()
    return "", progress_gen
