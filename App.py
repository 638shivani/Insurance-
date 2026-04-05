import streamlit as st
import google.generativeai as genai
import os
import PyPDF2
import json

# ---------------- CONFIG ----------------
st.set_page_config(page_title="PolicyMind Pro", layout="wide", page_icon="🧠")

# ---------------- API SETUP ----------------
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("❌ GEMINI_API_KEY Missing")
    st.stop()

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")
model_name = "gemini-1.5-flash"

# ---------------- SIDEBAR ----------------
st.sidebar.title("Settings")
lang = st.sidebar.selectbox("🌐 Select Language", ["English", "Hindi", "Kannada"])
st.sidebar.success(f"⚡ Connected to: {model_name}")

# ---------------- STATE ----------------
if "history" not in st.session_state:
    st.session_state.history = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""
if "latest" not in st.session_state:
    st.session_state.latest = None

# ---------------- FUNCTIONS ----------------
def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    return "\n".join([p.extract_text() or "" for p in reader.pages])

def analyze_claim(query, context):
    prompt = f"""
    Policy: {context[:12000]}
    Scenario: {query}
    Respond in {lang}. Output STRICT JSON ONLY:
    {{
        "decision": "Approved/Rejected",
        "reason": "Clear explanation",
        "conf": "X%",
        "age": "Detected age",
        "proc": "Medical procedure"
    }}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except:
        return {
            "decision": "Error",
            "reason": "AI failed to respond",
            "conf": "0%",
            "age": "N/A",
            "proc": "N/A"
        }

# ---------------- UI ----------------
st.title("🧠 PolicyMind Pro")
st.caption("AI-powered insurance analyzer")

# Upload
uploaded_file = st.file_uploader("📄 Upload Policy PDF", type="pdf")

if uploaded_file:
    st.session_state.pdf_text = extract_text(uploaded_file)
    st.success("✅ Policy loaded")

# Query
query = st.text_input("💬 Ask your insurance question")

if st.button("🚀 Analyze"):
    if st.session_state.pdf_text and query:
        with st.spinner("Analyzing..."):
            result = analyze_claim(query, st.session_state.pdf_text)
            st.session_state.latest = result
            st.session_state.history.append(result)
    else:
        st.warning("Upload PDF and enter question")

# Result
if st.session_state.latest:
    r = st.session_state.latest

    color = "green" if r["decision"] == "Approved" else "red"

    st.markdown(f"## 🧾 Decision: <span style='color:{color}'>{r['decision']}</span>", unsafe_allow_html=True)
    st.write("📌 Reason:", r["reason"])
    st.write("📊 Confidence:", r["conf"])
    st.write("👤 Age:", r["age"])
    st.write("🏥 Procedure:", r["proc"])

# History
st.subheader("📊 History")

for item in reversed(st.session_state.history):
    with st.expander(f"{item['proc']} - {item['decision']}"):
        st.write(item)
