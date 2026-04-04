
import streamlit as st
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from transformers import pipeline

st.set_page_config(page_title="Insurance Claim AI", layout="wide")

st.title("🧠 Insurance Claim AI Assistant")

# Load models
@st.cache_resource
def load_models():
    embed_model = SentenceTransformer('all-MiniLM-L6-v2')
    generator = pipeline("text2text-generation", model="google/flan-t5-small")
    return embed_model, generator

embed_model, generator = load_models()

# Upload PDF
uploaded_file = st.file_uploader("📄 Upload Insurance Document (PDF)", type="pdf")

text = ""

if uploaded_file:
    pdf = PdfReader(uploaded_file)
    for page in pdf.pages:
        if page.extract_text():
            text += page.extract_text()

    st.success("✅ Document uploaded successfully")

# Split text into chunks
def split_text(text, chunk_size=500):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# Create FAISS index
def create_vector_store(chunks):
    embeddings = embed_model.encode(chunks)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))
    return index, embeddings

# User input (like HackRx)
query = st.text_area("💬 Enter full case details (Example: 46M, knee surgery, 3-month policy):")

if query and text:

    # Improve query understanding
    query = query + " Consider waiting periods, exclusions, and conditions."

    chunks = split_text(text)
    index, embeddings = create_vector_store(chunks)

    # Retrieve relevant chunks
    query_embedding = embed_model.encode([query])
    D, I = index.search(np.array(query_embedding), k=3)

    context = " ".join([chunks[i] for i in I[0]])

    # Prompt (HackRx style)
    prompt = f"""
You are an insurance claim decision assistant.

Analyze the user query and policy document carefully.

Rules:
- Use ONLY the given context
- Be strict like real insurance company
- Consider waiting period, exclusions, conditions

Context:
{context}

User Case:
{query}

Return STRICTLY in this format:

Decision: (Approved / Rejected)
Amount: (Exact amount if available, else Not specified)
Justification: (Short clause-based explanation)
"""

    # Generate answer
    result = generator(prompt, max_length=200)
    output = result[0]['generated_text']

    st.subheader("📊 Claim Decision")

    try:
        decision = output.split("Decision:")[1].split("Amount:")[0].strip()
        amount = output.split("Amount:")[1].split("Justification:")[0].strip()
        justification = output.split("Justification:")[1].strip()

        if "Approved" in decision:
            st.success(f"✅ Decision: {decision}")
        else:
            st.error(f"❌ Decision: {decision}")

        st.info(f"💰 Amount: {amount}")
        st.write(f"📘 Justification: {justification}")

    except:
        st.write(output)