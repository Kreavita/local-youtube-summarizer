# YouTube Video Summarizer

A CLI tool that downloads audio from YouTube videos, transcribes using Whisper, and generates summaries via Ollama.

## Features

- Download audio from YouTube videos (yt-dlp)
- Local transcription with OpenAI Whisper
- Customizable summary prompts via Ollama
- Simple CLI interface

## Requirements

- Python 3.10+
- FFmpeg (for audio extraction)
- Ollama running locally or remote

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd summarizer
```

2. Run the setup script to create virtual environment and install dependencies:

**Linux/macOS:**
```bash
./setup.sh
```

**Windows:**
```cmd
setup.bat
```

3. Activate the virtual environment:

**Linux/macOS:**
```bash
source venv/bin/activate
```

**Windows:**
```cmd
venv\Scripts\activate
```

The package is installed in editable mode, so you can run it from anywhere.

4. Configure your environment:
```bash
cp .env.example .env
# Edit .env with your Ollama endpoint and other settings
```

## Configuration

Create a `.env` file with the following variables:

```env
# Ollama endpoint (default: http://localhost:11434)
OLLAMA_BASE_URL=http://localhost:11434

# Ollama model to use for summarization
OLLAMA_MODEL=llama3.2

# Custom summary prompt (optional)
SUMMARY_PROMPT=Provide a concise summary of the following transcript in bullet points:

# Whisper model size (tiny, base, small, medium, large)
WHISPER_MODEL=base
```

## Usage

```bash
# Basic usage - summarize a YouTube video
summarizer "https://www.youtube.com/watch?v=VIDEO_ID"

# Or with python -m (if in project directory)
python -m summarizer "https://www.youtube.com/watch?v=VIDEO_ID"

# Specify a custom prompt
summarizer "https://www.youtube.com/watch?v=VIDEO_ID" --prompt "Summarize in German:"

# Use a different Ollama model
summarizer "https://www.youtube.com/watch?v=VIDEO_ID" --model llama3.1

# Save output to file
summarizer "https://www.youtube.com/watch?v=VIDEO_ID" --output summary.txt
```

## CLI Options

| Option | Description |
|--------|-------------|
| `url` | YouTube video URL (required) |
| `--prompt`, `-p` | Custom summary prompt |
| `--model`, `-m` | Ollama model name |
| `--output`, `-o` | Output file for summary |
| `--whisper-model` | Whisper model size |
| `--keep-audio` | Keep downloaded audio file after processing |

## Project Structure

```
summarizer/
├── src/
│   └── summarizer/
│       ├── __init__.py
│       ├── cli.py          # CLI entry point
│       ├── downloader.py   # YouTube audio downloader
│       ├── transcriber.py  # Whisper transcription
│       ├── summarizer.py   # Ollama summarization
│       └── config.py       # Configuration handling
├── setup.sh                # Virtual environment setup (Linux/macOS)
├── setup.bat               # Virtual environment setup (Windows)
├── .env.example            # Environment template
├── requirements.txt        # Python dependencies
└── README.md
```

## Development

Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

## License

MIT
