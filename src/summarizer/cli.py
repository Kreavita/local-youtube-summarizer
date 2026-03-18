import argparse
import os
import sys
import tempfile
import webbrowser
import threading
import time
import subprocess
import hashlib
from pathlib import Path

from . import downloader, transcriber, summarizer, transcript_fetcher
from .config import SUMMARY_PROMPT, WHISPER_MODEL, OLLAMA_MODEL

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def open_browser():
    time.sleep(2)
    webbrowser.open("http://localhost:12820")


def main():
    parser = argparse.ArgumentParser(description="Summarize YouTube videos using Whisper and Ollama")
    parser.add_argument("url", help="YouTube video URL or local file path (video/audio file)", nargs="?")
    parser.add_argument("--prompt", "-p", default=SUMMARY_PROMPT, help="Summary prompt")
    parser.add_argument("--model", "-m", default=OLLAMA_MODEL, help="Ollama model")
    parser.add_argument("--whisper-model", default=WHISPER_MODEL, help="Whisper model size (tiny, base, small, medium, large-v3-turbo, large-v3, turbo)")
    parser.add_argument("--output", "-o", help="Output file for summary")
    parser.add_argument("--keep-audio", action="store_true", help="Keep downloaded audio file after processing")
    parser.add_argument("--no-cache", action="store_true", help="Disable transcript caching")
    parser.add_argument("--no-yt-subs", action="store_true", help="Skip YouTube transcript and use Whisper directly")
    parser.add_argument("--no-whisper", action="store_true", help="Skip Whisper transcription")

    args = parser.parse_args()

    if not args.url:
        threading.Thread(target=open_browser, daemon=True).start()
        script_path = os.path.join(os.path.dirname(__file__), "streamlit_app.py")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "--server.port", "12820",
            "--server.headless", "true",
            script_path
        ])
        sys.exit(0)

    with tempfile.TemporaryDirectory() as temp_dir:
        is_local = downloader.is_local_path(args.url)
        
        audio_path = None
        metadata: dict = {}
        transcript = None
        
        if is_local:
            metadata = downloader.get_file_metadata(args.url)
        else:
            metadata = downloader.get_video_metadata(args.url)
            
        file_id = metadata['id']
            
        if not args.no_cache:
            transcript = transcriber.load_cached_transcript(file_id)
            if transcript:
                print(f"Using cached transcript. (length: {len(transcript)})")
        
        if not transcript and not is_local and not args.no_yt_subs:
            print("Trying to fetch YouTube transcript...")
            transcript, status = transcript_fetcher.fetch_youtube_transcript(args.url)
            if transcript:
                print(f"{GREEN}Using YouTube transcript: {status}{RESET}")
                transcriber.save_transcript(file_id, transcript)
            else:
                print(f"{YELLOW}YouTube transcript unavailable: {status}{RESET}")
        
        if not transcript:
            if args.no_whisper:
                print(f"{RED}Error: No transcript source available. Enable YouTube or Whisper.{RESET}")
                sys.exit(1)
            if is_local:
                print("Extracting audio from local file...")
                audio_path, metadata = downloader.extract_audio_from_file(args.url, temp_dir)
                print(f"{GREEN}File: {metadata.get('title', 'N/A')}{RESET}")
            else:
                print("Downloading audio...")
                audio_path, metadata = downloader.download_audio(args.url, temp_dir)
                print(f"{GREEN}Video: {metadata.get('title', 'N/A')} by {metadata.get('channel', 'N/A')}{RESET}")
            print(f"{GREEN}Audio extracted: {audio_path}{RESET}")

        if not transcript and audio_path:
            print("Transcribing with Whisper...")
            transcript = transcriber.transcribe_audio(audio_path, args.whisper_model)
            
            if not args.no_cache:
                transcriber.save_transcript(file_id, transcript)
                print(f"{GREEN}Transcription complete and cached.{RESET}")
            else:
                print(f"{GREEN}Transcription complete.{RESET}")

            if not args.keep_audio:
                os.remove(audio_path)
                print(f"Audio file removed.")

        print("Generating summary with Ollama...")
        try:
            assert transcript is not None
            summary = summarizer.summarize_text(transcript, args.prompt, args.model, metadata)
        except Exception as e:
            print(f"{RED}Error: {str(e)}{RESET}")
            sys.exit(1)
        
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(summary)
            print(f"{GREEN}Summary saved to: {args.output}{RESET}")
        else:
            print("\n--- Summary ---\n")
            print(summary)


if __name__ == "__main__":
    main()
