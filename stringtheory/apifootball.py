"""Thin API-Football (api-sports.io) client + normaliser into the shortlist model.

Auth: the key is read from the ``API_FOOTBALL_KEY`` environment variable — it
never lives in code or git. Two access styles are supported:

* **direct**  : host ``v3.football.api-sports.io``, header ``x-apisports-key``
* **rapidapi**: host ``api-football-v1.p.rapidapi.com``, header ``x-rapidapi-key``

Network note: this cloud container's egress policy currently blocks api-sports.io,
so run the live fetch on your own machine (or allow-list the host). The client is
written against API-Football v3's documented schema; the pure normaliser and the
scoring engine are fully testable offline with cached JSON.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from .shortlist import Fixture, TeamForm

DIRECT_HOST = "https://v3.football.api-sports.io"
RAPIDAPI_HOST = "https://api-football-v1.p.rapidapi.com/v3"

# Map how API-Football labels a competition to our on/off-method buckets.
# league.type is "League" or "Cup"; national-team comps carry country "World".
def _competition_type(league: dict) -> str:
    country = (league.get("country") or "").strip().lower()
    if country in ("world", "") or "international" in country:
        return "international"
    return "cup" if (league.get("type") or "").lower() == "cup" else "league"


@dataclass
class Client:
    api_key: Optional[str] = None
    mode: str = "direct"                 # "direct" | "rapidapi"
    # Injectable fetcher for testing; defaults to real HTTP.
    fetch: Optional[Callable[[str, str, dict], dict]] = None

    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.environ.get("API_FOOTBALL_KEY")
        if self.fetch is None:
            self.fetch = self._http_get

    @property
    def _base(self) -> str:
        return RAPIDAPI_HOST if self.mode == "rapidapi" else DIRECT_HOST

    def _headers(self) -> dict:
        if self.mode == "rapidapi":
            return {"x-rapidapi-key": self.api_key or "",
                    "x-rapidapi-host": "api-football-v1.p.rapidapi.com"}
        return {"x-apisports-key": self.api_key or ""}

    def _http_get(self, path: str, params: dict) -> dict:
        query = urllib.parse.urlencode(params)
        url = f"{self._base}{path}?{query}"
        req = urllib.request.Request(url, headers=self._headers())
        with urllib.request.urlopen(req, timeout=30) as resp:   # nosec - user-run
            return json.loads(resp.read().decode("utf-8"))

    # --- endpoints ---
    def fixtures_by_date(self, date: str) -> List[dict]:
        return self.fetch("/fixtures", {"date": date}).get("response", [])

    def standings(self, league_id: int, season: int) -> List[dict]:
        data = self.fetch("/standings", {"league": league_id, "season": season})
        resp = data.get("response", [])
        if not resp:
            return []
        # response[0].league.standings is a list of groups; flatten.
        groups = resp[0].get("league", {}).get("standings", [])
        return [row for group in groups for row in group]


# --- normalisation (pure; testable offline) ----------------------------------

def _team_from_standing(row: dict) -> TeamForm:
    team = row.get("team", {})
    allrec = row.get("all", {})
    goals = allrec.get("goals", {})
    return TeamForm(
        name=team.get("name", "?"),
        rank=row.get("rank"),
        points=row.get("points"),
        played=allrec.get("played", 0) or 0,
        goals_for=goals.get("for", 0) or 0,
        goals_against=goals.get("against", 0) or 0,
        form=(row.get("form") or "")[-10:],
    )


def normalise(fixtures_raw: List[dict],
              standings_by_league: Dict[int, List[dict]]) -> List[Fixture]:
    """Turn raw API-Football fixtures + standings into Fixture objects.

    ``standings_by_league`` maps league_id -> list of standing rows (as returned
    by ``Client.standings``). Teams are matched to their standing row by team id.
    """
    out: List[Fixture] = []
    for fx in fixtures_raw:
        league = fx.get("league", {})
        teams = fx.get("teams", {})
        home = teams.get("home", {})
        away = teams.get("away", {})
        rows = standings_by_league.get(league.get("id"), [])
        by_id = {r.get("team", {}).get("id"): r for r in rows}

        def form_for(team):
            row = by_id.get(team.get("id"))
            return _team_from_standing(row) if row else TeamForm(name=team.get("name", "?"))

        out.append(
            Fixture(
                league_name=league.get("name", "?"),
                country=league.get("country", "?"),
                competition_type=_competition_type(league),
                home=form_for(home),
                away=form_for(away),
                kickoff=(fx.get("fixture", {}).get("date", "") or "")[11:16],
                league_size=len(rows) or 20,
            )
        )
    return out


def fixtures_for_date(date: str, client: Optional[Client] = None,
                      season: Optional[int] = None) -> List[Fixture]:
    """Live path: fetch fixtures + the standings for each league in play."""
    client = client or Client()
    raw = client.fixtures_by_date(date)
    season = season or int(date[:4])
    standings: Dict[int, List[dict]] = {}
    for fx in raw:
        lid = fx.get("league", {}).get("id")
        if lid is not None and lid not in standings:
            try:
                standings[lid] = client.standings(lid, fx["league"].get("season", season))
            except Exception:
                standings[lid] = []
    return normalise(raw, standings)
