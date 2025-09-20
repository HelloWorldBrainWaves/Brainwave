from flask import Flask, request, jsonify, render_template
import json
from langroid import Chat, tools

app = Flask(__name__)

# Load study spots dynamically
with open("study_spots.json", "r") as f:
    study_spots = json.load(f)

# Format study spots for prompt
def format_spots(spots):
    lines = []
    for spot in spots:
        tags = ", ".join(spot["tags"])
        lines.append(f"{spot['name']}: {tags}")
    return "\n".join(lines)

knowledge_base = format_spots(study_spots)

# Initialize Ollama + web access
web_search = tools.WebSearch()
chat = Chat(tools=[web_search])

# Serve frontend
@app.route("/")
def home():
    return render_template("index.html")

# Store users temporarily (in real app, use a database)
user_profiles = {}

# API endpoint
@app.route("/api/recommend", methods=["POST"])
def recommend():
    data = request.json
    email = data.get("email")  # identify returning users
    profile = user_profiles.get(email, {})

    # Merge previous profile with new data
    profile.update(data)
    user_profiles[email] = profile

    # Build prompt for AI
    prompt = f"""
You are a Purdue study space recommender.

Student Profile: {profile}

Available study spots:
{knowledge_base}

Return a JSON object with two fields:
- "spot": the recommended study spot name
- "reason": a brief explanation of why it's suitable

Example:
{{ "spot": "Hicks Undergraduate Library", "reason": "Quiet, open late, individual desks" }}
"""

    response = chat.send_message(prompt)
    return jsonify({"reply": response})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
