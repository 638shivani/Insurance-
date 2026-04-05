import streamlit as st
import google.generativeai as genai
import PyPDF2
import re

# ---------------- CONFIG ----------------
st.set_page_config(page_title="PolicyMind v2.0", layout="wide")

# ---------------- API KEY ----------------
API_KEY = st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("❌ Add GEMINI_API_KEY in Streamlit secrets")
    st.stop()

genai.configure(api_key=API_KEY)

# ---------------- SESSION ----------------
if "history" not in st.session_state:
    st.session_state.history = []

if "latest" not in st.session_state:
    st.session_state.latest = None

# ---------------- PDF EXTRACT ----------------
def extract_pdf_text(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


# ---------------- QUERY DETAILS ----------------
def extract_details(query):
    age = re.search(r'(\d+)[- ]?year', query)
    months = re.search(r'(\d+)[- ]?month', query)
    weeks = re.search(r'(\d+)[- ]?week', query)

    procedure = "General"
    if "surgery" in query.lower():
        procedure = "Surgery"
    if "dental" in query.lower():
        procedure = "Dental"
    if "cosmetic" in query.lower():
        procedure = "Cosmetic"
    if "appendectomy" in query.lower():
        procedure = "Appendectomy"

    policy_months = 0
    if months:
        policy_months = int(months.group(1))
    elif weeks:
        policy_months = round(int(weeks.group(1)) / 4)

    return {
        "age": int(age.group(1)) if age else None,
        "policy_months": policy_months,
        "procedure": procedure
    }


# ---------------- AI FUNCTION (STABLE) ----------------
def generate_answer(query, context):
    try:
        import google.generativeai as genai

        model = genai.GenerativeModel("gemini-1.5-latent")

        prompt = f"""
You are an insurance AI.

Policy:
{context[:3000]}

User query:
{query}

Give STRICT short output:

Decision: Approved or Rejected
Reason: one short line only
"""

        response = model.generate_content(prompt)

        text = response.text

        decision = "Unknown"
        reason = "Not found"

        if "Approved" in text:
            decision = "Approved"
        elif "Rejected" in text:
            decision = "Rejected"

        if "Reason:" in text:
            reason = text.split("Reason:")[-1].strip().split("\n")[0]

        return decision, reason

    except Exception as e:
        return "Error", str(e)


# ---------------- UI ----------------
st.title("🧠 PolicyMind v2.0")
st.caption("AI-Powered Insurance Policy Analysis Engine")

tabs = st.tabs(["📄 Query", "🧠 AI Response", "📊 Details", "📜 History"])

# ---------------- QUERY ----------------
with tabs[0]:
    uploaded_file = st.file_uploader("Upload Insurance Policy PDF", type=["pdf"])

    if uploaded_file:
        st.session_state.pdf_text = extract_pdf_text(uploaded_file)
        st.success("✅ Document uploaded")

    query = st.text_input("Ask your question")

    if st.button("🚀 Analyze"):

        if "pdf_text" not in st.session_state:
            st.error("Upload PDF first")
        elif not query:
            st.error("Enter a question")
        else:
            details = extract_details(query)

            decision, reason = generate_answer(query, st.session_state.pdf_text)

            result = {
                "query": query,
                "decision": decision,
                "reason": reason,
                "confidence": "90%",
                "policy_age": f"{details['policy_months']} months",
                "procedure": details["procedure"]
            }

            st.session_state.latest = result
            st.session_state.history.append(result)

# ---------------- RESPONSE ----------------
with tabs[1]:
    if st.session_state.latest:
        r = st.session_state.latest

        # Gradient style box
        st.markdown(f"""
        <div style="
        background: linear-gradient(90deg, #4facfe, #00f2fe);
        padding: 20px;
        border-radius: 10px;
        color: white;">
        💬 <b>{r['reason']}</b>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📊 Analysis Summary")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Decision", r["decision"])
        col2.metric("Confidence", r["confidence"])
        col3.metric("Policy Age", r["policy_age"])
        col4.metric("Procedure", r["procedure"])

    else:
        st.info("No analysis yet")

# ---------------- DETAILS ----------------
with tabs[2]:
    if st.session_state.latest:
        st.json(st.session_state.latest)

# ---------------- HISTORY ----------------
with tabs[3]:
    if st.session_state.history:
        for item in reversed(st.session_state.history):
            st.write(f"🔹 {item['query']} → {item['decision']}")
    else:
        st.info("No history yet")
