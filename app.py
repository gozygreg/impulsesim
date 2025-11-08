from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from openai import OpenAI
import base64, os, json, uuid, re
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

client = OpenAI(api_key=os.environ.get("is_api_key"))

CODES_FILE = "codes.json"
FEEDBACK_FILE = "feedback_history.json"

# -------------------------------------------------------------------------
@app.route("/")
def home():
    return "✅ Impulse Sim AI Feedback API — Pay-Per-Use | OSATS-aligned | PDF Reporting active"

# -------------------------------------------------------------------------
# 1️⃣ Evaluate uploaded suture photo
@app.route("/evaluate", methods=["POST"])
def evaluate():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        image_b64 = base64.b64encode(file.read()).decode('utf-8')
        mime_type = file.mimetype or "image/jpeg"

        system_prompt = (
            "You are a clinical educator evaluating a student's suturing technique "
            "using domains from the Objective Structured Assessment of Technical Skill (OSATS), "
            "Direct Observation of Procedural Skills (DOPS), and Procedure-Based Assessments (PBAs). "
            "Assess and score: Wound Edge Approximation, Suture Spacing & Symmetry, "
            "Tension & Knot Appearance, Tissue Handling, and Aesthetic Outcome (each /10). "
            "After domain feedback, provide a short Global Impression (/10), Summary, and 2–3 Improvement Suggestions. "
            "Write in clear plain text without markdown symbols."
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Evaluate this suturing photo objectively:"},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}}
                    ]
                }
            ]
        )

        feedback = response.choices[0].message.content
        entry_id = str(uuid.uuid4())[:8]

        # Save feedback history
        log_entry = {"id": entry_id, "feedback": feedback}
        with open(FEEDBACK_FILE, "a") as log:
            json.dump(log_entry, log)
            log.write("\n")

        return jsonify({"feedback": feedback, "entry_id": entry_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------------------------------------------------
# 2️⃣ Add a new code (Zapier)
@app.route("/add_code", methods=["POST"])
def add_code():
    data = request.get_json()
    code = data["code"].upper()
    uses = int(data.get("uses", 10))
    email = data.get("email", "")

    codes = json.load(open(CODES_FILE)) if os.path.exists(CODES_FILE) else {}
    codes[code] = {"uses_left": uses, "email": email}
    json.dump(codes, open(CODES_FILE, "w"))
    return jsonify({"success": True})

# -------------------------------------------------------------------------
# 3️⃣ Verify a code (or admin override)
@app.route("/verify", methods=["POST"])
def verify_code():
    data = request.get_json()
    code = data.get("code", "").strip().upper()

    if not os.path.exists(CODES_FILE):
        return jsonify({"valid": False})

    codes = json.load(open(CODES_FILE))
    OWNER_CODE = "IMP-ADMIN-ACCESS"

    if code == OWNER_CODE:
        return jsonify({"valid": True, "uses_left": "∞"})

    record = codes.get(code)
    if record and record["uses_left"] > 0:
        record["uses_left"] -= 1
        codes[code] = record
        json.dump(codes, open(CODES_FILE, "w"))
        return jsonify({"valid": True, "uses_left": record["uses_left"]})
    return jsonify({"valid": False})

# -------------------------------------------------------------------------
# 4️⃣ Manual registration
@app.route("/register-code", methods=["POST"])
def register_code():
    try:
        data = request.json
        email = data.get("email")
        code = data.get("code")
        if not email or not code:
            return jsonify({"error": "Missing fields"}), 400
        codes = json.load(open(CODES_FILE)) if os.path.exists(CODES_FILE) else {}
        codes[code] = {"uses_left": 10, "email": email, "plan": "AI_Feedback_10uploads"}
        json.dump(codes, open(CODES_FILE, "w"), indent=2)
        return jsonify({"status": "success", "code": code})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------------------------------------------------
# 5️⃣ Download feedback PDF (logo + OSATS attribution)
@app.route("/download_feedback/<entry_id>", methods=["GET"])
def download_feedback(entry_id):
    try:
        if not os.path.exists(FEEDBACK_FILE):
            return jsonify({"error": "No history found"}), 404

        feedback_text = None
        for line in open(FEEDBACK_FILE):
            try:
                record = json.loads(line.strip())
                if record["id"] == entry_id:
                    feedback_text = record["feedback"]
                    break
            except json.JSONDecodeError:
                continue
        if not feedback_text:
            return jsonify({"error": "Feedback not found"}), 404

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        # --- Header & logo ---
        logo_url = "https://img1.wsimg.com/isteam/ip/8aaa8186-6e53-4a39-9191-17ebbbb58eca/logo-horizontal-transparent.png/:/rs=w:250,h:70,cg:true,m/cr=w:250,h:70/qt=q:95"
        story.append(Image(logo_url, width=180, height=50))
        story.append(Spacer(1, 12))
        story.append(Paragraph("<b>Impulse Sim AI Feedback Report</b>", styles["Title"]))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>Feedback ID:</b> {entry_id}", styles["Normal"]))
        story.append(Spacer(1, 8))
        story.append(Paragraph("<b>Rubric:</b> OPATS (adapted from OSATS / DOPS / PBA frameworks)", styles["Normal"]))
        story.append(Spacer(1, 15))

        # --- Emphasise scores ---
        feedback_text = re.sub(r'(\d+)/10', r'<b>\1/10</b>', feedback_text)
        feedback_text = feedback_text.replace("\n", "<br/>")

        story.append(Paragraph(feedback_text, styles["Normal"]))
        story.append(Spacer(1, 25))

        # --- Attribution footer ---
        story.append(Paragraph(
            "🩺 <b>Assessment Framework:</b> Impulse Sim OPATS™ — adapted from validated UK surgical education models including "
            "the Objective Structured Assessment of Technical Skill (OSATS), Direct Observation of Procedural Skills (DOPS), "
            "and Procedure-Based Assessments (PBAs) recognised by the Intercollegiate Surgical Curriculum Programme (ISCP).",
            styles["Normal"]
        ))
        story.append(Spacer(1, 20))
        story.append(Paragraph("© 2025 Impulse Sim | Empowering Clinical Skill Mastery", styles["Normal"]))

        doc.build(story)
        buffer.seek(0)
        return send_file(buffer,
                         as_attachment=True,
                         download_name=f"ImpulseSim_Feedback_{entry_id}.pdf",
                         mimetype="application/pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
