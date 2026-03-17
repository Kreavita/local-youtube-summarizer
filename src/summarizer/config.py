import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
SUMMARY_PROMPT = os.getenv("SUMMARY_PROMPT", "Provide a concise summary of the following transcript in bullet points:")
CONTEXT_WINDOW = int(os.getenv("CONTEXT_WINDOW", "32768"))
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "large-v3-turbo")
