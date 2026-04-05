import streamlit as st
import google.generativeai as genai
import PyPDF2
import re

# ---------------------------
# CONFIG
# ---------------------------
st.set_page_config(page_title="PolicyMind v2.0", layout="wide")

API_KEY = st.secrets.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ---------------------------
# SESSION STATE
# ---------------------------
if "history" not in st.session_state:
    st.session_state.history = []

if "last_result" not in st.session_state:
    st.session_state.last_result = None

# ---------------------------
# PDF TEXT EXTRACTION
# ---------------------------
def extract_text(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text[:10000]

# ---------------------------
# QUERY INFO EXTRACTION
# ---------------------------
def extract_query_details(query):
    age = re.search(r'(\d+)[- ]?year', query.lower())
    duration = re.search(r'(\d+)[- ]?(month|year|week)', query.lower())

    age_val = int(age.group(1)) if age else "Unknown"

    if duration:
        val = int(duration.group(1))
        unit = duration.group(2)
        if "year" in unit:
            months = val * 12
        elif "week" in unit:
            months = 1
        else:
            months = val
    else:
        months = "Unknown"

    procedure = "General"
    if "appendectomy" in query.lower():
        procedure = "Appendectomy"
    elif "dental" in query.lower():
        procedure = "Dental"
    elif "cosmetic" in query.lower():
        procedure = "Cosmetic"
    elif "surgery" in query.lower():
        procedure = "Surgery"

    return age_val, months, procedure

# ---------------------------
# GEMINI AI
# ---------------------------
def generate_answer(query, context):
    prompt = f"""
You are an expert insurance claim AI.

STRICT RULES:
- Use ONLY given policy
- Answer SHORT (1 line reason)
- DO NOT explain long
- FOLLOW FORMAT EXACTLY

Policy:
{context}

Query:
{query}

FORMAT:

Decision: Approved OR Rejected
Reason: one short line
Confidence: number%

If not found:

Decision: Unknown
Reason: Not found in policy
Confidence: 50%
"""

    try:
        response = model.generate_content(prompt)

        if response and hasattr(response, "text") and response.text.strip():
            return response.text.strip()
        else:
            return "Decision: Unknown\nReason: No response\nConfidence: 50%"

    except Exception as e:
        return f"Decision: Error\nReason: {str(e)}\nConfidence: 0%"

# ---------------------------
# PARSE OUTPUT
# ---------------------------
def parse_output(text):
    decision = "Unknown"
    reason = "Not available"
    confidence = "80%"

    for line in text.split("\n"):
        line = line.strip().lower()

        if line.startswith("decision"):
            decision = line.split(":")[-1].strip().capitalize()

        elif line.startswith("reason"):
            reason = line.split(":")[-1].strip().capitalize()

        elif line.startswith("confidence"):
            confidence = line.split(":")[-1].strip()

    return decision, reason, confidence

# ---------------------------
# UI HEADER
# ---------------------------
st.title("🧠 PolicyMind v2.0")
st.caption("AI-Powered Insurance Policy Analysis Engine")

tabs = st.tabs(["🏠 Home", "📄 Query", "🧠 AI Response", "📊 Details", "🕘 History"])

# ---------------------------
# QUERY TAB
# ---------------------------
with tabs[1]:
    st.subheader("Upload Policy Document")
    pdf = st.file_uploader("Upload PDF", type=["pdf"])

    if pdf:
        context = extract_text(pdf)
        st.success("Document indexed successfully ✅")

        query = st.text_input("Ask your question")

        if st.button("🚀 Analyze with AI"):
            if query.strip() != "":
                age, months, procedure = extract_query_details(query)

                result = generate_answer(query, context)
                decision, reason, confidence = parse_output(result)

                # SAVE HISTORY
                st.session_state.history.append({
                    "query": query,
                    "decision": decision,
                    "reason": reason
                })

                # SAVE RESULT
                st.session_state.last_result = {
                    "decision": decision,
                    "reason": reason,
                    "confidence": confidence,
                    "months": months,
                    "procedure": procedure
                }

                st.success("✅ Analysis complete → Go to AI Response")

# ---------------------------
# AI RESPONSE TAB
# ---------------------------
with tabs[2]:
    st.subheader("🧠 AI Analysis Result")

    if st.session_state.last_result:
        r = st.session_state.last_result

        # Gradient box
        st.markdown(f"""
        <div style="
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        padding: 18px;
        border-radius: 10px;
        color: white;
        font-size: 16px;">
        💬 <b>{r['reason'] if r['reason'] else "No explanation found"}</b>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📊 Analysis Summary")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Decision", r["decision"])
        col2.metric("Confidence", r["confidence"])
        col3.metric("Policy Age", f"{r['months']} months")
        col4.metric("Procedure", r["procedure"])

    else:
        st.info("No analysis yet")

# ---------------------------
# HISTORY TAB
# ---------------------------
with tabs[4]:
    st.subheader("🕘 History")

    if st.session_state.history:
        for item in reversed(st.session_state.history):
            st.markdown(f"""
            🔍 **Query:** {item['query']}  
            ✅ **Decision:** {item['decision']}  
            💡 **Reason:** {item['reason']}
            ---
            """)
    else:
        st.info("No history yet")

# ---------------------------
# DETAILS TAB
# ---------------------------
with tabs[3]:
    st.subheader("📊 Details")
    st.write("Structured extraction shown here (can extend)")
