"""www.nba.com path segment per franchise (e.g. /cavaliers/game/{game_id}/...).

These match team subsite URLs such as https://www.nba.com/cavaliers/game/...
Generic https://www.nba.com/game/{game_id}/play-by-play is often broken for older games
while team routes still serve __NEXT_DATA__.
"""

from __future__ import annotations

# NBA Stats API TEAM_ID -> last path segment under www.nba.com/<slug>/...
TEAM_ID_TO_NBA_COM_SLUG: dict[int, str] = {
    1610612737: "hawks",
    1610612738: "celtics",
    1610612751: "nets",
    1610612766: "hornets",
    1610612741: "bulls",
    1610612739: "cavaliers",
    1610612742: "mavericks",
    1610612743: "nuggets",
    1610612765: "pistons",
    1610612744: "warriors",
    1610612745: "rockets",
    1610612754: "pacers",
    1610612746: "clippers",
    1610612747: "lakers",
    1610612763: "grizzlies",
    1610612748: "heat",
    1610612749: "bucks",
    1610612750: "timberwolves",
    1610612740: "pelicans",
    1610612752: "knicks",
    1610612760: "thunder",
    1610612753: "magic",
    1610612755: "sixers",
    1610612756: "suns",
    1610612757: "blazers",
    1610612758: "kings",
    1610612759: "spurs",
    1610612761: "raptors",
    1610612762: "jazz",
    1610612764: "wizards",
}


def team_site_urls(game_id: str, home_team_id: int | None, away_team_id: int | None) -> list[tuple[str, str]]:
    """Return (url, label) pairs for team-site game pages to try after the generic URL fails."""
    out: list[tuple[str, str]] = []
    seen_urls: set[str] = set()
    for tid, role in ((home_team_id, "home"), (away_team_id, "away")):
        if tid is None:
            continue
        slug = TEAM_ID_TO_NBA_COM_SLUG.get(int(tid))
        if not slug:
            continue
        for suffix, kind in (("play-by-play", "pbp"), ("box-score", "box")):
            url = f"https://www.nba.com/{slug}/game/{game_id}/{suffix}"
            if url not in seen_urls:
                seen_urls.add(url)
                out.append((url, f"team_{role}_{kind}"))
    return out
