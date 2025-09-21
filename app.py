import os
import json
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, jsonify, session

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

# Paths
BASE = Path(__file__).parent
USER_FILE = BASE / "users.json"
SPOTS_FILE = BASE / "study_spots.json"

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Load study spots
with open(SPOTS_FILE, "r", encoding="utf-8") as f:
    STUDY_SPOTS = json.load(f)

# helper: load/save users
def load_users():
    if USER_FILE.exists():
        return json.loads(USER_FILE.read_text(encoding="utf-8"))
    return []

def save_users(users):
    USER_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")

# -----------------------
# Routes - pages
# -----------------------
@app.route("/")
def welcome():
    return render_template("welcome.html")

@app.route("/auth", methods=["GET", "POST"])
def auth():
    # simple signup/login - user stored in users.json by email
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        if not email:
            return render_template("auth.html", error="Email required")
        users = load_users()
        user = next((u for u in users if u["email"] == email), None)
        if not user:
            # create new user
            user = {"name": name or email.split("@")[0], "email": email}
            users.append(user)
            save_users(users)
        session["email"] = email
        return redirect(url_for("questionnaire"))
    return render_template("auth.html")

@app.route("/logout")
def logout():
    session.pop("email", None)
    session.pop("selected_match", None)
    return redirect(url_for("welcome"))

@app.route("/questionnaire", methods=["GET", "POST"])
def questionnaire():
    if "email" not in session:
        return redirect(url_for("auth"))
    if request.method == "POST":
        # Collect fields
        data = {
            "name": request.form.get("name", "").strip(),
            "email": session["email"],
            "year": request.form.get("year"),
            "major": request.form.get("major"),
            "classes": request.form.get("classes"),
            "groupSize": request.form.get("groupSize"),
            "comfortLevel": request.form.get("comfortLevel"),
            "spacePrefs": request.form.getlist("spacePrefs"),
            "travelDistance": request.form.get("travelDistance"),
            "studyTimes": request.form.get("studyTimes"),
            "personality": request.form.get("personality"),
            "goal": request.form.get("goal"),
            "bio": request.form.get("bio"),
        }
        # try to get lat/lng from form if present (JS geolocation writes these hidden fields)
        lat = request.form.get("latitude")
        lng = request.form.get("longitude")
        if lat and lng:
            try:
                data["latitude"] = float(lat)
                data["longitude"] = float(lng)
            except:
                pass
        # save/update user
        users = load_users()
        existing = next((u for u in users if u["email"] == data["email"]), None)
        if existing:
            existing.update(data)
        else:
            users.append(data)
        save_users(users)
        # call OpenAI to pick recommended spot (server-side)
        try:
            rec = recommend_spot_from_preferences(data)
            # store recommended in user record
            existing = next((u for u in users if u["email"] == data["email"]), None)
            if existing:
                existing["recommended"] = rec
                save_users(users)
        except Exception as e:
            print("Recommendation error:", e)
        return redirect(url_for("profile"))
    # GET
    return render_template("questionnaire.html", spots=STUDY_SPOTS)

@app.route("/profile")
def profile():
    if "email" not in session:
        return redirect(url_for("auth"))
    users = load_users()
    user = next((u for u in users if u["email"] == session["email"]), None)
    return render_template("profile.html", user=user)

@app.route("/matches")
def matches():
    if "email" not in session:
        return redirect(url_for("auth"))
    users = load_users()
    current = next((u for u in users if u["email"] == session["email"]), None)
    # compute compatibility simple scoring
    candidates = []
    for u in users:
        if u["email"] == session["email"]:
            continue
        score = 0
        # group size
        if u.get("groupSize") and current.get("groupSize") and u["groupSize"] == current["groupSize"]:
            score += 2
        # comfort
        if u.get("comfortLevel") and current.get("comfortLevel") and u["comfortLevel"] == current["comfortLevel"]:
            score += 2
        # space pref overlap
        a = set(u.get("spacePrefs", []))
        b = set(current.get("spacePrefs", []))
        score += len(a & b)
        # basic location proximity (if both have coords)
        dist_km = None
        if u.get("latitude") and current.get("latitude"):
            from math import radians, cos, sin, asin, sqrt
            lat1, lon1 = current["latitude"], current["longitude"]
            lat2, lon2 = u["latitude"], u["longitude"]
            # haversine
            R = 6371
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a_h = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
            c = 2 * asin(sqrt(a_h))
            dist_km = R * c
        candidates.append({"user": u, "score": score, "distance_km": dist_km})
    candidates = sorted(candidates, key=lambda x: (x["score"], - (x["distance_km"] or 0)), reverse=True)
    return render_template("matches.html", candidates=candidates)

