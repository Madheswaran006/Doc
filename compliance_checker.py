import os
import torch
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import re
from transformers import pipeline

# ----------------- Windows-specific HuggingFace settings -----------------
# Disable symlink warnings on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
# Optional: set cache directory
os.environ["HF_HOME"] = os.path.join(os.path.expanduser("~"), ".cache", "huggingface")

# Force CPU usage (optional, set to "cuda" if GPU available)
device = 0 if torch.cuda.is_available() else -1

# ----------------- Initialize App -----------------
app = Flask(__name__)
CORS(app)

# ----------------- Load Legal-BERT QA Pipeline -----------------
qa_pipeline = pipeline(
    "question-answering",
    model="nlpaueb/legal-bert-base-uncased",
    tokenizer="nlpaueb/legal-bert-base-uncased",
    device=device  # CPU=-1, GPU=0,1,2...
)

# ----------------- Define Legal Checks -----------------
LEGAL_CHECKS = [
    ("Is child labour allowed under 14 years?", "Child Labour (Prohibition and Regulation) Act, 1986, Section 3"),
    ("Does this contract discriminate by gender, caste, or religion?", "Indian Constitution, Article 15"),
    ("Does this contract violate minimum wage rules?", "Minimum Wages Act, 1948"),
    ("Does this contract restrict digital privacy rights?", "Information Technology Act, 2000, Section 43A"),
    ("Does this contract prevent consumer protection?", "Consumer Protection Act, 2019"),
]

# ----------------- Helper Functions -----------------
def highlight_text(text, substring):
    sentences = re.split(r'(?<=[.!?]) +', text)
    for sent in sentences:
        if substring.lower() in sent.lower():
            highlighted = f'<span style="background-color: yellow; color: red; font-weight: bold;">{sent}</span>'
            text = text.replace(sent, highlighted)
    return text

def check_compliance(text):
    violations = []
    highlighted_text = text

    for question, law in LEGAL_CHECKS:
        try:
            result = qa_pipeline(question=question, context=text)
            answer = result['answer']
            score = result['score']

            if answer.lower() in ["yes", "true", "allowed"] and score > 0.5:
                violations.append({
                    "law": law,
                    "issue": question,
                    "answer": answer,
                    "confidence": round(score, 2),
                    "suggestion": "This clause may violate Indian law. Please review."
                })
                highlighted_text = highlight_text(highlighted_text, answer)

        except Exception as e:
            violations.append({"error": str(e)})

    if not violations:
        return {"violations": "Compliant ✅ No major legal risks detected.", "highlighted": text}

    return {"violations": violations, "highlighted": highlighted_text}

# ----------------- Routes -----------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/check_compliance", methods=["POST"])
def compliance_route():
    data = request.get_json()
    text = data.get("text", "")
    result = check_compliance(text)
    return jsonify(result)

# ----------------- Run App -----------------
if __name__ == "__main__":
    app.run(debug=True)
