"""Web browsing utilities using DuckDuckGo."""
from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


def search(query: str) -> str:
    """Search the web using DuckDuckGo.

    Parameters
    ----------
    query:
        Search query string.

    Returns
    -------
    str
        A short snippet from the first search result if available, otherwise
        an empty string.
    """
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_redirect": 1, "no_html": 1}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
    except Exception as exc:  # pragma: no cover - network errors
        logger.exception("DuckDuckGo search failed: %s", exc)
        return ""

    if data.get("AbstractText"):
        return data["AbstractText"]
    topics = data.get("RelatedTopics")
    if isinstance(topics, list) and topics:
        first = topics[0]
        if isinstance(first, dict) and "Text" in first:
            return str(first["Text"])
    return ""
