import streamlit as st
from groq import Groq
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv

# ======================================================
# LOAD ENV VARIABLES
# ======================================================
load_dotenv("api.env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ======================================================
# GROQ CLIENT
# ======================================================
client = Groq(
    api_key=GROQ_API_KEY
)

# ======================================================
# DATABASE SETUP
# ======================================================
conn = sqlite3.connect(
    "chat_history.db",
    check_same_thread=False
)

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

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="AI Law & Society Chatbot",
    page_icon="⚖️",
    layout="wide"
)

# ======================================================
# CUSTOM CSS
# ======================================================
st.markdown("""
<style>

.main {
    background-color: #f5f7fa;
}

.stChatMessage {
    border-radius: 10px;
    padding: 10px;
}

.sidebar .sidebar-content {
    background-color: #ffffff;
}

</style>
""", unsafe_allow_html=True)

# ======================================================
# TITLE
# ======================================================
st.title("⚖️ AI Law & Society Chatbot")

st.markdown("""
### Ask Questions About:
- Indian Laws
- Cyber Crime
- FIR & Police Complaints
- Consumer Rights
- Women Rights
- Constitution
- Traffic Rules
- Social Issues
- Legal Awareness
""")

# ======================================================
# SIDEBAR SETTINGS
# ======================================================
st.sidebar.title("⚙️ Chat Settings")

answer_mode = st.sidebar.selectbox(
    "Select Answer Type",
    [
        "Short",
        "Medium",
        "Detailed",
        "Extra Detailed"
    ]
)

# ======================================================
# TOKEN MANAGEMENT
# ======================================================
if answer_mode == "Short":

    max_tokens = 250

    instruction = """
Give a short and direct answer.
Use simple language.
Maximum 5 concise points.
"""

elif answer_mode == "Medium":

    max_tokens = 600

    instruction = """
Give a medium-length explanation.

Include:
- Simple explanation
- Important points
- Small examples

Use bullet points and headings.
"""

elif answer_mode == "Detailed":

    max_tokens = 1200

    instruction = """
Give a detailed explanation.

Include:
- Introduction
- Definitions
- Important legal points
- Examples
- Safety precautions
- Advantages and disadvantages if applicable

Use headings and bullet points.
"""

else:

    max_tokens = 2200

    instruction = """
Give a highly detailed professional explanation.

Include:
- Introduction
- Full explanation
- Legal sections if relevant
- Real-life examples
- Step-by-step guidance
- Important precautions
- Advantages and disadvantages
- FAQs if useful
- Conclusion

Use:
- Headings
- Bullet points
- Numbered lists
- Tables where necessary
"""

# ======================================================
# SESSION STATE
# ======================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# ======================================================
# DISPLAY OLD SESSION CHATS
# ======================================================
for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ======================================================
# USER INPUT
# ======================================================
prompt = st.chat_input(
    "Ask your legal question..."
)

# ======================================================
# PROCESS USER INPUT
# ======================================================
if prompt:

    # Save User Message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    # ==================================================
    # AI RESPONSE
    # ==================================================
    with st.chat_message("assistant"):

        try:

            response = client.chat.completions.create(

                model="llama-3.1-8b-instant",

                messages=[
                    {
                        "role": "system",
                        "content": f"""
You are an AI legal and social awareness assistant.

RULES:
- Explain legal concepts in simple language.
- Educational purposes only.
- Do not provide harmful or illegal advice.
- Use examples whenever useful.
- Use headings and bullet points.
- Mention precautions when necessary.
- Keep answers clear and structured.

IMPORTANT FORMATTING RULES:

1. If user asks:
- Difference between
- Compare
- Comparison
- Vs
- Differentiate

THEN ALWAYS show answer in MARKDOWN TABLE format.

Example:

| Feature | Item 1 | Item 2 |
|---|---|---|
| Meaning | ... | ... |
| Purpose | ... | ... |

2. If user asks:
- Steps
- Procedure
- How to

THEN ALWAYS give numbered step-by-step explanation.

3. If user asks briefly:
Give concise answer only.

4. If user asks in detail:
Give detailed answer.

5. Never generate false legal claims.

{instruction}
"""
                    },

                    *st.session_state.messages
                ],

                temperature=0.5,
                max_tokens=max_tokens
            )

            answer = response.choices[0].message.content

        except Exception as e:

            answer = f"""
❌ Error Occurred:

{e}
"""

        st.markdown(answer)

    # ==================================================
    # SAVE ASSISTANT MESSAGE
    # ==================================================
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    # ==================================================
    # SAVE TO DATABASE
    # ==================================================
    cursor.execute("""
    INSERT INTO chats (
        question,
        answer,
        time
    )
    VALUES (?, ?, ?)
    """, (
        prompt,
        answer,
        str(datetime.now())
    ))

    conn.commit()

# ======================================================
# SIDEBAR CHAT HISTORY
# ======================================================
st.sidebar.title("📜 Chat History")

# ======================================================
# DELETE ALL CHATS
# ======================================================
if st.sidebar.button("🗑 Delete All Chats"):

    cursor.execute("DELETE FROM chats")

    conn.commit()

    st.session_state.messages = []

    st.sidebar.success("All chats deleted successfully!")

    st.rerun()

# ======================================================
# FETCH CHAT HISTORY
# ======================================================
cursor.execute("""
SELECT id, question, time
FROM chats
ORDER BY id DESC
""")

rows = cursor.fetchall()

# ======================================================
# SHOW HISTORY
# ======================================================
for row in rows[:20]:

    chat_id = row[0]
    question = row[1]
    chat_time = row[2]

    with st.sidebar.expander(f"❓ {question[:30]}..."):

        st.write(f"🕒 {chat_time}")

        # ==============================================
        # LOAD CHAT BUTTON
        # ==============================================
        if st.button(
            f"View Chat {chat_id}"
        ):

            cursor.execute("""
            SELECT question, answer
            FROM chats
            WHERE id=?
            """, (chat_id,))

            data = cursor.fetchone()

            if data:

                st.info(f"Q: {data[0]}")
                st.success(f"A: {data[1]}")

        # ==============================================
        # DELETE SINGLE CHAT
        # ==============================================
        if st.button(
            f"Delete Chat {chat_id}"
        ):

            cursor.execute("""
            DELETE FROM chats
            WHERE id=?
            """, (chat_id,))

            conn.commit()

            st.sidebar.success(
                f"Deleted chat {chat_id}"
            )

            st.rerun()

# ======================================================
# EXTRA SIDEBAR INFO
# ======================================================
st.sidebar.markdown("---")

st.sidebar.markdown("""
### 🤖 Features
✅ Legal Awareness  
✅ Cyber Crime Info  
✅ Women Rights  
✅ Consumer Rights  
✅ Traffic Rules  
✅ Detailed Explanations  
✅ Comparison Tables  
✅ Chat History  
✅ Delete Chats  
""")

# ======================================================
# FOOTER
# ======================================================
st.markdown("---")

st.caption("""
⚠️ Disclaimer:
This chatbot provides educational legal information only.
It is NOT a substitute for professional legal advice,
lawyers, or government authorities.
""")
