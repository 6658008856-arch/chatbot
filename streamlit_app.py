import streamlit as st
from openai import OpenAI
import hashlib
import tempfile
import faiss
import numpy as np
from pypdf import PdfReader

# =================================
# LOGIN PROTECTION
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
        if (
            username == st.secrets["auth"]["username"]
            and hashlib.sha256(password.encode()).hexdigest()
            == st.secrets["auth"]["password_hash"]
        ):
            st.session_state.auth = True
            return True
        st.error("Invalid credentials")

    return False


if not check_password():
    st.stop()

# =================================
# OPENAI CLIENT
# =================================
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# =================================
# TEXT SPLITTING (NO LANGCHAIN)
# =================================
def split_text(text, chunk_size=1000, overlap=200):
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

# =================================
# EMBEDDING WITHOUT LANGCHAIN
# =================================
def embed_texts(text_list):
    result = client.embeddings.create(
        model="text-embedding-3-small",
        input=text_list
    )
    return np.array([d.embedding for d in result.data]).astype("float32")

# =================================
# PDF READING
# =================================
def read_pdf(path):
    reader = PdfReader(path)
    return "\n".join([page.extract_text() or "" for page in reader.pages])

# =================================
# VECTOR STORE (FAISS)
# =================================
if "faiss_index" not in st.session_state:
    st.session_state.faiss_index = None
    st.session_state.chunks = []

st.title("💬 Chatbot with Local Knowledge (No LangChain)")

uploaded_files = st.file_uploader(
    "Upload PDFs or TXT files for local knowledge",
    accept_multiple_files=True,
    type=["pdf", "txt", "md"]
)

if uploaded_files:
    all_chunks = []

    for uploaded in uploaded_files:
        temp_path = tempfile.mktemp()

        with open(temp_path, "wb") as f:
            f.write(uploaded.read())

        if uploaded.name.endswith(".pdf"):
            text = read_pdf(temp_path)
        else:
            text = open(temp_path, "r", errors="ignore").read()

        chunks = split_text(text)
        all_chunks.extend(chunks)

    embeds = embed_texts(all_chunks)

    dim = embeds.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeds)

    st.session_state.faiss_index = index
    st.session_state.chunks = all_chunks

    st.success(f"Indexed {len(all_chunks)} knowledge chunks!")

# ====
