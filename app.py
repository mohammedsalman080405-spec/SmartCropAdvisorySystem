from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests

load_dotenv()

app = Flask(__name__)
CORS(app)

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ---------- Crop Advisory Logic ----------

CROP_DATA = {
    "wheat":    {"temp_min": 12, "temp_max": 25, "humidity_min": 40, "humidity_max": 70, "ph_min": 6.0, "ph_max": 7.5},
    "rice":     {"temp_min": 20, "temp_max": 35, "humidity_min": 60, "humidity_max": 90, "ph_min": 5.5, "ph_max": 7.0},
    "maize":    {"temp_min": 18, "temp_max": 32, "humidity_min": 50, "humidity_max": 80, "ph_min": 5.8, "ph_max": 7.0},
    "potato":   {"temp_min": 10, "temp_max": 22, "humidity_min": 60, "humidity_max": 80, "ph_min": 5.0, "ph_max": 6.5},
    "tomato":   {"temp_min": 18, "temp_max": 30, "humidity_min": 50, "humidity_max": 70, "ph_min": 6.0, "ph_max": 7.0},
    "cotton":   {"temp_min": 20, "temp_max": 38, "humidity_min": 40, "humidity_max": 65, "ph_min": 6.0, "ph_max": 8.0},
    "soybean":  {"temp_min": 20, "temp_max": 30, "humidity_min": 60, "humidity_max": 80, "ph_min": 6.0, "ph_max": 7.0},
    "sugarcane":{"temp_min": 21, "temp_max": 38, "humidity_min": 60, "humidity_max": 90, "ph_min": 6.0, "ph_max": 7.5},
}


def evaluate_crop(crop_name, temp, humidity, ph):
    crop = CROP_DATA.get(crop_name.lower())
    if not crop:
        return None

    issues = []
    suggestions = []

    if temp < crop["temp_min"]:
        issues.append(f"Temperature too low ({temp}°C). Minimum is {crop['temp_min']}°C.")
        suggestions.append("Consider using row covers or greenhouse protection.")
    elif temp > crop["temp_max"]:
        issues.append(f"Temperature too high ({temp}°C). Maximum is {crop['temp_max']}°C.")
        suggestions.append("Provide shade nets and increase irrigation frequency.")

    if humidity < crop["humidity_min"]:
        issues.append(f"Humidity too low ({humidity}%). Minimum is {crop['humidity_min']}%.")
        suggestions.append("Increase irrigation or use mulching to retain moisture.")
    elif humidity > crop["humidity_max"]:
        issues.append(f"Humidity too high ({humidity}%). Maximum is {crop['humidity_max']}%.")
        suggestions.append("Improve field drainage and ensure good air circulation.")

    if ph < crop["ph_min"]:
        issues.append(f"Soil pH too acidic ({ph}). Minimum is {crop['ph_min']}.")
        suggestions.append("Apply agricultural lime to raise the pH.")
    elif ph > crop["ph_max"]:
        issues.append(f"Soil pH too alkaline ({ph}). Maximum is {crop['ph_max']}.")
        suggestions.append("Add sulfur or acidic organic matter to lower the pH.")

    status = "Optimal" if not issues else "Needs Attention"
    return {
        "crop": crop_name,
        "status": status,
        "issues": issues,
        "suggestions": suggestions,
        "ideal_conditions": crop,
    }


# ---------- Routes ----------

@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "SmartCropAdvisorySystem API is running."})


@app.route("/api/crops", methods=["GET"])
def list_crops():
    """Return the list of supported crops."""
    return jsonify({"supported_crops": list(CROP_DATA.keys())})


