import os, time, requests
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
FPL_BASE = "https://fantasy.premierleague.com/api"

CACHE = {}
def cache_get(key, ttl=60):
    item = CACHE.get(key)
    if not item: return None
    ts, data = item
    if time.time() - ts > ttl:
        return None
    return data
def cache_set(key, data):
    CACHE[key] = (time.time(), data)

def fpl_get(path, ttl=60):
    key = f"FPL:{path}"
    data = cache_get(key, ttl)
    if  return data
    r = requests.get(f"{FPL_BASE}{path}", timeout=20)
    r.raise_for_status()
    data = r.json()
    cache_set(key, data)
    return data

@app.route("/api/league")
def default_league():
    league_id = int(os.getenv("MAIN_LEAGUE_ID", "0"))
    if not league_id:
        return jsonify({"error": "MAIN_LEAGUE_ID not set"}), 400
    return jsonify(fpl_get(f"/leagues-classic/{league_id}/standings/", ttl=60))

@app.route("/api/league/<int:league_id>/summary")
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
            "total": x.get("total")
        } for x in standings[:5]
    ]
    return jsonify({
        "league_id": league_id,
        "league_name": league_name,
        "top5": top5,
        "managers": data.get("standings", {}).get("total", len(standings))
    })

@app.route("/api/event/<int:event_id>/live")
def event_live(event_id: int):
    return jsonify(fpl_get(f"/event/{event_id}/live/", ttl=30))

@app.route("/api/entry/<int:manager_id>/gw/<int:event_id>")
def entry_picks(manager_id: int, event_id: int):
    return jsonify(fpl_get(f"/entry/{manager_id}/event/{event_id}/picks/", ttl=60))

import os, json

# Optional: a JSON array to hold future rule configs
PRIZE_RULES = json.loads(os.getenv("PRIZE_RULES_JSON", "[]"))

@app.route("/api/prizes/<int:league_id>/gw/<int:event_id>")
def compute_prizes(league_id: int, event_id: int):
    try:
        topN = int(os.getenv("PRIZE_TOP_N", "20"))
    except ValueError:
        topN = 20

    # Get league standings (reuse your cached fetch helper if you have one)
    league_data = requests.get(
        f"https://fantasy.premierleague.com/api/leagues-classic/{league_id}/standings/",
        timeout=20
    ).json()
    standings = league_data.get("standings", {}).get("results", [])

    best = None
    for row in standings[:topN]:
        entry_id = row.get("entry")
        # Picks + entry_history include GW points
        picks = requests.get(
            f"https://fantasy.premierleague.com/api/entry/{entry_id}/event/{event_id}/picks/",
            timeout=20
        ).json()
        gw_points = picks.get("entry_history", {}).get("points", 0)

        if best is None or gw_points > best["points"]:
            best = {
                "entry": entry_id,
                "entry_name": row.get("entry_name"),
                "player_name": row.get("player_name"),
                "points": gw_points
            }

    return jsonify({
        "league_id": league_id,
        "event_id": event_id,
        "topN": topN,
        "highest_gw_points": best
    })

