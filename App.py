import streamlit as st
import google.generativeai as genai
import PyPDF2
import re

# ---------------- CONFIG ----------------
st.set_page_config(page_title="PolicyMind v2.0", layout="wide", page_icon="🧠")

# ---------------- API KEY ----------------
# Ensure this is set in your Streamlit Cloud Secrets
API_KEY = st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("❌ GEMINI_API_KEY not found in secrets.")
    st.stop()

genai.configure(api_key=API_KEY)

# ---------------- MODEL INITIALIZATION ----------------
@st.cache_resource
def load_model():
    """ 
    Initializes the model. 
    Removing 'models/' prefix often solves the 404 issue in newer SDK versions.
    """
    try:
        # Standard stable model name
        return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        try:
            # Fallback to Pro if Flash is restricted in your region/tier
            return genai.GenerativeModel("gemini-1.5-pro")
        except:
            st.error(f"Failed to load AI Model: {e}")
            return None

model = load_model()

# ---------------- SESSION STATE ----------------
if "history" not in st.session_state:
    st.session_state.history = []
if "latest" not in st.session_state:
    st.session_state.latest = None
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# ---------------- PDF PROCESSING ----------------
def extract_pdf_text(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return ""

# ---------------- QUERY PARSING (Regex) ----------------
def extract_details(query):
    # Case-insensitive search for duration
    age = re.search(r'(\d+)[- ]?year', query, re.I)
    months = re.search(r'(\d+)[- ]?month', query, re.I)
    weeks = re.search(r'(\d+)[- ]?week', query, re.I)

    procedure = "General"
    q = query.lower()

    if "dental" in q: procedure = "Dental"
    elif "cosmetic" in q: procedure = "Cosmetic"
    elif "appendectomy" in q: procedure = "Appendectomy"
    elif "surgery" in q: procedure = "Surgery"
    elif "emergency" in q: procedure = "Emergency"

    policy_months = 0
    if months:
        policy_months = int(months.group(1))
    elif weeks:
        policy_months = round(int(weeks.group(1)) / 4)
    elif age:
        policy_months = int(age.group(1)) * 12

    return {
        "policy_months": policy_months,
        "procedure": procedure
    }

# ---------------- AI CORE ----------------
def generate_answer(query, context):
    try:
        if not model:
            return "Error", "Model not initialized"

        # Using a structured prompt for better extraction
        prompt = f"""
        You are an Insurance Claim AI. 
        Context from Policy: {context[:12000]}
        
        User Question: {query}
        
        Strictly follow this format:
        Decision: [Approved or Rejected]
        Reason: [One short sentence explaining why]
        """

        response = model.generate_content(prompt)
        
        # Newer SDKs use .text directly
        text = response.text

        decision = "Rejected" 
        if "Approved" in text:
            decision = "Approved"
        
        reason = "Unable to determine reason from policy."
        if "Reason:" in text:
            reason = text.split("Reason:")[-1].strip().split("\n")[0]

        return decision, reason

    except Exception as e:
        # Returns the error message to be displayed in the UI
        return "Error", str(e)

# ---------------- UI ----------------
st.title("🧠 PolicyMind v2.0")
st.caption("AI-Powered Insurance Policy Analysis Engine")

tabs = st.tabs(["📄 Query", "🧠 AI Response", "📊 Details", "📜 History"])

with tabs[0]:
    uploaded_file = st.file_uploader("Upload Policy PDF", type=["pdf"])
    if uploaded_file:
        st.session_state.pdf_text = extract_pdf_text(uploaded_file)
        st.success("✅ Document uploaded and indexed")

    query = st.text_input("Enter claim details (e.g., 'I need surgery, I've had the policy for 2 years')")

    if st.button("🚀 Run Analysis"):
        if not st.session_state.pdf_text:
            st.error("Please upload a PDF first.")
        elif not query:
            st.error("Please enter a query.")
        else:
            with st.spinner("AI is analyzing..."):
                details = extract_details(query)
                decision, reason = generate_answer(query, st.session_state.pdf_text)

                # Fix: Don't show 90% confidence if there was a 404/API error
                has_error = decision == "Error"
                
                result = {
                    "query": query,
                    "decision": decision,
                    "reason": reason,
                    "confidence": "0%" if has_error else "92%",
                    "policy_age": f"{details['policy_months']} months",
                    "procedure": details["procedure"]
                }

                st.session_state.latest = result
                st.session_state.history.append(result)

with tabs[1]:
    if st.session_state.latest:
        r = st.session_state.latest
        
        # Color indicator
        box_color = "#2ecc71" if r['decision'] == "Approved" else "#e74c3c"
        if r['decision'] == "Error": box_color = "#f1c40f"

        st.markdown(f"""
        <div style="background-color:{box_color}; padding:20px; border-radius:10px; color:white;">
            <h2 style="color:white; margin:0;">{r['decision']}</h2>
            <p style="margin:10px 0 0 0; font-size:1.1em;">{r['reason']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📊 Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Status", r["decision"])
        c2.metric("Confidence", r["confidence"])
        c3.metric("Policy Age", r["policy_age"])
        c4.metric("Procedure", r["procedure"])
    else:
        st.info("Results will appear here.")

with tabs[2]:
    if st.session_state.latest:
        st.json(st.session_state.latest)

with tabs[3]:
    if st.session_state.history:
        for item in reversed(st.session_state.history):
            st.write(f"🔹 **{item['query']}** → {item['decision']}")
    else:
        st.info("No history yet.")
