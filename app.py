import base64
import os
import secrets
import sqlite3
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "smartcrop.db"))

app = Flask(__name__, template_folder="templates")
CORS(app)

SUPPORTED_CROPS = [
    "rice",
    "wheat",
    "maize",
    "potato",
    "tomato",
    "cotton",
    "soybean",
    "sugarcane",
]

OWM_API_KEY = os.getenv("OWM_API_KEY", "").strip()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free").strip()
HF_API_KEY = os.getenv("HF_API_KEY", os.getenv("HF_TOKEN", "")).strip()
HF_CHAT_MODEL = os.getenv("HF_CHAT_MODEL", "google/gemma-2-2b-it").strip()
PLANTNET_API_KEY = os.getenv("PLANTNET_API_KEY", "").strip()


def get_db_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            village TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS community_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            photo_b64 TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS community_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            is_expert INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES community_posts(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    connection.commit()
    connection.close()


def json_error(message, status_code=400):
    return jsonify({"error": message}), status_code


def get_json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def parse_float(value, field_name):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid or missing '{field_name}'")


def normalize_image_metadata(mime_type):
    allowed_types = {
        "image/jpeg": ("crop.jpeg", "image/jpeg"),
        "image/jpg": ("crop.jpeg", "image/jpeg"),
        "image/png": ("crop.png", "image/png"),
    }
    return allowed_types.get((mime_type or "").lower(), ("crop.jpeg", "image/jpeg"))


def resolve_language_name(language_code):
    languages = {"en": "English", "hi": "Hindi", "te": "Telugu"}
    return languages.get((language_code or "en").lower(), "English")


def find_user_by_phone(phone):
    connection = get_db_connection()
    row = connection.execute(
        "SELECT id, name, phone, village, password_hash FROM users WHERE phone = ?",
        (phone,),
    ).fetchone()
    connection.close()
    return dict(row) if row else None


def create_user(name, phone, village, password):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO users (name, phone, village, password_hash)
        VALUES (?, ?, ?, ?)
        """,
        (name, phone, village, generate_password_hash(password)),
    )
    connection.commit()
    connection.close()


def create_session(user_id):
    token = secrets.token_hex(24)
    connection = get_db_connection()
    connection.execute(
        "INSERT INTO sessions (token, user_id) VALUES (?, ?)",
        (token, user_id),
    )
    connection.commit()
    connection.close()
    return token


def get_user_by_token(token):
    connection = get_db_connection()
    row = connection.execute(
        """
        SELECT users.id, users.name, users.phone, users.village
        FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE sessions.token = ?
        """,
        (token,),
    ).fetchone()
    connection.close()
    return dict(row) if row else None


def delete_session(token):
    connection = get_db_connection()
    connection.execute("DELETE FROM sessions WHERE token = ?", (token,))
    connection.commit()
    connection.close()


def get_bearer_token():
    auth_header = request.headers.get("Authorization", "").strip()
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return ""


def build_recommendations(temperature, humidity, soil_ph):
    crop_profiles = {
        "rice": {"temperature": 28, "humidity": 80, "soil_ph": 6.0},
        "wheat": {"temperature": 22, "humidity": 55, "soil_ph": 6.5},
        "maize": {"temperature": 26, "humidity": 65, "soil_ph": 6.2},
        "potato": {"temperature": 20, "humidity": 70, "soil_ph": 5.8},
        "tomato": {"temperature": 24, "humidity": 60, "soil_ph": 6.4},
        "cotton": {"temperature": 30, "humidity": 50, "soil_ph": 6.8},
        "soybean": {"temperature": 25, "humidity": 60, "soil_ph": 6.3},
        "sugarcane": {"temperature": 29, "humidity": 75, "soil_ph": 6.5},
    }

    recommendations = []
    for crop, profile in crop_profiles.items():
        temp_score = max(0, 4 - abs(temperature - profile["temperature"]) / 5)
        humidity_score = max(0, 3 - abs(humidity - profile["humidity"]) / 15)
        ph_score = max(0, 3 - abs(soil_ph - profile["soil_ph"]) / 0.7)
        match_score = round(temp_score + humidity_score + ph_score, 1)
        recommendations.append(
            {"crop": crop, "match_score": match_score, "max_score": 10}
        )

    recommendations.sort(key=lambda item: item["match_score"], reverse=True)
    return recommendations[:5]


def generate_local_advice(payload):
    crop = payload.get("crop") or "crop"
    question = (payload.get("question") or "Give practical farming advice.").strip()
    temperature = payload.get("temperature")
    humidity = payload.get("humidity")
    soil_ph = payload.get("soil_ph")
    location = payload.get("location") or "your area"

    notes = [f"For {crop} in {location}, here is a practical answer to: {question}"]

    if temperature is not None:
        if temperature > 35:
            notes.append(
                "Temperature is high, so irrigate in the early morning and reduce heat stress."
            )
        elif temperature < 15:
            notes.append(
                "Temperature is on the lower side, so avoid overwatering and watch for slow growth."
            )

    if humidity is not None and humidity < 40:
        notes.append("Humidity is low, so mulching can help retain soil moisture.")

    if soil_ph is not None:
        if soil_ph < 5.5:
            notes.append("Soil is acidic, so lime can help correct pH over time.")
        elif soil_ph > 7.5:
            notes.append(
                "Soil is alkaline, so compost and organic matter can improve nutrient uptake."
            )

    notes.append(
        "Inspect the field twice a week for pests, leaf discoloration, and water stress."
    )
    return " ".join(notes)


def call_openrouter(messages):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "SmartCropAdvisorySystem",
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 220,
        },
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def call_huggingface_chat(messages):
    response = requests.post(
        "https://router.huggingface.co/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {HF_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": HF_CHAT_MODEL,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 220,
        },
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


@app.route("/")
def index():
    return render_template("login.html")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/home")
def home_page():
    return render_template("home.html")


@app.route("/api/register", methods=["POST"])
def register():
    data = get_json_body()
    if not data:
        return json_error("Expected a JSON request body")

    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()
    village = str(data.get("village", "")).strip()
    password = str(data.get("password", ""))

    if not all([name, phone, village, password]):
        return json_error("All fields are required")

    if len(password) < 6:
        return json_error("Password must be at least 6 characters")

    if find_user_by_phone(phone):
        return json_error("Phone number already registered", 409)

    create_user(name, phone, village, password)
    return jsonify({"success": True, "message": "Account created successfully"})


@app.route("/api/login", methods=["POST"])
def login():
    data = get_json_body()
    if not data:
        return json_error("Expected a JSON request body")

    phone = str(data.get("phone", "")).strip()
    password = str(data.get("password", ""))

    if not phone or not password:
        return json_error("Phone and password are required")

    user = find_user_by_phone(phone)
    if not user or not check_password_hash(user["password_hash"], password):
        return json_error("Invalid phone or password", 401)

    token = create_session(user["id"])
    return jsonify(
        {
            "success": True,
            "token": token,
            "farmer": {
                "name": user["name"],
                "phone": user["phone"],
                "village": user["village"],
            },
        }
    )


@app.route("/api/logout", methods=["POST"])
def logout():
    token = get_bearer_token()
    if token:
        delete_session(token)
    return jsonify({"success": True})


@app.route("/api/verify")
def verify():
    token = get_bearer_token()
    if not token:
        return jsonify({"valid": False}), 401

    user = get_user_by_token(token)
    if not user:
        return jsonify({"valid": False}), 401

    return jsonify({"valid": True, "farmer": user})


@app.route("/api/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "Smart Crop Advisory backend",
            "ai_provider": (
                "openrouter"
                if OPENROUTER_API_KEY
                else "huggingface"
                if HF_API_KEY
                else "local-fallback"
            ),
        }
    )


@app.route("/api/crops")
def crops():
    return jsonify({"supported_crops": SUPPORTED_CROPS})


@app.route("/api/weather")
def weather():
    city = (request.args.get("city") or "").strip()
    if not city:
        return json_error("Missing 'city' query parameter")

    if not OWM_API_KEY:
        return json_error("OWM_API_KEY is not configured on the backend", 503)

    response = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": city, "appid": OWM_API_KEY, "units": "metric"},
        timeout=15,
    )
    data = response.json()
    return jsonify(data), response.status_code


@app.route("/api/recommend", methods=["POST"])
def recommend():
    data = get_json_body()
    if not data:
        return json_error("Expected a JSON request body")

    try:
        temperature = parse_float(data.get("temperature"), "temperature")
        humidity = parse_float(data.get("humidity"), "humidity")
        soil_ph = parse_float(data.get("soil_ph"), "soil_ph")
    except ValueError as exc:
        return json_error(str(exc))

    return jsonify(
        {
            "recommendations": build_recommendations(
                temperature=temperature, humidity=humidity, soil_ph=soil_ph
            )
        }
    )


@app.route("/api/advisory", methods=["POST"])
def advisory():
    data = get_json_body()
    if not data:
        return json_error("Expected a JSON request body")

    try:
        temp = parse_float(data.get("temperature"), "temperature")
        humidity = parse_float(data.get("humidity"), "humidity")
        soil_ph = parse_float(data.get("soil_ph"), "soil_ph")
    except ValueError as exc:
        return json_error(str(exc))

    issues = []
    suggestions = []

    if temp > 35:
        issues.append("Temperature too high")
        suggestions.append("Irrigate more frequently and avoid midday watering")
    elif temp < 15:
        issues.append("Temperature too low")
        suggestions.append("Reduce watering and monitor for slow growth")

    if humidity < 40:
        issues.append("Low humidity")
        suggestions.append("Use mulching to retain moisture")

    if soil_ph < 5.5:
        issues.append("Soil too acidic")
        suggestions.append("Add lime gradually after checking dosage")
    elif soil_ph > 7.5:
        issues.append("Soil too alkaline")
        suggestions.append("Add compost or organic matter")

    return jsonify(
        {
            "status": "Optimal" if not issues else "Needs Attention",
            "issues": issues,
            "suggestions": suggestions,
        }
    )


@app.route("/api/ai-advisory", methods=["POST"])
def ai_advisory():
    data = get_json_body()
    if not data:
        return json_error("Expected a JSON request body")

    try:
        temperature = parse_float(data.get("temperature"), "temperature")
        humidity = parse_float(data.get("humidity"), "humidity")
        soil_ph = parse_float(data.get("soil_ph"), "soil_ph")
    except ValueError as exc:
        return json_error(str(exc))

    crop = (data.get("crop") or "unknown crop").strip()
    question = (data.get("question") or "Give simple farming advice.").strip()
    location = (data.get("location") or "India").strip()
    language_name = resolve_language_name(data.get("language"))

    messages = [
        {
            "role": "system",
            "content": (
                "You are an agricultural advisor. Give concise, practical advice for a farmer. "
                "Use simple language, avoid medical or legal claims, and focus on crop health, "
                "watering, soil, pests, and next actions. "
                "Do not use markdown tables. Do not use pipe characters. "
                "Reply in short paragraphs or simple dash bullets with clear spacing. "
                f"Always answer in {language_name}."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Crop: {crop}\n"
                f"Location: {location}\n"
                f"Temperature: {temperature} C\n"
                f"Humidity: {humidity}%\n"
                f"Soil pH: {soil_ph}\n"
                f"Question: {question}"
            ),
        },
    ]

    provider_used = "local-fallback"
    advisory_text = ""

    try:
        if OPENROUTER_API_KEY:
            provider_used = "openrouter"
            advisory_text = call_openrouter(messages)
        elif HF_API_KEY:
            provider_used = "huggingface"
            advisory_text = call_huggingface_chat(messages)
        else:
            advisory_text = generate_local_advice(
                {
                    "crop": crop,
                    "location": location,
                    "temperature": temperature,
                    "humidity": humidity,
                    "soil_ph": soil_ph,
                    "question": question,
                }
            )
    except requests.RequestException as exc:
        advisory_text = (
            generate_local_advice(
                {
                    "crop": crop,
                    "location": location,
                    "temperature": temperature,
                    "humidity": humidity,
                    "soil_ph": soil_ph,
                    "question": question,
                }
            )
            + f" External AI provider failed: {exc.__class__.__name__}."
        )
        provider_used = "local-fallback"

    return jsonify({"advisory": advisory_text, "provider": provider_used})


@app.route("/api/disease", methods=["POST"])
def disease():
    data = get_json_body()
    if not data:
        return json_error("Expected a JSON request body")

    image = data.get("image")
    if not image:
        return json_error("Missing 'image' in request body")

    filename, content_type = normalize_image_metadata(data.get("mime_type"))

    if not PLANTNET_API_KEY:
        return json_error(
            "Disease detection is not configured. Add PLANTNET_API_KEY to the project's .env file and restart the Flask server.",
            503,
        )

    try:
        image_bytes = base64.b64decode(image)
    except Exception:
        return json_error("Image must be base64 encoded")

    try:
        response = requests.post(
            "https://my-api.plantnet.org/v2/diseases/identify",
            params={
                "api-key": PLANTNET_API_KEY,
                "lang": "en",
                "include-related-images": "false",
                "no-reject": "true",
                "nb-results": 3,
            },
            data={"organs": "auto"},
            files={"images": (filename, image_bytes, content_type)},
            timeout=20,
        )
        if not response.ok:
            error_body = response.text.strip()
            return json_error(
                f"Disease API request failed: {response.status_code} {error_body}",
                502,
            )
        result = response.json()
    except requests.RequestException as exc:
        return json_error(f"Disease API request failed: {exc}", 502)

    predictions = result.get("results") if isinstance(result, dict) else None
    if isinstance(predictions, list) and predictions:
        top_result = predictions[0]
        score = round(float(top_result.get("score", 0)) * 100)
        common_name = top_result.get("species", {}).get("commonNames", [])
        common_name = common_name[0] if common_name else None
        label = top_result.get("label") or top_result.get("name") or "Unknown issue"
        disease_name = f"{label} ({common_name})" if common_name else label
        suggestions = [
            "Inspect nearby plants for similar symptoms.",
            "Remove heavily affected leaves if the infection is spreading.",
            "Avoid overhead watering until the issue is confirmed.",
        ]
        return jsonify(
            {
                "disease": disease_name,
                "confidence": f"{score}%",
                "severity": "High" if score >= 85 else "Medium" if score >= 60 else "Low",
                "action": " ".join(suggestions),
                "matches": [
                    {
                        "name": item.get("label") or item.get("name") or "Unknown",
                        "confidence": f"{round(float(item.get('score', 0)) * 100)}%",
                    }
                    for item in predictions[:3]
                ],
            }
        )

    return json_error("Disease API returned no matches for this image", 502)


# ── Crop Calendar ─────────────────────────────────────────────
CROP_CALENDARS = {
    "rice": [
        {"day": 0, "event": "Land preparation & sowing", "icon": "🌱"},
        {"day": 7, "event": "Germination check & gap filling", "icon": "🔍"},
        {"day": 21, "event": "1st Weeding & thinning", "icon": "🌿"},
        {"day": 30, "event": "1st Nitrogen top dressing (Urea)", "icon": "💊"},
        {"day": 45, "event": "Irrigation scheduling review", "icon": "💧"},
        {"day": 55, "event": "Pest & disease scouting", "icon": "🐛"},
        {"day": 60, "event": "2nd Nitrogen top dressing", "icon": "💊"},
        {"day": 75, "event": "Panicle initiation – stop weeding", "icon": "🌾"},
        {"day": 90, "event": "Flowering / pollination phase", "icon": "🌸"},
        {"day": 105, "event": "Grain filling – reduce irrigation", "icon": "🌾"},
        {"day": 120, "event": "Harvesting", "icon": "🚜"},
    ],
    "wheat": [
        {"day": 0, "event": "Land preparation & sowing", "icon": "🌱"},
        {"day": 10, "event": "Germination & emergence check", "icon": "🔍"},
        {"day": 25, "event": "1st Irrigation (Crown Root Initiation)", "icon": "💧"},
        {"day": 35, "event": "1st Nitrogen top dressing", "icon": "💊"},
        {"day": 45, "event": "2nd Irrigation (Tillering stage)", "icon": "💧"},
        {"day": 60, "event": "Rust & aphid scouting", "icon": "🐛"},
        {"day": 70, "event": "3rd Irrigation (Jointing)", "icon": "💧"},
        {"day": 80, "event": "Herbicide application if needed", "icon": "🧪"},
        {"day": 95, "event": "Flowering phase – avoid waterlogging", "icon": "🌸"},
        {"day": 110, "event": "Grain filling stage", "icon": "🌾"},
        {"day": 135, "event": "Harvesting", "icon": "🚜"},
    ],
    "maize": [
        {"day": 0, "event": "Land preparation & sowing", "icon": "🌱"},
        {"day": 7, "event": "Germination check", "icon": "🔍"},
        {"day": 20, "event": "1st Weeding & thinning", "icon": "🌿"},
        {"day": 30, "event": "1st Nitrogen top dressing", "icon": "💊"},
        {"day": 40, "event": "2nd Irrigation", "icon": "💧"},
        {"day": 50, "event": "Stem borer scouting", "icon": "🐛"},
        {"day": 60, "event": "2nd Nitrogen top dressing", "icon": "💊"},
        {"day": 70, "event": "Tasseling / Silking phase", "icon": "🌸"},
        {"day": 85, "event": "Grain filling", "icon": "🌽"},
        {"day": 100, "event": "Harvesting", "icon": "🚜"},
    ],
    "tomato": [
        {"day": 0, "event": "Nursery sowing", "icon": "🌱"},
        {"day": 25, "event": "Transplanting to main field", "icon": "🏡"},
        {"day": 35, "event": "Staking & training", "icon": "🪵"},
        {"day": 40, "event": "1st Fertilizer application", "icon": "💊"},
        {"day": 50, "event": "Pest & disease check (blight, whitefly)", "icon": "🐛"},
        {"day": 60, "event": "Flowering – foliar spray", "icon": "🌸"},
        {"day": 70, "event": "Fruit set – potassium application", "icon": "🍅"},
        {"day": 80, "event": "1st Harvest (continues for 4–6 weeks)", "icon": "🚜"},
    ],
    "cotton": [
        {"day": 0, "event": "Soil preparation & sowing", "icon": "🌱"},
        {"day": 15, "event": "Germination check & gap filling", "icon": "🔍"},
        {"day": 30, "event": "1st Weeding & thinning", "icon": "🌿"},
        {"day": 45, "event": "Nitrogen top dressing", "icon": "💊"},
        {"day": 60, "event": "Bollworm scouting & pheromone traps", "icon": "🐛"},
        {"day": 75, "event": "Squaring stage – potassium application", "icon": "💊"},
        {"day": 90, "event": "Flowering phase", "icon": "🌸"},
        {"day": 110, "event": "Boll development", "icon": "☁️"},
        {"day": 140, "event": "1st Picking (hand harvest)", "icon": "🚜"},
        {"day": 160, "event": "2nd Picking", "icon": "🚜"},
    ],
    "potato": [
        {"day": 0, "event": "Seed preparation & planting", "icon": "🌱"},
        {"day": 15, "event": "Emergence check", "icon": "🔍"},
        {"day": 25, "event": "Earthing up & 1st fertilizer", "icon": "⛏️"},
        {"day": 35, "event": "2nd Irrigation", "icon": "💧"},
        {"day": 45, "event": "Late blight spray", "icon": "🧪"},
        {"day": 60, "event": "Tuber bulking – stop nitrogen", "icon": "🥔"},
        {"day": 75, "event": "Haulm cutting (if needed)", "icon": "✂️"},
        {"day": 90, "event": "Harvesting", "icon": "🚜"},
    ],
    "soybean": [
        {"day": 0, "event": "Seed inoculation & sowing", "icon": "🌱"},
        {"day": 10, "event": "Germination check", "icon": "🔍"},
        {"day": 20, "event": "Weeding", "icon": "🌿"},
        {"day": 35, "event": "Foliar micro-nutrient spray", "icon": "🧪"},
        {"day": 50, "event": "Flowering – avoid stress", "icon": "🌸"},
        {"day": 65, "event": "Pod filling stage", "icon": "🫘"},
        {"day": 90, "event": "Harvesting", "icon": "🚜"},
    ],
    "sugarcane": [
        {"day": 0, "event": "Planting setts", "icon": "🌱"},
        {"day": 20, "event": "Germination check & gap filling", "icon": "🔍"},
        {"day": 45, "event": "1st Weeding & earthing up", "icon": "🌿"},
        {"day": 60, "event": "Nitrogen top dressing", "icon": "💊"},
        {"day": 90, "event": "De-trashing & irrigation", "icon": "💧"},
        {"day": 120, "event": "Grand growth phase – fertilizer", "icon": "💊"},
        {"day": 180, "event": "Maturity assessment – stop irrigation", "icon": "🔍"},
        {"day": 330, "event": "Harvesting", "icon": "🚜"},
    ],
}


@app.route("/api/crop-calendar", methods=["POST"])
def crop_calendar():
    data = get_json_body()
    if not data:
        return json_error("JSON body required")
    crop = (data.get("crop") or "").strip().lower()
    if crop not in CROP_CALENDARS:
        return json_error(f"Crop '{crop}' not supported. Supported: {', '.join(CROP_CALENDARS)}")
    sowing_date_str = (data.get("sowing_date") or "").strip()
    from datetime import datetime, timedelta
    try:
        sowing_date = datetime.strptime(sowing_date_str, "%Y-%m-%d") if sowing_date_str else datetime.today()
    except ValueError:
        return json_error("Invalid sowing_date format. Use YYYY-MM-DD.")
    timeline = []
    for entry in CROP_CALENDARS[crop]:
        target = sowing_date + timedelta(days=entry["day"])
        timeline.append({
            "day": entry["day"],
            "date": target.strftime("%Y-%m-%d"),
            "week": entry["day"] // 7 + 1,
            "event": entry["event"],
            "icon": entry["icon"],
        })
    return jsonify({
        "crop": crop,
        "sowing_date": sowing_date.strftime("%Y-%m-%d"),
        "harvest_date": timeline[-1]["date"],
        "total_days": timeline[-1]["day"],
        "timeline": timeline,
    })


# ── Kisan Community Forum ──────────────────────────────────────
@app.route("/api/community/posts", methods=["GET"])
def get_community_posts():
    tag_filter = request.args.get("tag", "").strip()
    conn = get_db_connection()
    if tag_filter:
        rows = conn.execute(
            """
            SELECT p.id, p.title, p.body, p.photo_b64, p.tags, p.created_at,
                   u.name AS author, u.village,
                   (SELECT COUNT(*) FROM community_replies r WHERE r.post_id = p.id) AS reply_count
            FROM community_posts p JOIN users u ON u.id = p.user_id
            WHERE p.tags LIKE ?
            ORDER BY p.created_at DESC LIMIT 50
            """,
            (f"%{tag_filter}%",),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT p.id, p.title, p.body, p.photo_b64, p.tags, p.created_at,
                   u.name AS author, u.village,
                   (SELECT COUNT(*) FROM community_replies r WHERE r.post_id = p.id) AS reply_count
            FROM community_posts p JOIN users u ON u.id = p.user_id
            ORDER BY p.created_at DESC LIMIT 50
            """,
        ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/community/posts", methods=["POST"])
def create_community_post():
    token = get_bearer_token()
    user = get_user_by_token(token)
    if not user:
        return json_error("Unauthorized", 401)
    data = get_json_body()
    if not data:
        return json_error("JSON body required")
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()
    if not title or not body:
        return json_error("title and body are required")
    photo_b64 = data.get("photo_b64")
    tags = (data.get("tags") or "").strip()
    conn = get_db_connection()
    cursor = conn.execute(
        "INSERT INTO community_posts (user_id, title, body, photo_b64, tags) VALUES (?, ?, ?, ?, ?)",
        (user["id"], title, body, photo_b64, tags),
    )
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": post_id, "message": "Post created"}), 201


@app.route("/api/community/posts/<int:post_id>", methods=["GET"])
def get_community_post(post_id):
    conn = get_db_connection()
    post = conn.execute(
        """
        SELECT p.id, p.title, p.body, p.photo_b64, p.tags, p.created_at,
               u.name AS author, u.village
        FROM community_posts p JOIN users u ON u.id = p.user_id
        WHERE p.id = ?
        """,
        (post_id,),
    ).fetchone()
    if not post:
        conn.close()
        return json_error("Post not found", 404)
    replies = conn.execute(
        """
        SELECT r.id, r.body, r.is_expert, r.created_at, u.name AS author, u.village
        FROM community_replies r JOIN users u ON u.id = r.user_id
        WHERE r.post_id = ?
        ORDER BY r.created_at ASC
        """,
        (post_id,),
    ).fetchall()
    conn.close()
    return jsonify({"post": dict(post), "replies": [dict(r) for r in replies]})


@app.route("/api/community/posts/<int:post_id>/replies", methods=["POST"])
def create_community_reply(post_id):
    token = get_bearer_token()
    user = get_user_by_token(token)
    if not user:
        return json_error("Unauthorized", 401)
    data = get_json_body()
    if not data:
        return json_error("JSON body required")
    body = (data.get("body") or "").strip()
    if not body:
        return json_error("body is required")
    conn = get_db_connection()
    post = conn.execute("SELECT id FROM community_posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        conn.close()
        return json_error("Post not found", 404)
    cursor = conn.execute(
        "INSERT INTO community_replies (post_id, user_id, body) VALUES (?, ?, ?)",
        (post_id, user["id"], body),
    )
    reply_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({"id": reply_id, "message": "Reply added"}), 201


init_db()

if __name__ == "__main__":
    app.run(debug=True)

