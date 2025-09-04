import os
import time
import json
import requests
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

FPL_BASE = "https://fantasy.premierleague.com/api"

# -------- Simple in-memory cache --------
CACHE = {}

def cache_get(key: str, ttl: int = 60):
    item = CACHE.get(key)
    if not item:
        return None
    ts, data = item
    if time.time() - ts > ttl:
        return None
    return data

def cache_set(key: str, data):
    CACHE[key] = (time.time(), data)

def fpl_get(path: str, ttl: int = 60):
    """
    Fetch and cache responses from the official FPL API.
    Example path: '/leagues-classic/{league_id}/standings/'
    """
    key = f"FPL:{path}"
    data = cache_get(key, ttl)
    if 
        return data
    r = requests.get(f"{FPL_BASE}{path}", timeout=20)
    r.raise_for_status()
    data = r.json()
    cache_set(key, data)
    return data

# -------- Core endpoints --------
@app.route("/api/league")
def default_league():
    league_id = int(os.getenv("MAIN_LEAGUE_ID", "0"))
    if not league_id:
        return jsonify({"error": "MAIN_LEAGUE_ID not set"}), 400
    data = fpl_get(f"/leagues-classic/{league_id}/standings/", ttl=60)
    return jsonify(data)

@app.route("/api/league/<int:league_id>/summary

