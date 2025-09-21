import os
from flask import Flask, request, jsonify, render_template
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure OpenAI Chat Model
llm = ChatOpenAI(
    model_name="gpt-4",  # or gpt-3.5-turbo
    temperature=0.7
)

# Define a chat prompt template
prompt_template = ChatPromptTemplate.from_messages([
    HumanMessagePromptTemplate.from_template(
        """Act as a Purdue University study planner. Based on the following student information,
        recommend a specific and ideal study location on campus.

Student Profile:
- Name: {name}
- Year: {year}
- Major: {major}
- Classes: {classes}
- Desired Group Size: {groupSize}
- Comfort Level: {comfortLevel}
- Space Preferences: {spacePrefs}
- Travel Distance: {travelDistance}
- Study Times: {times}
- Personality: {personality}
- Goal: {goal}
- Bio: {bio}

Current Context:
- Current Location (Latitude, Longitude): ({latitude}, {longitude})
- Current Time: {currentTime}

The recommendation should be a specific building or location, with a brief explanation of why it fits the criteria. Be friendly and helpful."""
    )
])

# Initialize chain
chain = LLMChain(llm=llm, prompt=prompt_template)

@app.route("/ask", methods=["POST"])
def ask_assistant():
    data = request.json or {}

    # Build context for the prompt
    context = {
        "name": data.get("name", "Not specified"),
        "year": data.get("year", "Not specified"),
        "major": data.get("major", "Not specified"),
        "classes": data.get("classes", "Not specified"),
        "groupSize": data.get("groupSize", "Not specified"),
        "comfortLevel": data.get("comfortLevel", "Not specified"),
        "spacePrefs": ", ".join(data.get("spacePrefs", [])) or "None",
        "travelDistance": data.get("travelDistance", "Not specified"),
        "times": data.get("times", "Not specified"),
        "personality": data.get("personality", "Not specified"),
        "goal": data.get("goal", "Not specified"),
        "bio": data.get("bio", "Not specified"),
        "latitude": data.get("latitude", "Not specified"),
        "longitude": data.get("longitude", "Not specified"),
        "currentTime": data.get("currentTime", "Not specified")
    }

    try:
        response = chain.run(context)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
