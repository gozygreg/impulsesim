from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import base64, os, json

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

client = OpenAI(api_key=os.environ.get("is_api_key"))
CODES_FILE = "codes.json"

@app.route("/")
def home():
    return "Impulse Sim AI Feedback API is running with Pay-Per-Use enabled!"

# --- AI FEEDBACK ---
@app.route("/evaluate", methods=["POST"])
def evaluate():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        image_b64 = base64.b64encode(file.read()).decode('utf-8')
        mime_type = file.mimetype or "image/jpeg"

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
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}
                        }
                    ]
                }
            ]
        )

        feedback = (
            response.choices[0].message.content[0].text
            if isinstance(response.choices[0].message.content, list)
            else response.choices[0].message.content
        )
        return jsonify({"feedback": feedback})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- NEW: Add a Code (Zapier will POST here) ---
@app.route("/add_code", methods=["POST"])
def add_code():
    data = request.get_json()
    code = data["code"].upper()
    uses = int(data.get("uses", 10))  # default 10 uses
    email = data.get("email", "")

    if os.path.exists(CODES_FILE):
        with open(CODES_FILE, "r") as f:
            codes = json.load(f)
    else:
        codes = {}

    codes[code] = {"uses_left": uses, "email": email}

    with open(CODES_FILE, "w") as f:
        json.dump(codes, f)

    return jsonify({"success": True})


# --- NEW: Verify a Code (Frontend will call this before showing upload form) ---
@app.route("/verify", methods=["POST"])
def verify_code():
    data = request.get_json()
    code = data.get("code", "").strip().upper()

    if not os.path.exists(CODES_FILE):
        return jsonify({"valid": False})

    with open(CODES_FILE, "r") as f:
        codes = json.load(f)

    record = codes.get(code)
    if record and record["uses_left"] > 0:
        record["uses_left"] -= 1
        codes[code] = record
        with open(CODES_FILE, "w") as f:
            json.dump(codes, f)
        return jsonify({"valid": True, "uses_left": record["uses_left"]})
    else:
        return jsonify({"valid": False})

@app.route("/register-code", methods=["POST"])
def register_code():
    import json
    try:
        data = request.json
        email = data.get("email")
        code = data.get("code")
        plan = data.get("plan", "AI_Feedback_10uploads")

        if not email or not code:
            return jsonify({"error": "Missing email or code"}), 400

        # Create codes.json file if it doesn’t exist
        if not os.path.exists("codes.json"):
            with open("codes.json", "w") as f:
                json.dump({}, f)

        # Load existing codes
        with open("codes.json", "r") as f:
            codes = json.load(f)

        # Save new code entry
        codes[code] = {"uses_left": 10, "email": email, "plan": plan}

        with open("codes.json", "w") as f:
            json.dump(codes, f, indent=2)

        print(f"✅ Registered code {code} for {email}")
        return jsonify({"status": "success", "code": code, "email": email}), 200

    except Exception as e:
        print("❌ Error in /register-code:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

