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
    parser.add_argument("--whisper-model", default=WHISPER_MODEL, help="Whisper model size (tiny, base, small, medium, large-v3-turbo, large-v3, turbo)")
    parser.add_argument("--output", "-o", help="Output file for summary")
    parser.add_argument("--keep-audio", action="store_true", help="Keep downloaded audio file after processing")
    parser.add_argument("--no-cache", action="store_true", help="Disable transcript caching")

    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as temp_dir:
        metadata = downloader.get_video_metadata(args.url)
        
        transcript = None
        if not args.no_cache:
            transcript = transcriber.load_cached_transcript(metadata['id'])
                    
        if transcript:
            print(f"Using cached transcript. (length: {len(transcript)})")
        else:
            print("Downloading audio...")
            audio_path, metadata = downloader.download_audio(args.url, temp_dir)
            print(f"Audio downloaded: {audio_path}")
            print(f"Video: {metadata.get('title', 'N/A')} by {metadata.get('channel', 'N/A')}")

            print("Transcribing with Whisper...")
            transcript = transcriber.transcribe_audio(audio_path, args.whisper_model)
            
            if not args.no_cache:
                transcriber.save_transcript(metadata['id'], transcript)
                print("Transcription complete and cached.")
            else:
                print("Transcription complete.")

            if not args.keep_audio:
                os.remove(audio_path)
                print("Audio file removed.")

        print("Generating summary with Ollama...")
        summary = summarizer.summarize_text(transcript, args.prompt, args.model, metadata)
        
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(summary)
            print(f"Summary saved to: {args.output}")
        else:
            print("\n--- Summary ---\n")
            print(summary)


if __name__ == "__main__":
    main()