@app.route("/api/advisory", methods=["POST"])
def crop_advisory():
    """
    Accepts JSON body:
    {
        "crop": "wheat",
        "temperature": 20,
        "humidity": 55,
        "soil_ph": 6.5
    }
    Returns advisory based on local crop data.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body provided."}), 400

    crop = data.get("crop")
    temp = data.get("temperature")
    humidity = data.get("humidity")
    ph = data.get("soil_ph")

    if not all([crop, temp is not None, humidity is not None, ph is not None]):
        return jsonify({"error": "Fields required: crop, temperature, humidity, soil_ph"}), 400

    result = evaluate_crop(crop, float(temp), float(humidity), float(ph))
    if result is None:
        return jsonify({"error": f"Crop '{crop}' not found. Use /api/crops to see supported crops."}), 404

    return jsonify(result)


@app.route("/api/weather", methods=["GET"])
def get_weather():
    """
    Query params: ?city=Hyderabad
    Returns current weather from OpenWeatherMap.
    """
    city = request.args.get("city")
    if not city:
        return jsonify({"error": "Query parameter 'city' is required."}), 400

    if not OPENWEATHER_API_KEY:
        return jsonify({"error": "OPENWEATHER_API_KEY not set in environment."}), 500

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }
    resp = requests.get(url, params=params, timeout=10)

    if resp.status_code != 200:
        return jsonify({"error": "Failed to fetch weather data.", "details": resp.json()}), resp.status_code

    weather = resp.json()
    return jsonify({
        "city": weather["name"],
        "country": weather["sys"]["country"],
        "temperature": weather["main"]["temp"],
        "feels_like": weather["main"]["feels_like"],
        "humidity": weather["main"]["humidity"],
        "weather": weather["weather"][0]["description"],
        "wind_speed": weather["wind"]["speed"],
    })


@app.route("/api/recommend", methods=["POST"])
def recommend_crop():
    """
    Accepts JSON body:
    {
        "temperature": 25,
        "humidity": 65,
        "soil_ph": 6.5,
        "rainfall": 200    (optional, mm/month)
    }
    Returns the best matching crop(s).
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body provided."}), 400

    temp = float(data.get("temperature", 0))
    humidity = float(data.get("humidity", 0))
    ph = float(data.get("soil_ph", 0))

    matches = []
    for crop_name, cond in CROP_DATA.items():
        score = 0
        if cond["temp_min"] <= temp <= cond["temp_max"]:
            score += 1
        if cond["humidity_min"] <= humidity <= cond["humidity_max"]:
            score += 1
        if cond["ph_min"] <= ph <= cond["ph_max"]:
            score += 1
        if score > 0:
            matches.append({"crop": crop_name, "match_score": score, "max_score": 3})

    matches.sort(key=lambda x: x["match_score"], reverse=True)
    return jsonify({
        "input": {"temperature": temp, "humidity": humidity, "soil_ph": ph},
        "recommendations": matches[:5],
    })


@app.route("/api/ai-advisory", methods=["POST"])
def ai_advisory():
    """
    Uses Google Gemini to provide a natural language crop advisory.
    Accepts JSON body:
    {
        "crop": "wheat",
        "temperature": 20,
        "humidity": 55,
        "soil_ph": 6.5,
        "location": "Punjab, India"   (optional)
    }
    """
    if not GEMINI_API_KEY:
        return jsonify({"error": "GEMINI_API_KEY not set in environment."}), 500

    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body provided."}), 400

    crop = data.get("crop", "unknown")
    temp = data.get("temperature", "unknown")
    humidity = data.get("humidity", "unknown")
    ph = data.get("soil_ph", "unknown")
    location = data.get("location", "unspecified location")

    prompt = (
        f"You are an expert agricultural advisor. A farmer in {location} is growing {crop}. "
        f"Current conditions: Temperature={temp}°C, Humidity={humidity}%, Soil pH={ph}. "
        f"Provide a concise advisory (3-5 sentences) covering: crop health assessment, "
        f"any immediate concerns, and top 2 actionable recommendations."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    resp = requests.post(url, json=payload, timeout=20)

    if resp.status_code != 200:
        return jsonify({"error": "Gemini API call failed.", "details": resp.json()}), resp.status_code

    try:
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return jsonify({"error": "Unexpected Gemini response format."}), 500

    return jsonify({"crop": crop, "location": location, "advisory": text})


if __name__ == "__main__":
    app.run(debug=True, port=5000)