import json
import os
from flask import Flask, request, jsonify
from langroid.agent.chat_agent import ChatAgent
from langroid.agent.task import Task
from langroid.language_models import OpenAIGPTConfig, OpenAIChatModel
from langroid.agent.tool_message import ToolMessage
from langroid.tools.web_search import WebSearch
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

# Set up the Flask application
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
    It takes a JSON payload with a 'question' key.
    """
    data = request.json
    question = data.get('question')

    if not question:
        return jsonify({"error": "No question provided"}), 400

    try:
        # Pass the user's question to the Langroid agent and get a response
        response = task.run(question)
        return jsonify({"response": response})
    except Exception as e:
        # Handle potential errors during agent processing
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    """
    Renders a simple HTML page to interact with the assistant.
    This is for demonstration purposes.
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Local AI Assistant</title>
        <style>
            body { font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; }
            #chat-container { border: 1px solid #ccc; padding: 10px; height: 300px; overflow-y: scroll; margin-bottom: 10px; }
            #user-input { width: 100%; padding: 8px; }
            .message { margin-bottom: 10px; }
            .user { text-align: right; color: blue; }
            .assistant { text-align: left; color: green; }
        </style>
    </head>
    <body>
        <h1>Local AI Assistant</h1>
        <div id="chat-container"></div>
        <input type="text" id="user-input" placeholder="Type your question...">
        <button onclick="sendMessage()">Send</button>

        <script>
            async function sendMessage() {
                const input = document.getElementById('user-input');
                const chatContainer = document.getElementById('chat-container');
                const question = input.value;

                if (!question.trim()) return;

                // Display user message
                chatContainer.innerHTML += `<div class="message user">You: ${question}</div>`;
                input.value = '';

                // Send message to the backend
                try {
                    const response = await fetch('/ask', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ question: question })
                    });
                    const data = await response.json();
                    
                    // Display assistant's response
                    const assistantResponse = data.response;
                    chatContainer.innerHTML += `<div class="message assistant">Assistant: ${assistantResponse}</div>`;
                } catch (error) {
                    chatContainer.innerHTML += `<div class="message assistant" style="color: red;">Error: ${error.message}</div>`;
                }
                
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

            document.getElementById('user-input').addEventListener('keypress', function(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
    """

# This block ensures the Flask app runs only when the script is executed directly
if __name__ == '__main__':
    # Use a port from environment variable, or default to 5000
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

