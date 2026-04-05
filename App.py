import streamlit as st
import google.generativeai as genai
import PyPDF2
import re
import json

# ---------------- CONFIG & OBSIDIAN DARK CSS ----------------
st.set_page_config(page_title="PolicyMind Pro", layout="wide", page_icon="🧠")

st.markdown("""
    <style>
    /* Obsidian Pro Theme */
    .stApp {
        background-color: #080A0D;
        color: #E5E7EB;
    }
    /* Sleek Cards */
    .css-1r6slb0, .stExpander, .metric-container {
        background-color: #0F1217 !important;
        border: 1px solid #1F2937 !important;
        border-radius: 12px !important;
        padding: 20px !important;
    }
    /* Neon Accents */
    h1, h2, h3 { color: #60A5FA !important; }
    .stButton>button {
        background: linear-gradient(90deg, #1D4ED8, #2563EB);
        color: white; border: none; border-radius: 8px;
        padding: 10px 24px; transition: 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0px 0px 15px rgba(37, 99, 235, 0.4);
        transform: translateY(-2px);
    }
    /* Metric Cards */
    .stat-card {
        background: #111827;
        border: 1px solid #1F2937;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
    }
    .stat-val { font-size: 32px; font-weight: bold; margin-bottom: 5px; }
    .stat-label { color: #9CA3AF; font-size: 14px; text-transform: uppercase; }
    
    /* Clean Tabs */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
    .stTabs [data-baseweb="tab"] { color: #9CA3AF; }
    .stTabs [aria-selected="true"] { color: #60A5FA !important; border-bottom-color: #60A5FA !important; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- API & MODEL ----------------
API_KEY = st.secrets.get("GEMINI_API_KEY")
if not API_KEY:
    st.error("❌ GEMINI_API_KEY Missing")
    st.stop()

genai.configure(api_key=API_KEY)

@st.cache_resource
def load_model():
    for name in ["gemini-3-flash", "gemini-2.5-flash", "gemini-1.5-flash"]:
        try:
            m = genai.GenerativeModel(name)
            m.generate_content("hi", generation_config={"max_output_tokens": 1})
            return m
        except: continue
    return None

model = load_model()

# ---------------- TRANSLATIONS ----------------
LANG = {
    "English": {
        "welcome": "Welcome to PolicyMind Pro",
        "how": "How to use",
        "steps": ["Upload your PDF Policy", "Type your medical query", "Get instant AI validation"],
        "examples_label": "💡 Try these examples:",
        "examples": ["I have a dental checkup after 6 months, is it covered?", "Is emergency appendectomy covered for a 25-year-old?"],
        "stats": ["Total Requests", "Approved", "Rejected"],
        "analysis": "AI Deep Analysis",
        "history": "Analytics & History"
    },
    "Hindi": {
        "welcome": "पॉलिसीमाइंड प्रो में आपका स्वागत है",
        "how": "कैसे उपयोग करें",
        "steps": ["अपनी PDF पॉलिसी अपलोड करें", "अपनी मेडिकल समस्या लिखें", "AI से तुरंत निर्णय लें"],
        "examples_label": "💡 इन उदाहरणों को आजमाएं:",
        "examples": ["6 महीने बाद मेरा डेंटल चेकअप है, क्या यह कवर है?", "क्या 25 साल के व्यक्ति के लिए इमरजेंसी अपेंडक्टोमी कवर है?"],
        "stats": ["कुल अनुरोध", "स्वीकृत", "अस्वीकृत"],
        "analysis": "AI गहरा विश्लेषण",
        "history": "एनालिटिक्स और इतिहास"
    },
    "Kannada": {
        "welcome": "ಪಾಲಿಸಿಮೈಂಡ್ ಪ್ರೊಗೆ ಸುಸ್ವಾಗತ",
        "how": "ಬಳಸುವುದು ಹೇಗೆ",
        "steps": ["ನಿಮ್ಮ PDF ಪಾಲಿಸಿಯನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ", "ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಿ", "AI ತೀರ್ಮಾನವನ್ನು ಪಡೆಯಿರಿ"],
        "examples_label": "💡 ಈ ಉದಾಹರಣೆಗಳನ್ನು ಪ್ರಯತ್ನಿಸಿ:",
        "examples": ["6 ತಿಂಗಳ ನಂತರ ನನಗೆ ಹಲ್ಲಿನ ತಪಾಸಣೆ ಇದೆ, ಅದು ಕವರ್ ಆಗುತ್ತದೆಯೇ?", "25 ವರ್ಷದ ವ್ಯಕ್ತಿಗೆ ತುರ್ತು ಅಪೆಂಡೆಕ್ಟೊಮಿ ಕವರ್ ಆಗುತ್ತದೆಯೇ?"],
        "stats": ["ಒಟ್ಟು ವಿನಂತಿಗಳು", "ಅನುಮೋದಿಸಲಾಗಿದೆ", "ತಿರಸ್ಕರಿಸಲಾಗಿದೆ"],
        "analysis": "AI ಆಳವಾದ ವಿಶ್ಲೇಷಣೆ",
        "history": "ಅನಾಲಿಟಿಕ್ಸ್ ಮತ್ತು ಇತಿಹಾಸ"
    }
}

# ---------------- SIDEBAR & STATE ----------------
sel_lang = st.sidebar.selectbox("🌐 UI Language", ["English", "Hindi", "Kannada"])
T = LANG[sel_lang]

if "history" not in st.session_state: st.session_state.history = []
if "pdf_text" not in st.session_state: st.session_state.pdf_text = ""
if "latest" not in st.session_state: st.session_state.latest = None

# ---------------- LOGIC ----------------
def get_pdf_text(file):
    reader = PyPDF2.PdfReader(file)
    return "\n".join([p.extract_text() or "" for p in reader.pages])

def process_ai(query, context, lang):
    prompt = f"""
    Context: {context[:12000]}
    Query: {query}
    Respond in {lang}. Output ONLY a JSON:
    {{"decision": "Approved/Rejected", "reason": "why", "confidence": "X%", "age": "X", "proc": "X"}}
    """
    try:
        raw = model.generate_content(prompt).text
        clean = raw.replace('```json', '').replace('```', '').strip()
        return json.loads(clean)
    except:
        return {"decision": "Error", "reason": "Failed to parse", "confidence": "0%", "age": "N/A", "proc": "N/A"}

# ---------------- UI: HOME ----------------
st.title(T["welcome"])

c1, c2 = st.columns([2, 1])
with c1:
    st.markdown(f"### {T['how']}")
    for step in T["steps"]:
        st.write(f"🔹 {step}")
with c2:
    st.markdown(f"#### {T['examples_label']}")
    for ex in T["examples"]:
        st.info(ex)

st.divider()

# ---------------- TABS ----------------
tab1, tab2, tab3 = st.tabs(["📄 Document Center", "🧠 " + T["analysis"], "📊 " + T["history"]])

with tab1:
    up = st.file_uploader("Drop your PDF Policy here", type="pdf")
    if up: 
        st.session_state.pdf_text = get_pdf_text(up)
        st.success("Policy Authenticated")
    
    q = st.text_input("Describe the medical scenario:")
    if st.button("🚀 Execute Analysis"):
        if st.session_state.pdf_text and q:
            with st.spinner("AI Engine Processing..."):
                res = process_ai(q, st.session_state.pdf_text, sel_lang)
                st.session_state.latest = res
                st.session_state.history.append(res)
        else: st.warning("Upload PDF and enter a query.")

with tab2:
    if st.session_state.latest:
        res = st.session_state.latest
        # Decision Card
        status_color = "#10B981" if res["decision"] in ["Approved", "स्वीकृत", "ಅನುಮೋದಿಸಲಾಗಿದೆ"] else "#EF4444"
        st.markdown(f"""
        <div style="border-left: 8px solid {status_color}; background: #111827; padding: 25px; border-radius: 12px; margin-bottom: 25px;">
            <h2 style="margin:0; color:{status_color} !important;">{res['decision']}</h2>
            <p style="font-size: 1.1em; color: #D1D5DB; margin-top:10px;">{res['reason']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Metrics
        cols = st.columns(4)
        m_vals = [res["decision"], res["confidence"], res["age"], res["proc"]]
        m_keys = ["Status", "Certainty", "Policy Age", "Procedure"]
        for i, col in enumerate(cols):
            with col:
                st.markdown(f"""
                <div class="stat-card">
                    <div class="stat-label">{m_keys[i]}</div>
                    <div class="stat-val" style="color:#60A5FA;">{m_vals[i]}</div>
                </div>
                """, unsafe_allow_html=True)
    else: st.info("Run analysis to see results.")

with tab3:
    # Stats Summary
    total = len(st.session_state.history)
    appr = sum(1 for x in st.session_state.history if x['decision'] in ["Approved", "स्वीकृत", "ಅನುಮೋದಿಸಲಾಗಿದೆ"])
    rej = total - appr
    
    st.markdown("### Coverage Insights")
    st1, st2, st3 = st.columns(3)
    st1.markdown(f'<div class="stat-card"><div class="stat-label">{T["stats"][0]}</div><div class="stat-val">{total}</div></div>', unsafe_allow_html=True)
    st2.markdown(f'<div class="stat-card"><div class="stat-label">{T["stats"][1]}</div><div class="stat-val" style="color:#10B981;">{appr}</div></div>', unsafe_allow_html=True)
    st3.markdown(f'<div class="stat-card"><div class="stat-label">{T["stats"][2]}</div><div class="stat-val" style="color:#EF4444;">{rej}</div></div>', unsafe_allow_html=True)
    
    st.divider()
    for i, item in enumerate(reversed(st.session_state.history)):
        with st.expander(f"Analysis #{total-i} | {item['proc']} | {item['decision']}"):
            st.write(f"**Justification:** {item['reason']}")
            st.write(f"**Reliability:** {item['confidence']}")
