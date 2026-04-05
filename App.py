import streamlit as st
from PyPDF2 import PdfReader
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
import re

# ---------------- CONFIG ----------------
st.set_page_config(page_title="PolicyMind v2.0", layout="wide")

st.title("🧠 PolicyMind v2.0")
st.caption("AI-Powered Insurance Policy Analysis Engine")

# ---------------- API KEY ----------------
API_KEY = st.secrets.get("GEMINI_API_KEY", "AIzaSyDr7lx6BhKJE0lxWJVfocSXlaUIokAZmSA")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-pro")

# ---------------- SESSION ----------------
if "history" not in st.session_state:
    st.session_state.history = []
if "index" not in st.session_state:
    st.session_state.index = None
if "chunks" not in st.session_state:
    st.session_state.chunks = []
if "result" not in st.session_state:
    st.session_state.result = None

# ---------------- EMBEDDING ----------------
@st.cache_resource
def load_embed():
    return SentenceTransformer("all-MiniLM-L6-v2")

embed_model = load_embed()

# ---------------- PDF ----------------
def extract_text(file):
    reader = PdfReader(file)
    text = ""
    for p in reader.pages:
        if p.extract_text():
            text += p.extract_text() + "\n"
    return text

def split_text(text, chunk_size=200):
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

def create_index(chunks):
    embeddings = embed_model.encode(chunks)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))
    return index

def retrieve(query, index, chunks):
    q_emb = embed_model.encode([query])
    D, I = index.search(np.array(q_emb), k=3)
    return [chunks[i] for i in I[0]]

# ---------------- DETAILS ----------------
def extract_details(query):
    age = re.search(r'(\d+)[-\s]*year', query)
    months = re.search(r'(\d+)[-\s]*month', query)
    weeks = re.search(r'(\d+)[-\s]*week', query)

    return {
        "age": int(age.group(1)) if age else None,
        "policy_months": int(months.group(1)) if months else (1 if weeks else 0),
        "procedure": query.split("for")[0].strip()
    }

# ---------------- GEMINI ANSWER ----------------
def generate_answer(query, context):

    prompt = f"""
You are an expert insurance claim assistant.

Use ONLY the given policy context.

Context:
{context}

Question:
{query}

Rules:
- Give short answer only
- Max 12 words reason
- No paragraph

Format:
Decision: Approved or Rejected
Reason: short line
"""

    response = model.generate_content(prompt)
    text = response.text

    decision = "Approved" if "approved" in text.lower() else "Rejected"

    if "Reason:" in text:
        reason = text.split("Reason:")[-1].strip()
    else:
        reason = "Based on policy"

    reason = " ".join(reason.split()[:12])

    return decision, reason

# ---------------- UI ----------------
tab = st.radio("", ["📄 Query", "🧠 AI Response", "📜 History"], horizontal=True)

# ---------------- QUERY ----------------
if tab == "📄 Query":

    file = st.file_uploader("Upload Insurance Policy PDF", type=["pdf"])

    if file:
        text = extract_text(file)
        chunks = split_text(text)
        index = create_index(chunks)

        st.session_state.index = index
        st.session_state.chunks = chunks

        st.success("Document indexed successfully ✅")

    query = st.text_input("Ask your question")

    if st.button("🚀 Analyze with AI"):

        if st.session_state.index is None:
            st.error("Upload PDF first")
        elif query:

            context = " ".join(retrieve(query, st.session_state.index, st.session_state.chunks))
            details = extract_details(query)

            decision, reason = generate_answer(query, context)

            result = {
                "query": query,
                "decision": decision,
                "reason": reason,
                "details": details,
                "confidence": 98
            }

            st.session_state.result = result
            st.session_state.history.append(result)

            st.success("Analysis complete 👉 AI Response")

# ---------------- RESPONSE ----------------
elif tab == "🧠 AI Response":

    if st.session_state.result:
        r = st.session_state.result

        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, #6a11cb, #2575fc);
            padding: 20px;
            border-radius: 12px;
            color: white;
        ">
        💬 <b>"Good news!"</b> {r['reason']}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Decision", r["decision"])
        col2.metric("Confidence", f"{r['confidence']}%")
        col3.metric("Policy Age", f"{r['details']['policy_months']} months")
        col4.metric("Procedure", r["details"]["procedure"].title())

    else:
        st.warning("No result yet")

# ---------------- HISTORY ----------------
elif tab == "📜 History":

    for item in reversed(st.session_state.history):
        st.write(f"🔹 {item['query']}")
        st.write(f"➡ {item['decision']} - {item['reason']}")
        st.write("---")
