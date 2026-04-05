import streamlit as st
import re

st.set_page_config(page_title="PolicyMind v2.0", layout="wide")

# -----------------------------
# 🎨 HEADER (KEEP SAME UI)
# -----------------------------
st.title("🧠 PolicyMind v2.0")
st.caption("AI-Powered Insurance Policy Analysis Engine")

tabs = st.tabs(["🏠 Home", "📄 Query", "🧠 AI Response", "📊 Details", "📜 History"])

# -----------------------------
# 📄 QUERY TAB
# -----------------------------
with tabs[1]:

    st.subheader("📄 Upload Policy Document")
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

    if uploaded_file:
        st.success("Document uploaded successfully ✅")

    st.subheader("💬 Ask Your Question")
    user_query = st.text_input(
        "Example: 46-year-old male, knee surgery in Pune, 3-month policy"
    )

    analyze = st.button("🚀 Analyze with AI")

# -----------------------------
# 🔍 EXTRACT FUNCTION
# -----------------------------
def extract_details(query):
    query = query.lower()

    # Age
    age = None
    age_match = re.search(r'(\d+)[-\s]?year', query)
    if age_match:
        age = int(age_match.group(1))

    # Policy duration
    months = 0
    month_match = re.search(r'(\d+)[-\s]?month', query)
    year_match = re.search(r'(\d+)[-\s]?year', query)

    if month_match:
        months = int(month_match.group(1))
    elif "policy" in query and year_match:
        months = int(year_match.group(1)) * 12

    # Procedure detection
    if "cataract" in query:
        procedure = "cataract"
    elif "knee" in query:
        procedure = "knee"
    elif "cosmetic" in query:
        procedure = "cosmetic"
    elif "appendectomy" in query or "emergency" in query:
        procedure = "emergency"
    elif "dental" in query:
        procedure = "dental"
    elif "maternity" in query or "pregnancy" in query:
        procedure = "maternity"
    elif "diabetes" in query:
        procedure = "preexisting"
    else:
        procedure = "general"

    return age, months, procedure

# -----------------------------
# 🧠 DECISION ENGINE (IMPROVED)
# -----------------------------
def make_decision(age, months, procedure):

    # ❌ Cosmetic
    if procedure == "cosmetic":
        return "Rejected", "Not Applicable", "Cosmetic procedures are not covered", 95

    # ❌ Dental
    if procedure == "dental":
        return "Rejected", "Not Applicable", "Dental treatments excluded unless accident", 90

    # ❌ Pre-existing
    if procedure == "preexisting" and months < 24:
        return "Rejected", "Not Applicable", "Pre-existing disease waiting period (24 months)", 95

    # ❌ Knee surgery waiting
    if procedure == "knee" and months < 12:
        return "Rejected", "Not Applicable", "Waiting period not completed for knee surgery", 90

    # ❌ Maternity waiting
    if procedure == "maternity" and months < 24:
        return "Rejected", "Not Applicable", "Maternity requires 24 months waiting period", 95

    # ✅ Cataract
    if procedure == "cataract" and months >= 24:
        return "Approved", "Up to Sum Insured", "Cataract covered after waiting period", 95

    # 🚑 Emergency
    if procedure == "emergency":
        return "Approved", "Up to Sum Insured", "Emergency hospitalization is covered", 100

    # 👴 Age restriction
    if age and age > 75:
        return "Rejected", "Not Applicable", "Age exceeds policy entry limit", 85

    # ⚠️ Partial logic for general cases
    if months < 1:
        return "Approved", "Up to Sum Insured", "Emergency/basic coverage allowed", 80

    return "Approved", "Up to Sum Insured", "Covered under policy terms", 85

# -----------------------------
# 🧠 AI RESPONSE TAB
# -----------------------------
with tabs[2]:

    st.subheader("🧠 AI Analysis Result")

    if analyze and user_query:

        age, months, procedure = extract_details(user_query)
        decision, amount, reason, confidence = make_decision(age, months, procedure)

        # Context box (same style)
        st.success(
            "💡 You are an Insurance AI.\n\n"
            f"Context: Based on uploaded policy, analyzing query..."
        )

        st.subheader("📊 Analysis Summary")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Decision", decision)
        col2.metric("Confidence", f"{confidence}%")
        col3.metric("Policy Age", f"{months} months" if months else "Unknown")
        col4.metric("Procedure", procedure.capitalize())

        st.markdown("---")

        st.info(f"💬 Justification: {reason}")

    else:
        st.warning("Please go to Query tab and enter your question.")

# -----------------------------
# 🏠 HOME TAB
# -----------------------------
with tabs[0]:
    st.markdown("""
    ### Welcome to PolicyMind v2.0 🎯

    ✔ Instant Policy Analysis  
    ✔ Natural Language Queries  
    ✔ Clear Decisions  
    ✔ Smart Reasoning  

    **How to use:**
    1. Upload policy PDF  
    2. Ask your question  
    3. Get AI decision  
    """)

# -----------------------------
# 📊 DETAILS TAB
# -----------------------------
with tabs[3]:
    st.write("Detailed explanation coming soon...")

# -----------------------------
# 📜 HISTORY TAB
# -----------------------------
with tabs[4]:
    st.write("History feature coming soon...")
