import streamlit as st
import google.generativeai as genai
import PyPDF2
import re

# ---------------- CONFIG ----------------
st.set_page_config(page_title="PolicyMind v2.0", layout="wide")

# ---------------- API SETUP ----------------
API_KEY = st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("❌ API Key not found. Add GEMINI_API_KEY in secrets.")
    st.stop()

genai.configure(api_key=API_KEY)

# Safe model loader (no error)
def load_model():
    try:
        return genai.GenerativeModel("gemini-1.5-flash-latest")
    except:
        try:
            return genai.GenerativeModel("gemini-1.5-flash")
        except:
            return genai.GenerativeModel("models/text-bison-001")

model = load_model()

# ---------------- SESSION ----------------
if "history" not in st.session_state:
    st.session_state.history = []

if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# ---------------- FUNCTIONS ----------------

def extract_pdf_text(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


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
    if "emergency" in query.lower():
        procedure = "Emergency"

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


def generate_answer(query, context):
    try:
        prompt = f"""
You are an insurance claim decision AI.

Based ONLY on the policy document below:

{context[:3000]}

User query:
{query}

Give STRICT output:

Decision: Approved / Rejected
Reason: One short line only
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

tabs = st.tabs(["🏠 Home", "📄 Query", "🧠 AI Response", "📊 Details", "📜 History"])

# ---------------- QUERY TAB ----------------
with tabs[1]:
    st.subheader("Upload Insurance Policy PDF")
    uploaded_file = st.file_uploader("", type=["pdf"])

    if uploaded_file:
        st.session_state.pdf_text = extract_pdf_text(uploaded_file)
        st.success("✅ Document indexed successfully")

    query = st.text_input("Ask your question")

    if st.button("🚀 Analyze with AI"):

        if not st.session_state.pdf_text:
            st.error("Upload PDF first")
        elif not query:
            st.error("Enter query")
        else:
            details = extract_details(query)

            decision, reason = generate_answer(query, st.session_state.pdf_text)

            result = {
                "query": query,
                "decision": decision,
                "reason": reason,
                "confidence": "90%" if decision != "Error" else "0%",
                "policy_age": f"{details['policy_months']} months",
                "procedure": details["procedure"]
            }

            st.session_state.latest = result
            st.session_state.history.append(result)

# ---------------- AI RESPONSE ----------------
with tabs[2]:
    st.subheader("🧠 AI Analysis Result")

    if "latest" in st.session_state:
        r = st.session_state.latest

        st.markdown(f"""
### 💬 Decision: {r['decision']}

📌 Reason: {r['reason']}

🚀 Next Steps:
- Proceed if approved
- Keep documents ready
""")

        st.divider()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Decision", r["decision"])
        col2.metric("Confidence", r["confidence"])
        col3.metric("Policy Age", r["policy_age"])
        col4.metric("Procedure", r["procedure"])

    else:
        st.info("No analysis yet")

# ---------------- DETAILS ----------------
with tabs[3]:
    st.subheader("📊 Extracted Details")

    if "latest" in st.session_state:
        st.json(st.session_state.latest)

# ---------------- HISTORY ----------------
with tabs[4]:
    st.subheader("📜 History")

    if st.session_state.history:
        for h in reversed(st.session_state.history):
            st.write(f"🔹 {h['query']} → {h['decision']}")
    else:
        st.info("No history yet")
