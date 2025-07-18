from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Render PostgreSQL connection
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://aircraft_data_user:6PZIW63RoeCj5cthsEPTZaCeSZm2ZQEQ@dpg-d1t092emcj7s73b0mhlg-a.oregon-postgres.render.com/aircraft_data"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# SQLAlchemy Model
class AircraftData(db.Model):
    __tablename__ = 'aircraft_data'

    id = db.Column(db.Integer, primary_key=True)
    icao24 = db.Column(db.String(10))
    callsign = db.Column(db.String(10))
    origin_country = db.Column(db.String(50))
    time_position = db.Column(db.BigInteger)
    last_contact = db.Column(db.BigInteger)
    longitude = db.Column(db.Float)
    latitude = db.Column(db.Float)
    baro_altitude = db.Column(db.Float)
    on_ground = db.Column(db.Boolean)
    velocity = db.Column(db.Float)
    true_track = db.Column(db.Float)
    vertical_rate = db.Column(db.Float)
    sensors = db.Column(db.String(200))
    geo_altitude = db.Column(db.Float)
    squawk = db.Column(db.String(10))
    spi = db.Column(db.Boolean)
    position_source = db.Column(db.Integer)
    category = db.Column(db.Integer)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)  # Renamed from 'timestamp'

@app.route('/')
def home():
    return "Aircraft Tracker API with OpenSky fallback to DB."

@app.route('/aircrafts', methods=['GET'])
def get_aircrafts():
    try:
        # Fetch live data from OpenSky Network
        response = requests.get("https://opensky-network.org/api/states/all", timeout=5)
        response.raise_for_status()
        data = response.json()

        aircrafts = []
        for state in data.get("states", [])[:10]:  # Limit to 10 entries
            aircrafts.append({
                'icao24': state[0],
                'callsign': state[1],
                'origin_country': state[2],
                'longitude': state[5],
                'latitude': state[6],
                'baro_altitude': state[7],
                'geo_altitude': state[13],
                'velocity': state[9],
                'on_ground': state[8]
            })
        return jsonify({'source': 'opensky', 'aircrafts': aircrafts})

    except Exception as e:
        print("OpenSky fetch failed, using database. Reason:", str(e))

        # Fallback to database
        aircrafts = AircraftData.query.order_by(AircraftData.recorded_at.desc()).limit(10).all()
        data = [{
            'icao24': a.icao24,
            'callsign': a.callsign,
            'origin_country': a.origin_country,
            'longitude': a.longitude,
            'latitude': a.latitude,
            'baro_altitude': a.baro_altitude,
            'geo_altitude': a.geo_altitude,
            'velocity': a.velocity,
            'on_ground': a.on_ground
        } for a in aircrafts]
        return jsonify({'source': 'database', 'aircrafts': data})

# Local dev entry point; use Gunicorn for production
if __name__ == '__main__':
    app.run(debug=True)
