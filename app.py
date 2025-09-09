from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import re
import os

# ----------------- Initialize Flask App -----------------
app = Flask(__name__)
CORS(app)

# ----------------- Define Lightweight Legal Checks -----------------
LEGAL_KEYWORDS = {
    "child labour": "Child Labour (Prohibition and Regulation) Act, 1986, Section 3",
    "gender discrimination": "Indian Constitution, Article 15",
    "religion discrimination": "Indian Constitution, Article 15",
    "caste discrimination": "Indian Constitution, Article 15",
    "minimum wage": "Minimum Wages Act, 1948",
    "digital privacy": "Information Technology Act, 2000, Section 43A",
    "consumer protection": "Consumer Protection Act, 2019"
}

# ----------------- Helper Functions -----------------
def highlight_text(text, keyword):
    """
    Highlight sentences containing the keyword.
    """
    sentences = re.split(r'(?<=[.!?]) +', text)
    for sent in sentences:
        if keyword.lower() in sent.lower():
            highlighted = f'<span style="background-color: yellow; color: red; font-weight: bold;">{sent}</span>'
            text = text.replace(sent, highlighted)
    return text

def check_compliance(text):
    """
    Run keyword-based legal checks on the input text.
    """
    violations = []
    highlighted_text = text

    for keyword, law in LEGAL_KEYWORDS.items():
        if keyword.lower() in text.lower():
            violations.append({
                "law": law,
                "issue": f"Possible violation related to '{keyword}'",
                "suggestion": "Please review this clause carefully."
            })
            highlighted_text = highlight_text(highlighted_text, keyword)

    if not violations:
        return {"violations": "✅ Compliant. No major legal risks detected.", "highlighted": text}

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
