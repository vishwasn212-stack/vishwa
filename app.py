import streamlit as st
from groq import Groq
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv

# =========================
# LOAD ENV VARIABLES
# =========================
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# =========================
# GROQ API SETUP
# =========================
client = Groq(
    api_key=GROQ_API_KEY
)

# =========================
# DATABASE SETUP
# =========================
conn = sqlite3.connect("chat_history.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    answer TEXT,
    time TEXT
)
""")

conn.commit()

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="AI Law Chatbot")

st.title("⚖️ AI Law & Society Chatbot")

st.markdown("""
Ask questions about:

- Indian laws
- Cyber crime
- FIR
- Consumer rights
- Women rights
- Constitution
- Traffic rules
- Society issues
""")

# =========================
# SESSION HISTORY
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []

# =========================
# DISPLAY OLD CHATS
# =========================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =========================
# USER INPUT
# =========================
prompt = st.chat_input("Ask your legal question...")

if prompt:

    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    # =========================
    # AI RESPONSE
    # =========================
    with st.chat_message("assistant"):

        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "system",
                    "content": """
You are an AI legal and social awareness assistant.

Explain laws in simple language.
Give educational information only.
Do not provide harmful or illegal advice.
Explain clearly with examples whenever possible.
"""
                },
                *st.session_state.messages
            ],
            temperature=0.5,
            max_tokens=1024
        )

        answer = response.choices[0].message.content
        st.markdown(answer)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )

    # =========================
    # SAVE TO DATABASE
    # =========================
    cursor.execute("""
    INSERT INTO chats (question, answer, time)
    VALUES (?, ?, ?)
    """, (prompt, answer, str(datetime.now())))

    conn.commit()

# =========================
# SIDEBAR HISTORY
# =========================
st.sidebar.title("📜 Chat History")

cursor.execute("SELECT question, time FROM chats ORDER BY id DESC")
rows = cursor.fetchall()

for row in rows[:20]:
    st.sidebar.write(f"🕒 {row[1]}")
    st.sidebar.write(f"❓ {row[0]}")
    st.sidebar.markdown("---")
