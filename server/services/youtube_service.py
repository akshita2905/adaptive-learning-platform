"""
YouTube Data API v3: search for tutorial videos by topic string.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

logger = logging.getLogger(__name__)


def get_youtube_videos(topic: str, api_key: str, max_results: int = 3) -> list[dict[str, Any]]:
    """
    Fetch up to ``max_results`` videos for a search query.

    Returns list of dicts: title, thumbnail, url. Empty list if API key missing or on error.
    Missing ``YOUTUBE_API_KEY`` is logged once at startup in ``config.get_settings``.
    """
    if not (api_key or "").strip() or not str(topic).strip():
        return []

    params = {
        "part": "snippet",
        "q": topic.strip(),
        "type": "video",
        "maxResults": str(max(1, min(int(max_results), 10))),
        "key": api_key,
        "safeSearch": "moderate",
    }
    url = "https://www.googleapis.com/youtube/v3/search?" + urlencode(params)

    try:
        with urlopen(url, timeout=18) as resp:
            raw = resp.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        logger.warning("YouTube API request failed for topic=%r: %s", topic[:80], exc)
        return []

    import json

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("YouTube API returned non-JSON")
        return []

    out: list[dict[str, Any]] = []
    for it in data.get("items", [])[:max_results]:
        vid = (it.get("id") or {}).get("videoId")
        if not vid:
            continue
        sn = it.get("snippet") or {}
        thumbs = sn.get("thumbnails") or {}
        thumb = thumbs.get("medium") or thumbs.get("default") or {}
        out.append(
            {
                "title": sn.get("title", "Video")[:200],
                "thumbnail": thumb.get("url", ""),
                "url": f"https://www.youtube.com/watch?v={vid}",
            }
        )
    return out
