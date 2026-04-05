import streamlit as st
import google.generativeai as genai
import PyPDF2
import re

# ---------------- CONFIG & UI STYLING ----------------
st.set_page_config(page_title="PolicyMind v2.1", layout="wide", page_icon="🧠")

# ---------------- LANGUAGES DICTIONARY ----------------
LANG = {
    "English": {
        "title": "🧠 PolicyMind v2.1",
        "how_works": "🔍 How it Works",
        "step1": "1. Upload your Insurance Policy (PDF).",
        "step2": "2. Ask a question about a claim or coverage.",
        "step3": "3. AI analyzes the policy and gives a Decision.",
        "examples": "💡 Example Questions",
        "ex1": "I have had this policy for 2 years, is dental surgery covered?",
        "ex2": "Does this policy cover emergency appendectomy?",
        "upload_label": "Upload Policy PDF",
        "query_placeholder": "Ask your question here...",
        "analyze_btn": "🚀 Analyze with AI",
        "stats_title": "📊 Analytics Dashboard",
        "total_q": "Total Queries",
        "appr": "Approved",
        "rej": "Rejected",
        "history_tab": "📜 History & Stats",
        "decision": "Decision",
        "reason": "Reason"
    },
    "Hindi": {
        "title": "🧠 पॉलिसीमाइंड (PolicyMind) v2.1",
        "how_works": "🔍 यह कैसे काम करता है",
        "step1": "1. अपनी बीमा पॉलिसी (PDF) अपलोड करें।",
        "step2": "2. दावे या कवरेज के बारे में प्रश्न पूछें।",
        "step3": "3. AI पॉलिसी का विश्लेषण करता है और निर्णय देता है।",
        "examples": "💡 उदाहरण प्रश्न",
        "ex1": "मेरे पास यह पॉलिसी 2 साल से है, क्या डेंटल सर्जरी कवर है?",
        "ex2": "क्या यह पॉलिसी इमरजेंसी अपेंडक्टोमी को कवर करती है?",
        "upload_label": "पॉलिसी PDF अपलोड करें",
        "query_placeholder": "अपना प्रश्न यहाँ पूछें...",
        "analyze_btn": "🚀 AI के साथ विश्लेषण करें",
        "stats_title": "📊 एनालिटिक्स डैशबोर्ड",
        "total_q": "कुल प्रश्न",
        "appr": "स्वीकृत (Approved)",
        "rej": "अस्वीकृत (Rejected)",
        "history_tab": "📜 इतिहास और आंकड़े",
        "decision": "निर्णय",
        "reason": "कारण"
    },
    "Kannada": {
        "title": "🧠 ಪಾಲಿಸಿಮೈಂಡ್ (PolicyMind) v2.1",
        "how_works": "🔍 ಇದು ಹೇಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ",
        "step1": "1. ನಿಮ್ಮ ವಿಮಾ ಪಾಲಿಸಿಯನ್ನು (PDF) ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
        "step2": "2. ಕ್ಲೈಮ್ ಅಥವಾ ಕವರೇಜ್ ಬಗ್ಗೆ ಪ್ರಶ್ನೆ ಕೇಳಿ.",
        "step3": "3. AI ಪಾಲಿಸಿಯನ್ನು ವಿಶ್ಲೇಷಿಸುತ್ತದೆ ಮತ್ತು ತೀರ್ಮಾನವನ್ನು ನೀಡುತ್ತದೆ.",
        "examples": "💡 ಉದಾಹರಣೆ ಪ್ರಶ್ನೆಗಳು",
        "ex1": "ನನ್ನ ಬಳಿ ಈ ಪಾಲಿಸಿ 2 ವರ್ಷಗಳಿಂದ ಇದೆ, ಹಲ್ಲಿನ ಶಸ್ತ್ರಚಿಕಿತ್ಸೆ ಕವರ್ ಆಗುತ್ತದೆಯೇ?",
        "ex2": "ಈ ಪಾಲಿಸಿಯು ತುರ್ತು ಅಪೆಂಡೆಕ್ಟೊಮಿಯನ್ನು ಕವರ್ ಮಾಡುತ್ತದೆಯೇ?",
        "upload_label": "ಪಾಲಿಸಿ PDF ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
        "query_placeholder": "ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಇಲ್ಲಿ ಕೇಳಿ...",
        "analyze_btn": "🚀 AI ವಿಶ್ಲೇಷಣೆ",
        "stats_title": "📊 ಅನಾಲಿಟಿಕ್ಸ್ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
        "total_q": "ಒಟ್ಟು ಪ್ರಶ್ನೆಗಳು",
        "appr": "ಅನುಮೋದಿಸಲಾಗಿದೆ (Approved)",
        "rej": "ತಿರಸ್ಕರಿಸಲಾಗಿದೆ (Rejected)",
        "history_tab": "📜 ಇತಿಹಾಸ ಮತ್ತು ಅಂಕಿಅಂಶಗಳು",
        "decision": "ತೀರ್ಮಾನ",
        "reason": "ಕಾರಣ"
    }
}

