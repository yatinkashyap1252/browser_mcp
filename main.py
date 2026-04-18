import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from groq import Groq

client = Groq()

def ask_ai(messages):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages
    )
    
    return response.choices[0].message.content

def search_web(query):
    results = []
    
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=3):
            results.append(r["href"])
    
    return results

# ---------------- TOOL ----------------
def open_url(url):
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")

        # Extract visible text
        text = soup.get_text()
        return text[:2000]  # limit to avoid overload

    except Exception as e:
        return f"Error fetching URL: {e}"

# ---------------- AGENT LOOP ----------------
SYSTEM_PROMPT = """
You are an AI agent with tools.

Available tools:

1. search_web(query)
Format: TOOL:search_web:<query>

2. open_url(url)
Format: TOOL:open_url:<url>

Rules:
- NEVER explain your steps
- NEVER mention tools in final answer
- NEVER show TOOL commands to user
- Use tools silently when needed
- First search, then open one link
- After getting content, give final answer
- If enough info is available, answer directly
- Keep answers clean and user-friendly
"""

while True:
    user_input = input("You: ")

    if user_input.lower() == "exit":
        break

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]

    final_answer = None

    for _ in range(2):
        ai_response = ask_ai(messages)

        if ai_response.startswith("TOOL:search_web:"):
            query = ai_response.replace("TOOL:search_web:", "").strip()
            # print("🔍 Searching:", query)

            results = search_web(query)

            messages.append({"role": "assistant", "content": ai_response})
            messages.append({
                "role": "user",
                "content": f"Search results: {results}"
            })

        elif ai_response.startswith("TOOL:open_url:"):
            url = ai_response.replace("TOOL:open_url:", "").strip()
            # print("🌐 Opening:", url)

            content = open_url(url)

            messages.append({"role": "assistant", "content": ai_response})
            messages.append({
                "role": "user",
                "content": f"Content from {url}:\n{content}\nNow give final answer. Do NOT use any tool."
            })

        else:
            final_answer = ai_response
            break

    if final_answer:
        print("AI:", final_answer)