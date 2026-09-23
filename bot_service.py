"""
Bot Service for WhatsApp & Telegram Rural Farmer Advisory
Handles webhook message parsing, automated crop/weather/disease queries,
and in-app interactive simulation.
"""

import re
from datetime import datetime


def get_welcome_message(channel="whatsapp"):
    prefix = "🌾 *AgriAI SmartCrop Assistant* 🌾\n\n"
    body = (
        "Namaste / Vanakkam! I am your 24/7 farming advisory assistant.\n\n"
        "*Quick Commands:*\n"
        "• *weather <city>* - Get live weather & field advice (e.g. `weather Hyderabad`)\n"
        "• *recommend <temp> <humidity> <ph>* - Crop suitability (e.g. `recommend 28 75 6.5`)\n"
        "• *tips <crop>* - Cultivation tips for rice, wheat, tomato, etc.\n"
        "• *Send a leaf photo* - Instant plant disease detection & remedies\n"
        "• Ask any farming question in plain text!\n\n"
        "Reply with a command or question to get started."
    )
    return prefix + body


def parse_recommendation_args(text):
    """
    Look for 3 numbers in the string (temperature, humidity, pH).
    Example: 'recommend 28 65 6.5' or '28, 70, 6.2'
    """
    numbers = re.findall(r"[-+]?\d*\.?\d+", text)
    if len(numbers) >= 3:
        try:
            temp = float(numbers[0])
            humidity = float(numbers[1])
            ph = float(numbers[2])
            return temp, humidity, ph
        except ValueError:
            return None
    return None