# ---------------- SIDEBAR: LANGUAGE ----------------
selected_lang = st.sidebar.selectbox("🌐 Select Language / ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ / भाषा चुनें", ["English", "Hindi", "Kannada"])
T = LANG[selected_lang]

# ---------------- API & MODEL ----------------
API_KEY = st.secrets.get("GEMINI_API_KEY")
if not API_KEY:
    st.error("❌ Add GEMINI_API_KEY in Secrets")
    st.stop()

genai.configure(api_key=API_KEY)

@st.cache_resource
def load_working_model():
    for name in ["gemini-1.5-flash", "gemini-1.5-pro"]:
        try:
            m = genai.GenerativeModel(name)
            m.generate_content("test", generation_config={"max_output_tokens": 1})
            return m
        except: continue
    return None

model = load_working_model()

# ---------------- SESSION ----------------
if "history" not in st.session_state: st.session_state.history = []
if "pdf_text" not in st.session_state: st.session_state.pdf_text = ""

# ---------------- LOGIC ----------------
def extract_pdf_text(file):
    reader = PyPDF2.PdfReader(file)
    return "\n".join([p.extract_text() or "" for p in reader.pages])

def generate_ai_response(query, context, lang):
    prompt = f"""
    You are an Insurance Policy AI. 
    Policy Content: {context[:12000]}
    
    User Query: {query}
    
    Respond STRICTLY in {lang}. 
    Format:
    Decision: [Approved or Rejected]
    Reason: [One short sentence]
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

# ---------------- UI: HOME ----------------
st.title(T["title"])

with st.expander(T["how_works"], expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.write(T["step1"])
        st.write(T["step2"])
        st.write(T["step3"])
    with col2:
        st.info(f"**{T['examples']}**\n\n* {T['ex1']}\n* {T['ex2']}")

# ---------------- MAIN TABS ----------------
tab1, tab2, tab3 = st.tabs(["📄 " + T["upload_label"], "🧠 AI Response", T["history_tab"]])

with tab1:
    uploaded = st.file_uploader(T["upload_label"], type="pdf")
    if uploaded:
        st.session_state.pdf_text = extract_pdf_text(uploaded)
        st.success("✅ Policy Loaded!")

    user_query = st.text_input(T["query_placeholder"])

    if st.button(T["analyze_btn"]):
        if not st.session_state.pdf_text:
            st.error("Please upload a PDF first!")
        elif not user_query:
            st.error("Please enter a question!")
        else:
            with st.spinner("Analyzing..."):
                raw_res = generate_ai_response(user_query, st.session_state.pdf_text, selected_lang)
                
                # Logic to determine approved/rejected from text for stats
                decision_status = "Rejected"
                if "Approved" in raw_res or "स्वीकृत" in raw_res or "ಅನುಮೋದಿಸಲಾಗಿದೆ" in raw_res:
                    decision_status = "Approved"

                # Save to history
                entry = {
                    "query": user_query,
                    "response": raw_res,
                    "decision": decision_status,
                    "lang": selected_lang
                }
                st.session_state.history.append(entry)
                st.session_state.latest = entry
                st.success("Analysis Complete! Check the 'AI Response' tab.")

with tab2:
    if "latest" in st.session_state:
        res = st.session_state.latest
        color = "#2ecc71" if res["decision"] == "Approved" else "#e74c3c"
        st.markdown(f"""
        <div style="background:{color}; padding:25px; border-radius:15px; color:white; font-size:1.2em;">
            {res['response']}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Results will appear here.")

with tab3:
    st.subheader(T["stats_title"])
    total = len(st.session_state.history)
    approved = sum(1 for x in st.session_state.history if x['decision'] == "Approved")
    rejected = total - approved

    c1, c2, c3 = st.columns(3)
    c1.metric(T["total_q"], total)
    c2.metric(T["appr"], approved, delta_color="normal")
    c3.metric(T["rej"], rejected, delta_color="inverse")

    st.divider()
    if st.session_state.history:
        for item in reversed(st.session_state.history):
            with st.expander(f"🕒 {item['query'][:50]}... ({item['decision']})"):
                st.write(f"**Query:** {item['query']}")
                st.write(f"**Response:** {item['response']}")
    else:
        st.info("No history found.")
