from flask import Flask, render_template, request
from classifier import classify_text
from file_processor import *
from document_qa import answer_question
import os
import csv
import pandas as pd
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

latest_document_text = ""

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
RESULTS_FILE = "data/results.csv"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("data", exist_ok=True)

# Create results.csv if not exists
if not os.path.exists(RESULTS_FILE):
    with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "filename",
            "category",
            "priority",
            "confidence",
            "sentiment",
            "action"
        ])


@app.route("/")
def home():
    return render_template("index.html")


# ==========================
# FILE ANALYSIS ROUTE
# ==========================
@app.route("/analyze", methods=["POST"])
def analyze():

    global latest_document_text

    uploaded_file = request.files["file"]

    filepath = os.path.join(
        UPLOAD_FOLDER,
        uploaded_file.filename
    )

    uploaded_file.save(filepath)

    ext = uploaded_file.filename.split(".")[-1].lower()

    if ext == "txt":
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

    elif ext == "pdf":
        text = read_pdf(filepath)
        latest_document_text = text

    elif ext == "html":
        text = read_html(filepath)

    elif ext == "csv":
        text = read_csv(filepath)

    else:
        text = "Unsupported file"

    result = classify_text(text)

    category = "Unknown"
    priority = "Medium"
    action = "Review"
    summary = ""
    suggested_action = ""
    suggested_reply = ""
    needs_human = False
    confidence = 0
    data = {}

    try:
        cleaned = result.replace("```json", "").replace("```", "").strip()
        data = json.loads(cleaned)

        category = data.get("category", "Unknown")
        priority = data.get("priority", "Medium")
        summary = data.get("summary", "")
        suggested_action = data.get("suggested_action", "")
        suggested_reply = data.get("suggested_reply", "")
        needs_human = data.get("needs_human", False)
        confidence = data.get("confidence", 80)

    except Exception as e:
        print("JSON Parsing Error:", e)

    # Save to CSV
    with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            uploaded_file.filename,
            category,
            priority,
            confidence,
            "Neutral",
            suggested_action
        ])

    return render_template(
        "result.html",
        result_json=json.dumps(data, indent=4)
    )


# ==========================
# DASHBOARD
# ==========================
@app.route("/dashboard")
def dashboard():

    df = pd.read_csv(RESULTS_FILE)

    total_files = len(df)

    billing_count = len(
        df[df["category"].astype(str).str.lower() == "billing"]
    )

    category_counts = df["category"].value_counts().to_dict()
    priority_counts = df["priority"].value_counts().to_dict()

    human_reviews = len(df)

    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce")

    avg_confidence = round(df["confidence"].mean(), 2) if len(df) > 0 else 0

    records = df.tail(10).to_dict("records")

    human_review_cases = df[
        df["confidence"] < 75
    ].to_dict("records")

    return render_template(
        "dashboard.html",
        total_files=total_files,
        billing_count=billing_count,
        human_reviews=human_reviews,
        avg_confidence=avg_confidence,
        records=records,
        human_review_cases=human_review_cases,
        category_counts=category_counts,
        priority_counts=priority_counts
    )


# ==========================
# DOCUMENT Q&A
# ==========================
@app.route("/qa")
def qa():
    return render_template("qa.html", answer=None)


@app.route("/ask", methods=["POST"])
def ask():

    global latest_document_text

    question = request.form["question"]

    if not latest_document_text:
        answer = "Please upload a PDF first before asking questions."
    else:
        answer = answer_question(latest_document_text, question)

    return render_template("qa.html", answer=answer)


# ==========================
# MULTILINGUAL CHAT (NEW FEATURE)
# ==========================
@app.route("/chat", methods=["GET", "POST"])
def chat():

    result = None

    if request.method == "POST":

        user_text = request.form["message"]

        prompt = f"""
You are an AI customer support system.

User may write in ANY language.

1. Detect language
2. Translate to English
3. Classify ticket
4. Return ONLY JSON

Output format:
{{
  "original_language": "...",
  "translated_english": "...",
  "category": "...",
  "priority": "...",
  "summary": "...",
  "suggested_action": "...",
  "suggested_reply": "...",
  "needs_human": true,
  "confidence": 0-100
}}

Message:
{user_text}
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )

        result = response.choices[0].message.content

    return render_template("chat.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)