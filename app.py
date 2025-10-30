from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import base64
import os

app = Flask(__name__)
# Only allow requests from your GoDaddy domain
CORS(app, resources={r"/evaluate": {"origins": "https://impulsesim.com"}})

# Use your Render variable (is_api_key) instead of default
client = OpenAI(api_key=os.environ.get("is_api_key"))

@app.route("/")
def home():
    return "Impulse Sim AI Feedback API is running! Use /evaluate to submit an image."

@app.route("/evaluate", methods=["POST"])
def evaluate():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        image_b64 = base64.b64encode(file.read()).decode('utf-8')

        # Log for debugging (shows in Render logs)
        print("✅ Image received, sending to OpenAI...")

        system_prompt = (
            "You are a clinical educator analysing a student's suturing technique. "
            "Evaluate spacing, tension, knot security, and wound edge alignment. "
            "Provide a score (1–10) and 2–3 constructive improvement suggestions."
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Evaluate this suture pad photo:"},
                        {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_b64}"}
                    ]
                }
            ]
        )

        # Handle new response format safely
        feedback = (
            response.choices[0].message.content[0].text
            if isinstance(response.choices[0].message.content, list)
            else response.choices[0].message.content
        )

        print("✅ OpenAI response received successfully.")
        return jsonify({"feedback": feedback})

    except Exception as e:
        error_str = str(e)
        print("❌ Error caught:", error_str)

        if "insufficient_quota" in error_str or "You exceeded your current quota" in error_str:
            return jsonify({
                "feedback": "⚠️ AI feedback service is temporarily unavailable (usage limit reached). Please try again later."
            }), 200

        elif "invalid_request_error" in error_str:
            return jsonify({
                "feedback": "⚠️ Invalid request. Please ensure your image file is a valid JPEG or PNG."
            }), 200

        else:
            return jsonify({"error": error_str}), 500






