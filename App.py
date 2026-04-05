import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader

# -------------------------------
# 🔑 CONFIG
# -------------------------------
st.set_page_config(page_title="PolicyMind AI", layout="wide")

# Load API key safely
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

if not API_KEY:
    st.error("❌ API Key missing! Add it in secrets.toml")
    st.stop()

genai.configure(api_key=API_KEY)

# Initialize model
model = genai.GenerativeModel("gemini-1.5-flash")

# -------------------------------
# 📄 PDF TEXT EXTRACTION
# -------------------------------
def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    return text


# -------------------------------
# 🤖 AI ANSWER FUNCTION
# -------------------------------
def generate_answer(query, context):
    try:
        prompt = f"""
You are an Insurance Policy Assistant.

STRICT RULES:
- Answer ONLY from given context
- If answer not found → say "Not mentioned in policy"
- Be precise and factual
- Do NOT hallucinate

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:
"""

        response = model.generate_content(prompt)

        if not response or not response.text:
            return "⚠️ No response from model"

        return response.text.strip()

    except Exception as e:
        return f"❌ Error: {str(e)}"


# -------------------------------
# 🎨 UI
# -------------------------------
st.title("🧠 PolicyMind AI - Insurance Assistant")

uploaded_file = st.file_uploader("📄 Upload Insurance Policy PDF", type=["pdf"])

if uploaded_file:
    with st.spinner("📄 Processing document..."):
        context = extract_text_from_pdf(uploaded_file)
        st.session_state["context"] = context

    st.success("✅ Document indexed successfully")

# -------------------------------
# ❓ ASK QUESTION
# -------------------------------
query = st.text_input("💬 Ask your question")

if st.button("🚀 Analyze with AI"):

    if "context" not in st.session_state:
        st.warning("⚠️ Please upload a PDF first")
    elif not query:
        st.warning("⚠️ Please enter a question")
    else:
        with st.spinner("🤖 Thinking..."):
            answer = generate_answer(query, st.session_state["context"])

        st.subheader("📌 Answer")
        st.write(answer)

# -------------------------------
# 🐞 DEBUG MODE (Optional)
# -------------------------------
with st.expander("🛠 Debug Info"):
    st.write("API Key Loaded:", bool(API_KEY))
    st.write("Context Loaded:", "context" in st.session_state)
