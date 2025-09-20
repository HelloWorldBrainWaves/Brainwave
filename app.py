import json
import os
from flask import Flask, request, jsonify, render_template
from langroid.agent.chat_agent import ChatAgent
from langroid.agent.task import Task
from langroid.language_models import OpenAIGPTConfig, OpenAIChatModel
from langroid.agent.tool_message import ToolMessage
from langroid.tools.web_search import WebSearch
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

# Set up the Flask application
# Flask will look for HTML files in a folder named 'templates'
app = Flask(__name__)

# Configure the LLM to use a local Ollama model.
# This config object is designed to be compatible with OpenAI-like APIs,
# which Ollama provides out of the box.
llm_config = OpenAIGPTConfig(
    chat_model="ollama/llama3",  # Change "llama3" to the model you have pulled with Ollama
    api_base="http://localhost:11434/v1"
)

# Initialize the chat agent with a web search tool.
# This tool allows the agent to perform Google searches to answer
# questions that require up-to-date or specific information.
web_search = WebSearch()
agent = ChatAgent(
    config=llm_config,
    tools=[web_search]
)

# Initialize a task for the agent. The system message gives the LLM
# its instructions and persona.
task = Task(
    agent=agent,
    system_message="You are a helpful assistant. You are capable of using a web search tool to find information. If you are asked a question that requires current information or facts you don't know, you must use the web search tool."
)

@app.route('/ask', methods=['POST'])
def ask_assistant():
    """
    Handles a POST request to ask the Langroid chat assistant a question.
    It now takes all form data and builds a single, detailed prompt.
    """
    data = request.json
    
    # Construct the comprehensive prompt for the AI from the form data
    prompt = f"""Act as a Purdue University study planner. Based on the following student information, recommend a specific and ideal study location on campus.

Student Profile:
- Name: {data.get('name', 'Not specified')}
- Year: {data.get('year', 'Not specified')}
- Major: {data.get('major', 'Not specified')}
- Classes: {data.get('classes', 'Not specified')}
- Desired Group Size: {data.get('groupSize', 'Not specified')}
- Comfort Level: {data.get('comfortLevel', 'Not specified')}
- Space Preferences: {', '.join(data.get('spacePrefs', []) ) or 'None'}
- Travel Distance: {data.get('travelDistance', 'Not specified')}
- Study Times: {data.get('times', 'Not specified')}
- Personality: {data.get('personality', 'Not specified')}
- Goal: {data.get('goal', 'Not specified')}
- Bio: {data.get('bio', 'Not specified')}

Current Context:
- Current Location (Latitude, Longitude): ({data.get('latitude', 'Not specified')}, {data.get('longitude', 'Not specified')})
- Current Time: {data.get('currentTime', 'Not specified')}

The recommendation should be a specific building or location, with a brief explanation of why it fits the criteria. Be friendly and helpful.
"""
    
    try:
        # Pass the detailed prompt to the Langroid agent and get a response
        response = task.run(prompt)
        return jsonify({"response": response})
    except Exception as e:
        # Handle potential errors during agent processing
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    """
    Renders the HTML page to interact with the assistant.
    """
    return render_template('index.html')

# This block ensures the Flask app runs only when the script is executed directly
if __name__ == '__main__':
    # Use a port from environment variable, or default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
