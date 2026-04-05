import streamlit as st
import google.generativeai as genai
import PyPDF2
import re
import json

# ---------------- CONFIG & OBSIDIAN DEEP DARK CSS ----------------
st.set_page_config(page_title="PolicyMind Pro", layout="wide", page_icon="🧠")

st.markdown("""
    <style>
    /* Global Obsidian Theme */
    .stApp, [data-testid="stSidebar"], section[data-testid="stSidebar"] > div {
        background-color: #080A0D !important;
        color: #E5E7EB !important;
    }

    /* LANGUAGE SELECTBOX FIX (Matches your 2nd photo) */
    div[data-baseweb="select"] > div {
        background-color: #0F1217 !important;
        color: white !important;
        border: 1px solid #1F2937 !important;
        border-radius: 8px;
    }
    div[role="listbox"] {
        background-color: #0F1217 !important;
        border: 1px solid #1F2937 !important;
    }
    div[role="option"] {
        background-color: #0F1217 !important;
        color: white !important;
    }
    div[role="option"]:hover {
        background-color: #1F2937 !important;
    }
    /* Hide the default white text shadows */
    div[data-testid="stMarkdownContainer"] p { color: #E5E7EB !important; }

    /* Dashboard Cards */
    .stat-card {
        background-color: #0F1217;
        border: 1px solid #1F2937;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: 0.3s;
    }
    .stat-card:hover { border-color: #3B82F6; }
    
    /* Neon Accents */
    h1, h2, h3 { color: #60A5FA !important; }
    .stButton>button {
        background: linear-gradient(90deg, #1E40AF, #3B82F6);
        color: white; border: none; border-radius: 8px;
        width: 100%; transition: 0.2s;
    }
    .stButton>button:hover {
        box-shadow: 0px 0px 15px rgba(59, 130, 246, 0.5);
        transform: translateY(-1px);
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
    .stTabs [aria-selected="true"] { color: #60A5FA !important; border-bottom-color: #60A5FA !important; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- API & MODEL (2026 STABLE) ----------------
API_KEY = st.secrets.get("GEMINI_API_KEY")
if not API_KEY:
    st.error("❌ GEMINI_API_KEY Missing in Secrets")
    st.stop()

genai.configure(api_key=API_KEY)

@st.cache_resource
def load_stable_model():
    # 2026 Stability: Gemini 3 is the new standard
    for m_id in ["gemini-3-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash"]:
        try:
            m = genai.GenerativeModel(m_id)
            m.generate_content("ok", generation_config={"max_output_tokens": 1})
            return m
        except: continue
    return None

model = load_stable_model()

# ---------------- LANGUAGE MAPPING ----------------
LANG_DB = {
    "English": {
        "title": "🧠 PolicyMind Pro v4.5",
        "how": "How PolicyMind Works",
        "steps": ["1. Upload Policy (PDF)", "2. Describe Medical Case", "3. Get Instant Result"],
        "examples": ["I have had this policy for 2 years, is dental checkup covered?", "Is emergency heart surgery covered for a 45-year-old?"],
        "stats": ["Total Queries", "Approved", "Rejected"],
        "upload_lbl": "Upload Insurance Document",
        "query_lbl": "Ask your question:"
    },
    "Hindi": {
        "title": "🧠 पॉलिसीमाइंड प्रो v4.5",
        "how": "पॉलिसी कैसे काम करती है",
        "steps": ["1. पॉलिसी PDF अपलोड करें", "2. चिकित्सा मामले का वर्णन करें", "3. तुरंत परिणाम प्राप्त करें"],
        "examples": ["मेरे पास यह पॉलिसी 2 साल से है, क्या डेंटल चेकअप कवर है?", "क्या 45 वर्षीय व्यक्ति के लिए आपातकालीन हृदय सर्जरी कवर है?"],
        "stats": ["कुल प्रश्न", "स्वीकृत", "अस्वीकृत"],
        "upload_lbl": "बीमा दस्तावेज अपलोड करें",
        "query_lbl": "अपना प्रश्न पूछें:"
    },
    "Kannada": {
        "title": "🧠 ಪಾಲಿಸಿಮೈಂಡ್ ಪ್ರೊ v4.5",
        "how": "ಇದು ಹೇಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ",
        "steps": ["1. ಪಾಲಿಸಿ PDF ಅಪ್‌ಲೋಡ್ ಮಾಡಿ", "2. ವೈದ್ಯಕೀಯ ಪ್ರಕರಣವನ್ನು ವಿವರಿಸಿ", "3. ತಕ್ಷಣದ ಫಲಿತಾಂಶ ಪಡೆಯಿರಿ"],
        "examples": ["ನನ್ನ ಬಳಿ ಈ ಪಾಲಿಸಿ 2 ವರ್ಷಗಳಿಂದ ಇದೆ, ಹಲ್ಲಿನ ತಪಾಸಣೆ ಕವರ್ ಆಗುತ್ತದೆಯೇ?", "45 ವರ್ಷದ ವ್ಯಕ್ತಿಗೆ ತುರ್ತು ಹೃದಯ ಶಸ್ತ್ರಚಿಕಿತ್ಸೆ ಕವರ್ ಆಗುತ್ತದೆಯೇ?"],
        "stats": ["ಒಟ್ಟು ಪ್ರಶ್ನೆಗಳು", "ಅನುಮೋದಿಸಲಾಗಿದೆ", "ತಿರಸ್ಕರಿಸಲಾಗಿದೆ"],
        "upload_lbl": "ವಿಮಾ ದಾಖಲೆಯನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
        "query_lbl": "ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ:"
    }
}

# ---------------- SIDEBAR ----------------
st.sidebar.title("App Settings")
sel_lang = st.sidebar.selectbox("🌐 Choose Language / ಭಾಷೆ / भाषा", ["English", "Hindi", "Kannada"])
L = LANG_DB[sel_lang]

# ---------------- STATE ----------------
if "history" not in st.session_state: st.session_state.history = []
if "pdf_text" not in st.session_state: st.session_state.pdf_text = ""
if "latest" not in st.session_state: st.session_state.latest = None

# ---------------- LOGIC ----------------
def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    return "\n".join([p.extract_text() or "" for p in reader.pages])

def analyze_claim(query, context, lang):
    prompt = f"""
    Policy: {context[:12000]}
    Claim: {query}
    Respond in {lang}. Output valid JSON ONLY:
    {{"decision": "Approved/Rejected", "reason": "Short logic", "conf": "X%", "age": "X", "proc": "X"}}
    """
    try:
        raw = model.generate_content(prompt).text
        clean = raw.replace('```json', '').replace('```', '').strip()
        return json.loads(clean)
    except:
        return {"decision": "Error", "reason": "AI Connection Issue", "conf": "0%", "age": "N/A", "proc": "N/A"}

# ---------------- UI: HOME DASHBOARD ----------------
st.title(L["title"])

with st.container():
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader(f"🔍 {L['how']}")
        for step in L["steps"]:
            st.write(f"🔹 **{step}**")
    with c2:
        st.markdown("### 💡 Example Questions")
        for ex in L["examples"]:
            st.info(ex)

st.divider()

if not model:
    st.error("🚨 AI Handshake Failed. Verify API Key permissions.")
    st.stop()

# ---------------- MAIN TABS ----------------
t1, t2, t3 = st.tabs(["📄 Document Center", "🧠 AI Analysis Deep-Dive", "📜 History & Stats"])

with t1:
    up = st.file_uploader(L["upload_lbl"], type="pdf")
    if up: 
        st.session_state.pdf_text = extract_text(up)
        st.success("Policy Data Authenticated")
    
    q = st.text_input(L["query_lbl"], placeholder="Type here...")
    if st.button("🚀 Execute Analysis"):
        if st.session_state.pdf_text and q:
            with st.spinner("Processing Policy..."):
                res = analyze_claim(q, st.session_state.pdf_text, sel_lang)
                st.session_state.latest = res
                st.session_state.history.append(res)
                st.toast("Analysis Successful!")
        else: st.warning("Please upload a policy and enter a claim detail.")

with t2:
    if st.session_state.latest:
        r = st.session_state.latest
        color = "#10B981" if r["decision"] in ["Approved", "ಅನುಮೋದಿಸಲಾಗಿದೆ", "स्वीकृत"] else "#EF4444"
        
        st.markdown(f"""
        <div style="border-left: 10px solid {color}; background-color: #0F1217; padding: 30px; border-radius: 12px; margin-bottom: 25px;">
            <h1 style="color: {color} !important; margin: 0;">{r['decision']}</h1>
            <p style="color: #D1D5DB; font-size: 1.2em; margin-top: 10px;">{r['reason']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Metric Grid
        m_cols = st.columns(4)
        m_data = [r["decision"], r["conf"], r["age"], r["proc"]]
        m_lbls = ["Decision Status", "AI Confidence", "Policy Context", "Detected Procedure"]
        for i, col in enumerate(m_cols):
            with col:
                st.markdown(f"""
                <div class="stat-card">
                    <div style="color: #9CA3AF; font-size: 0.8em; text-transform: uppercase;">{m_lbls[i]}</div>
                    <div style="font-size: 1.6em; font-weight: bold; color: #60A5FA; margin-top:5px;">{m_data[i]}</div>
                </div>
                """, unsafe_allow_html=True)
    else: st.info("Results will appear here after analysis.")

with t3:
    # --- Statistics Analytics ---
    total = len(st.session_state.history)
    appr = sum(1 for x in st.session_state.history if x['decision'] in ["Approved", "ಅನುಮೋದಿಸಲಾಗಿದೆ", "स्वीकृत"])
    rej = total - appr

    st.markdown(f"### 📈 {L['stats'][0]}")
    sc1, sc2, sc3 = st.columns(3)
    with sc1: st.markdown(f'<div class="stat-card"><div style="color:#9CA3AF;">{L["stats"][0]}</div><div style="font-size:2.5em; font-weight:bold;">{total}</div></div>', unsafe_allow_html=True)
    with sc2: st.markdown(f'<div class="stat-card"><div style="color:#9CA3AF;">{L["stats"][1]}</div><div style="font-size:2.5em; font-weight:bold; color:#10B981;">{appr}</div></div>', unsafe_allow_html=True)
    with sc3: st.markdown(f'<div class="stat-card"><div style="color:#9CA3AF;">{L["stats"][2]}</div><div style="font-size:2.5em; font-weight:bold; color:#EF4444;">{rej}</div></div>', unsafe_allow_html=True)

    st.divider()
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history)):
            with st.expander(f"Case #{total-i} | {item['proc']} | {item['decision']}"):
                st.write(f"**Justification:** {item['reason']}")
                st.write(f"**Certainty:** {item['conf']}")
    else:
        st.info("No historical analyses found.")