@app.route("/select_match", methods=["POST"])
def select_match():
    if "email" not in session:
        return redirect(url_for("auth"))
    chosen_email = request.form.get("chosen_email")
    session["selected_match"] = chosen_email
    return redirect(url_for("map_view"))

@app.route("/map")
def map_view():
    if "email" not in session:
        return redirect(url_for("auth"))
    users = load_users()
    current = next((u for u in users if u["email"] == session["email"]), None)
    selected = None
    if session.get("selected_match"):
        selected = next((u for u in users if u["email"] == session["selected_match"]), None)
    # recommended spot name stored in current['recommended'] if previously saved
    recommended = None
    if current:
        recommended = current.get("recommended")
    # Pass spots as list for mapping coordinates
    return render_template("map.html", current=current, selected=selected, recommended=recommended, spots=STUDY_SPOTS, google_api_key=GOOGLE_MAPS_API_KEY)

# -----------------------
# Backend helper: OpenAI recommend
# -----------------------
def recommend_spot_from_preferences(user_data):
    # This function calls OpenAI to choose a spot name from STUDY_SPOTS and return {spot, reason}
    # It will prompt the model to pick ONLY names from the list and return JSON.
    import openai
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set in environment")
    openai.api_key = OPENAI_API_KEY

    # prepare list of spot names
    names = [s["name"] for s in STUDY_SPOTS]
    prompt = f"""You are a helpful assistant that recommends the best study spot on Purdue campus.
Given the student's preferences and this list of candidate spots, pick exactly one spot name from the list and respond ONLY in JSON with fields "spot" and "reason".
Candidate spots: {names}

Student preferences:
Name: {user_data.get('name')}
Group size: {user_data.get('groupSize')}
Comfort level: {user_data.get('comfortLevel')}
Space preferences: {', '.join(user_data.get('spacePrefs', []))}
Travel distance: {user_data.get('travelDistance')}
Study times: {user_data.get('studyTimes')}
Personality: {user_data.get('personality')}
Goal: {user_data.get('goal')}

Return a JSON object, e.g.
{{ "spot": "Hicks Undergraduate Library", "reason": "Quiet, open late, individual desks and outlets" }}
"""
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":"You are concise and return only the requested JSON."},
                  {"role":"user","content":prompt}],
        max_tokens=200,
        temperature=0.1,
    )
    text = resp["choices"][0]["message"]["content"].strip()
    # attempt to parse JSON substring
    import json, re
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise RuntimeError("OpenAI did not return JSON")
    parsed = json.loads(m.group(0))
    # find matching spot in STUDY_SPOTS and attach lat/lng if available
    for s in STUDY_SPOTS:
        if s["name"] == parsed["spot"]:
            parsed["lat"] = s.get("lat")
            parsed["lng"] = s.get("lng")
            break
    return parsed

# -----------------------
# API helper for frontend if needed
# -----------------------
@app.route("/api/get_recommendation")
def api_get_recommendation():
    if "email" not in session:
        return jsonify({"error": "not logged in"}), 401
    users = load_users()
    current = next((u for u in users if u["email"] == session["email"]), None)
    if not current:
        return jsonify({"error":"no user data"}), 400
    if not current.get("recommended"):
        # attempt to compute again
        try:
            rec = recommend_spot_from_preferences(current)
            current["recommended"] = rec
            users = load_users()
            e = next((u for u in users if u["email"] == current["email"]), None)
            if e:
                e["recommended"] = rec
                save_users(users)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return jsonify(current["recommended"])

if __name__ == "__main__":
    app.run(debug=True)