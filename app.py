from flask import Flask, request, jsonify
import base64, openai, os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Get your OpenAI API key from Render later
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/evaluate", methods=["POST"])
def evaluate():
    # Get uploaded image
    image = request.files["file"]
    image_b64 = base64.b64encode(image.read()).decode("utf-8")

    # What the AI should do
    system_prompt = """
    You are a UK clinical skills educator assessing basic suturing technique.
    Evaluate the uploaded photo for spacing, tension, knot security, and wound edge alignment.
    Return feedback in this structure:
    Score (1–10)
    Summary (1 line)
    Strengths (2–3 bullets)
    Areas for improvement (2–3 bullets)
    Next steps (short actionable advice)
    Use British-English spelling.
    """

    # Send to OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # supports image input
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_b64}"}
            ]}
        ]
    )

    # Return the feedback as JSON
    return jsonify({"feedback": response["choices"][0]["message"]["content"]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
