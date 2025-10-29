from openai import OpenAI
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route("/")
def home():
    return "Impulse Sim AI Feedback API is running! Use /evaluate to submit an image."

@app.route("/evaluate", methods=["POST"])
def evaluate():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    image_b64 = base64.b64encode(file.read()).decode('utf-8')

    system_prompt = """You are a clinical educator. 
    Evaluate the suturing technique shown in the uploaded image.
    Consider spacing, tension, knot security, and wound edge alignment.
    Give a score (1–10) and 2–3 constructive improvement suggestions."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "input_text", "text": "Analyse this suture pad photo:"},
                    {"type": "input_image", "image_url": f"data:image/jpeg;base64,{image_b64}"}
                ]}
            ]
        )

        feedback = response.choices[0].message.content[0].text
        return jsonify({"feedback": feedback})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

