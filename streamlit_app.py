import streamlit as st
from openai import OpenAI
import hashlib

# =================================
# LOGIN SYSTEM
# =================================
def check_password():
    if "auth" not in st.session_state:
        st.session_state.auth = False

    if st.session_state.auth:
        return True

    st.title("🔐 Login Required")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        # Check against Streamlit secrets
        if (
            username == st.secrets["auth"]["username"]
            and hashlib.sha256(password.encode()).hexdigest()
            == st.secrets["auth"]["password_hash"]
        ):
            st.session_state.auth = True
            return True
        else:
            st.error("Invalid credentials")

    return False


if not check_password():
    st.stop()

# =================================
# OPENAI CLIENT
# =============================
