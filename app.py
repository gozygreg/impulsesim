from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from openai import OpenAI
from datetime import datetime
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import base64, os, json

app = Flask(__name__)
CORS(app)

client = OpenAI(api_key=os.environ.get("is_api_key"))

CODES_FILE = "codes.json"
LOG_FILE = "feedback_history.json"


# ---------------------- UTILITIES ----------------------
def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)


@app.route("/")
def home():
    return "Impulse Sim AI Feedback API v3 — OPATS rubric + progress log + PDF export."


# ---------------------- EVALUATE IMAGE ----------------------
@app.route("/evaluate", methods=["POST"])
def evaluate():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        image_b64 = base64.b64encode(file.read()).decode("utf-8")
        mime_type = file.mimetype or "image/jpeg"

        system_prompt = (
            "You are a clinical educator assessing a learner’s suturing technique. "
            "Use an OSATS-style framework (adapted to Impulse Sim OPATS). "
            "Evaluate the following domains and give each a score out of 10: "
            "1. Wound Edge Approximation, 2. Suture Spacing & Symmetry, 3. Tension & Knot Security, "
            "4. Tissue Handling, 5. Aesthetic Outcome, 6. Global Impression. "
            "Then provide a concise summary and 2–3 improvement suggestions."
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Evaluate this suture pad image:"},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}}
                    ]
                },
            ],
        )

        feedback = response.choices[0].message.content

        # Save feedback in log file
        log = load_json(LOG_FILE)
        entry_id = str(len(log) + 1)
        log[entry_id] = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "feedback": feedback,
        }
        save_json(LOG_FILE, log)

        return jsonify({"feedback": feedback, "entry_id": entry_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------- ADD CODE ----------------------
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


# ---------------------- VERIFY CODE ----------------------
@app.route("/verify", methods=["POST"])
def verify_code():
    data = request.get_json()
    code = data.get("code", "").strip().upper()
    codes = load_json(CODES_FILE)

    OWNER_CODE = "IMP-ADMIN-ACCESS"
    if code == OWNER_CODE:
        return jsonify({"valid": True, "uses_left": "∞"})

    record = codes.get(code)
    if record and record["uses_left"] > 0:
        record["uses_left"] -= 1
        codes[code] = record
        save_json(CODES_FILE, codes)
        return jsonify({"valid": True, "uses_left": record["uses_left"]})
    else:
        return jsonify({"valid": False})


# ---------------------- DOWNLOAD FEEDBACK PDF ----------------------
@app.route("/download_feedback/<entry_id>", methods=["GET"])
def download_feedback(entry_id):
    log = load_json(LOG_FILE)
    entry = log.get(entry_id)
    if not entry:
        return jsonify({"error": "No such feedback entry"}), 404

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=40, leftMargin=40,
                            topMargin=60, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    # Header
    logo_url = "https://img1.wsimg.com/isteam/ip/8aaa8186-6e53-4a39-9191-17ebbbb58eca/logo-horizontal-transparent.png"
    try:
        story.append(Image(logo_url, width=180, height=50))
    except Exception:
        pass

    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>AI Feedback Summary</b>", styles["Title"]))
    story.append(Paragraph(f"Date: {entry['timestamp']}", styles["Normal"]))
    story.append(Spacer(1, 15))

    feedback = entry["feedback"]
    rubric_data = [["Domain", "Score (/10)"]]
    for line in feedback.split("\n"):
        if ":" in line and "/" in line:
            parts = line.split(":")
            rubric_data.append([parts[0].strip(), parts[1].strip()])

    if len(rubric_data) > 1:
        table = Table(rubric_data, colWidths=[3.5 * inch, 1.3 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#007c7e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ]))
        story.append(table)
        story.append(Spacer(1, 15))

    story.append(Paragraph("<b>Summary & Recommendations</b>", styles["Heading3"]))
    story.append(Paragraph(feedback, styles["Normal"]))
    story.append(Spacer(1, 30))

    story.append(Paragraph(
        "<para align='center'><font color='#007c7e'>© 2025 Impulse Sim | Empowering Clinical Skill Mastery</font></para>",
        styles["Normal"]
    ))

    doc.build(story)
    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"ImpulseSim_Feedback_{entry_id}.pdf",
        mimetype="application/pdf"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
