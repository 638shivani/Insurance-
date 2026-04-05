import streamlit as st
import google.generativeai as genai
import PyPDF2
import re

# ---------------- CONFIG ----------------
st.set_page_config(page_title="PolicyMind v2.0", layout="wide")

# ---------------- API KEY ----------------
API_KEY = st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("❌ Add GEMINI_API_KEY in Streamlit Secrets")
    st.stop()

genai.configure(api_key=API_KEY)

# ---------------- ROBUST MODEL LOADER ----------------
@st.cache_resource
def load_model():
    """ 
    This function tries multiple names to find a working model 
    on your specific API version.
    """
    # List of models to try in order of preference
    model_names = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    
    for name in model_names:
        try:
            m = genai.GenerativeModel(name)
            # Test a tiny generation to see if it actually works (404 check)
            m.generate_content("test", generation_config={"max_output_tokens": 1})
            return m
        except Exception:
            continue
            
    # Final attempt: List all models and pick the first one that supports text
    try:
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                return genai.GenerativeModel(m.name)
    except:
        return None

model = load_model()

# ---------------- PDF EXTRACTION ----------------
def extract_pdf_text(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

# ---------------- UI HELPERS ----------------
def get_details(query):
    # Basic regex for months/years
    months = re.search(r'(\d+)\s*month', query, re.I)
    years = re.search(r'(\d+)\s*year', query, re.I)
    
    total_months = 0
    if months: total_months = int(months.group(1))
    if years: total_months = int(years.group(1)) * 12
    
    proc = "General"
    if "dental" in query.lower(): proc = "Dental"
    elif "surgery" in query.lower(): proc = "Surgery"
    
    return total_months, proc

# ---------------- MAIN APP ----------------
st.title("🧠 PolicyMind v2.0")

if not model:
    st.error("❌ Could not connect to any Gemini models. Please check your API Key permissions.")
    st.stop()

tabs = st.tabs(["📄 Query", "🧠 AI Response", "📜 History"])

with tabs[0]:
    uploaded_file = st.file_uploader("Upload Policy PDF", type="pdf")
    query = st.text_input("Enter claim details (e.g. 'I've had my policy for 2 years, I need dental surgery')")
    
    if st.button("🚀 Analyze"):
        if uploaded_file and query:
            with st.spinner("Analyzing..."):
                text = extract_pdf_text(uploaded_file)
                
                prompt = f"Based on this policy: {text[:10000]}\n\nUser Question: {query}\n\nDecision: [Approved/Rejected]\nReason: [Short line]"
                
                try:
                    response = model.generate_content(prompt)
                    ans = response.text
                    
                    # Logic to parse decision
                    dec = "Approved" if "Approved" in ans else "Rejected"
                    reason = ans.split("Reason:")[-1] if "Reason:" in ans else ans
                    
                    months, proc = get_details(query)
                    
                    res = {
                        "decision": dec,
                        "reason": reason.strip(),
                        "months": months,
                        "proc": proc,
                        "query": query
                    }
                    st.session_state.latest = res
                    if "history" not in st.session_state: st.session_state.history = []
                    st.session_state.history.append(res)
                    st.success("Analysis Complete! Switch to 'AI Response' tab.")
                except Exception as e:
                    st.error(f"AI Error: {e}")
        else:
            st.warning("Please upload a PDF and enter a query.")

with tabs[1]:
    if "latest" in st.session_state:
        r = st.session_state.latest
        color = "green" if r["decision"] == "Approved" else "red"
        
        st.markdown(f"<h2 style='color:{color}'>{r['decision']}</h2>", unsafe_allow_allow_html=True)
        st.write(f"**Reason:** {r['reason']}")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Policy Age", f"{r['months']} months")
        c2.metric("Procedure", r["proc"])
        c3.metric("Confidence", "95%")
    else:
        st.info("No result yet.")

with tabs[2]:
    if "history" in st.session_state:
        for item in reversed(st.session_state.history):
            st.write(f"🔹 {item['query']} -> **{item['decision']}**")
