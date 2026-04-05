import streamlit as st
import PyPDF2
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import pipeline
import re

# ------------------ CONFIG ------------------
st.set_page_config(page_title="PolicyMind v2.0", layout="wide")

# ------------------ SESSION ------------------
if "history" not in st.session_state:
    st.session_state.history = []
if "vector_db" not in st.session_state:
    st.session_state.vector_db = None
if "chunks" not in st.session_state:
    st.session_state.chunks = []

# ------------------ LOAD MODELS ------------------
@st.cache_resource
def load_models():
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    generator = pipeline("text-generation", model="distilgpt2")
    return embed_model, generator

embed_model, generator = load_models()

# ------------------ PDF PROCESS ------------------
def extract_text_from_pdf(file):
    pdf = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf.pages:
        text += page.extract_text() + "\n"
    return text

def split_text(text, chunk_size=300):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i+chunk_size]))
    return chunks

def create_vector_db(chunks):
    embeddings = embed_model.encode(chunks)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))
    return index, embeddings

def retrieve(query, index, chunks):
    q_emb = embed_model.encode([query])
    D, I = index.search(np.array(q_emb), k=3)
    return [chunks[i] for i in I[0]]

# ------------------ INFO EXTRACTION ------------------
def extract_age(query):
    match = re.search(r'(\d+)[-\s]?year', query.lower())
    return int(match.group(1)) if match else None

def extract_policy_months(query):
    if "week" in query:
        num = int(re.findall(r'\d+', query)[-1])
        return round(num/4,2)
    if "month" in query:
        return int(re.findall(r'\d+', query)[-1])
    if "year" in query:
        return int(re.findall(r'\d+', query)[-1]) * 12
    return None

# ------------------ LLM RESPONSE ------------------
def generate_answer(query, context):
    prompt = f"""
You are an expert insurance AI.

Use ONLY the context below to answer.

Context:
{context}

Question:
{query}

Give output in this format:
Decision:
Reason:
"""

    output = generator(prompt, max_length=300, do_sample=True)[0]["generated_text"]
    return output

# ------------------ UI ------------------

st.title("🧠 PolicyMind v2.0")
tab = st.radio("", ["🏠 Home", "📄 Query", "🧠 AI Response", "📊 Details", "📜 History"], horizontal=True)

# ------------------ HOME ------------------
if tab == "🏠 Home":
    st.subheader("Welcome 🚀")
    st.write("Upload policy → Ask question → Get AI decision")

# ------------------ QUERY ------------------
elif tab == "📄 Query":

    st.subheader("Upload Policy Document")
    file = st.file_uploader("Upload PDF", type=["pdf"])

    if file:
        text = extract_text_from_pdf(file)
        chunks = split_text(text)

        index, embeddings = create_vector_db(chunks)

        st.session_state.vector_db = index
        st.session_state.chunks = chunks

        st.success("Document indexed successfully ✅")

    query = st.text_input("Ask your question")

    if st.button("Analyze"):

        if st.session_state.vector_db is None:
            st.error("Upload PDF first")
        elif query:

            relevant_chunks = retrieve(query, st.session_state.vector_db, st.session_state.chunks)

            context = " ".join(relevant_chunks)

            answer = generate_answer(query, context)

            result = {
                "query": query,
                "answer": answer,
                "context": context,
                "age": extract_age(query),
                "policy_months": extract_policy_months(query)
            }

            st.session_state.result = result
            st.session_state.history.append(result)

            st.success("Go to AI Response tab 👉")

# ------------------ AI RESPONSE ------------------
elif tab == "🧠 AI Response":

    if "result" in st.session_state:
        r = st.session_state.result

        st.subheader("AI Result")

        st.write(r["answer"])

    else:
        st.warning("No result yet")

# ------------------ DETAILS ------------------
elif tab == "📊 Details":

    if "result" in st.session_state:
        st.json(st.session_state.result)

# ------------------ HISTORY ------------------
elif tab == "📜 History":

    for item in reversed(st.session_state.history):
        st.write(item["query"])
        st.write(item["answer"])
        st.write("---")
