import streamlit as st
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from transformers import pipeline

st.title("Insurance Claim AI Assistant 🧠")

# Load models
@st.cache_resource
def load_models():
    embed_model = SentenceTransformer('all-MiniLM-L6-v2')
    generator = pipeline("text-generation", model="google/flan-t5-base")
    return embed_model, generator

embed_model, generator = load_models()

# Upload PDF
uploaded_file = st.file_uploader("Upload Insurance Document (PDF)", type="pdf")

text = ""

if uploaded_file:
    pdf = PdfReader(uploaded_file)
    for page in pdf.pages:
        text += page.extract_text()

    st.success("Document uploaded successfully ✅")

# Split text into chunks
def split_text(text, chunk_size=500):
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

# Create embeddings
def create_vector_store(chunks):
    embeddings = embed_model.encode(chunks)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))
    return index, embeddings

# Query
query = st.text_input("Ask your insurance question:")

if query and text:
    chunks = split_text(text)
    index, embeddings = create_vector_store(chunks)

    # Search relevant chunks
    query_embedding = embed_model.encode([query])
    D, I = index.search(np.array(query_embedding), k=3)

    context = " ".join([chunks[i] for i in I[0]])

    # Generate answer
    prompt = f"""
    Based on the following insurance document, answer clearly:

    Context:
    {context}

    Question:
    {query}

    Give answer in this format:
    Decision:
    Amount:
    Justification:
    """

    result = generator(prompt, max_length=300, do_sample=True)

    st.subheader("📊 AI Result")
    st.write(result[0]['generated_text'])
