import requests
from .config import OLLAMA_BASE_URL, OLLAMA_MODEL


def summarize_text(text: str, prompt: str, model: str = None) -> str:
    """Send transcript to Ollama and get summary."""
    model = model or OLLAMA_MODEL
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
