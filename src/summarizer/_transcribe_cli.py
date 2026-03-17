import argparse
import sys
from faster_whisper import WhisperModel


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--device", required=True)
    parser.add_argument("--compute_type", required=True)
    parser.add_argument("--output_file", required=True)
    parser.add_argument("--filename_timestamps", action="store_true")
    parser.add_argument("audio_path")
    args = parser.parse_args()

    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)
    segments, _ = model.transcribe(args.audio_path, log_progress=True)

    if args.filename_timestamps:
        result = "\n".join([f"[{seg.start:.2f}s - {seg.end:.2f}s] {seg.text}" for seg in segments])
    else:
        result = "\n".join([seg.text for seg in segments])

    with open(args.output_file, "w", encoding="utf-8") as f:
        f.write(result)


if __name__ == "__main__":
    main()
