import re
import json
import os
import streamlit as st
from groq import Groq

# 1. Connect to Groq safely (uses Streamlit Secrets online, or your key locally)
api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key, timeout=30.0)
MODEL_NAME = "qwen/qwen3.8-27b"  # Change to the exact Qwen model ID you used!

# 2. Mock Internships Database (Expand this to 6-8 roles so demos feel real)
JOBS_DB = [
    {"id": 1, "role": "SDE Intern", "company": "Elip",
        "city": "Bengaluru", "pay": "₹75,000/mo"},
    {"id": 2, "role": "AI Engineer Intern", "company": "Zoho",
        "city": "Chennai", "pay": "₹40,000/mo"},
    {"id": 3, "role": "Python Backend Intern", "company": "Sarvam AI",
        "city": "Bengaluru", "pay": "₹60,000/mo"},
    {"id": 4, "role": "ML Research Intern", "company": "Krutrim",
        "city": "Bengaluru", "pay": "₹50,000/mo"},
    {"id": 5, "role": "Full Stack Intern", "company": "Freshworks",
        "city": "Chennai", "pay": "₹35,000/mo"},
]


def search_jobs(city: str):
    matches = [job for job in JOBS_DB if city.lower() in job["city"].lower()]
    return json.dumps(matches)


tools = [
    {
        "type": "function",
        "function": {
            "name": "search_jobs",
            "description": "Search available internships by city name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name, e.g., Bengaluru or Chennai"}
                },
                "required": ["city"],
            },
        },
    }
]

# 3. Build the Web Interface
st.set_page_config(page_title="AI Internship Finder", page_icon="🚀")
st.title("🚀 Conversational AI Internship Finder")
st.caption("Built with Python, Groq LLM Tool-Calling, and Streamlit")

# Keep chat history in browser memory
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful AI internship finder. Use search_jobs when users ask about roles in a city. Keep answers concise."}
    ]

# Display previous chat messages
for msg in st.session_state.messages:
    if msg["role"] in ["user", "assistant"] and msg.get("content"):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Chat input box at the bottom of the webpage
if user_prompt := st.chat_input("Ask me: 'Find internships in Bengaluru' or 'Roles in Chennai'"):
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching internships..."):
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=st.session_state.messages,
                tools=tools,
                tool_choice="auto",
            )
            ai_msg = response.choices[0].message

            if ai_msg.tool_calls:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": ai_msg.content or "",
                    "tool_calls": [tc.model_dump() for tc in ai_msg.tool_calls]
                })
                for tool_call in ai_msg.tool_calls:
                    args = json.loads(tool_call.function.arguments)
                    st.toast(
                        f"🤖 Tool Called: search_jobs(city='{args['city']}')")
                    result = search_jobs(city=args["city"])
                    st.session_state.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": "search_jobs",
                        "content": result,
                    })

                final_response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=st.session_state.messages
                )
                reply = final_response.choices[0].message.content
            else:
                reply = ai_msg.content

            reply = re.sub(r"<think.*?</think>", "",
                           reply, flags=re.DOTALL).strip()
            st.markdown(reply)
            st.session_state.messages.append(
                {"role": "assistant", "content": reply})
