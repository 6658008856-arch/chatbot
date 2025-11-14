import streamlit as st
from openai import OpenAI
import hashlib

# =================================
# LOGIN SYSTEM
# =================================
if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Login Required")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if (
            username == st.secrets["auth"]["username"]
            and hashlib.sha256(password.encode()).hexdigest()
            == st.secrets["auth"]["password_hash"]
        ):
            st.session_state.auth = True
            st.success("Login successful! Scroll down to start chatting.")
        else:
            st.error("Invalid credentials")

# Only show chat interface if authenticated
if st.session_state.auth:

    # =================================
    # OPENAI CLIENT
    # =================================
    client = OpenAI(api_key=st.secrets["openai"]["api_key"])

    # =================================
    # CHATBOT UI
    # =================================
    st.title("💬 Simple Chatbot (GPT-4.1)")
    st.write("You are logged in. Ask anything!")

    # Chat memory
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Show chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User input
    user_input = st.chat_input("Type your message…")

    if user_input:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        # Query OpenAI
        stream = client.chat.completions.create(
            model="gpt-4.1",
            messages=st.session_state.messages,
            stream=True
        )

        # Stream response
        with st.chat_message("assistant"):
            response = st.write_stream(stream)

        # Save assistant message
        st.session_state.messages.append({"role": "assistant", "content": response})
