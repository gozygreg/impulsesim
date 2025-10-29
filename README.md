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

