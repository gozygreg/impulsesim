from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from openai import OpenAI
import base64, os, json, datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

client = OpenAI(api_key=os.environ.get("is_api_key"))
CODES_FILE = "codes.json"
LOG_FILE = "feedback_history.json"

# ✅ Helper: Load / Save JSON
def load_json(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/")
def home():
    return "Impulse Sim AI Feedback API v3 — OPATS rubric + progress log + PDF export."

# ✅ Evaluate suture image and log feedback
@app.route("/evaluate", methods=["POST"])
def evaluate():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        image_b64 = base64.b64encode(file.read()).decode('utf-8')
        mime_type = file.mimetype or "image/jpeg"

        system_prompt = (
            "You are an experienced clinical educator evaluating a student's suturing technique "
            "from a photo. Use OPATS/OSATS criteria to assess:\n"
            "1. Wound Edge Approximation\n2. Suture Spacing & Symmetry\n3. Tension & Knot Appearance\n"
            "4. Tissue Handling\n5. Aesthetic Outcome\n6. Global Impression\n"
            "Give each domain a score out of 10 and provide a brief summary and recommendations."
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Evaluate this suturing pad photo objectively."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}
                        }
                    ]
                }
            ]
        )

        feedback_text = (
            response.choices[0].message.content[0].text
            if isinstance(response.choices[0].message.content, list)
            else response.choices[0].message.content
        ).strip()

        # --- Store in feedback log ---
        log = load_json(LOG_FILE)
        entry_id = str(len(log) + 1)
        log[entry_id] = {
            "timestamp": str(datetime.datetime.now()),
            "feedback": feedback_text
        }
        save_json(LOG_FILE, log)

        print(f"✅ Logged feedback #{entry_id}")
        return jsonify({"feedback": feedback_text})

    except Exception as e:
        print("❌ Error:", str(e))
        return jsonify({"error": str(e)}), 500

# ✅ Add a new access code (for Zapier)
@app.route("/add_code", methods=["POST"])
def add_code():
    data = request.get_json()
    code = data["code"].upper()
    uses = int(data.get("uses", 10))
    email = data.get("email", "")
    codes = load_json(CODES_FILE)
    codes[code] = {"uses_left": uses, "email": email}
    save_json(CODES_FILE, codes)
    return jsonify({"success": True})

# ✅ Verify user code (frontend calls this)
@app.route("/verify", methods=["POST"])
def verify_code():
    data = request.get_json()
    code = data.get("code", "").strip().upper()
    codes = load_json(CODES_FILE)

    if code == "IMP-ADMIN-ACCESS":  # Owner access
        return jsonify({"valid": True, "uses_left": "∞"})

    record = codes.get(code)
    if record and record["uses_left"] > 0:
        record["uses_left"] -= 1
        codes[code] = record
        save_json(CODES_FILE, codes)
        return jsonify({"valid": True, "uses_left": record["uses_left"]})
    else:
        return jsonify({"valid": False})

# ✅ Allow user to view progress history
@app.route("/get_history", methods=["GET"])
def get_history():
    log = load_json(LOG_FILE)
    return jsonify(log)

# ✅ Download PDF report
@app.route("/download_feedback/<entry_id>", methods=["GET"])
def download_feedback(entry_id):
    log = load_json(LOG_FILE)
    entry = log.get(entry_id)
    if not entry:
        return jsonify({"error": "No such feedback entry"}), 404

    pdf_path = f"feedback_{entry_id}.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Impulse Sim AI Feedback Report</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Entry ID: {entry_id}", styles["Normal"]))
    story.append(Paragraph(f"Date: {entry['timestamp']}", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(entry["feedback"], styles["Normal"]))

    doc.build(story)
    return send_file(pdf_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
