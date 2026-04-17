from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from groq import Groq
import os
app = Flask(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """
You are an AI agent with tools.

Available tools:
1. search_web(query)
2. open_url(url)

Rules:
- Never mention tools
- Use tools silently
- First search, then open one link
- Then give final answer
"""

# -------- Tools --------
def search_web(query):
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=3):
            results.append(r["href"])
    return results

def open_url(url):
    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        return soup.get_text()[:2000]
    except Exception as e:
        return str(e)

# -------- AI --------
def ask_ai(messages):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages
    )
    return response.choices[0].message.content or ""

# -------- API --------
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]

    for _ in range(2):
        ai_response = ask_ai(messages)

        if ai_response.startswith("TOOL:search_web:"):
            query = ai_response.replace("TOOL:search_web:", "").strip()
            results = search_web(query)

            messages.append({"role": "assistant", "content": ai_response})
            messages.append({"role": "user", "content": f"Search results: {results}"})

        elif ai_response.startswith("TOOL:open_url:"):
            url = ai_response.replace("TOOL:open_url:", "").strip()
            content = open_url(url)

            messages.append({"role": "assistant", "content": ai_response})
            messages.append({
                "role": "user",
                "content": f"Content:\n{content}\nGive final answer."
            })

        else:
            return jsonify({"response": ai_response})

    return jsonify({"response": "Could not complete request"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)