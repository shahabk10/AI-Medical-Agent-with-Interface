import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from gtts import gTTS
from streamlit_option_menu import option_menu
from PIL import Image
import io
import datetime
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Sehat Sahulat Pro",
    page_icon="🏥",
    layout="wide"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stChatMessage { border-radius: 15px; border: 1px solid #e0e0e0; }
    div.stButton > button { 
        background-color: #FF4B4B; color: white; border-radius: 10px; width: 100%;
    }
    div.stButton > button:hover { background-color: #FF0000; color: white; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR & SETUP ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063176.png", width=80)
    st.title("🏥 Sehat Sahulat")
    api_key = st.text_input("🔑 API Key:", type="password")
    
    st.subheader("Patient Profile")
    p_name = st.text_input("Name", "Guest Patient")
    p_age = st.text_input("Age", "25")
    p_gender = st.selectbox("Gender", ["Male", "Female"])

# --- PDF GENERATOR FUNCTION (STRUCTURED) ---
def create_structured_prescription(user_text, ai_response):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "SEHAT SAHULAT - MEDICAL REPORT", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, "AI Powered Medical Assistant | Date: " + datetime.datetime.now().strftime("%Y-%m-%d"), ln=True, align='C')
    pdf.line(10, 30, 200, 30)
    pdf.ln(10)
    
    # Patient Details
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "PATIENT DETAILS:", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, f"Name: {p_name}  |  Age: {p_age}  |  Gender: {p_gender}", ln=True)
    pdf.ln(5)
    
    # Section 1: Symptoms
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. REPORTED SYMPTOMS / QUERY:", ln=True, fill=True)
    pdf.set_font("Arial", size=11)
    # Sanitize and write user text
    safe_user_text = user_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, safe_user_text)
    pdf.ln(5)
    
    # Section 2: AI Diagnosis & Advice
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. DIAGNOSIS, DIET & MEDICINE:", ln=True, fill=True)
    pdf.set_font("Arial", size=11)
    # Sanitize and write AI text
    safe_ai_text = ai_response.replace("*", "").encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, safe_ai_text)
    pdf.ln(10)
    
    # Disclaimer
    pdf.set_text_color(255, 0, 0)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, "DISCLAIMER: This is an AI-generated report. Please consult a real doctor for emergencies.", ln=True, align='C')
    
    return pdf.output(dest="S").encode("latin-1")

# --- AI MODEL FUNCTION (WITH FALLBACK) ---
def get_response(prompt, image=None):
    if not api_key: return "⚠️ Please enter API Key."
    
    genai.configure(api_key=api_key)
    
    sys_prompt = f"""
    Act as a Doctor. Patient: {p_name}, {p_age} years, {p_gender}.
    Task: Analyze the symptoms: '{prompt}'.
    
    Provide output in this EXACT structure:
    1. **Possible Cause:** (Short explanation)
    2. **Recommended Diet:** (What to eat/avoid)
    3. **Daily Routine:** (Rest/Exercise guidelines)
    4. **Suggested Medicines:** (Generic names only with dosage)
    
    Keep it strictly medical.
    """
    
    # Try Flash Model first, if fails, use Pro
    try:
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=sys_prompt)
        if image:
            response = model.generate_content([prompt, image])
        else:
            response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        try:
            # Fallback to older model if Flash fails
            model = genai.GenerativeModel("gemini-pro") 
            # Pro doesn't support system_instruction easily in old versions, so we append to prompt
            full_prompt = sys_prompt + "\n\nUser Query: " + prompt
            if image:
                return "Error: Image not supported in fallback mode. Please use text."
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e2:
            return f"Error: {str(e2)}. Please check your API Key."

# --- MAIN APP UI ---
st.title("🏥 Sehat Sahulat - Intelligent Prescription System")

# Chat Container
if "history" not in st.session_state:
    st.session_state.history = []
if "last_advice" not in st.session_state:
    st.session_state.last_advice = None
if "last_query" not in st.session_state:
    st.session_state.last_query = None

# Show History
for role, text in st.session_state.history:
    with st.chat_message(role):
        st.markdown(text)

# Input Area
with st.container():
    uploaded_file = st.file_uploader("Upload Report/Image (Optional)", type=["jpg", "png"])
    user_input = st.chat_input("Apni bimari ya symptoms batayein (e.g. Bukhar aur sar dard)...")

    if user_input:
        # User Message
        st.session_state.history.append(("user", user_input))
        with st.chat_message("user"):
            st.markdown(user_input)
            
        # Image Processing
        img = Image.open(uploaded_file) if uploaded_file else None
        
        # AI Response
        with st.spinner("Dr. AI report tayyar kar rahe hain..."):
            advice = get_response(user_input, img)
        
        # Assistant Message
        st.session_state.history.append(("assistant", advice))
        with st.chat_message("assistant"):
            st.markdown(advice)
            
        # Store for PDF
        st.session_state.last_query = user_input
        st.session_state.last_advice = advice
        st.rerun() # Refresh to show button

# --- DOWNLOAD BUTTON SECTION ---
# Ye button hamesha latest advice ke baad dikhega
if st.session_state.last_advice:
    st.markdown("### 📥 Download Prescription")
    st.info("Download your official AI Medical Report below:")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        pdf_bytes = create_structured_prescription(st.session_state.last_query, st.session_state.last_advice)
        
        st.download_button(
            label="📄 CLICK HERE TO DOWNLOAD PDF REPORT",
            data=pdf_bytes,
            file_name=f"Prescription_{p_name}.pdf",
            mime="application/pdf",
        )
