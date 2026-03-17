import argparse
import os
import sys
import tempfile

from . import downloader, transcriber, summarizer
from .config import SUMMARY_PROMPT, WHISPER_MODEL, OLLAMA_MODEL


def main():
    parser = argparse.ArgumentParser(description="Summarize YouTube videos using Whisper and Ollama")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--prompt", "-p", default=SUMMARY_PROMPT, help="Summary prompt")
    parser.add_argument("--model", "-m", default=OLLAMA_MODEL, help="Ollama model")
    parser.add_argument("--whisper-model", default=WHISPER_MODEL, help="Whisper model size")
    parser.add_argument("--output", "-o", help="Output file for summary")
    parser.add_argument("--keep-audio", action="store_true", help="Keep audio file after processing")

    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as temp_dir:
        print("Downloading audio...")
        audio_path = downloader.download_audio(args.url, temp_dir)
        print(f"Audio downloaded: {audio_path}")

        print("Transcribing with Whisper...")
        transcript = transcriber.transcribe_audio(audio_path, args.whisper_model)
        print("Transcription complete.")

        if not args.keep_audio:
            os.remove(audio_path)
            print("Audio file removed.")

        print("Generating summary with Ollama...")
        summary = summarizer.summarize_text(transcript, args.prompt, args.model)
        
        if args.output:
            with open(args.output, "w") as f:
                f.write(summary)
            print(f"Summary saved to: {args.output}")
        else:
            print("\n--- Summary ---\n")
            print(summary)


if __name__ == "__main__":
    main()
