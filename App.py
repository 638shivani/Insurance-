import streamlit as st
import google.generativeai as genai
import PyPDF2
import re

# ---------------- CONFIG & UI STYLING ----------------
st.set_page_config(page_title="PolicyMind v2.1", layout="wide", page_icon="🧠")

# ---------------- API & MODEL (FIXED FOR NONETYPE) ----------------
API_KEY = st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("❌ GEMINI_API_KEY is missing from Streamlit Secrets.")
    st.stop()

genai.configure(api_key=API_KEY)

@st.cache_resource
def load_working_model():
    """ 
    Tries 4 different ways to connect to Gemini to prevent 'NoneType' errors.
    """
    # Try different model strings that work across different API versions
    test_names = [
        "gemini-1.5-flash", 
        "models/gemini-1.5-flash", 
        "gemini-pro", 
        "models/gemini-pro"
    ]
    
    for name in test_names:
        try:
            m = genai.GenerativeModel(name)
            # Health check: if this fails, we move to the next name
            m.generate_content("health check", generation_config={"max_output_tokens": 1})
            return m
        except:
            continue
    return None

# Initialize the model
model = load_working_model()

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
        "ai_tab": "🧠 AI Response",
        "no_pdf": "Please upload a PDF first!",
        "no_query": "Please enter a question!"
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
        "appr": "स्वीकृत",
        "rej": "अस्वीकृत",
        "history_tab": "📜 इतिहास और आंकड़े",
        "ai_tab": "🧠 AI प्रतिक्रिया",
        "no_pdf": "कृपया पहले PDF अपलोड करें!",
        "no_query": "कृपया एक प्रश्न दर्ज करें!"
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
        "appr": "ಅನುಮೋದಿಸಲಾಗಿದೆ",
        "rej": "ತಿರಸ್ಕರಿಸಲಾಗಿದೆ",
        "history_tab": "📜 ಇತಿಹಾಸ ಮತ್ತು ಅಂಕಿಅಂಶಗಳು",
        "ai_tab": "🧠 AI ಪ್ರತಿಕ್ರಿಯೆ",
        "no_pdf": "ದಯವಿಟ್ಟು ಮೊದಲು PDF ಅಪ್‌ಲೋಡ್ ಮಾಡಿ!",
        "no_query": "ದಯವಿಟ್ಟು ಪ್ರಶ್ನೆಯನ್ನು ನಮೂದಿಸಿ!"
    }
}

# ---------------- SESSION STATE ----------------
if "history" not in st.session_state: st.session_state.history = []
if "pdf_text" not in st.session_state: st.session_state.pdf_text = ""
if "latest" not in st.session_state: st.session_state.latest = None

# ---------------- SIDEBAR ----------------
st.sidebar.title("Settings")
selected_lang = st.sidebar.selectbox("🌐 Select Language", ["English", "Hindi", "Kannada"])
T = LANG[selected_lang]

# Connection Status
if model:
    st.sidebar.success("✅ AI Connected")
else:
    st.sidebar.error("❌ AI Disconnected (NoneType)")
    st.error("AI Model failed to load. Please check your API Key and refresh.")
    st.stop()

# ---------------- LOGIC ----------------
def extract_pdf_text(file):
    reader = PyPDF2.PdfReader(file)
    return "\n".join([p.extract_text() or "" for p in reader.pages])

def generate_ai_response(query, context, lang):
    # Prompt logic to handle language-specific decisions
    prompt = f"""
    You are a Health Insurance Adjuster.
    POLICY: {context[:12000]}
    QUESTION: {query}
    
    Respond in {lang}. 
    Your first word MUST be either 'Approved' or 'Rejected' (or the equivalent in {lang}).
    Followed by 'Reason:' and a one-sentence explanation.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error during AI generation: {e}"

# ---------------- UI: HOME DASHBOARD ----------------
st.title(T["title"])

with st.container():
    st.markdown(f"### {T['how_works']}")
    c1, c2, c3 = st.columns(3)
    c1.info(f"**Step 1**\n{T['step1']}")
    c2.info(f"**Step 2**\n{T['step2']}")
    c3.info(f"**Step 3**\n{T['step3']}")

with st.expander(T["examples"]):
    st.write(f"1. {T['ex1']}")
    st.write(f"2. {T['ex2']}")

st.divider()

# ---------------- MAIN TABS ----------------
tab1, tab2, tab3 = st.tabs(["📄 " + T["upload_label"], T["ai_tab"], T["history_tab"]])

with tab1:
    uploaded = st.file_uploader(T["upload_label"], type="pdf")
    if uploaded:
        st.session_state.pdf_text = extract_pdf_text(uploaded)
        st.success("✅ Policy Indexed")

    user_query = st.text_input(T["query_placeholder"])

    if st.button(T["analyze_btn"]):
        if not st.session_state.pdf_text:
            st.error(T["no_pdf"])
        elif not user_query:
            st.error(T["no_query"])
        else:
            with st.spinner("Analyzing policy..."):
                raw_res = generate_ai_response(user_query, st.session_state.pdf_text, selected_lang)
                
                # Check decision for stats
                status = "Rejected"
                # Check for approval keywords in all 3 languages
                if any(word in raw_res for word in ["Approved", "स्वीकृत", "ಅನುಮೋದಿಸಲಾಗಿದೆ"]):
                    status = "Approved"

                entry = {
                    "query": user_query,
                    "response": raw_res,
                    "decision": status
                }
                st.session_state.history.append(entry)
                st.session_state.latest = entry
                st.toast("Analysis Complete!")

with tab2:
    if st.session_state.latest:
        res = st.session_state.latest
        color = "#2ecc71" if res["decision"] == "Approved" else "#e74c3c"
        st.markdown(f"""
        <div style="background:{color}; padding:30px; border-radius:15px; color:white; font-size:1.3em; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
            <b>{res['response']}</b>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Results will be shown here after you click 'Analyze'.")

with tab3:
    st.subheader(T["stats_title"])
    total = len(st.session_state.history)
    approved = sum(1 for x in st.session_state.history if x['decision'] == "Approved")
    rejected = total - approved

    col1, col2, col3 = st.columns(3)
    col1.metric(T["total_q"], total)
    col2.metric(T["appr"], approved)
    col3.metric(T["rej"], rejected)

    st.divider()
    if st.session_state.history:
        for item in reversed(st.session_state.history):
            with st.expander(f"🕒 {item['query'][:50]}... ({item['decision']})"):
                st.write(f"**Question:** {item['query']}")
                st.write(f"**AI Response:** {item['response']}")
    else:
        st.info("History is empty.")
