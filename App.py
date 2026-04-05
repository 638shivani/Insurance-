import streamlit as st
import google.generativeai as genai
import PyPDF2
import re
import json

# ---------------- CONFIG & OBSIDIAN CSS ----------------
st.set_page_config(page_title="PolicyMind Pro", layout="wide", page_icon="🧠")

# Custom CSS to force deep dark theme and style the dropdown
st.markdown("""
    <style>
    /* Global Background */
    .stApp, [data-testid="stSidebar"] {
        background-color: #080A0D !important;
        color: #E5E7EB !important;
    }

    /* Sidebar Language Dropdown (Fixes the White Color) */
    div[data-baseweb="select"] > div {
        background-color: #111827 !important;
        color: white !important;
        border: 1px solid #30363D !important;
    }
    div[role="listbox"] ul {
        background-color: #111827 !important;
    }
    div[role="option"] {
        color: white !important;
        background-color: #111827 !important;
    }
    div[role="option"]:hover {
        background-color: #1F2937 !important;
    }

    /* Cards and Containers */
    .metric-card {
        background-color: #0F1217;
        border: 1px solid #1F2937;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(94deg, #1E40AF 0%, #3B82F6 100%);
        color: white; border: none; border-radius: 8px;
        width: 100%; transition: 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0px 0px 20px rgba(59, 130, 246, 0.4);
        border: none;
    }

    /* Text Inputs */
    input {
        background-color: #0F1217 !important;
        color: white !important;
        border: 1px solid #30363D !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------- API & MODEL LOADER ----------------
API_KEY = st.secrets.get("GEMINI_API_KEY")
if not API_KEY:
    st.error("❌ GEMINI_API_KEY Missing in Secrets")
    st.stop()

genai.configure(api_key=API_KEY)

@st.cache_resource
def load_model():
    # Attempt to find a working 2026 model to avoid 404
    for m_name in ["gemini-3-flash", "gemini-2.5-flash", "gemini-1.5-flash"]:
        try:
            m = genai.GenerativeModel(m_name)
            m.generate_content("ok", generation_config={"max_output_tokens": 1})
            return m
        except: continue
    return None

model = load_model()

# ---------------- LANGUAGE DATA ----------------
LANG_MAP = {
    "English": {
        "welcome": "Welcome to PolicyMind Pro",
        "how": "How to use",
        "steps": ["1. Upload Policy PDF", "2. Ask a Claim Question", "3. Get AI Analysis"],
        "examples": ["I have had this policy for 2 years, is dental checkup covered?", "Does this policy cover emergency heart surgery?"],
        "metrics": ["Decision", "Confidence", "Policy Age", "Procedure"],
        "stats_labels": ["Total Queries", "Approved", "Rejected"]
    },
    "Hindi": {
        "welcome": "पॉलिसीमाइंड प्रो में आपका स्वागत है",
        "how": "उपयोग कैसे करें",
        "steps": ["1. पॉलिसी PDF अपलोड करें", "2. दावा प्रश्न पूछें", "3. AI विश्लेषण प्राप्त करें"],
        "examples": ["मेरे पास यह पॉलिसी 2 साल से है, क्या डेंटल चेकअप कवर है?", "क्या यह पॉलिसी इमरजेंसी हार्ट सर्जरी को कवर करती है?"],
        "metrics": ["निर्णय", "विश्वास", "पॉलिसी आयु", "प्रक्रिया"],
        "stats_labels": ["कुल प्रश्न", "स्वीकृत", "अस्वीकृत"]
    },
    "Kannada": {
        "welcome": "ಪಾಲಿಸಿಮೈಂಡ್ ಪ್ರೊಗೆ ಸುಸ್ವಾಗತ",
        "how": "ಬಳಸುವುದು ಹೇಗೆ",
        "steps": ["1. ಪಾಲಿಸಿ PDF ಅಪ್‌ಲೋಡ್ ಮಾಡಿ", "2. ಕ್ಲೈಮ್ ಪ್ರಶ್ನೆ ಕೇಳಿ", "3. AI ವಿಶ್ಲೇಷಣೆ ಪಡೆಯಿರಿ"],
        "examples": ["ನನ್ನ ಬಳಿ ಈ ಪಾಲಿಸಿ 2 ವರ್ಷಗಳಿಂದ ಇದೆ, ಹಲ್ಲಿನ ತಪಾಸಣೆ ಕವರ್ ಆಗುತ್ತದೆಯೇ?", "ಈ ಪಾಲಿಸಿಯು ತುರ್ತು ಹೃದಯ ಶಸ್ತ್ರಚಿಕಿತ್ಸೆಯನ್ನು ಕವರ್ ಮಾಡುತ್ತದೆಯೇ?"],
        "metrics": ["ತೀರ್ಮಾನ", "ನಂಬಿಕೆ", "ಪಾಲಿಸಿ ಅವಧಿ", "ಕಾರ್ಯವಿಧಾನ"],
        "stats_labels": ["ಒಟ್ಟು ಪ್ರಶ್ನೆಗಳು", "ಅನುಮೋದಿಸಲಾಗಿದೆ", "ತಿರಸ್ಕರಿಸಲಾಗಿದೆ"]
    }
}

# ---------------- SIDEBAR ----------------
st.sidebar.title("Settings")
sel_lang = st.sidebar.selectbox("🌐 Language / ಭಾಷೆ / भाषा", ["English", "Hindi", "Kannada"])
L = LANG_MAP[sel_lang]

# ---------------- SESSION STATE ----------------
if "history" not in st.session_state: st.session_state.history = []
if "pdf_text" not in st.session_state: st.session_state.pdf_text = ""
if "latest" not in st.session_state: st.session_state.latest = None

# ---------------- LOGIC ----------------
def get_pdf_text(file):
    reader = PyPDF2.PdfReader(file)
    return "\n".join([p.extract_text() or "" for p in reader.pages])

def run_ai_logic(query, context, lang_name):
    prompt = f"""
    Policy: {context[:12000]}
    Query: {query}
    Respond in {lang_name}. Output JSON:
    {{"decision": "Approved/Rejected", "reason": "Short explanation", "conf": "X%", "age": "Detected", "proc": "Detected"}}
    """
    try:
        raw = model.generate_content(prompt).text
        clean = raw.replace('```json', '').replace('```', '').strip()
        return json.loads(clean)
    except:
        return {"decision": "Error", "reason": "Check AI Connection", "conf": "0%", "age": "N/A", "proc": "N/A"}

# ---------------- UI: HOME ----------------
st.title(L["welcome"])

# Home Page Info
c1, c2 = st.columns([2, 1])
with c1:
    st.subheader(L["how"])
    for step in L["steps"]:
        st.write(f"🔹 {step}")
with c2:
    st.markdown("### 💡 Example Questions")
    for ex in L["examples"]:
        st.info(ex)

st.divider()

if not model:
    st.error("🚨 AI Handshake Failed. Verify API Key and check logs.")
    st.stop()

# ---------------- TABS ----------------
t1, t2, t3 = st.tabs(["📄 Upload", "🧠 AI Analysis", "📊 History & Stats"])

with t1:
    up = st.file_uploader("Upload Insurance Document", type="pdf")
    if up: 
        st.session_state.pdf_text = get_pdf_text(up)
        st.success("Document Indexed")
    
    q = st.text_input("Ask about your coverage:")
    if st.button("🚀 Analyze Now"):
        if st.session_state.pdf_text and q:
            with st.spinner("Analyzing..."):
                res = run_ai_logic(q, st.session_state.pdf_text, sel_lang)
                st.session_state.latest = res
                st.session_state.history.append(res)
        else: st.warning("Please upload a file and enter a query.")

with t2:
    if st.session_state.latest:
        res = st.session_state.latest
        banner_color = "#10B981" if res["decision"] in ["Approved", "ಅನುಮೋದಿಸಲಾಗಿದೆ", "स्वीकृत"] else "#EF4444"
        
        st.markdown(f"""
        <div style="background-color: {banner_color}; padding: 25px; border-radius: 12px; margin-bottom: 25px;">
            <h2 style="color: white !important; margin:0;">{res['decision']}</h2>
            <p style="color: white; font-size: 1.1em; margin-top:10px;">{res['reason']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        cols = st.columns(4)
        m_vals = [res["decision"], res["conf"], res["age"], res["proc"]]
        for i, col in enumerate(cols):
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="color: #9CA3AF; font-size: 0.8em; text-transform: uppercase;">{L['metrics'][i]}</div>
                    <div style="font-size: 1.5em; font-weight: bold; color: #60A5FA;">{m_vals[i]}</div>
                </div>
                """, unsafe_allow_html=True)
    else: st.info("Results will appear here.")

with t3:
    # --- Statistics Dashboard ---
    total = len(st.session_state.history)
    appr = sum(1 for x in st.session_state.history if x['decision'] in ["Approved", "ಅನುಮೋದಿಸಲಾಗಿದೆ", "स्वीकृत"])
    rej = total - appr

    st.subheader(f"📊 {L['stats_labels'][0]}")
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown(f'<div class="metric-card"><div style="color:#9CA3AF;">{L["stats_labels"][0]}</div><div style="font-size:2em; font-weight:bold;">{total}</div></div>', unsafe_allow_html=True)
    with sc2:
        st.markdown(f'<div class="metric-card"><div style="color:#9CA3AF;">{L["stats_labels"][1]}</div><div style="font-size:2em; font-weight:bold; color:#10B981;">{appr}</div></div>', unsafe_allow_html=True)
    with sc3:
        st.markdown(f'<div class="metric-card"><div style="color:#9CA3AF;">{L["stats_labels"][2]}</div><div style="font-size:2em; font-weight:bold; color:#EF4444;">{rej}</div></div>', unsafe_allow_html=True)

    st.divider()
    for item in reversed(st.session_state.history):
        with st.expander(f"🕒 {item['proc']} - {item['decision']}"):
            st.write(f"**Justification:** {item['reason']}")
            st.write(f"**Certainty:** {item['conf']}")
