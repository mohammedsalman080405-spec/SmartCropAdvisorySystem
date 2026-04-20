<<<<<<< HEAD
import base64
import os
import secrets
import sqlite3
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "smartcrop.db"))
=======
from __future__ import annotations
>>>>>>> 7d7a118 (Update SmartCropAdvisorySystem)

import base64
import os
import secrets
from pathlib import Path

import mysql.connector
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file
from flask_cors import CORS
from mysql.connector import Error
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

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

<<<<<<< HEAD
=======
CROP_PROFILES = {
    "rice": {"temperature": 28, "humidity": 80, "soil_ph": 6.0},
    "wheat": {"temperature": 22, "humidity": 55, "soil_ph": 6.5},
    "maize": {"temperature": 26, "humidity": 65, "soil_ph": 6.2},
    "potato": {"temperature": 20, "humidity": 70, "soil_ph": 5.8},
    "tomato": {"temperature": 24, "humidity": 60, "soil_ph": 6.4},
    "cotton": {"temperature": 30, "humidity": 50, "soil_ph": 6.8},
    "soybean": {"temperature": 25, "humidity": 60, "soil_ph": 6.3},
    "sugarcane": {"temperature": 29, "humidity": 75, "soil_ph": 6.5},
}

>>>>>>> 7d7a118 (Update SmartCropAdvisorySystem)
OWM_API_KEY = os.getenv("OWM_API_KEY", "").strip()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free").strip()
HF_API_KEY = os.getenv("HF_API_KEY", os.getenv("HF_TOKEN", "")).strip()
HF_CHAT_MODEL = os.getenv("HF_CHAT_MODEL", "google/gemma-2-2b-it").strip()
PLANTNET_API_KEY = os.getenv("PLANTNET_API_KEY", "").strip()
<<<<<<< HEAD


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
    connection.commit()
    connection.close()


def json_error(message, status_code=400):
    return jsonify({"error": message}), status_code


=======

MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "agriai")

db_ready = False


def json_error(message, status_code=400):
    return jsonify({"error": message}), status_code


>>>>>>> 7d7a118 (Update SmartCropAdvisorySystem)
def get_json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def parse_float(value, field_name):
    try:
        return float(value)
<<<<<<< HEAD
    except (TypeError, ValueError):
        raise ValueError(f"Invalid or missing '{field_name}'")
=======
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid or missing '{field_name}'") from exc
>>>>>>> 7d7a118 (Update SmartCropAdvisorySystem)


def normalize_image_metadata(mime_type):
    allowed_types = {
        "image/jpeg": ("crop.jpeg", "image/jpeg"),
        "image/jpg": ("crop.jpeg", "image/jpeg"),
        "image/png": ("crop.png", "image/png"),
    }
    return allowed_types.get((mime_type or "").lower(), ("crop.jpeg", "image/jpeg"))


<<<<<<< HEAD
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
=======
def get_server_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
    )


def get_db_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
    )


def ensure_database_ready() -> None:
    global db_ready
    if db_ready:
        return

    try:
        server_connection = get_server_connection()
        server_cursor = server_connection.cursor()
        server_cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        server_cursor.close()
        server_connection.close()

        db_connection = get_db_connection()
        db_cursor = db_connection.cursor()
        db_cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS farmers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(120) NOT NULL,
                phone VARCHAR(30) NOT NULL UNIQUE,
                village VARCHAR(120) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        db_connection.commit()
        db_cursor.close()
        db_connection.close()
        db_ready = True
    except Error as exc:
        raise RuntimeError(f"MySQL setup failed: {exc}") from exc


def find_user(phone: str) -> dict | None:
    ensure_database_ready()
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, name, phone, village, password_hash FROM farmers WHERE phone = %s",
        (phone,),
    )
    user = cursor.fetchone()
    cursor.close()
    connection.close()
    return user


def create_user(name: str, phone: str, village: str, password: str) -> None:
    ensure_database_ready()
>>>>>>> 7d7a118 (Update SmartCropAdvisorySystem)
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
<<<<<<< HEAD
        INSERT INTO users (name, phone, village, password_hash)
        VALUES (?, ?, ?, ?)
=======
        INSERT INTO farmers (name, phone, village, password_hash)
        VALUES (%s, %s, %s, %s)
