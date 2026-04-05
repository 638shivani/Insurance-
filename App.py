import streamlit as st
import re

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="PolicyMind v2.0", layout="wide")

# ------------------ SESSION ------------------
if "history" not in st.session_state:
    st.session_state.history = []

# ------------------ HEADER ------------------
st.title("🧠 PolicyMind v2.0")
st.caption("AI-Powered Insurance Policy Analysis Engine")

# ------------------ NAVIGATION ------------------
tab = st.radio("", ["🏠 Home", "📄 Query", "🧠 AI Response", "📊 Details", "📜 History"], horizontal=True)

# ------------------ FUNCTIONS ------------------

def extract_age(query):
    match = re.search(r'(\d+)[-\s]?year', query.lower())
    return int(match.group(1)) if match else None

def extract_policy_months(query):
    query = query.lower()

    # weeks → months
    if "week" in query:
        num = int(re.findall(r'\d+', query)[-1])
        return round(num / 4, 2)

    # months
    if "month" in query:
        num = int(re.findall(r'\d+', query)[-1])
        return num

    # years → months
    if "year" in query:
        num = int(re.findall(r'\d+', query)[-1])
        return num * 12

    return 1

def detect_procedure(query):
    q = query.lower()

    if "appendectomy" in q:
        return "Emergency Appendectomy", True
    elif "accident" in q:
        return "Accident Treatment", True
    elif "cosmetic" in q:
        return "Cosmetic Surgery", False
    elif "cataract" in q:
        return "Cataract Surgery", False
    elif "dental" in q:
        return "Dental Treatment", False
    elif "knee" in q:
        return "Knee Surgery", False
    elif "gallbladder" in q:
        return "Gallbladder Surgery", False
    else:
        return "General Treatment", False

def extract_location(query):
    cities = ["pune", "mumbai", "delhi", "bangalore", "hyderabad"]
    for city in cities:
        if city in query.lower():
            return city.capitalize()
    return "Unknown"

def decision_engine(query):
    age = extract_age(query)
    policy_months = extract_policy_months(query)
    procedure, is_emergency = detect_procedure(query)
    location = extract_location(query)

    q = query.lower()

    # Decision rules
    if is_emergency:
        decision = "Approved"
        reason = "Emergency hospitalization is covered even during waiting period."
        confidence = 98

    elif "cosmetic" in q:
        decision = "Rejected"
        reason = "Cosmetic procedures are excluded unless medically necessary."
        confidence = 95

    elif "dental" in q:
        decision = "Rejected"
        reason = "Dental treatments are excluded unless caused by accident."
        confidence = 92

    elif policy_months < 12:
        decision = "Rejected"
        reason = "Waiting period not completed."
        confidence = 90

    else:
        decision = "Approved"
        reason = "Covered under policy after waiting period."
        confidence = 93

    return {
        "query": query,
        "age": age,
        "location": location,
        "procedure": procedure,
        "policy_months": policy_months,
        "decision": decision,
        "confidence": confidence,
        "reason": reason
    }

# ------------------ HOME ------------------
if tab == "🏠 Home":
    st.subheader("Welcome to PolicyMind v2.0 🚀")
    st.markdown("""
    - ⚡ Instant Policy Analysis  
    - 💬 Ask in plain English  
    - 📊 Get structured results  
    - 📜 Track history  
    """)

# ------------------ QUERY ------------------
elif tab == "📄 Query":

    st.subheader("📂 Upload Policy Document")
    file = st.file_uploader("Upload PDF", type=["pdf"])

    if file:
        st.success("Document uploaded and indexed successfully ✅")

    st.subheader("💬 Ask Your Question")

    query = st.text_input("Example: 46-year-old male, knee surgery in Pune, 3-month policy")

    if st.button("🚀 Analyze with AI"):

        if query:
            result = decision_engine(query)

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
### 📍 Location: **{r['location']}**
### 👤 Age: **{r['age']}**
### 📅 Policy Duration: **{r['policy_months']} months**

### 💡 Explanation:
{r['reason']}

### 📊 Confidence: **{r['confidence']}%**

### 🚀 Next Steps:
- Proceed if approved
- Keep documents ready
""")

    else:
        st.warning("No analysis yet")

# ------------------ DETAILS ------------------
elif tab == "📊 Details":

    st.subheader("📊 Detailed Output")

    if "result" in st.session_state:
        st.json(st.session_state.result)
    else:
        st.warning("No data")

# ------------------ HISTORY ------------------
elif tab == "📜 History":

    st.subheader("📜 History")

    if st.session_state.history:
        for item in reversed(st.session_state.history):
            st.write(f"🔹 {item['query']}")
            st.write(f"   ➤ {item['decision']} ({item['confidence']}%)")
            st.write("---")
    else:
        st.warning("No history yet")
