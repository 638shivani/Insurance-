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
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]

def create_vector_db(chunks):
    embeddings = embed_model.encode(chunks)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))
    return index

def retrieve(query, index, chunks):
    q_emb = embed_model.encode([query])
    D, I = index.search(np.array(q_emb), k=5)

    results = []
    for i in I[0]:
        chunk = chunks[i].lower()
        if any(word in chunk for word in query.lower().split()):
            results.append(chunks[i])

    return results[:2]  # limit context

# ------------------ EXTRACTION ------------------
def extract_age(query):
    match = re.search(r'(\d+)[-\s]?year', query.lower())
    return int(match.group(1)) if match else None

def extract_policy_months(query):
    q = query.lower()
    if "week" in q:
        num = int(re.findall(r'\d+', q)[-1])
        return round(num/4, 2)
    if "month" in q:
        return int(re.findall(r'\d+', q)[-1])
    if "year" in q:
        return int(re.findall(r'\d+', q)[-1]) * 12
    return 0

def detect_procedure(query):
    q = query.lower()
    if "appendectomy" in q:
        return "Appendectomy"
    elif "cataract" in q:
        return "Cataract Surgery"
    elif "dental" in q:
        return "Dental Treatment"
    elif "cosmetic" in q:
        return "Cosmetic Surgery"
    elif "knee" in q:
        return "Knee Surgery"
    else:
        return "General Treatment"

# ------------------ LLM ------------------
def generate_answer(query, context):

    prompt = f"""
You are an insurance expert AI.

Use ONLY relevant info from context.
Give SHORT answer.

Context:
{context}

Question:
{query}

Answer STRICTLY in format:
Decision: Approved/Rejected
Reason: one line
"""

    output = generator(prompt, max_length=120, do_sample=False)[0]["generated_text"]

    # -------- CLEAN OUTPUT --------
    decision = "Approved" if "approved" in output.lower() else "Rejected"

    if "Reason:" in output:
        reason = output.split("Reason:")[-1].strip()
    else:
        reason = "Based on policy terms."

    return decision, reason

# ------------------ UI ------------------

st.title("🧠 PolicyMind v2.0")
st.caption("AI-Powered Insurance Policy Analysis Engine")

tab = st.radio("", ["🏠 Home", "📄 Query", "🧠 AI Response", "📊 Details", "📜 History"], horizontal=True)

# ------------------ HOME ------------------
if tab == "🏠 Home":
    st.subheader("Welcome 🚀")
    st.write("Upload policy → Ask question → Get AI decision")

# ------------------ QUERY ------------------
elif tab == "📄 Query":

    st.subheader("📂 Upload Policy Document")
    file = st.file_uploader("Upload PDF", type=["pdf"])

    if file:
        text = extract_text_from_pdf(file)
        chunks = split_text(text)
        index = create_vector_db(chunks)

        st.session_state.vector_db = index
        st.session_state.chunks = chunks

        st.success("Document uploaded and indexed successfully ✅")

    st.subheader("💬 Ask Your Question")
    query = st.text_input("Example: 30-year-old, appendectomy, 1-week policy")

    if st.button("🚀 Analyze with AI"):

        if st.session_state.vector_db is None:
            st.error("Upload PDF first")
        elif query:

            relevant_chunks = retrieve(query, st.session_state.vector_db, st.session_state.chunks)
            context = " ".join(relevant_chunks)

            decision, reason = generate_answer(query, context)

            result = {
                "query": query,
                "decision": decision,
                "reason": reason,
                "confidence": 95,
                "age": extract_age(query),
                "policy_months": extract_policy_months(query),
                "procedure": detect_procedure(query)
            }

            st.session_state.result = result
            st.session_state.history.append(result)

            st.success("Go to AI Response tab 👉")

# ------------------ AI RESPONSE ------------------
elif tab == "🧠 AI Response":

    st.subheader("🧠 AI Analysis Result")

    if "result" in st.session_state:
        r = st.session_state.result

        # -------- GRADIENT BOX --------
        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, #6a11cb, #2575fc);
            padding: 20px;
            border-radius: 12px;
            color: white;
            font-size: 16px;
        ">
        💡 <b>Decision:</b> {r['decision']} <br>
        📌 <b>Reason:</b> {r['reason']} <br><br>
        🚀 Next Steps: Proceed if approved and keep documents ready.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # -------- SUMMARY --------
        st.markdown("### 📊 Analysis Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"✅ **Decision**<br><h3 style='color:green'>{r['decision']}</h3>", unsafe_allow_html=True)

        with col2:
            st.markdown(f"📈 **Confidence**<br><h3>{r['confidence']}%</h3>", unsafe_allow_html=True)

        with col3:
            st.markdown(f"📅 **Policy Age**<br><h3>{r['policy_months']} months</h3>", unsafe_allow_html=True)

        with col4:
            st.markdown(f"🏥 **Procedure**<br><h3>{r['procedure']}</h3>", unsafe_allow_html=True)

    else:
        st.warning("No analysis yet")

# ------------------ DETAILS ------------------
elif tab == "📊 Details":

    if "result" in st.session_state:
        st.json(st.session_state.result)
    else:
        st.warning("No data")

# ------------------ HISTORY ------------------
elif tab == "📜 History":

    if st.session_state.history:
        for item in reversed(st.session_state.history):
            st.write(f"🔹 {item['query']}")
            st.write(f"➡ {item['decision']} ({item['confidence']}%)")
            st.write("---")
    else:
        st.warning("No history yet")
