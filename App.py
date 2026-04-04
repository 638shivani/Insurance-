
import streamlit as st
from PyPDF2 import PdfReader
from transformers import pipeline

st.set_page_config(page_title="Insurance AI", layout="centered")

st.title("🧠 Insurance Claim AI Assistant")

# Load AI model
@st.cache_resource
def load_model():
    return pipeline("text-generation", model="distilgpt2")

generator = load_model()

# Upload PDF
uploaded_file = st.file_uploader("Upload Insurance Document (PDF)", type="pdf")

context = ""

if uploaded_file:
    reader = PdfReader(uploaded_file)
    for page in reader.pages:
        context += page.extract_text()
    st.success("Document uploaded successfully ✅")

# Question input
question = st.text_input("Ask your insurance question:")

if st.button("Analyze"):
    if not context:
        st.warning("Please upload a document first.")
    elif not question:
        st.warning("Please enter a question.")
    else:
        prompt = f"""
You are an Insurance Claim AI Assistant.

Read the policy and answer clearly.

Context:
{context[:2000]}

Question:
{question}

Give answer strictly in this format:

Decision: (Approved / Rejected)
Amount: (estimate or NA)
Justification: (clear explanation in simple English)
"""

        result = generator(prompt, max_length=300, num_return_sequences=1)

        output = result[0]["generated_text"]

        st.subheader("📊 AI Result")
        st.write(output)