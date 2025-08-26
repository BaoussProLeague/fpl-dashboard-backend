from flask import Flask, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

@app.route('/api/leagues/<int:league_id>')
def league_standings(league_id):
    url = f'https://fantasy.premierleague.com/api/leagues-classic/{league_id}/standings/'
    resp = requests.get(url)
    return jsonify(resp.json())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