>>>>>>> 7d7a118 (Update SmartCropAdvisorySystem)
        """,
        (name, phone, village, generate_password_hash(password)),
    )
    connection.commit()
<<<<<<< HEAD
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
=======
    cursor.close()
    connection.close()


def build_recommendations(temperature, humidity, soil_ph):
    recommendations = []

    for crop, profile in CROP_PROFILES.items():
>>>>>>> 7d7a118 (Update SmartCropAdvisorySystem)
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
<<<<<<< HEAD
            notes.append(
                "Temperature is high, so irrigate in the early morning and reduce heat stress."
            )
        elif temperature < 15:
            notes.append(
                "Temperature is on the lower side, so avoid overwatering and watch for slow growth."
            )
=======
            notes.append("Temperature is high, so irrigate in the early morning and reduce heat stress.")
        elif temperature < 15:
            notes.append("Temperature is on the lower side, so avoid overwatering and watch for slow growth.")
>>>>>>> 7d7a118 (Update SmartCropAdvisorySystem)

    if humidity is not None and humidity < 40:
        notes.append("Humidity is low, so mulching can help retain soil moisture.")

    if soil_ph is not None:
        if soil_ph < 5.5:
            notes.append("Soil is acidic, so lime can help correct pH over time.")
        elif soil_ph > 7.5:
<<<<<<< HEAD
            notes.append(
                "Soil is alkaline, so compost and organic matter can improve nutrient uptake."
            )

    notes.append(
        "Inspect the field twice a week for pests, leaf discoloration, and water stress."
    )
    return " ".join(notes)


=======
            notes.append("Soil is alkaline, so compost and organic matter can improve nutrient uptake.")

    notes.append("Inspect the field twice a week for pests, leaf discoloration, and water stress.")
    return " ".join(notes)


def resolve_language_name(language_code):
    languages = {
        "en": "English",
        "hi": "Hindi",
        "te": "Telugu",
    }
    return languages.get((language_code or "en").lower(), "English")


>>>>>>> 7d7a118 (Update SmartCropAdvisorySystem)
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
<<<<<<< HEAD
    return send_file("login.html")
=======
    frontend_path = os.path.join(app.root_path, "frontend.html")
    if os.path.exists(frontend_path):
        return send_file(frontend_path)
    return render_template("login.html")
>>>>>>> 7d7a118 (Update SmartCropAdvisorySystem)


@app.route("/login")
def login_page():
<<<<<<< HEAD
    return send_file("login.html")
=======
    return render_template("login.html")
>>>>>>> 7d7a118 (Update SmartCropAdvisorySystem)


@app.route("/register")
def register_page():
<<<<<<< HEAD
    return send_file("register.html")
=======
    return render_template("register.html")
>>>>>>> 7d7a118 (Update SmartCropAdvisorySystem)


@app.route("/home")
def home_page():
<<<<<<< HEAD
    return send_file("frontend.html")


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
=======
    return render_template("home.html")
>>>>>>> 7d7a118 (Update SmartCropAdvisorySystem)


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


<<<<<<< HEAD
=======
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

    try:
        if find_user(phone):
            return jsonify({"success": False, "error": "Phone number already registered"}), 409
        create_user(name, phone, village, password)
    except RuntimeError as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    except Error as exc:
        return jsonify({"success": False, "error": f"MySQL error: {exc}"}), 500

    return jsonify({"success": True, "message": "Account created successfully"})


@app.route("/api/login", methods=["POST"])
def login():
    data = get_json_body()
    if not data:
        return json_error("Expected a JSON request body")

    phone = str(data.get("phone", "")).strip()
    password = str(data.get("password", ""))

    if not phone or not password:
        return jsonify({"success": False, "error": "Phone and password are required"}), 400

    try:
        user = find_user(phone)
    except RuntimeError as exc:
        return jsonify({"success": False, "error": str(exc)}), 500
    except Error as exc:
        return jsonify({"success": False, "error": f"MySQL error: {exc}"}), 500

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"success": False, "error": "Invalid phone or password"}), 401

    token = secrets.token_hex(16)
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


@app.route("/api/verify")
def verify():
    auth_header = request.headers.get("Authorization", "")
    return jsonify({"valid": bool(auth_header.startswith("Bearer "))})


>>>>>>> 7d7a118 (Update SmartCropAdvisorySystem)
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
<<<<<<< HEAD
        return json_error("Disease detection needs PLANTNET_API_KEY on the backend", 503)

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


init_db()

=======
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


>>>>>>> 7d7a118 (Update SmartCropAdvisorySystem)
if __name__ == "__main__":
    app.run(debug=True)
