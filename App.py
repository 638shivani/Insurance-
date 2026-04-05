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
    .stApp, div[data-testid="stSidebar"] {
        background-color: #080A0D;
        color: #E5E7EB;
    }
    /* Selectbox Dropdown Container Styling - Matches Image 2 */
    .stSelectbox > div[data-baseweb="select"] {
        background-color: #111827 !important;
        border: 1px solid #30363D !important;
        border-radius: 8px;
    }
    /* Selectbox Dropdown Value Text (White Text) */
    .stSelectbox div[data-testid="stMarkdownContainer"] p {
        color: #E5E7EB !important;
    }
    /* Selectbox Arrow Color */
    .stSelectbox svg { color: #60A5FA !important; }

    /* Sleek Obsidian Cards */
    .metric-container, div.stExpander, div.stButton button {
        background-color: #0F1217 !important;
        border: 1px solid #1F2937 !important;
        border-radius: 12px !important;
        padding: 15px !important;
    }
    /* Input Fields (Ask a Question) */
    div.stTextInput input {
        background-color: #0F1217;
        color: white; border-color: #30363D;
        border-radius: 8px;
    }
    div.stTextInput input:focus {
        border-color: #58A6FF;
    }

    /* Metric Cards Styling */
    .stat-card {
        background: #111827; border: 1px solid #1F2937;
        padding: 20px; border-radius: 15px; text-align: center;
    }
    .stat-val { font-size: 32px; font-weight: bold; margin-bottom: 5px; color: #58A6FF; }
    .stat-label { color: #9CA3AF; font-size: 14px; text-transform: uppercase; }
    
    /* Neon Accents and Headers */
    h1, h2, h3, h4 { color: #60A5FA !important; }
    div[data-testid="stMetricValue"] { color: #58A6FF; }
    div[data-testid="toast-container"] { background-color: #111827; }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
    .stTabs [data-baseweb="tab"] { color: #9CA3AF; }
    .stTabs [aria-selected="true"] { color: #60A5FA !important; border-bottom-color: #60A5FA !important; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- API SETUP ----------------
API_KEY = st.secrets.get("GEMINI_API_KEY")
if not API_KEY:
    st.error("❌ GEMINI_API_KEY is missing from Streamlit Secrets.")
    st.stop()

genai.configure(api_key=API_KEY)

# ---------------- ROBUST 2026 MODEL LOADER (ERROR FIX) ----------------
@st.cache_resource
def load_working_model():
    """ 
    Tries stable model names for 2026 to prevent 404 errors. 
    Returns: (Model Object, Error Message)
    """
    latest_models = ["gemini-3-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-pro"]
    
    last_error = "No models attempted"
    for name in latest_models:
        try:
            m = genai.GenerativeModel(name)
            # Health check generation
            m.generate_content("healthcheck", generation_config={"max_output_tokens": 1})
            return m, None
        except Exception as e:
            last_error = str(e)
            continue
    return None, last_error

# Attempt to load the model
model, connection_error = load_working_model()

# ---------------- LANGUAGES DICTIONARY ----------------
LANG = {
    "English": {
        "title": "🧠 PolicyMind Pro",
        "labels": ["Decision", "Certainty", "Policy Age", "Procedure"],
        "history_tab": "📜 Analytics & History",
        "ai_tab": "🧠 AI Analysis Deep Dive",
        "analyze_btn": "🚀 Analyze Coverage",
        "upload_doc": "Upload Insurance Policy (PDF)",
        "ask_label": "Describe the medical scenario:",
        "placeholder": "e.g., I have had this policy for 2 years, is dental checkup covered?",
        "history_title": "Coverage Insights (Analytics Summary)",
        "stats": ["Total Requests", "Approved", "Rejected"],
        "how_works": "🔍 How PolicyMind Pro Works",
        "steps": ["Upload your PDF Policy", "Ask a medical question", "Get instance AI validation"]
    },
    "Hindi": {
        "title": "🧠 पॉलिसीमाइंड प्रो (PolicyMind Pro)",
        "labels": ["निर्णय", "विश्वास", "पॉलिसी की आयु", "प्रक्रिया"],
        "history_tab": "📜 एनालिटिक्स और इतिहास",
        "ai_tab": "🧠 AI विश्लेषण डीप डाइव",
        "analyze_btn": "🚀 कवरेज विश्लेषण",
        "upload_doc": "बीमा पॉलिसी (PDF) अपलोड करें",
        "ask_label": "चिकित्सा परिदृश्य का वर्णन करें:",
        "placeholder": "उदाहरण के लिए, मेरे पास यह पॉलिसी 2 वर्षों से है, क्या डेंटल चेकअप कवर है?",
        "history_title": "कवरेज अंतर्दृष्टि (एनालिटिक्स सारांश)",
        "stats": ["कुल अनुरोध", "स्वीकृत", "अस्वीकृत"],
        "how_works": "🔍 पॉलिसीमाइंड प्रो कैसे काम करता है",
        "steps": ["अपनी PDF पॉलिसी अपलोड करें", "एक चिकित्सा प्रश्न पूछें", "AI निर्णय प्राप्त करें"]
    },
    "Kannada": {
        "title": "🧠 ಪಾಲಿಸಿಮೈಂಡ್ ಪ್ರೊ (PolicyMind Pro)",
        "labels": ["ತೀರ್ಮಾನ", "ನಂಬಿಕೆ", "ಪಾಲಿಸಿ ಅವಧಿ", "ಕಾರ್ಯವಿಧಾನ"],
        "history_tab": "📜 ಅನಾಲಿಟಿಕ್ಸ್ ಮತ್ತು ಇತಿಹಾಸ",
        "ai_tab": "🧠 AI ವಿಶ್ಲೇಷಣೆಯ ಆಳವಾದ ಡೈವ್",
        "analyze_btn": "🚀 ಕವರೇಜ್ ವಿಶ್ಲೇಷಣೆ ನಡೆಸಿ",
        "upload_doc": "ವಿಮಾ ಪಾಲಿಸಿ (PDF) ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
        "ask_label": "ವೈದ್ಯಕೀಯ ಸನ್ನಿವೇಶವನ್ನು ವಿವರಿಸಿ:",
        "placeholder": "ಉದಾಹರಣೆಗೆ, ನನ್ನ ಬಳಿ ಈ ಪಾಲಿಸಿ 2 ವರ್ಷಗಳಿಂದ ಇದೆ, ಹಲ್ಲಿನ ತಪಾಸಣೆ ಕವರ್ ಆಗುತ್ತದೆಯೇ?",
        "history_title": "ಕವರೇಜ್ ಒಳನೋಟಗಳು (ಅನಾಲಿಟಿಕ್ಸ್ ಸಾರಾಂಶ)",
        "stats": ["ಒಟ್ಟು ವಿನಂತಿಗಳು", "ಅನುಮೋದಿಸಲಾಗಿದೆ", "ತಿರಸ್ಕರಿಸಲಾಗಿದೆ"],
        "how_works": "🔍 ಪಾಲಿಸಿಮೈಂಡ್ ಪ್ರೊ ಹೇಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ",
        "steps": ["ನಿಮ್ಮ PDF ಪಾಲಿಸಿಯನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ", "ವೈದ್ಯಕೀಯ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ", "AI ತೀರ್ಮಾನವನ್ನು ಪಡೆಯಿರಿ"]
    }
}

# ---------------- SIDEBAR: LANGUAGE SELECTION ----------------
# Dropdown style defined in CSS above (data-baseweb="select")
st.sidebar.markdown("### UI Controls")
selected_lang = st.sidebar.selectbox("🌐 Select Interface Language", ["English", "Hindi", "Kannada"])
T = LANG[selected_lang]

# ---------------- SESSION STATE ----------------
if "history" not in st.session_state: st.session_state.history = []
if "pdf_text" not in st.session_state: st.session_state.pdf_text = ""
if "latest" not in st.session_state: st.session_state.latest = None

# ---------------- LOGIC ----------------
def extract_pdf_text(file):
    reader = PyPDF2.PdfReader(file)
    return "\n".join([p.extract_text() or "" for p in reader.pages])

def generate_ai_analysis(query, context, lang):
    """ Instructs Gemini to return structured JSON for metrics display """
    prompt = f"""
    Context: {context[:12000]}
    Query: {query}
    Respond in {lang}. 
    Output ONLY a clean JSON object (no markdown formatting):
    {{
        "decision": "Approved or Rejected",
        "reason": "Clear explanation",
        "confidence": "Estimation in %",
        "policy_age": "Detected age of policy",
        "procedure": "Detected medical procedure"
    }}
    """
    try:
        raw_response = model.generate_content(prompt).text
        # Safety for markdown code blocks
        json_clean = raw_response.replace('```json', '').replace('```', '').strip()
        return json.loads(json_clean)
    except Exception as e:
        return {"decision": "Error", "reason": str(e), "confidence": "0%", "policy_age": "N/A", "procedure": "N/A"}

# ---------------- UI: HOME DASHBOARD ----------------
st.title(T["title"])

with st.expander(T["how_works"], expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        for step in T["steps"]:
            st.write(f"🔹 {step}")
    with col2:
        st.info(f"💡 **Try an Example Question:**\n\n{T['placeholder']}")

st.divider()

# Connection Status Guard
if not model:
    st.error(f"🚨 AI Offline. Model handshake failed. | Last Error: {connection_error}")
    st.info("Check API Key permissions or Streamlit Cloud region settings.")
    st.stop()

# ---------------- MAIN TABS ----------------
tab1, tab2, tab3 = st.tabs(["📄 Document Center", "🧠 " + T["ai_tab"], "📊 " + T["history_tab"]])

with tab1:
    uploaded = st.file_uploader(T["upload_doc"], type="pdf")
    if uploaded:
        st.session_state.pdf_text = extract_pdf_text(uploaded)
        st.success("✅ Policy Indexed and Ready")

    user_query = st.text_input(T["ask_label"], placeholder=T["placeholder"])

    if st.button(T["analyze_btn"]):
        if not st.session_state.pdf_text or not user_query:
            st.warning("Please upload a policy and describe the medical scenario first.")
        else:
            with st.spinner("AI analyzing policy document..."):
                res = generate_ai_analysis(user_query, st.session_state.pdf_text, selected_lang)
                st.session_state.latest = res
                st.session_state.history.append(res)
                st.toast("Analysis Complete!")

with tab2:
    if st.session_state.latest:
        res = st.session_state.latest
        
        # Decision Banner
        decision_color = "#10B981" if res["decision"] in ["Approved", "स्वीकृत", "ಅನುಮೋದಿಸಲಾಗಿದೆ"] else "#EF4444"
        if res["decision"] == "Error": decision_color = "#F59E0B" # Orange for error

        st.markdown(f"""
        <div style="border-left: 10px solid {decision_color}; background-color: #111827; padding: 30px; border-radius: 12px; margin-bottom: 25px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
            <h1 style="color: {decision_color} !important; margin: 0;">{res['decision']}</h1>
            <p style="color: #E5E7EB; font-size: 1.2rem; margin-top: 10px;">{res['reason']}</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"### 📊 Analysis Metrics Summary")
        
        # Metric Grid (Styled obsidian cards)
        m_labels = T["labels"]
        col1, col2, col3, col4 = st.columns(4)
        
        # Metric 1: Status
        with col1:
            st.markdown(f'<div class="metric-container"><small style="color:#9CA3AF;">{m_labels[0]}</small><br><b style="font-size:1.8em; color:{decision_color};">{res["decision"]}</b></div>', unsafe_allow_html=True)
        # Metric 2: Confidence
        with col2:
            st.markdown(f'<div class="metric-container"><small style="color:#9CA3AF;">{m_labels[1]}</small><br><b style="font-size:1.8em; color:#58A6FF;">{res["confidence"]}</b></div>', unsafe_allow_html=True)
        # Metric 3: Age
        with col3:
            st.markdown(f'<div class="metric-container"><small style="color:#9CA3AF;">{m_labels[2]}</small><br><b style="font-size:1.8em; color:#E5E7EB;">{res["policy_age"]}</b></div>', unsafe_allow_html=True)
        # Metric 4: Procedure
        with col4:
            st.markdown(f'<div class="metric-container"><small style="color:#9CA3AF;">{m_labels[3]}</small><br><b style="font-size:1.8em; color:#E5E7EB;">{res["procedure"]}</b></div>', unsafe_allow_html=True)

    else:
        st.info("Results will appear here after you analyze your query.")

with tab3:
    st.subheader(T["history_title"])
    
    # Coverage Insights (Multilingual Counters)
    total = len(st.session_state.history)
    # Checks for Translated "Approved" across English, Hindi, and Kannada
    approved = sum(1 for x in st.session_state.history if x['decision'] in ["Approved", "स्वीकृत", "ಅನುಮೋದಿಸಲಾಗಿದೆ"])
    rejected = total - approved

    c1, c2, c3 = st.columns(3)
    # Analytics Metrics Cards
    with c1: st.markdown(f'<div class="stat-card"><div class="stat-label">{T["stats"][0]}</div><div class="stat-val">{total}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="stat-card"><div class="stat-label">{T["stats"][1]}</div><div class="stat-val" style="color:#10B981;">{approved}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="stat-card"><div class="stat-label">{T["stats"][2]}</div><div class="stat-val" style="color:#EF4444;">{rejected}</div></div>', unsafe_allow_html=True)
    
    st.divider()
    
    if st.session_state.history:
        for item in reversed(st.session_state.history):
            exp_color = "#10B981" if item["decision"] in ["Approved", "स्वीकृत", "ಅನುಮೋದಿಸಲಾಗಿದೆ"] else "#EF4444"
            with st.expander(f"🕒 {item['query'][:60]}... (Status: {item['decision']})"):
                st.write(f"**Question:** {item['query']}")
                st.write(f"**AI Decision:** {item['response']}") # Use item['response'] or parse from JSON entry
                # If parsed to historical data structure
                st.write(f"**Decision:** {item['decision']}")
                st.write(f"**Justification:** {item['reason']}")
    else:
        st.info("Historical data is currently empty.")
