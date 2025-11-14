import streamlit as st
from openai import OpenAI
import hashlib
import tempfile
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader, TextLoader

# ---------------------------
# AUTHENTICATION
# ---------------------------
def check_password():
    """Simple username/password login based on Streamlit session state."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
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
            st.session_state.authenticated = True
            return True
        else:
            st.error("Invalid username or password.")

    return False

if not check_password():
    st.stop()

# ---------------------------
# INITIALIZE CLIENT
# ---------------------------
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# ---------------------------
# APP LAYOUT
# ---------------------------
st.title("💬 Chatbot with Local Knowledge (RAG)")

st.write(
    "This chatbot uses GPT-4.1 + locally uploaded knowledge files. "
    "Upload PDFs or text files, and the bot will use them to answer your questions."
)

# ---------------------------
# FILE UPLOAD + VECTOR STORE
# ---------------------------
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

uploaded_files = st.file_uploader(
    "Upload knowledge files (PDF or text)", type=["pdf", "txt", "md"], accept_multiple_files=True
)

if uploaded_files:
    docs = []

    for uploaded in uploaded_files:
        temp_path = tempfile.mktemp()
        with open(temp_path, "wb") as f:
            f.write(uploaded.read())

        if uploaded.name.endswith(".pdf"):
            loader = PyPDFLoader(temp_path)
        else:
            loader = TextLoader(temp_path)

        docs.extend(loader.load())

    # Chunking
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    # Embeddings
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large", api_key=st.secrets["openai"]["api_key"])

    # Build vector store
    st.session_state.vectorstore = FAISS.from_documents(chunks, embeddings)
    st.success(f"Indexed {len(chunks)} knowledge chunks!")

# ---------------------------
# CHAT STATE
# ---------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------
# CHAT INPUT
# ---------------------------
query = st.chat_input("Ask something…")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    # Retrieve local context
    retrieved_text = ""
    if st.session_state.vectorstore:
        results = st.session_state.vectorstore.similarity_search(query, k=4)
        retrieved_text = "\n\n".join([d.page_content for d in results])

    system_instruction = (
        "You are an AI assistant. Use the provided local knowledge if relevant. "
        "If the knowledge does not help, fall back to general reasoning.\n\n"
        f"Local knowledge:\n{retrieved_text}"
    )

    # Generate response
    stream = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": system_instruction},
            *st.session_state.messages,
        ],
        stream=True,
    )

    # Stream the reply
    with st.chat_message("assistant"):
        response_text = st.write_stream(stream)

    # Save history
    st.session_state.messages.append({"role": "assistant", "content": response_text})
