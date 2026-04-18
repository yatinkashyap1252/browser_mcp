from flask import Flask, request, jsonify
from groq import Groq
import os
import time
import threading

app = Flask(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

# ---------------- FAST AI ----------------
def ask_ai_fast(user_input):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Give fast, concise answers."},
            {"role": "user", "content": user_input}
        ],
        temperature=0.3,
        max_tokens=300
    )
    return response.choices[0].message.content or ""


# ---------------- OPTIONAL BACKGROUND SEARCH ----------------
def enrich_async(query):
    try:
        from ddgs import DDGS
        import requests
        from bs4 import BeautifulSoup

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=1))

        if results:
            url = results[0]["href"]
            res = requests.get(url, timeout=5)
            soup = BeautifulSoup(res.text, "html.parser")
            text = soup.get_text()[:1000]

            print("\n🔎 Background info fetched:\n", text[:300])

    except Exception as e:
        print("Background error:", e)


# ---------------- HEALTH ROUTE ----------------
@app.route("/")
def home():
    return "OK"


# ---------------- CHAT API ----------------
@app.route("/chat", methods=["POST"])
def chat():
    start = time.time()

    try:
        data = request.get_json()
        user_input = data.get("message", "")

        if not user_input:
            return jsonify({"response": "Empty message"}), 400

        # ⚡ FAST RESPONSE (main goal)
        answer = ask_ai_fast(user_input)

        # ⏱ HARD TIME LIMIT (safety)
        if time.time() - start > 3:
            return jsonify({"response": "Server busy, try again."})

        # 🚀 OPTIONAL: run search in background (non-blocking)
        threading.Thread(target=enrich_async, args=(user_input,)).start()

        return jsonify({
            "response": answer,
            "time_taken": round(time.time() - start, 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

    
# from flask import Flask, request, jsonify
# import requests
# from bs4 import BeautifulSoup
# from ddgs import DDGS
# from groq import Groq
# import os
# app = Flask(__name__)

# client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# MODEL = "llama-3.3-70b-versatile"

# SYSTEM_PROMPT = """
# You are an AI agent with tools.

# Available tools:
# 1. search_web(query)
# 2. open_url(url)

# Rules:
# - Never mention tools
# - Use tools silently
# - First search, then open one link
# - Then give final answer
# """

# # -------- Tools --------
# def search_web(query):
#     results = []
#     with DDGS() as ddgs:
#         for r in ddgs.text(query, max_results=3):
#             results.append(r["href"])
#     return results

# def open_url(url):
#     try:
#         res = requests.get(url, timeout=20)
#         soup = BeautifulSoup(res.text, "html.parser")
#         return soup.get_text()[:2000]
#     except Exception as e:
#         return str(e)

# # -------- AI --------
# def ask_ai(messages):
#     response = client.chat.completions.create(
#         model=MODEL,
#         messages=messages
#     )
#     return response.choices[0].message.content or ""

# # -------- API --------
# @app.route("/chat", methods=["POST"])
# def chat():
#     try:
#         user_input = request.json.get("message")

#         if not user_input:
#             return jsonify({"response": "No input provided"}), 400

#         messages = [
#             {"role": "system", "content": SYSTEM_PROMPT},
#             {"role": "user", "content": user_input}
#         ]

#         # Maximum number of tool invocation steps allowed per request
#         MAX_TOOL_STEPS = 2
#         for _ in range(MAX_TOOL_STEPS):
#             ai_response = ask_ai(messages)

#             if ai_response.startswith("TOOL:search_web:"):
#                 query = ai_response.replace("TOOL:search_web:", "").strip()
#                 results = search_web(query)

#                 messages.append({"role": "assistant", "content": ai_response})
#                 messages.append({"role": "user", "content": f"Search results: {results}"})

#             elif ai_response.startswith("TOOL:open_url:"):
#                 url = ai_response.replace("TOOL:open_url:", "").strip()
#                 content = open_url(url)

#                 messages.append({"role": "assistant", "content": ai_response})
#                 messages.append({
#                     "role": "user",
#                     "content": f"Content:\n{content}\nGive final answer."
#                 })

#             else:
#                 return jsonify({"response": ai_response})

#         return jsonify({"response": "Could not complete request"})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @app.route("/")
# def home():
#     return "Server is running"


# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)