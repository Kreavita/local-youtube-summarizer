import requests
from .config import OLLAMA_BASE_URL, OLLAMA_MODEL


def format_metadata(metadata: dict) -> str:
    """Format video metadata for the prompt."""
    upload_date = metadata.get('upload_date', '')
    if upload_date and len(upload_date) == 8:
        upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    
    lines = [
        "Video Information:",
        f"- Title: {metadata.get('title', 'N/A')}",
        f"- Channel: {metadata.get('channel', 'N/A')}",
        f"- Upload Date: {upload_date or 'N/A'}",
    ]
    desc = metadata.get('description', '').strip()
    if desc:
        lines.append(f"- Description: {desc[:500]}{'...' if len(desc) > 500 else ''}")
    return '\n'.join(lines)


def summarize_text(text: str, prompt: str, model: str = None, metadata: dict = None) -> str:
    """Send transcript to Ollama and get summary."""
    model = model or OLLAMA_MODEL
    
    metadata_section = format_metadata(metadata) if metadata else ""
    
    if metadata_section:
        full_prompt = f"{prompt}\n\n{metadata_section}\n\nTranscript:\n{text}"
    else:
        full_prompt = f"{prompt}\n\n{text}"

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": model,
            "prompt": full_prompt,
            "stream": False
        }
    )

    result = response.json()
    return result.get("response", "")
