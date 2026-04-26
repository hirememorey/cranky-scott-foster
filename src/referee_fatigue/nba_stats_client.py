"""Small NBA Stats API client for referee fatigue analysis."""

from __future__ import annotations

import hashlib
import json
import logging
import random
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class NBAStatsClient:
    """Cached, rate-limited client for the NBA Stats endpoints used here."""

    def __init__(
        self,
        cache_dir: str | Path = "data/cache",
        cache_expiration: timedelta = timedelta(days=30),
        min_request_interval: float = 1.2,
        timeout: int = 60,
    ) -> None:
        self.base_url = "https://stats.nba.com/stats"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_expiration = cache_expiration
        self.min_request_interval = min_request_interval
        self.timeout = timeout
        self.last_request_time = 0.0

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
                "Origin": "https://www.nba.com",
                "Referer": "https://www.nba.com/",
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/140.0.0.0 Safari/537.36"
                ),
                "x-nba-stats-origin": "stats",
                "x-nba-stats-token": "true",
            }
        )

        retries = Retry(
            total=5,
            backoff_factor=2,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get_box_score_summary(self, game_id: str) -> dict[str, Any]:
        """Get game metadata, including OfficialsInfo, from boxscoresummaryv2."""
        return self._make_request("boxscoresummaryv2", {"GameID": game_id})

    def get_nba_game_page_data(self, game_id: str) -> dict[str, Any]:
        """Get embedded page data from nba.com/game/{game_id}/play-by-play."""
        cache_path = self._cache_path("nba_game_page", {"GameID": game_id})
        cached = self._read_cache(cache_path)
        if cached is not None:
            return cached

        self._wait()
        url = f"https://www.nba.com/game/{game_id}/play-by-play"
        logger.info("Requesting NBA game page %s", url)
        response = self.session.get(
            url,
            headers={
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,"
                    "image/avif,image/webp,image/apng,*/*;q=0.8"
                ),
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Referer": "https://www.nba.com/games",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Upgrade-Insecure-Requests": "1",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = parse_next_data(response.text)
        page_props = data.get("props", {}).get("pageProps", {})
        self._write_cache(cache_path, page_props)
        return page_props

    def get_l2m_report_json(self, game_id: str) -> dict[str, Any]:
        """Get official NBA Last Two Minute report JSON for a game."""
        cache_path = self._cache_path("l2m_report", {"GameID": game_id})
        cached = self._read_cache(cache_path)
        if cached is not None:
            return cached

        self._wait()
        url = f"https://official.nba.com/l2m/json/{game_id}.json"
        logger.info("Requesting L2M JSON %s", url)
        response = self.session.get(
            url,
            headers={
                "Accept": "application/json, text/plain, */*",
                "Referer": f"https://official.nba.com/l2m/L2MReport.html?gameId={game_id}",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        self._write_cache(cache_path, data)
        return data

    def get_play_by_play(
        self, game_id: str, start_period: int = 1, end_period: int = 10
    ) -> dict[str, Any]:
        """Get play-by-play rows from playbyplayv2."""
        return self._make_request(
            "playbyplayv2",
            {
                "GameID": game_id,
                "StartPeriod": str(start_period),
                "EndPeriod": str(end_period),
            },
        )

    def _make_request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        cache_path = self._cache_path(endpoint, params)
        cached = self._read_cache(cache_path)
        if cached is not None:
            return cached

        self._wait()
        url = f"{self.base_url}/{endpoint}"
        logger.info("Requesting %s params=%s", endpoint, params)
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        self._write_cache(cache_path, data)
        return data

    def _cache_path(self, endpoint: str, params: dict[str, Any]) -> Path:
        payload = {"endpoint": endpoint, "params": params}
        cache_key = hashlib.md5(
            json.dumps(payload, sort_keys=True).encode("utf-8")
        ).hexdigest()
        return self.cache_dir / f"{cache_key}.json"

    def _read_cache(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        modified_at = datetime.fromtimestamp(path.stat().st_mtime)
        if datetime.now() - modified_at > self.cache_expiration:
            return None
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_cache(self, path: Path, data: dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle)

    def _wait(self) -> None:
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        time.sleep(random.uniform(0.2, 0.8))
        self.last_request_time = time.time()


def result_set_to_records(
    response: dict[str, Any], result_set_name: str
) -> list[dict[str, Any]]:
    """Convert a named NBA Stats result set into dict records."""
    result_sets = response.get("resultSets") or response.get("ResultSets") or []
    for result_set in result_sets:
        if result_set.get("name") != result_set_name:
            continue
        headers = result_set.get("headers", [])
        return [dict(zip(headers, row)) for row in result_set.get("rowSet", [])]
    return []


def parse_next_data(html: str) -> dict[str, Any]:
    """Parse the JSON payload embedded in a Next.js NBA page."""
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
    )
    if not match:
        raise ValueError("NBA page did not include __NEXT_DATA__")
    return json.loads(match.group(1))