def process_bot_query(
    message_text,
    image_url_or_b64=None,
    channel="whatsapp",
    weather_func=None,
    recommend_func=None,
    advisory_func=None,
    disease_func=None,
):
    """
    Process incoming text or image query from WhatsApp or Telegram.
    Returns: string response formatted for messaging.
    """
    clean_text = (message_text or "").strip()
    lower_text = clean_text.lower()

    # 1. Handle leaf photo / disease
    if image_url_or_b64:
        if disease_func:
            try:
                res = disease_func(image_url_or_b64)
                if isinstance(res, dict) and "disease" in res:
                    return (
                        f"🌿 *Disease Diagnosis Result*\n\n"
                        f"• *Detected:* {res.get('disease')}\n"
                        f"• *Confidence:* {res.get('confidence')}\n"
                        f"• *Severity:* {res.get('severity')}\n\n"
                        f"📋 *Recommended Action:*\n{res.get('action')}\n\n"
                        f"_Keep leaf dry and isolate severely infected branches._"
                    )
            except Exception as e:
                return f"⚠️ Could not analyze the leaf image: {str(e)}"
        return (
            "🌿 *Disease Detection:* Please upload this leaf photo through our web dashboard "
            "or ensure your backend PLANTNET_API_KEY is configured."
        )

    # 2. Greeting / Help
    if not clean_text or lower_text in ["hi", "hello", "hey", "start", "/start", "help", "/help", "namaste", "vanakkam"]:
        return get_welcome_message(channel)

    # 3. Weather command: 'weather Hyderabad' or '/weather Delhi'
    if lower_text.startswith("weather") or lower_text.startswith("/weather"):
        parts = clean_text.split(maxsplit=1)
        if len(parts) > 1 and parts[1].strip():
            city = parts[1].strip()
            if weather_func:
                try:
                    w_data = weather_func(city)
                    if isinstance(w_data, dict) and "main" in w_data:
                        temp = w_data["main"].get("temp", "--")
                        hum = w_data["main"].get("humidity", "--")
                        desc = (
                            w_data.get("weather", [{}])[0].get("description", "clear")
                            .capitalize()
                        )
                        wind = w_data.get("wind", {}).get("speed", "--")
                        spray_alert = (
                            "⚠️ *Spray Alert:* High wind speed. Postpone pesticide spraying."
                            if float(wind or 0) > 4.5
                            else "✅ Wind speed is favorable for spraying."
                        )
                        return (
                            f"🌦️ *Live Weather for {city.title()}*\n\n"
                            f"• *Condition:* {desc}\n"
                            f"• *Temperature:* {temp} °C\n"
                            f"• *Humidity:* {hum} %\n"
                            f"• *Wind Speed:* {wind} m/s\n\n"
                            f"{spray_alert}"
                        )
                except Exception as exc:
                    return f"⚠️ Unable to fetch weather for '{city}': {str(exc)}"
            return f"🌦️ Weather for *{city}*: Normal seasonal conditions (approx 26-30°C). Good for general fieldwork."
        return "Please specify a city. Example: `weather Hyderabad` or `weather Pune`"

    # 4. Crop recommendation command: 'recommend 28 65 6.5' or '/recommend'
    if "recommend" in lower_text:
        coords = parse_recommendation_args(clean_text)
        if coords and recommend_func:
            temp, hum, ph = coords
            recs = recommend_func(temp, hum, ph)
            if recs:
                rec_lines = []
                for i, r in enumerate(recs[:3], 1):
                    rec_lines.append(f"{i}. *{r['crop'].capitalize()}* (Match: {r['match_score']}/10)")
                return (
                    f"🌱 *Top Recommended Crops for your Soil & Weather*\n"
                    f"(Temp: {temp}°C | Humidity: {hum}% | pH: {ph})\n\n"
                    + "\n".join(rec_lines)
                    + "\n\n💡 _Type 'tips <crop>' for step-by-step cultivation guidance!_"
                )
        return (
            "🌱 *Crop Recommendation Helper:*\n"
            "Please provide temperature, humidity, and soil pH.\n"
            "Example: `recommend 28 75 6.5`"
        )

    # 5. Crop tips command: 'tips rice'
    if lower_text.startswith("tips") or lower_text.startswith("/tips"):
        parts = clean_text.split(maxsplit=1)
        if len(parts) > 1 and parts[1].strip():
            crop = parts[1].strip().lower()
            crop_tips = {
                "rice": "🌾 *Rice/Paddy Tips:* Maintain 2-5 cm standing water during tillering. Apply Zinc Sulphate 10 kg/acre with basal fertilizer.",
                "wheat": "🌾 *Wheat Tips:* First irrigation at Crown Root Initiation (20-25 days after sowing) is critical for optimal yield.",
                "maize": "🌽 *Maize Tips:* Ensure good soil drainage. Apply nitrogen in splits: sowing, knee-high stage, and tasseling.",
                "cotton": "🌱 *Cotton Tips:* Avoid excess nitrogen to prevent vegetative growth. Monitor regularly for whitefly and bollworm.",
                "tomato": "🍅 *Tomato Tips:* Stake plants for better air circulation and to prevent fruit rot. Water at the base, not overhead.",
                "potato": "🥔 *Potato Tips:* Perform earthing-up at 30 days after planting to prevent greening of tubers.",
            }
            return crop_tips.get(
                crop,
                f"🌱 *{crop.title()} Cultivation Advice:* Ensure well-drained fertile soil with balanced N-P-K (4:2:1 ratio) and regular pest scouting."
            )
        return "Please specify a crop name. Example: `tips tomato` or `tips rice`"

    # 6. General agricultural query -> advisory fallback or AI
    if advisory_func:
        try:
            advice = advisory_func(clean_text)
            if advice:
                return f"🤖 *AgriAI Advisory:*\n\n{advice}"
        except Exception:
            pass

    return (
        f"🌾 *AgriAI Advisory for:* \"{clean_text}\"\n\n"
        "• Ensure regular field inspection every 3-4 days.\n"
        "• Apply balanced organic compost and check soil moisture before next irrigation.\n"
        "• Avoid spraying chemicals during midday peak sunlight.\n\n"
        "_Tip: Type 'help' to see all available commands._"
    )


def format_twiml_response(reply_text):
    """Format reply text as valid Twilio Messaging TwiML XML."""
    escaped_reply = (
        reply_text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<Response>\n"
        f"  <Message>{escaped_reply}</Message>\n"
        "</Response>"
    )
