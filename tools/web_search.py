"""Simple web search tool using DuckDuckGo as an example."""
from __future__ import annotations

import requests


def search(query: str) -> str:
    """Search the web and return a short summary.

    Parameters
    ----------
    query: str
        Search keyword.

    Returns
    -------
    str
        Summary text from the search result.
    """

    resp = requests.get(
        "https://duckduckgo.com/api",
        params={"q": query, "format": "json"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("AbstractText", "No summary available.")
