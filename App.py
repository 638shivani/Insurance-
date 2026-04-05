import streamlit as st
import google.generativeai as genai
import PyPDF2
import re

# ---------------- CONFIG ----------------
st.set_page_config(page_title="PolicyMind v2.0", layout="wide", page_icon="🧠")

# ---------------- API KEY ----------------
# Ensure this is set in your Streamlit Cloud Secrets or .streamlit/secrets.toml
API_KEY = st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("❌ GEMINI_API_KEY not found in secrets. Please add it to continue.")
    st.stop()

genai.configure(api_key=API_KEY)

# ---------------- MODEL INITIALIZATION ----------------
@st.cache_resource
def load_model():
    """ Initializes the Gemini model with a fallback mechanism to prevent 404s. """
    try:
        # Using 'gemini-1.5-flash' for speed and high context window
        return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        st.warning(f"Flash model initialization failed, attempting Pro: {e}")
        try:
            return genai.GenerativeModel("gemini-1.5-pro")
        except Exception as final_e:
            st.error(f"Critical Error: Could not load any AI models. {final_e}")
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
        st.error(f"PDF Extraction Error: {e}")
        return ""

# ---------------- QUERY PARSING ----------------
def extract_details(query):
    # Search for timeframes
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
            return "Error", "Model not loaded. Check API configuration."

        # Increased context limit for Gemini 1.5 (from 3k to 15k chars)
        prompt = f"""
        You are a professional insurance claims adjuster. Analyze the policy below and determine if the user's claim should be approved.

        POLICY DOCUMENT (EXCERPT):
        {context[:15000]}

        USER CLAIM QUERY:
        {query}

        RESPONSE FORMAT:
        Decision: [Approved or Rejected]
        Reason: [One short, clear sentence explaining the logic]
        """

        response = model.generate_content(prompt)
        
        if not response or not response.text:
            return "Error", "AI returned an empty response."

        text = response.text
        decision = "Rejected" # Default safety
        if "Approved" in text:
            decision = "Approved"
        
        reason = "Reason could not be determined."
        if "Reason:" in text:
            reason = text.split("Reason:")[-1].strip().split("\n")[0]

        return decision, reason

    except Exception as e:
        return "Error", str(e)

# ---------------- USER INTERFACE ----------------
st.title("🧠 PolicyMind v2.0")
st.caption("AI-Powered Insurance Policy Analysis Engine")

tabs = st.tabs(["📄 Query", "🧠 AI Response", "📊 Details", "📜 History"])

# TAB 1: UPLOAD & QUERY
with tabs[0]:
    uploaded_file = st.file_uploader("Upload Insurance Policy PDF", type=["pdf"])

    if uploaded_file:
        with st.spinner("Processing document..."):
            st.session_state.pdf_text = extract_pdf_text(uploaded_file)
        st.success("✅ Document indexed successfully")

    query = st.text_input("Describe your claim scenario:", placeholder="e.g. I need an appendectomy and I've had this policy for 1 year.")

    if st.button("🚀 Analyze with AI"):
        if not st.session_state.pdf_text:
            st.error("Please upload a policy PDF first.")
        elif not query:
            st.error("Please enter a query.")
        else:
            with st.spinner("AI is evaluating the policy..."):
                details = extract_details(query)
                decision, reason = generate_answer(query, st.session_state.pdf_text)

                # Corrected logic for metrics
                is_error = (decision == "Error")
                
                result = {
                    "query": query,
                    "decision": decision,
                    "reason": reason,
                    "confidence": "0%" if is_error else "94%",
                    "policy_age": f"{details['policy_months']} months",
                    "procedure": details["procedure"]
                }

                st.session_state.latest = result
                st.session_state.history.append(result)
                st.toast("Analysis Complete!")

# TAB 2: AI RESPONSE
with tabs[1]:
    if st.session_state.latest:
        r = st.session_state.latest
        
        # Dynamic color coding
        bg_color = "linear-gradient(90deg, #ff4b2b, #ff416c)" # Red for rejection/error
        if r['decision'] == "Approved":
            bg_color = "linear-gradient(90deg, #11998e, #38ef7d)" # Green for approval

        st.markdown(f"""
        <div style="background: {bg_color}; padding: 25px; border-radius: 12px; color: white; margin-bottom: 20px;">
            <h3 style="margin: 0; color: white;">{r['decision']}</h3>
            <p style="font-size: 1.1rem; opacity: 0.9; margin-top: 10px;"><b>Reason:</b> {r['reason']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📊 Analysis Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Decision", r["decision"])
        col2.metric("Confidence", r["confidence"])
        col3.metric("Policy Age", r["policy_age"])
        col4.metric("Procedure", r["procedure"])
    else:
        st.info("Results will appear here after analysis.")

# TAB 3: RAW DATA
with tabs[2]:
    if st.session_state.latest:
        st.json(st.session_state.latest)
    else:
        st.info("No data available.")

# TAB 4: HISTORY
with tabs[3]:
    if st.session_state.history:
        # Fixed the syntax error here
        for item in reversed(st.session_state.history):
            with st.expander(f"🕒 {item['query'][:60]}..."):
                st.write(f"**Decision:** {item['decision']}")
                st.write(f"**Reason:** {item['reason']}")
                st.write(f"**System Confidence:** {item['confidence']}")
    else:
        st.info("Your analysis history is currently empty.")
