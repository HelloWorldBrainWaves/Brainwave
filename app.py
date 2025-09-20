from flask import Flask, request, jsonify, render_template
import json
from langroid.agents.chat import Chat
from langroid import tools
from langroid.tools.web_search import WebSearch



app = Flask(__name__)

with open("study_spots.json", "r") as f:
    study_spots = json.load(f)

def format_spots(spots):
    lines = []
    for spot in spots:
        tags = ", ".join(spot["tags"])
        lines.append(f"{spot['name']}: {tags}")
    return "\n".join(lines)

knowledge_base = format_spots(study_spots)

web_search = WebSearch()
chat = Chat(tools=[web_search])

@app.route("/")
def home():
    return render_template("index.html")

user_profiles = {}

@app.route("/api/recommend", methods=["POST"])
def recommend():
    data = request.json
    email = data.get("email")
    profile = user_profiles.get(email, {})
    profile.update(data)
    user_profiles[email] = profile

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
    response = chat.chat(prompt)
    return jsonify({"reply": response})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
