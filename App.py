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
model = genai.GenerativeModel("gemini-pro")

# ---------------------------
# SESSION STATE (HISTORY)
# ---------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# ---------------------------
# EXTRACT TEXT FROM PDF
# ---------------------------
def extract_text(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text[:8000]  # limit

# ---------------------------
# EXTRACT STRUCTURED DATA
# ---------------------------
def extract_query_details(query):
    age = re.search(r'(\d+)[- ]?year', query.lower())
    months = re.search(r'(\d+)[- ]?(month|year|week)', query.lower())
    
    age_val = int(age.group(1)) if age else "Unknown"

    if months:
        val = int(months.group(1))
        unit = months.group(2)
        if "year" in unit:
            months_val = val * 12
        elif "week" in unit:
            months_val = 1
        else:
            months_val = val
    else:
        months_val = "Unknown"

    procedure = "Unknown"
    if "surgery" in query.lower():
        procedure = "Surgery"
    elif "dental" in query.lower():
        procedure = "Dental"
    elif "cosmetic" in query.lower():
        procedure = "Cosmetic"
    elif "appendectomy" in query.lower():
        procedure = "Appendectomy"

    return age_val, months_val, procedure

# ---------------------------
# GEMINI ANSWER
# ---------------------------
def generate_answer(query, context):
    prompt = f"""
You are an insurance claim AI.

Based ONLY on policy:

{context}

User query:
{query}

Give SHORT answer:

Decision: Approved or Rejected  
Reason: One clear line  
Confidence: percentage  
"""

    try:
        response = model.generate_content(prompt)
        return response.text if response else "No response"
    except Exception as e:
        return str(e)

# ---------------------------
# PARSE OUTPUT
# ---------------------------
def parse_output(text):
    decision = "Unknown"
    reason = ""
    confidence = "80%"

    for line in text.split("\n"):
        if "Decision" in line:
            decision = line.split(":")[-1].strip()
        elif "Reason" in line:
            reason = line.split(":")[-1].strip()
        elif "Confidence" in line:
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
            if query:
                age, months, procedure = extract_query_details(query)
                result = generate_answer(query, context)
                decision, reason, confidence = parse_output(result)

                # Save to history
                st.session_state.history.append({
                    "query": query,
                    "decision": decision,
                    "reason": reason
                })

                # Store for response tab
                st.session_state.last_result = {
                    "decision": decision,
                    "reason": reason,
                    "confidence": confidence,
                    "months": months,
                    "procedure": procedure
                }

                st.success("Analysis complete → Go to AI Response tab")

# ---------------------------
# AI RESPONSE TAB (LIKE VIDEO)
# ---------------------------
with tabs[2]:
    st.subheader("🧠 AI Analysis Result")

    if "last_result" in st.session_state:
        r = st.session_state.last_result

        # Gradient box
        st.markdown(f"""
        <div style="
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        padding: 20px;
        border-radius: 12px;
        color: white;
        font-size: 16px;">
        💬 <b>{r['reason']}</b>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📊 Analysis Summary")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Decision", r["decision"])
        col2.metric("Confidence", r["confidence"])
        col3.metric("Policy Age", f"{r['months']} months")
        col4.metric("Procedure", r["procedure"])

# ---------------------------
# HISTORY TAB (FIXED)
# ---------------------------
with tabs[4]:
    st.subheader("🕘 History")

    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history)):
            st.markdown(f"""
            **Query:** {item['query']}  
            **Decision:** {item['decision']}  
            **Reason:** {item['reason']}
            ---
            """)
    else:
        st.info("No history yet")

# ---------------------------
# DETAILS TAB
# ---------------------------
with tabs[3]:
    st.subheader("📊 Details")
    st.write("Shows structured extraction (can extend later)")
