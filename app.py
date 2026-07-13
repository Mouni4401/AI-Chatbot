import os
import uuid
import random

from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Secret key for sessions
app.secret_key = os.getenv(
    "FLASK_SECRET",
    "change-this-secret-key"
)

# Gemini API Key
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found. Add it to your .env file."
    )

# Configure Gemini
genai.configure(api_key=API_KEY)

# Create Gemini model
model = genai.GenerativeModel("gemini-2.5-flash")

# Personas
PERSONAS = {
    "assistant": {
        "label": "Assistant",
        "emoji": "🤖",
        "system": "You are a helpful AI assistant.",
        "color": "#6366f1"
    },
    "philosopher": {
        "label": "Philosopher",
        "emoji": "🧠",
        "system": "You are a thoughtful philosopher who explains ideas deeply.",
        "color": "#8b5cf6"
    },
    "coder": {
        "label": "Code Wizard",
        "emoji": "💻",
        "system": "You are an expert software engineer. Use code examples whenever helpful.",
        "color": "#06b6d4"
    },
    "poet": {
        "label": "Poet",
        "emoji": "✍️",
        "system": "You are a creative poet and storyteller.",
        "color": "#ec4899"
    }
}

# Session memory
sessions = {}


@app.route("/")
def index():
    if "sid" not in session:
        session["sid"] = str(uuid.uuid4())

    return render_template(
        "index.html",
        personas=PERSONAS
    )


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    user_message = data.get(
        "message",
        ""
    ).strip()

    persona_key = data.get(
        "persona",
        "assistant"
    )

    if not user_message:
        return jsonify(
            {"error": "Message cannot be empty"}
        ), 400

    sid = session.get("sid")

    if sid not in sessions:
        sessions[sid] = []

    persona = PERSONAS.get(
        persona_key,
        PERSONAS["assistant"]
    )

    sessions[sid].append(
        {
            "role": "user",
            "content": user_message
        }
    )

    # Keep last 20 messages
    history = sessions[sid][-20:]

    try:
        # Build conversation context
        prompt = f"System: {persona['system']}\n\n"

        for msg in history:
            prompt += f"{msg['role']}: {msg['content']}\n"

        prompt += "\nassistant:"

        response = model.generate_content(prompt)

        reply = response.text

        sessions[sid].append(
            {
                "role": "assistant",
                "content": reply
            }
        )

        return jsonify(
            {
                "reply": reply,
                "persona_emoji": persona["emoji"],
                "persona_color": persona["color"],
                "message_count": len(sessions[sid]) // 2
            }
        )

    except Exception as e:
        print("Gemini Error:", e)

        return jsonify(
            {
                "error": str(e)
            }
        ), 500


@app.route("/clear", methods=["POST"])
def clear():
    sid = session.get("sid")

    if sid in sessions:
        del sessions[sid]

    return jsonify(
        {
            "status": "cleared"
        }
    )


@app.route("/suggest")
def suggest():
    persona_key = request.args.get(
        "persona",
        "assistant"
    )

    starters = {
        "assistant": [
            "Explain artificial intelligence simply.",
            "How can I improve productivity?",
            "Teach me Python basics."
        ],
        "philosopher": [
            "What is the meaning of life?",
            "Do humans have free will?",
            "Can machines think?"
        ],
        "coder": [
            "Explain REST API.",
            "What is recursion?",
            "Difference between SQL and NoSQL?"
        ],
        "poet": [
            "Write a poem about rain.",
            "Describe the moon beautifully.",
            "Tell a magical short story."
        ]
    }

    return jsonify(
        {
            "suggestion": random.choice(
                starters.get(
                    persona_key,
                    starters["assistant"]
                )
            )
        }
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )