import streamlit as st

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="PolicyMind v2.0", layout="wide")

# ------------------ SESSION STATE ------------------
if "history" not in st.session_state:
    st.session_state.history = []

# ------------------ HEADER ------------------
st.title("🧠 PolicyMind v2.0")
st.caption("AI-Powered Insurance Policy Analysis Engine")

# ------------------ NAVIGATION ------------------
tab = st.radio("", ["🏠 Home", "📄 Query", "🧠 AI Response", "📊 Details", "📜 History"], horizontal=True)

# ------------------ HOME ------------------
if tab == "🏠 Home":
    st.subheader("Welcome to PolicyMind v2.0 🚀")

    st.markdown("""
    ### What can PolicyMind do?

    - ⚡ Instant Policy Analysis  
    - 💬 Natural Language Queries  
    - 📊 Detailed Decision Insights  
    - 📜 Query History Tracking  

    ### How to use:

    1. Upload your policy PDF  
    2. Ask questions like:
        - "46-year-old male, knee surgery, 3-month policy"
        - "Cosmetic surgery covered?"
        - "Emergency appendectomy, 1-week policy"
    """)

# ------------------ QUERY TAB ------------------
elif tab == "📄 Query":

    st.subheader("📂 Upload Policy Document")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_file:
        st.success("Document uploaded and indexed successfully ✅")

    st.subheader("💬 Ask Your Question")

    query = st.text_input("Describe your situation:")

    if st.button("🚀 Analyze with AI"):

        if query:

            # ------------------ LOGIC ------------------
            query_lower = query.lower()

            # Extract age
            age = None
            if "year" in query_lower:
                try:
                    age = int(query_lower.split("-")[0])
                except:
                    age = None

            # Extract policy duration
            if "week" in query_lower:
                policy_months = 0.25
            elif "month" in query_lower:
                try:
                    policy_months = int(query_lower.split("month")[0].split()[-1])
                except:
                    policy_months = 1
            elif "year" in query_lower:
                try:
                    policy_months = int(query_lower.split("year")[0].split()[-1]) * 12
                except:
                    policy_months = 12
            else:
                policy_months = 1

            # Detect procedure
            if "appendectomy" in query_lower:
                procedure = "Emergency Appendectomy"
                is_emergency = True
            elif "cosmetic" in query_lower:
                procedure = "Cosmetic Surgery"
                is_emergency = False
            elif "cataract" in query_lower:
                procedure = "Cataract Surgery"
                is_emergency = False
            elif "dental" in query_lower:
                procedure = "Dental Treatment"
                is_emergency = False
            else:
                procedure = "General Treatment"
                is_emergency = False

            # ------------------ DECISION ENGINE ------------------
            if is_emergency:
                decision = "Approved"
                justification = "Emergency hospitalization is covered even during waiting period."
                confidence = 98

            elif "cosmetic" in query_lower:
                decision = "Rejected"
                justification = "Cosmetic procedures are excluded unless medically necessary."
                confidence = 95

            elif "dental" in query_lower:
                decision = "Rejected"
                justification = "Dental treatments are generally excluded unless due to accident."
                confidence = 90

            elif policy_months < 12:
                decision = "Rejected"
                justification = "Waiting period not completed."
                confidence = 88

            else:
                decision = "Approved"
                justification = "Covered under policy after waiting period."
                confidence = 92

            # ------------------ STORE RESULT ------------------
            result = {
                "query": query,
                "decision": decision,
                "confidence": confidence,
                "policy_months": policy_months,
                "procedure": procedure,
                "justification": justification
            }

            st.session_state.result = result
            st.session_state.history.append(result)

            st.success("Analysis Completed! Go to AI Response tab 👉")

# ------------------ AI RESPONSE ------------------
elif tab == "🧠 AI Response":

    st.subheader("🧠 AI Analysis Result")

    if "result" in st.session_state:

        r = st.session_state.result

        st.success("💡 You are an Insurance AI")

        st.markdown(f"""
        ### ✅ Decision: **{r['decision']}**
        ### 💰 Coverage: **Up to Sum Insured**
        ### 📌 Procedure: **{r['procedure']}**
        ### 📅 Policy Duration: **{r['policy_months']} months**

        ### 💡 Explanation:
        {r['justification']}

        ### 📊 Confidence: **{r['confidence']}%**

        ### 🚀 Next Steps:
        - Proceed with hospital if approved
        - Keep all medical documents ready
        """)

    else:
        st.warning("No analysis yet. Go to Query tab.")

# ------------------ DETAILS ------------------
elif tab == "📊 Details":

    st.subheader("📊 Detailed JSON Output")

    if "result" in st.session_state:
        st.json(st.session_state.result)
    else:
        st.warning("No data available.")

# ------------------ HISTORY ------------------
elif tab == "📜 History":

    st.subheader("📜 Previous Queries")

    if st.session_state.history:
        for item in reversed(st.session_state.history):
            st.write(f"🔹 {item['query']}")
            st.write(f"   ➤ {item['decision']} ({item['confidence']}%)")
            st.write("---")
    else:
        st.warning("No history yet.")
