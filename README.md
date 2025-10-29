# 🩺 Impulse Sim AI Feedback  
**AI-Powered Clinical Skills Evaluation System**  
[![Deployed on Render](https://img.shields.io/badge/Deployed%20on-Render-blue)](https://impulsesim.onrender.com)
[![Built with OpenAI GPT-4o-mini](https://img.shields.io/badge/Built%20with-OpenAI%20GPT--4o--mini-ff69b4)](https://platform.openai.com)

---

## 📘 Overview
**Impulse Sim AI Feedback** is an intelligent web-based system developed by **Impulse Health Ltd** under the *Impulse Sim* brand.  
It allows students and clinicians to upload a photo of their **suture practice pad** and instantly receive structured, clinically relevant feedback on their technique.

The AI evaluates:

- Suture spacing  
- Tension consistency  
- Knot security  
- Wound edge alignment  

and provides:

- A **numerical score (1–10)**  
- **2–3 personalised improvement suggestions**

This tool supports **clinical simulation training**, enabling objective, scalable feedback for students and educators in healthcare education.

---

## 🧠 Project Architecture

| Component | Description |
|------------|--------------|
| **Frontend** | HTML/JavaScript upload form embedded on GoDaddy site (`https://impulsesim.com/ai-skills-feedback`) |
| **Backend** | Flask web app hosted on Render (`https://impulsesim.onrender.com`) |
| **AI Model** | `gpt-4o-mini` multimodal model via OpenAI API |
| **Integration** | Frontend sends images to Flask API → encoded as Base64 → analysed by GPT-4o-mini |
| **Deployment** | Automatic redeploys via GitHub commits to Render |

---

## ⚙️ Features

✅ Upload and evaluate any Impulse Sim suture pad image  
✅ Automatic AI feedback in seconds  
✅ Uses OpenAI’s multimodal model (`gpt-4o-mini`)  
✅ Continuous deployment via GitHub → Render  
✅ Secure API key management  
✅ Expandable to ECG, TOE, sedation, and other training modules  

---

## 🧩 Tech Stack

| Layer | Technology |
|-------|-------------|
| **Frontend** | HTML, JavaScript |
| **Backend** | Python (Flask) |
| **AI Integration** | OpenAI Python SDK (v1.x) |
| **CORS Handling** | Flask-CORS |
| **Server** | Gunicorn |
| **Hosting** | Render |
| **Version Control** | GitHub |

---

## 🗂️ Repository Structure

### impulsesim/
- app.py # Flask backend application
- requirements.txt # Dependency list
- README.md # Project documentation
 (optional future files)
- **static/ # Frontend assets
- **templates/ # HTML templates if UI is expanded


---

## 🧰 Local Installation

### 1️⃣ Clone the repository
git clone https://github.com/gozygreg/impulsesim.git
cd impulsesim

### 2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate  # (Mac/Linux)
venv\Scripts\activate     # (Windows)

### 3️⃣ Install dependencies
pip install -r requirements.txt

### 4️⃣ Set your OpenAI API key
export OPENAI_API_KEY="your_api_key_here"

### 5️⃣ Run the app
gunicorn app:app --bind 0.0.0.0:5000
- Then open:

http://localhost:5000/evaluate

## Deployment (Render)
- Go to Render
 → create an account.
- Connect GitHub and select your repo (gozygreg/impulsesim).
- Choose New Web Service → configure
  
| Setting | Value |
|-------|-------------|
| **Enviroment** | Python 3 |
| **Build Command** | pip install -r requirements.txt |
| **Start Command** | gunicorn app:app |
| **Region** | London (recommended) |

- Add Environment Variable:
OPENAI_API_KEY = your_api_key_here
Render automatically redeploys when you commit to GitHub.
Live API example:
https://impulsesim.onrender.com/evaluate

## Website Integration (GoDaddy)
The AI feedback form is embedded on the Impulse Sim website:
👉 https://impulsesim.com/ai-skills-feedback
- Add page
- chose black HTML page
- embed HTML form
  
``` <h3>Impulse Sim AI Skills Feedback</h3>

<form id="uploadForm" enctype="multipart/form-data">
  <input type="file" id="file" name="file" accept="image/*" required><br><br>
  <button type="submit">Get Feedback</button>
</form>

<pre id="result" style="white-space: pre-wrap; background: #f5f5f5; padding: 10px; border-radius: 8px;"></pre>

<script>
document.getElementById('uploadForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  console.log("Submitting image to AI evaluator...");

  const fileInput = document.getElementById('file');
  const formData = new FormData();
  formData.append('file', fileInput.files[0]);

  const res = await fetch('https://impulsesim.onrender.com/evaluate', {
    method: 'POST',
    body: formData
  });

  const data = await res.json();
  document.getElementById('result').textContent = data.feedback || 'Error: could not generate feedback.';
});
</script> 
 
🧠 How It Works

User uploads a photo via the GoDaddy form.

Flask backend encodes the image (Base64).

Sends to OpenAI GPT-4o-mini for analysis.

AI analyses spacing, tension, knot security, and alignment.

Returns structured text with score and suggestions.

Flask returns JSON → displayed instantly on the webpage.

🚀 Example Output

Input: Photo of sutured pad
Output:

Score: 8/10
Comments: Good spacing and knot security. Slight tension variation.
Suggestions: Improve wound edge eversion and maintain uniform bite depth.

🧱 Planned Upgrades
Feature	Description
Multi-skill support	Add ECG, IV, TOE, and wound closure evaluation
Educator dashboard	Track learner performance over time
LMS integration	Connect with Moodle / Blackboard
Offline mode	Lightweight model for low-resource settings
API access	Allow universities or Trusts to integrate into their own training platforms
🏢 Developer Notes

Developed by: Greg Nnabuife (Echo CNS, Imperial College Healthcare NHS Trust)

Organisation: Impulse Health Ltd (Impulse Sim division)

Purpose: Accessible, scalable AI feedback for clinical simulation and education

Stack: Flask + OpenAI GPT-4o-mini + Render + GoDaddy

📞 Contact

Impulse Health Ltd
📧 info@impulsesim.com

🌐 https://impulsesim.com

📍 London, United Kingdom

