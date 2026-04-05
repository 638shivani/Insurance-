import streamlit as st
import google.generativeai as genai
import PyPDF2
import re

# ---------------- CONFIG ----------------
st.set_page_config(page_title="PolicyMind v2.0", layout="wide", page_icon="🧠")

# ---------------- API KEY ----------------
API_KEY = st.secrets.get("GEMINI_API_KEY")
if not API_KEY:
    st.error("❌ GEMINI_API_KEY missing in Secrets!")
    st.stop()

genai.configure(api_key=API_KEY)

# ---------------- ROBUST MODEL LOADER ----------------
@st.cache_resource
def load_working_model():
    """ 
    Tries to load Flash, then Pro. 
    If both fail, it scans your API key for ANY available model.
    """
    preferred_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    
    for model_id in preferred_models:
        try:
            m = genai.GenerativeModel(model_id)
            # Test if the model actually exists with a tiny call
            m.generate_content("ping", generation_config={"max_output_tokens": 1})
            return m
        except Exception:
            continue
            
    # Final Fallback: List all models and pick the first 'generateContent' one
    try:
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                return genai.GenerativeModel(m.name)
    except:
        return None

model = load_working_model()

# ---------------- PDF LOGIC ----------------
def extract_pdf_text(file):
    try:
        reader = PyPDF2.PdfReader(file)
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    except Exception as e:
        return ""

# ---------------- SESSION ----------------
if "history" not in st.session_state: st.session_state.history = []
if "latest" not in st.session_state: st.session_state.latest = None
if "pdf_text" not in st.session_state: st.session_state.pdf_text = ""

# ---------------- UI ----------------
st.title("🧠 PolicyMind v2.0")
st.caption("Auto-Detecting AI Insurance Engine")

if not model:
    st.error("❌ No compatible Gemini models found. Check your API Key permissions.")
    st.stop()

tabs = st.tabs(["📄 Query", "🧠 AI Response", "📜 History"])

with tabs[0]:
    uploaded = st.file_uploader("Upload Policy PDF", type="pdf")
    if uploaded:
        st.session_state.pdf_text = extract_pdf_text(uploaded)
        st.success("✅ Policy Loaded")

    query = st.text_input("Describe your claim:")

    if st.button("🚀 Run Analysis"):
        if not st.session_state.pdf_text or not query:
            st.error("Upload PDF and enter a query first!")
        else:
            with st.spinner("AI is evaluating..."):
                try:
                    prompt = f"Policy: {st.session_state.pdf_text[:12000]}\n\nClaim: {query}\n\nDecision: [Approved/Rejected]\nReason: [Short line]"
                    response = model.generate_content(prompt)
                    ans = response.text
                    
                    decision = "Approved" if "Approved" in ans else "Rejected"
                    reason = ans.split("Reason:")[-1].strip() if "Reason:" in ans else ans
                    
                    # Logic for metadata
                    proc = "Surgery" if "surgery" in query.lower() else "General"
                    age_match = re.search(r'(\d+)\s*month', query, re.I)
                    age = f"{age_match.group(1)} months" if age_match else "Unknown"

                    res = {
                        "query": query, "decision": decision, "reason": reason,
                        "confidence": "95%", "policy_age": age, "procedure": proc
                    }
                    st.session_state.latest = res
                    st.session_state.history.append(res)
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

with tabs[1]:
    if st.session_state.latest:
        r = st.session_state.latest
        color = "#2ecc71" if r["decision"] == "Approved" else "#e74c3c"
        
        st.markdown(f"""
        <div style="background:{color}; padding:20px; border-radius:10px; color:white;">
            <h2 style="color:white; margin:0;">{r['decision']}</h2>
            <p style="margin-top:10px;">{r['reason']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Status", r["decision"])
        col2.metric("Age", r["policy_age"])
        col3.metric("Procedure", r["procedure"])
    else:
        st.info("Results will appear here.")

with tabs[2]:
    for item in reversed(st.session_state.history):
        st.write(f"🔹 **{item['query']}** → {item['decision']}")
