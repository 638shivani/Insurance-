import streamlit as st
import google.generativeai as genai
import PyPDF2
import re
import json

# ---------------- CONFIG & OBSIDIAN DARK CSS ----------------
st.set_page_config(page_title="PolicyMind Pro", layout="wide", page_icon="🧠")

# Full Obsidian Theme Injection
st.markdown("""
    <style>
    /* Global Obsidian Background */
    .stApp, [data-testid="stSidebar"], section[data-testid="stSidebar"] > div {
        background-color: #080A0D !important;
        color: #E5E7EB !important;
    }

    /* LANGUAGE SELECTBOX FIX (Matches Dark UI) */
    div[data-baseweb="select"] > div {
        background-color: #0F1217 !important;
        color: white !important;
        border: 1px solid #30363D !important;
        border-radius: 8px;
    }
    div[role="listbox"] {
        background-color: #0F1217 !important;
        border: 1px solid #30363D !important;
    }
    div[role="option"] {
        background-color: #0F1217 !important;
        color: white !important;
    }
    div[role="option"]:hover {
        background-color: #1F2937 !important;
    }

    /* Dashboard & Metric Cards */
    .metric-card {
        background-color: #111827;
        border: 1px solid #1F2937;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Neon Accents */
    h1, h2, h3, h4 { color: #60A5FA !important; }
    .stButton>button {
        background: linear-gradient(90deg, #1E40AF, #3B82F6);
        color: white !important; border: none !important; border-radius: 8px;
        width: 100%; transition: 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0px 0px 15px rgba(59, 130, 246, 0.6);
        transform: translateY(-2px);
    }

    /* Text Inputs & Tabs */
    input {
        background-color: #0F1217 !important;
        color: white !important;
        border: 1px solid #30363D !important;
    }
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
    .stTabs [aria-selected="true"] { color: #60A5FA !important; border-bottom-color: #60A5FA !important; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- 2026 ROBUST MODEL LOADER ----------------
import os
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("❌ GEMINI_API_KEY Missing in Secrets")
    st.stop()

genai.configure(api_key=API_KEY)

@st.cache_resource
def load_stable_model():
    """ Tries the latest 2026 Gemini 3 models to avoid 404 errors """
    # Priority: Gemini 3.1 Flash-Lite -> Gemini 3 Flash -> Fallback to dynamic list
    preferred = ["gemini-3.1-flash-lite", "gemini-3-flash", "gemini-2.5-flash"]
    try:
        # Check allowed models for this key
        allowed = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for p in preferred:
            for a in allowed:
                if p in a:
                    m = genai.GenerativeModel(a)
                    m.generate_content("ping", generation_config={"max_output_tokens": 1})
                    return m, a
        if allowed:
            return genai.GenerativeModel(allowed[0]), allowed[0]
    except Exception as e:
        return None, str(e)
    return None, "No models available"

model, model_id = load_stable_model()

# ---------------- MULTILINGUAL DATA ----------------
LANG_DB = {
    "English": {
        "title": "🧠 PolicyMind Pro v5.0",
        "intro": "Welcome to the future of insurance analysis.",
        "how": "How to use",
        "steps": ["Upload Policy PDF", "Ask a Medical Scenario", "Analyze Coverage"],
        "examples_title": "💡 Example Scenarios",
        "examples": ["I have had this policy for 2 years, is dental checkup covered?", "Is emergency appendectomy covered for a 30-year-old?"],
        "stats": ["Total Requests", "Approved", "Rejected"],
        "labels": ["Decision", "Certainty", "Policy Age", "Procedure"]
    },
    "Hindi": {
        "title": "🧠 पॉलिसीमाइंड प्रो v5.0",
        "intro": "बीमा विश्लेषण के भविष्य में आपका स्वागत है।",
        "how": "उपयोग कैसे करें",
        "steps": ["पॉलिसी PDF अपलोड करें", "एक चिकित्सा स्थिति पूछें", "कवरेज का विश्लेषण करें"],
        "examples_title": "💡 उदाहरण प्रश्न",
        "examples": ["मेरे पास यह पॉलिसी 2 साल से है, क्या डेंटल चेकअप कवर है?", "क्या 30 वर्षीय व्यक्ति के लिए आपातकालीन अपेंडक्टोमी कवर है?"],
        "stats": ["कुल अनुरोध", "स्वीकृत", "अस्वीकृत"],
        "labels": ["निर्णय", "विश्वास", "पॉलिसी की आयु", "प्रक्रिया"]
    },
    "Kannada": {
        "title": "🧠 ಪಾಲಿಸಿಮೈಂಡ್ ಪ್ರೊ v5.0",
        "intro": "ವಿಮಾ ವಿಶ್ಲೇಷಣೆಯ ಭವಿಷ್ಯಕ್ಕೆ ಸುಸ್ವಾಗತ.",
        "how": "ಬಳಸುವುದು ಹೇಗೆ",
        "steps": ["ಪಾಲಿಸಿ PDF ಅಪ್‌ಲೋಡ್ ಮಾಡಿ", "ವೈದ್ಯಕೀಯ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ", "ಕವರೇಜ್ ವಿಶ್ಲೇಷಿಸಿ"],
        "examples_title": "💡 ಉದಾಹರಣೆ ಪ್ರಶ್ನೆಗಳು",
        "examples": ["ನನ್ನ ಬಳಿ ಈ ಪಾಲಿಸಿ 2 ವರ್ಷಗಳಿಂದ ಇದೆ, ಹಲ್ಲಿನ ತಪಾಸಣೆ ಕವರ್ ಆಗುತ್ತದೆಯೇ?", "30 ವರ್ಷದ ವ್ಯಕ್ತಿಗೆ ತುರ್ತು ಅಪೆಂಡೆಕ್ಟೊಮಿ ಕವರ್ ಆಗುತ್ತದೆಯೇ?"],
        "stats": ["ಒಟ್ಟು ವಿನಂತಿಗಳು", "ಅನುಮೋದಿಸಲಾಗಿದೆ", "ತಿರಸ್ಕರಿಸಲಾಗಿದೆ"],
        "labels": ["ತೀರ್ಮಾನ", "ನಂಬಿಕೆ", "ಪಾಲಿಸಿ ಅವಧಿ", "ಕಾರ್ಯವಿಧಾನ"]
    }
}

# ---------------- SIDEBAR ----------------
st.sidebar.title("Settings")
sel_lang = st.sidebar.selectbox("🌐 Select Language", ["English", "Hindi", "Kannada"])
L = LANG_DB[sel_lang]

if model:
    st.sidebar.success(f"⚡ Connected to: {model_id}")
else:
    st.sidebar.error("🚨 AI Handshake Failed. Verify API Key permissions.")

# ---------------- STATE ----------------
if "history" not in st.session_state: st.session_state.history = []
if "pdf_text" not in st.session_state: st.session_state.pdf_text = ""
if "latest" not in st.session_state: st.session_state.latest = None

# ---------------- LOGIC ----------------
def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    return "\n".join([p.extract_text() or "" for p in reader.pages])

def analyze_claim(query, context, lang_name):
    prompt = f"""
    Policy: {context[:12000]}
    Scenario: {query}
    Respond in {lang_name}. Output STRICT JSON ONLY:
    {{
        "decision": "Approved/Rejected",
        "reason": "Clear explanation",
        "conf": "X%",
        "age": "Detected policy/user age",
        "proc": "Medical procedure"
    }}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except:
        return {"decision": "Error", "reason": "AI Connection Issue", "conf": "0%", "age": "N/A", "proc": "N/A"}

# ---------------- UI: HOME DASHBOARD ----------------
st.title(L["title"])
st.caption(L["intro"])

with st.container():
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader(f"🔍 {L['how']}")
        for step in L["steps"]:
            st.write(f"🔹 {step}")
    with c2:
        st.markdown(f"#### {L['examples_title']}")
        for ex in L["examples"]:
            st.info(ex)

st.divider()

if not model: st.stop()

# ---------------- MAIN TABS ----------------
t1, t2, t3 = st.tabs(["📄 Doc Center", "🧠 AI Analysis", "📊 Analytics & History"])

with t1:
    up = st.file_uploader("Upload Policy PDF", type="pdf")
    if up: 
        st.session_state.pdf_text = extract_text(up)
        st.success("Policy Authenticated")
    
    q = st.text_input("Enter your coverage query:")
    if st.button("🚀 Analyze Now"):
        if st.session_state.pdf_text and q:
            with st.spinner("Analyzing Policy..."):
                res = analyze_claim(q, st.session_state.pdf_text, sel_lang)
                st.session_state.latest = res
                st.session_state.history.append(res)
                st.toast("Success!")
        else: st.warning("Upload PDF and enter a query first.")

with t2:
    if st.session_state.latest:
        r = st.session_state.latest
        color = "#10B981" if r["decision"] in ["Approved", "ಅನುಮೋದಿಸಲಾಗಿದೆ", "स्वीकृत"] else "#EF4444"
        
        st.markdown(f"""
        <div style="border-left: 10px solid {color}; background-color: #111827; padding: 25px; border-radius: 12px; margin-bottom: 25px;">
            <h1 style="color: {color} !important; margin: 0;">{r['decision']}</h1>
            <p style="color: #D1D5DB; font-size: 1.1em; margin-top: 10px;">{r['reason']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        cols = st.columns(4)
        m_vals = [r["decision"], r["conf"], r["age"], r["proc"]]
        for i, col in enumerate(cols):
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="color: #9CA3AF; font-size: 0.8em; text-transform: uppercase;">{L['labels'][i]}</div>
                    <div style="font-size: 1.5em; font-weight: bold; color: #60A5FA;">{m_vals[i]}</div>
                </div>
                """, unsafe_allow_html=True)
    else: st.info("No active result.")

with t3:
    # --- Statistics Dashboard ---
    total = len(st.session_state.history)
    appr = sum(1 for x in st.session_state.history if x['decision'] in ["Approved", "ಅನುಮೋದಿಸಲಾಗಿದೆ", "स्वीकृत"])
    rej = total - appr

    st.subheader(f"📊 {L['title']} Stats")
    sc1, sc2, sc3 = st.columns(3)
    with sc1: st.markdown(f'<div class="metric-card"><div style="color:#9CA3AF;">{L["stats"][0]}</div><div style="font-size:2em; font-weight:bold;">{total}</div></div>', unsafe_allow_html=True)
    with sc2: st.markdown(f'<div class="metric-card"><div style="color:#9CA3AF;">{L["stats"][1]}</div><div style="font-size:2em; font-weight:bold; color:#10B981;">{appr}</div></div>', unsafe_allow_html=True)
    with sc3: st.markdown(f'<div class="metric-card"><div style="color:#9CA3AF;">{L["stats"][2]}</div><div style="font-size:2em; font-weight:bold; color:#EF4444;">{rej}</div></div>', unsafe_allow_html=True)

    st.divider()
    for item in reversed(st.session_state.history):
        with st.expander(f"🕒 {item['proc']} - {item['decision']}"):
            st.write(f"**Justification:** {item['reason']}")
            st.write(f"**Confidence:** {item['conf']}")
