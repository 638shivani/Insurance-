import streamlit as st
import google.generativeai as genai
import PyPDF2
import re

# ---------------- CONFIG ----------------
st.set_page_config(page_title="PolicyMind v2.2", layout="wide", page_icon="🧠")

# ---------------- API SETUP ----------------
API_KEY = st.secrets.get("GEMINI_API_KEY")
if not API_KEY:
    st.error("❌ GEMINI_API_KEY is missing from Streamlit Secrets.")
    st.stop()

genai.configure(api_key=API_KEY)

# ---------------- 2026 ROBUST MODEL LOADER ----------------
@st.cache_resource
def load_working_model():
    """ 
    Tries the latest 2026 models. 
    Gemini 1.5 is now legacy; Gemini 3 and 2.5 are the current standards.
    """
    # Updated model list for April 2026
    latest_models = [
        "gemini-3-flash", 
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash", 
        "gemini-2.0-flash"
    ]
    
    last_error = "No models attempted"
    for name in latest_models:
        try:
            m = genai.GenerativeModel(name)
            # Connectivity check
            m.generate_content("ping", generation_config={"max_output_tokens": 1})
            return m, None
        except Exception as e:
            last_error = str(e)
            continue
    return None, last_error

model, error_msg = load_working_model()

# ---------------- LANGUAGES ----------------
LANG = {
    "English": {
        "title": "🧠 PolicyMind v2.2",
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
        "ai_tab": "🧠 AI Response"
    },
    "Hindi": {
        "title": "🧠 पॉलिसीमाइंड (PolicyMind) v2.2",
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
        "ai_tab": "🧠 AI प्रतिक्रिया"
    },
    "Kannada": {
        "title": "🧠 ಪಾಲಿಸಿಮೈಂಡ್ (PolicyMind) v2.2",
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
        "ai_tab": "🧠 AI ಪ್ರತಿಕ್ರಿಯೆ"
    }
}

# ---------------- SESSION ----------------
if "history" not in st.session_state: st.session_state.history = []
if "pdf_text" not in st.session_state: st.session_state.pdf_text = ""
if "latest" not in st.session_state: st.session_state.latest = None

# ---------------- SIDEBAR ----------------
st.sidebar.title("Settings")
selected_lang = st.sidebar.selectbox("🌐 Select Language", ["English", "Hindi", "Kannada"])
T = LANG[selected_lang]

if st.sidebar.button("🛠️ Debug Connection"):
    if model:
        st.sidebar.write(f"Connected to: {model.model_name}")
    else:
        st.sidebar.error(f"Last Error: {error_msg}")

# ---------------- UI: HOME ----------------
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

if not model:
    st.error("🚨 AI Connection Failed. Please click 'Debug Connection' in the sidebar to see why.")
    st.stop()

# ---------------- TABS ----------------
tab1, tab2, tab3 = st.tabs(["📄 " + T["upload_label"], T["ai_tab"], T["history_tab"]])

with tab1:
    uploaded = st.file_uploader(T["upload_label"], type="pdf")
    if uploaded:
        reader = PyPDF2.PdfReader(uploaded)
        st.session_state.pdf_text = "\n".join([p.extract_text() or "" for p in reader.pages])
        st.success("✅ Policy Loaded!")

    user_query = st.text_input(T["query_placeholder"])

    if st.button(T["analyze_btn"]):
        if not st.session_state.pdf_text or not user_query:
            st.warning("Please upload a PDF and enter your question.")
        else:
            with st.spinner("AI analyzing policy..."):
                try:
                    prompt = f"Analyze this policy: {st.session_state.pdf_text[:12000]}\n\nClaim: {user_query}\n\nRespond in {selected_lang}. MUST start with 'Approved' or 'Rejected' (or translation). Provide a short Reason."
                    response = model.generate_content(prompt)
                    res_text = response.text
                    
                    status = "Rejected"
                    if any(word in res_text for word in ["Approved", "स्वीकृत", "ಅನುಮೋದಿಸಲಾಗಿದೆ"]):
                        status = "Approved"

                    entry = {"query": user_query, "response": res_text, "decision": status}
                    st.session_state.history.append(entry)
                    st.session_state.latest = entry
                    st.toast("Success!")
                except Exception as e:
                    st.error(f"AI Error: {e}")

with tab2:
    if st.session_state.latest:
        res = st.session_state.latest
        color = "#2ecc71" if res["decision"] == "Approved" else "#e74c3c"
        st.markdown(f"<div style='background:{color}; padding:25px; border-radius:15px; color:white; font-size:1.2em;'>{res['response']}</div>", unsafe_allow_html=True)
    else:
        st.info("No active result.")

with tab3:
    st.subheader(T["stats_title"])
    total = len(st.session_state.history)
    appr = sum(1 for x in st.session_state.history if x['decision'] == "Approved")
    rej = total - appr

    m1, m2, m3 = st.columns(3)
    m1.metric(T["total_q"], total)
    m2.metric(T["appr"], appr)
    m3.metric(T["rej"], rej)

    st.divider()
    for item in reversed(st.session_state.history):
        with st.expander(f"🕒 {item['query'][:50]}... ({item['decision']})"):
            st.write(item['response'])
