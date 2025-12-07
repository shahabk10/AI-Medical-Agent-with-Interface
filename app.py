import streamlit as st
import os
from groq import Groq
from fpdf import FPDF
from streamlit_option_menu import option_menu
import plotly.graph_objects as go
from PIL import Image
import base64
import io
import datetime

# --- 1. PAGE SETUP ---
st.set_page_config(
    page_title="MediPro - Powered by Llama 3",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS STYLING ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    .css-card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .stChatMessage { border-radius: 15px; background-color: white; border: 1px solid #eee; }
    div.stButton > button { background-color: #f25c54; color: white; border-radius: 8px; border: none; }
    div.stButton > button:hover { background-color: #d94139; }
</style>
""", unsafe_allow_html=True)

# --- 3. API CLIENT SETUP ---
try:
    # Secrets se key uthayega
    api_key = st.secrets["GROQ_API_KEY"]
    client = Groq(api_key=api_key)
except Exception:
    st.error("⚠️ Error: Please add 'GROQ_API_KEY' to Streamlit Secrets.")
    st.stop()

# --- 4. SESSION STATE ---
if "history" not in st.session_state: st.session_state.history = []
if "user_data" not in st.session_state: st.session_state.user_data = {"name": "Guest", "age": "--", "gender": "--"}

# --- 5. HELPER FUNCTIONS ---

# Image ko Base64 mein convert karne ke liye (Groq requirement)
def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def get_groq_response(prompt, image=None):
    sys_msg = f"""
    You are 'MediPro AI', an expert medical assistant.
    Patient: {st.session_state.user_data['name']}, Age: {st.session_state.user_data['age']}.
    Rules:
    1. Answer only medical queries.
    2. Provide Diagnosis, Diet (in bullet points), and Generic Medicine.
    3. Be professional and strictly concise.
    """
    
    messages = [
        {"role": "system", "content": sys_msg}
    ]

    if image:
        # Agar image hai to Vision model use hoga
        base64_image = encode_image(image)
        user_content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
        messages.append({"role": "user", "content": user_content})
        model_id = "llama-3.2-11b-vision-preview" # Vision Model
    else:
        # Text only model
        messages.append({"role": "user", "content": prompt})
        model_id = "llama-3.1-70b-versatile" # Super Smart Text Model

    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_id,
            temperature=0.5,
            max_tokens=1024,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def create_pdf(chat_history):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "MediPro AI Medical Report", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Patient: {st.session_state.user_data['name']} | Date: {datetime.datetime.now().strftime('%Y-%m-%d')}", ln=True)
    pdf.line(10, 35, 200, 35)
    pdf.ln(10)
    
    for role, text in chat_history:
        # Sanitize text for PDF (Basic Latin encoding)
        clean_text = text.encode('latin-1', 'replace').decode('latin-1')
        prefix = "PATIENT: " if role == "user" else "AI DOCTOR: "
        pdf.set_font("Arial", 'B', 11) if role == "assistant" else pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 8, prefix + clean_text)
        pdf.ln(2)
        
    return pdf.output(dest="S").encode("latin-1")

# --- 6. SIDEBAR ---
with st.sidebar:
    st.title("⚡ MediPro (Llama 3)")
    selected = option_menu(
        menu_title=None,
        options=["Profile", "Consultation"],
        icons=["person", "heart-pulse"],
        default_index=1,
    )
    
    if st.button("Clear Chat"):
        st.session_state.history = []
        st.rerun()

# --- 7. MAIN PAGES ---

if selected == "Profile":
    st.header("👤 Patient Profile")
    with st.form("profile"):
        name = st.text_input("Name", st.session_state.user_data['name'])
        age = st.text_input("Age", st.session_state.user_data['age'])
        gender = st.selectbox("Gender", ["Male", "Female"])
        if st.form_submit_button("Update"):
            st.session_state.user_data = {"name": name, "age": age, "gender": gender}
            st.success("Profile Updated!")

elif selected == "Consultation":
    st.header("🩺 Instant AI Diagnosis")
    
    # Chat History
    for role, text in st.session_state.history:
        avatar = "🤖" if role == "assistant" else "👤"
        with st.chat_message(role, avatar=avatar):
            st.markdown(text)
            
    # Input Area
    with st.container():
        col1, col2 = st.columns([1, 10])
        with col1:
            uploaded_file = st.file_uploader("📷", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
        with col2:
            user_input = st.chat_input("Symptoms batayein...")
            
        if user_input:
            # User Msg
            st.session_state.history.append(("user", user_input))
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_input)
            
            # Image Check
            image_data = None
            if uploaded_file:
                image_data = Image.open(uploaded_file)
                st.image(image_data, caption="Analyzing Image...", width=200)
                user_input = f"Analyze this medical image: {user_input}"
            
            # AI Response
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Connecting to Llama 3..."):
                    response = get_groq_response(user_input, image_data)
                    st.markdown(response)
                    st.session_state.history.append(("assistant", response))
                    st.rerun()

    # PDF Download
    if st.session_state.history:
        st.markdown("---")
        pdf_data = create_pdf(st.session_state.history)
        st.download_button("📥 Download Report PDF", pdf_data, "Medical_Report.pdf", "application/pdf")
