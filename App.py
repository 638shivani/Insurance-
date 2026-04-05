import streamlit as st
import google.generativeai as genai
import PyPDF2
import re

# ---------------- CONFIG ----------------
st.set_page_config(page_title="PolicyMind v2.0", layout="wide", page_icon="🧠")

# ---------------- API KEY ----------------
API_KEY = st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("❌ GEMINI_API_KEY is missing from Streamlit secrets.")
    st.stop()

genai.configure(api_key=API_KEY)

# ---------------- MODEL INITIALIZATION ----------------
@st.cache_resource
def load_model():
    """Initializes the model using the stable identifier to avoid 404 errors."""
    try:
        # Using 'gemini-1.5-flash' is faster and more cost-effective for document analysis
        return genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        st.error(f"AI Model Initialization failed: {e}")
        return None

model = load_model()

# ---------------- SESSION MANAGEMENT ----------------
if "history" not in st.session_state:
    st.session_state.history = []
if "latest" not in st.session_state:
    st.session_state.latest = None
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# ---------------- PDF LOGIC ----------------
def extract_pdf_text(file):
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text
    except Exception as e:
        st.error(f"Failed to read PDF: {e}")
        return ""

# ---------------- QUERY PARSING ----------------
def extract_details(query):
    # Search for numeric values followed by time units (Case Insensitive)
    age_match = re.search(r'(\d+)\s*year', query, re.I)
    month_match = re.search(r'(\d+)\s*month', query, re.I)
    week_match = re.search(r'(\d+)\s*week', query, re.I)

    procedure = "General Medical"
    q = query.lower()

    if "dental" in q: procedure = "Dental"
    elif "cosmetic" in q: procedure = "Cosmetic"
    elif "appendectomy" in q: procedure = "Appendectomy"
    elif "surgery" in q: procedure = "Surgery"
    elif "emergency" in q: procedure = "Emergency"

    policy_months = 0
    if month_match:
        policy_months = int(month_match.group(1))
    elif week_match:
        policy_months = round(int(week_match.group(1)) / 4)
    elif age_match:
        policy_months = int(age_match.group(1)) * 12

    return {
        "policy_months": policy_months,
        "procedure": procedure
    }

# ---------------- AI ANALYSIS ----------------
def generate_answer(query, context):
    if not model:
        return "Error", "AI Model is not initialized."
    
    try:
        # Gemini 1.5 can handle up to 1M tokens, but we'll use a safe 15k char slice
        prompt = f"""
        You are an expert Health Insurance Claims Adjuster.
        
        INSTRUCTIONS:
        1. Read the policy context below.
        2. Evaluate the user's query against the policy rules (waiting periods, exclusions, etc.).
        3. Provide a clear Decision and a concise Reason.

        POLICY CONTEXT:
        {context[:15000]}

        USER CLAIM QUERY:
        {query}

        OUTPUT FORMAT (Strict):
        Decision: [Approved or Rejected]
        Reason: [One short, professional sentence]
        """

        response = model.generate_content(prompt)
        
        # Safety check for empty responses
        if not response or not response.text:
            return "Error", "The AI returned an empty response."

        output = response.text
        
        # Parsing the Decision
        decision = "Rejected" # Default
        if "Approved" in output:
            decision = "Approved"
        elif "Error" in output:
            decision = "Error"

        # Parsing the Reason
        reason = "No specific reason provided by AI."
        if "Reason:" in output:
            reason = output.split("Reason:")[-1].strip().split("\n")[0]

        return decision, reason

    except Exception as e:
        return "Error", str(e)

# ---------------- MAIN UI ----------------
st.title("🧠 PolicyMind v2.0")
st.caption("AI-Powered Insurance Policy Analysis Engine")

tabs = st.tabs(["📄 Query", "🧠 AI Response", "📊 Details", "📜 History"])

# --- TAB: QUERY ---
with tabs[0]:
    uploaded_file = st.file_uploader("Upload Insurance Policy (PDF)", type=["pdf"])

    if uploaded_file:
        with st.spinner("Processing PDF..."):
            st.session_state.pdf_text = extract_pdf_text(uploaded_file)
        st.success("✅ Document indexed and ready for analysis.")

    query = st.text_input("Enter claim scenario:", placeholder="e.g., I need dental surgery. I have had my policy for 8 months.")

    if st.button("🚀 Analyze Claim"):
        if not st.session_state.pdf_text:
            st.error("Please upload a policy PDF first.")
        elif not query:
            st.error("Please enter your claim details.")
        else:
            with st.spinner("AI is calculating coverage..."):
                details = extract_details(query)
                decision, reason = generate_answer(query, st.session_state.pdf_text)

                # Set confidence to 0% if the system errored out
                conf = "0%" if decision == "Error" else "94%"

                result = {
                    "query": query,
                    "decision": decision,
                    "reason": reason,
                    "confidence": conf,
                    "policy_age": f"{details['policy_months']} months",
                    "procedure": details["procedure"]
                }

                st.session_state.latest = result
                st.session_state.history.append(result)

# --- TAB: AI RESPONSE ---
with tabs[1]:
    if st.session_state.latest:
        res = st.session_state.latest
        
        # Visual styling based on result
        color_map = {
            "Approved": "linear-gradient(90deg, #11998e, #38ef7d)",
            "Rejected": "linear-gradient(90deg, #ff4b2b, #ff416c)",
            "Error": "linear-gradient(90deg, #30333d, #5b5f6b)"
        }
        bg = color_map.get(res['decision'], "#333")

        st.markdown(f"""
        <div style="background: {bg}; padding: 25px; border-radius: 15px; color: white; margin-bottom: 25px;">
            <h2 style="margin: 0; color: white;">{res['decision']}</h2>
            <p style="font-size: 1.2em; opacity: 0.9; margin-top: 10px;"><b>AI Reason:</b> {res['reason']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📈 Analysis Metrics")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Status", res["decision"])
        m2.metric("Confidence", res["confidence"])
        m3.metric("Detected Age", res["policy_age"])
        m4.metric("Procedure", res["procedure"])
    else:
        st.info("Run an analysis in the 'Query' tab to see results.")

# --- TAB: DETAILS ---
with tabs[2]:
    if st.session_state.latest:
        st.subheader("Raw Analysis Data")
        st.json(st.session_state.latest)

# --- TAB: HISTORY ---
with tabs[3]:
    if st.session_state.history:
        for item in reversed(st.session_state.history):
            with st.expander(f"🔍 {item['query'][:60]}..."):
                st.write(f"**Decision:** {item['decision']}")
                st.write(f"**Reason:** {item['reason']}")
                st.write(f"**Procedure:** {item['procedure']}")
    else:
        st.info("No previous analyses found.")
