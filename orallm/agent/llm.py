"""Interface with a local Ollama large language model."""
from __future__ import annotations

from typing import Any
import requests


def generate(prompt: str, model: str = "llama2", **kwargs: Any) -> str:
    """Generate text using a local Ollama server.

    Parameters
    ----------
    prompt:
        Prompt text to send to the model.
    model:
        Name of the model to use. Defaults to ``"llama2"``.
    **kwargs:
        Additional parameters forwarded to the API.

    Returns
    -------
    str
        The generated text returned by the model.  An empty string is
        returned if the request fails.
    """
    url = "http://localhost:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False, **kwargs}
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
    except Exception:
        return ""
    data = response.json()
    return data.get("response", "")
