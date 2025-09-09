from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import re
import os
from transformers import pipeline

# ----------------- Initialize Flask App -----------------
app = Flask(__name__)
CORS(app)

# ----------------- Load Legal-BERT QA Pipeline -----------------
qa_pipeline = pipeline(
    "question-answering",
    model="nlpaueb/legal-bert-base-uncased",
    tokenizer="nlpaueb/legal-bert-base-uncased"
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
    """
    Highlight sentences containing the substring.
    """
    sentences = re.split(r'(?<=[.!?]) +', text)
    for sent in sentences:
        if substring.lower() in sent.lower():
            highlighted = f'<span style="background-color: yellow; color: red; font-weight: bold;">{sent}</span>'
            text = text.replace(sent, highlighted)
    return text

def check_compliance(text):
    """
    Run all legal checks on the input text and highlight violations.
    """
    violations = []
    highlighted_text = text

    for question, law in LEGAL_CHECKS:
        try:
            result = qa_pipeline(question=question, context=text)
            answer = result['answer']
            score = result['score']

            # Only flag if QA predicts yes/true
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

# ----------------- Run Flask App -----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
