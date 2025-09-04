from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os, time, json, requests

app = FastAPI()
FPL_BASE = "https://fantasy.premierleague.com/api"
CACHE = {}

def cache_get(key, ttl=60):
    item = CACHE.get(key)
    if not item:
        return None
    ts, data = item
    if time.time() - ts > ttl:
        return None
    return data

def cache_set(key, data):
    CACHE[key] = (time.time(), data)

def fpl_get(path: str, ttl: int = 60):
    key = f"FPL:{path}"
    data = cache_get(key, ttl)
    if 
        return data
    r = requests.get(f"{FPL_BASE}{path}", timeout=20)
    r.raise_for_status()
    data = r.json()
    cache_set(key, data)
    return data

def getenv_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default

def load_json_env(var_name: str, default):
    raw = os.getenv(var_name, "")
    if not raw or not raw.strip():
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/league")
def default_league():
    league_id = getenv_int("MAIN_LEAGUE_ID", 0)
    if not league_id:
        return JSONResponse({"error": "MAIN_LEAGUE_ID not set"}, status_code=400)
    return fpl_get(f"/leagues-classic/{league_id}/standings/", ttl=60)

@app.get("/api/league/{league_id}/summary")
def league_summary(league_id: int):
    data = fpl_get(f"/leagues-classic/{league_id}/standings/", ttl=60)
    standings = data.get("standings", {}).get("results", [])
    league_name = data.get("league", {}).get("name")
    top5 = [
        {
            "rank": x.get("rank"),
            "entry": x.get("entry"),
            "entry_name": x.get("entry_name"),
            "player_name": x.get("player_name"),
            "total": x.get("total"),
        }
        for x in standings[:5]
    ]
    return {
        "league_id": league_id,
        "league_name": league_name,
        "top5": top5,
        "managers": data.get("standings", {}).get("total", len(standings)),
    }

@app.get("/api/event/{event_id}/live")
def event_live(event_id: int):
    return fpl_get(f"/event/{event_id}/live/", ttl=30)

@app.get("/api/entry/{manager_id}/gw/{event_id}")
def entry_picks(manager_id: int, event_id: int):
    return fpl_get(f"/entry/{manager_id}/event/{event_id}/picks/", ttl=60)

@app.get("/api/prizes/{league_id}/gw/{event_id}")
def compute_prizes(league_id: int, event_id: int):
    topN = getenv_int("PRIZE_TOP_N", 20)
    league_data = fpl_get(f"/leagues-classic/{league_id}/standings/", ttl=60)
    standings = league_data.get("standings", {}).get("results", [])

    best = None
    for row in standings[:topN]:
        entry_id = row.get("entry")
        if not entry_id:
            continue
        picks = fpl_get(f"/entry/{entry_id}/event/{event_id}/picks/", ttl=60)
        gw_points = picks.get("entry_history", {}).get("points", 0)
        if best is None or gw_points > best["points"]:
            best = {
                "entry": entry_id,
                "entry_name": row.get("entry_name"),
                "player_name": row.get("player_name"),
                "points": gw_points,
            }

    rules = load_json_env("PRIZE_RULES_JSON", [])
    return {
        "league_id": league_id,
        "event_id": event_id,
        "topN": topN,
        "highest_gw_points": best,
        "rules": rules,
    }
