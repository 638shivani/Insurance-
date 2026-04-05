import streamlit as st
import google.generativeai as genai
import PyPDF2
import re
import json

# ---------------- CONFIG & PREMIUM DARK CSS ----------------
st.set_page_config(page_title="PolicyMind v3.0", layout="wide", page_icon="🧠")

st.markdown("""
    <style>
    /* Premium Dark Theme */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: #0E1117;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #161B22;
        border-radius: 10px 10px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        color: white;
    }
    .stTabs [aria-selected="true"] {
        background-color: #21262D !important;
        border-bottom: 2px solid #58A6FF !important;
    }
    /* Metric Card Styling */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #58A6FF;
    }
    .metric-container {
        background-color: #161B22;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #30363D;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------- API SETUP ----------------
API_KEY = st.secrets.get("GEMINI_API_KEY")
if not API_KEY:
    st.error("❌ GEMINI_API_KEY is missing from Streamlit Secrets.")
    st.stop()

genai.configure(api_key=API_KEY)

# ---------------- ROBUST MODEL LOADER ----------------
@st.cache_resource
def load_working_model():
    latest_models = ["gemini-3-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash"]
    for name in latest_models:
        try:
            m = genai.GenerativeModel(name)
            m.generate_content("ping", generation_config={"max_output_tokens": 1})
            return m, None
        except: continue
    return None, "All models failed"

model, error_msg = load_working_model()

# ---------------- LANGUAGES ----------------
LANG = {
    "English": {
        "title": "🧠 PolicyMind v3.0",
        "how_works": "🔍 How it Works",
        "labels": ["Decision", "Confidence", "Policy Age", "Procedure"],
        "history_tab": "📜 History & Stats",
        "ai_tab": "🧠 AI Analysis",
        "analyze_btn": "🚀 Run AI Analysis",
        "upload": "Upload Policy PDF",
        "placeholder": "Enter claim scenario..."
    },
    "Hindi": {
        "title": "🧠 पॉलिसीमाइंड v3.0",
        "how_works": "🔍 यह कैसे काम करता है",
        "labels": ["निर्णय", "विश्वास", "पॉलिसी की आयु", "प्रक्रिया"],
        "history_tab": "📜 इतिहास और आंकड़े",
        "ai_tab": "🧠 AI विश्लेषण",
        "analyze_btn": "🚀 AI विश्लेषण चलाएँ",
        "upload": "पॉलिसी PDF अपलोड करें",
        "placeholder": "दावे का विवरण दर्ज करें..."
    },
    "Kannada": {
        "title": "🧠 ಪಾಲಿಸಿಮೈಂಡ್ v3.0",
        "how_works": "🔍 ಇದು ಹೇಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ",
        "labels": ["ತೀರ್ಮಾನ", "ನಂಬಿಕೆ", "ಪಾಲಿಸಿ ಅವಧಿ", "ಕಾರ್ಯವಿಧಾನ"],
        "history_tab": "📜 ಇತಿಹಾಸ ಮತ್ತು ಅಂಕಿಅಂಶಗಳು",
        "ai_tab": "🧠 AI ವಿಶ್ಲೇಷಣೆ",
        "analyze_btn": "🚀 AI ವಿಶ್ಲೇಷಣೆ ನಡೆಸಿ",
        "upload": "ಪಾಲಿಸಿ PDF ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
        "placeholder": "ಕ್ಲೈಮ್ ವಿವರಗಳನ್ನು ನಮೂದಿಸಿ..."
    }
}

# ---------------- SESSION ----------------
if "history" not in st.session_state: st.session_state.history = []
if "pdf_text" not in st.session_state: st.session_state.pdf_text = ""
if "latest" not in st.session_state: st.session_state.latest = None

# ---------------- SIDEBAR ----------------
selected_lang = st.sidebar.selectbox("🌐 Language", ["English", "Hindi", "Kannada"])
T = LANG[selected_lang]

# ---------------- LOGIC ----------------
def extract_pdf_text(file):
    reader = PyPDF2.PdfReader(file)
    return "\n".join([p.extract_text() or "" for p in reader.pages])

def analyze_claim(query, context, lang):
    prompt = f"""
    Analyze this insurance policy: {context[:15000]}
    User Claim: {query}
    Language: {lang}

    Return the result EXACTLY in this JSON format:
    {{
        "decision": "Approved or Rejected",
        "reason": "One sentence explanation",
        "confidence": "Estimation in %",
        "policy_age": "Detected age from document/query",
        "procedure": "Detected medical procedure"
    }}
    """
    try:
        response = model.generate_content(prompt)
        # Clean the response for potential markdown code blocks
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_text)
    except Exception as e:
        return {"decision": "Error", "reason": str(e), "confidence": "0%", "policy_age": "N/A", "procedure": "N/A"}

# ---------------- UI: HOME ----------------
st.title(T["title"])

with st.expander(T["how_works"]):
    st.write("1. Upload PDF | 2. Ask Question | 3. Get Professional AI Summary")

st.divider()

if not model:
    st.error("🚨 AI Offline. Check Connection.")
    st.stop()

# ---------------- TABS ----------------
tab1, tab2, tab3 = st.tabs(["📄 " + T["upload"], T["ai_tab"], T["history_tab"]])

with tab1:
    uploaded = st.file_uploader(T["upload"], type="pdf")
    if uploaded:
        st.session_state.pdf_text = extract_pdf_text(uploaded)
        st.success("✅ Policy Loaded into Secure Memory")

    user_query = st.text_input(T["placeholder"])

    if st.button(T["analyze_btn"]):
        if not st.session_state.pdf_text or not user_query:
            st.warning("Please provide both a policy and a query.")
        else:
            with st.spinner("🧠 Analyzing Coverage..."):
                res = analyze_claim(user_query, st.session_state.pdf_text, selected_lang)
                st.session_state.latest = res
                st.session_state.history.append(res)
                st.toast("Analysis Complete!")

with tab2:
    if st.session_state.latest:
        res = st.session_state.latest
        
        # Big Decision Banner
        color = "#2ecc71" if res["decision"] in ["Approved", "स्वीकृत", "ಅನುಮೋದಿಸಲಾಗಿದೆ"] else "#e74c3c"
        st.markdown(f"""
        <div style="background-color: {color}; padding: 30px; border-radius: 15px; text-align: center; margin-bottom: 25px;">
            <h1 style="color: white; margin: 0;">{res['decision']}</h1>
            <p style="color: white; font-size: 1.2em; margin-top: 10px;">{res['reason']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"### 📊 Analysis Summary")
        
        # Metric Grid
        m_labels = T["labels"]
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f'<div class="metric-container"><small>{m_labels[0]}</small><br><b>{res["decision"]}</b></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-container"><small>{m_labels[1]}</small><br><b>{res["confidence"]}</b></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-container"><small>{m_labels[2]}</small><br><b>{res["policy_age"]}</b></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="metric-container"><small>{m_labels[3]}</small><br><b>{res["procedure"]}</b></div>', unsafe_allow_html=True)

    else:
        st.info("No active analysis. Please run a query in the first tab.")

with tab3:
    st.subheader(T["history_tab"])
    if st.session_state.history:
        for item in reversed(st.session_state.history):
            with st.expander(f"🕒 {item['procedure']} - {item['decision']}"):
                st.write(f"**Reason:** {item['reason']}")
                st.write(f"**Confidence:** {item['confidence']}")
    else:
        st.info("History is empty.")
