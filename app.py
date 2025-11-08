from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from openai import OpenAI
import base64, os, json, uuid
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

client = OpenAI(api_key=os.environ.get("is_api_key"))

CODES_FILE = "codes.json"
FEEDBACK_FILE = "feedback_history.json"

# -------------------------------------------------------------------------
@app.route("/")
def home():
    return "✅ Impulse Sim AI Feedback API is running with pay-per-use + logging + PDF enabled!"


# -------------------------------------------------------------------------
# 🧠 1. Evaluate uploaded suture photo
@app.route("/evaluate", methods=["POST"])
def evaluate():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        image_b64 = base64.b64encode(file.read()).decode('utf-8')
        mime_type = file.mimetype or "image/jpeg"

        system_prompt = (
            "You are a clinical educator evaluating a learner's suturing technique "
            "based on a photo. Analyse wound edge approximation, suture spacing and symmetry, "
            "tension and knot appearance, tissue handling, and aesthetic outcome. "
            "Provide a structured assessment with scores (1–10 per domain), a global impression, "
            "a concise summary, and 2–3 improvement suggestions. "
            "Format response clearly for direct display (avoid markdown symbols like ** or ###)."
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Evaluate this suturing photo objectively:"},
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

        # ✅ Generate unique feedback ID
        entry_id = str(uuid.uuid4())[:8]

        # ✅ Log feedback in history file
        log_entry = {"id": entry_id, "feedback": feedback}
        with open(FEEDBACK_FILE, "a") as log:
            json.dump(log_entry, log)
            log.write("\n")

        # ✅ Return feedback + ID for frontend
        return jsonify({"feedback": feedback, "entry_id": entry_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# 🧩 2. Add a code (Zapier hook)
@app.route("/add_code", methods=["POST"])
def add_code():
    data = request.get_json()
    code = data["code"].upper()
    uses = int(data.get("uses", 10))
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


# -------------------------------------------------------------------------
# ✅ 3. Verify a code before upload
@app.route("/verify", methods=["POST"])
def verify_code():
    data = request.get_json()
    code = data.get("code", "").strip().upper()

    if not os.path.exists(CODES_FILE):
        return jsonify({"valid": False})

    with open(CODES_FILE, "r") as f:
        codes = json.load(f)

    OWNER_CODE = "IMP-ADMIN-ACCESS"

    # Owner always valid
    if code == OWNER_CODE:
        return jsonify({"valid": True, "uses_left": "∞"})

    record = codes.get(code)
    if record and record["uses_left"] > 0:
        record["uses_left"] -= 1
        codes[code] = record
        with open(CODES_FILE, "w") as f:
            json.dump(codes, f)
        return jsonify({"valid": True, "uses_left": record["uses_left"]})
    else:
        return jsonify({"valid": False})


# -------------------------------------------------------------------------
# 🧾 4. Register new code manually (if needed)
@app.route("/register-code", methods=["POST"])
def register_code():
    try:
        data = request.json
        email = data.get("email")
        code = data.get("code")
        plan = data.get("plan", "AI_Feedback_10uploads")

        if not email or not code:
            return jsonify({"error": "Missing email or code"}), 400

        if not os.path.exists(CODES_FILE):
            with open(CODES_FILE, "w") as f:
                json.dump({}, f)

        with open(CODES_FILE, "r") as f:
            codes = json.load(f)

        codes[code] = {"uses_left": 10, "email": email, "plan": plan}

        with open(CODES_FILE, "w") as f:
            json.dump(codes, f, indent=2)

        print(f"✅ Registered code {code} for {email}")
        return jsonify({"status": "success", "code": code, "email": email}), 200

    except Exception as e:
        print("❌ Error in /register-code:", e)
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
# 📄 5. Download feedback as PDF by entry ID
@app.route("/download_feedback/<entry_id>", methods=["GET"])
def download_feedback(entry_id):
    try:
        # Search in feedback_history.jsonl
        if not os.path.exists(FEEDBACK_FILE):
            return jsonify({"error": "No feedback history found"}), 404

        feedback_text = None
        with open(FEEDBACK_FILE, "r") as log:
            for line in log:
                try:
                    record = json.loads(line.strip())
                    if record["id"] == entry_id:
                        feedback_text = record["feedback"]
                        break
                except json.JSONDecodeError:
                    continue

        if not feedback_text:
            return jsonify({"error": "Feedback not found"}), 404

        # Generate PDF dynamically
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = [Paragraph("<b>Impulse Sim AI Feedback Report</b>", styles["Title"]), Spacer(1, 20)]
        story.append(Paragraph(feedback_text.replace("\n", "<br/>"), styles["Normal"]))
        doc.build(story)

        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f"feedback_{entry_id}.pdf", mimetype="application/pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
