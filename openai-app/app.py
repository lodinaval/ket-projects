import os
from flask import Flask, render_template, request, jsonify
from openai import OpenAI          # <— new import
from dotenv import load_dotenv

load_dotenv()
# instantiate once at startup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_msg = data.get("message", "").strip()
    print("Received message:", user_msg)           # for debugging

    try:
        resp = client.chat.completions.create(      # <— new method
            model="gpt-4o-2024-11-20",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user",   "content": user_msg}
            ],
            temperature=0.7,
        )
        assistant_msg = resp.choices[0].message.content
        return jsonify({"reply": assistant_msg})
    except Exception as e:
        app.logger.error(f"❌ OpenAI API error: {e}")
        return jsonify({"error": "OpenAI API error"}), 500

if __name__ == "__main__":
    app.run(debug=True)