import base64
import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
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
            notes.append("Temperature is high, so irrigate in the early morning and reduce heat stress.")
        elif temperature < 15:
            notes.append("Temperature is on the lower side, so avoid overwatering and watch for slow growth.")

    if humidity is not None and humidity < 40:
        notes.append("Humidity is low, so mulching can help retain soil moisture.")

    if soil_ph is not None:
        if soil_ph < 5.5:
            notes.append("Soil is acidic, so lime can help correct pH over time.")
        elif soil_ph > 7.5:
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
    return send_file("frontend.html")


@app.route("/api/health")
def home():
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


if __name__ == "__main__":
    app.run(debug=True)
