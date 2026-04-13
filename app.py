from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import base64

app = Flask(__name__)
CORS(app)

# 🔑 API KEYS
OWM_API_KEY = "bf5b5404d69f120646450e080dc5d3d8"
HF_API_KEY = "YOUR_HF_TOKEN_HERE"


# =========================
# ✅ ROOT
# =========================
@app.route('/')
def home():
    return "Backend running 🚀"


# =========================
# ✅ WEATHER API
# =========================
@app.route('/api/weather')
def weather():
    city = request.args.get('city')

    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OWM_API_KEY}&units=metric"
    data = requests.get(url).json()

    return jsonify(data)


# =========================
# ✅ CROP RECOMMENDATION
# =========================
@app.route('/api/recommend', methods=['POST'])
def recommend():
    crops = [
        {"crop": "rice", "match_score": 8, "max_score": 10},
        {"crop": "wheat", "match_score": 6, "max_score": 10},
        {"crop": "maize", "match_score": 7, "max_score": 10}
    ]
    return jsonify({"recommendations": crops})


# =========================
# ✅ ADVISORY API
# =========================
@app.route('/api/advisory', methods=['POST'])
def advisory():
    data = request.json

    temp = data.get("temperature")
    humidity = data.get("humidity")
    ph = data.get("soil_ph")

    issues = []
    suggestions = []

    if temp > 35:
        issues.append("Temperature too high")
        suggestions.append("Irrigate more frequently")

    if humidity < 40:
        issues.append("Low humidity")
        suggestions.append("Use mulching")

    if ph < 5.5:
        issues.append("Soil too acidic")
        suggestions.append("Add lime")

    if ph > 7.5:
        issues.append("Soil too alkaline")
        suggestions.append("Add compost")

    return jsonify({
        "status": "Optimal" if not issues else "Needs Attention",
        "issues": issues,
        "suggestions": suggestions
    })


# =========================
# ✅ AI ADVISORY (FIXED - NO LOADING LOOP)
# =========================
@app.route('/api/ai-advisory', methods=['POST'])
def ai_advisory():
    data = request.json

    prompt = f"""
    Give simple farming advice.

    Crop: {data['crop']}
    Temp: {data['temperature']}
    Humidity: {data['humidity']}
    Soil pH: {data['soil_ph']}
    """

    try:
        response = requests.post(
            "https://api-inference.huggingface.co/models/google/flan-t5-small",
            headers={
                "Authorization": f"Bearer {HF_API_KEY}"
            },
            json={"inputs": prompt},
            timeout=10
        )

        result = response.json()

        if isinstance(result, list):
            return jsonify({"advisory": result[0]["generated_text"]})

        # ✅ FIX: Don't loop forever
        return jsonify({"advisory": "AI is warming up... try again once"})

    except:
        return jsonify({"advisory": "AI temporarily unavailable"})


# =========================
# ✅ DISEASE DETECTION (STABLE)
# =========================
@app.route('/api/disease', methods=['POST'])
def disease():
    try:
        data = request.json
        image_bytes = base64.b64decode(data.get("image"))

        response = requests.post(
            "https://api-inference.huggingface.co/models/microsoft/resnet-50",
            headers={
                "Authorization": f"Bearer {HF_API_KEY}",
                "Content-Type": "application/octet-stream"
            },
            data=image_bytes,
            timeout=10,
            stream=True
        )

        try:
            result = response.json()
        except:
            return jsonify({"error": "Model loading... try again"})

        if isinstance(result, list):
            return jsonify({
                "disease": result[0]["label"],
                "confidence": f"{round(result[0]['score']*100)}%",
                "severity": "Medium",
                "action": "Monitor plant condition"
            })

        return jsonify({"error": "Model loading... try again"})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": "Server error"})


# =========================
# ▶ RUN
# =========================
if __name__ == '__main__':
    app.run(debug=True)x
