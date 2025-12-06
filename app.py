import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
from fpdf import FPDF
import io
import re
import os

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(page_title="MedCore-AI (Pakistan Edition)", page_icon="🇵🇰", layout="wide")

# API KEY SETUP
# Yahan apni actual Gemini API Key paste karein
os.environ["GOOGLE_API_KEY"] = "YOUR_GEMINI_API_KEY_HERE" 
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# --- 2. ADVANCED SYSTEM PROMPT (With 1122 Instruction) ---
SYSTEM_PROMPT = """
You are 'MedCore-AI', a Clinical AI Assistant customized for Pakistan. 
You adhere to WHO & Ministry of Health guidelines.

YOUR CORE PROTOCOLS:
1.  **Emergency Handling:** If user mentions heart attack, severe trauma, suicide, stroke, or heavy bleeding, YOU MUST START your response with: "🚨 EMERGENCY: PLEASE CALL 1122 IMMEDIATELY."
2.  **Language:** Respond in the language user uses (English or Roman Urdu).
3.  **Structure:** Use Markdown headers (Status, Summary, Differential Diagnosis, Plan).
4.  **No Prescriptions:** Do NOT prescribe specific meds. Suggest generic classes or "Consult Doctor".
5.  **Tone:** Professional, empathetic, and clear.

FORMAT:
#### 1. 🚨 TRIAGE STATUS
[Green/Yellow/Red] - [One line action]

#### 2. 📋 CLINICAL ANALYSIS
[Findings summary]

#### 3. 🧠 DIFFERENTIAL DIAGNOSIS
[List of possible conditions]

#### 4. 🇵🇰 LOCAL GUIDANCE
[Next steps, relevant specialist in Pakistan]
"""

model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)

# --- 3. HELPER FUNCTIONS ---

# Function A: Check for Emergency Keywords (Python Side for Speed)
def check_emergency(text):
    keywords = ["heart attack", "chest pain", "dard", "accident", "suicide", "khoon", "bleeding", "saans", "breath", "poison", "zehar", "behosh"]
    for word in keywords:
        if word in text.lower():
            return True
    return False

# Function B: Generate Voice (TTS)
def text_to_speech(text):
    # Cleaning markdown symbols for better audio
    clean_text = text.replace("*", "").replace("#", "").replace("-", "")
    tts = gTTS(text=clean_text, lang='en', tld='com') # 'en' reads Roman Urdu surprisingly well
    
    # Save to buffer/file
    audio_file = "response_audio.mp3"
    tts.save(audio_file)
    return audio_file

# Function C: Generate PDF Report
def create_pdf(user_input, ai_response):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="MedCore-AI Medical Report", ln=True, align='C')
    pdf.ln(10)
    
    # Disclaimer
    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(200, 0, 0)
    pdf.multi_cell(0, 10, txt="DISCLAIMER: This is an AI-generated report for informational purposes. Not a legal medical prescription. Call 1122 for emergencies.")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # User Input Section
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Patient Complaint / Input:", ln=True)
    pdf.set_font("Arial", '', 11)
    # Handling unicode issues by basic encoding (FPDF standard has limits with Urdu script, good for Roman/English)
    safe_input = user_input.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, txt=safe_input)
    pdf.ln(5)
    
    # AI Analysis Section
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Clinical Assessment:", ln=True)
    pdf.set_font("Arial", '', 10)
    
    # Strip markdown specific chars for cleaner PDF text
    clean_response = ai_response.replace("#", "").replace("*", "")
    safe_response = clean_response.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, txt=safe_response)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 4. MAIN UI LAYOUT ---

st.title("🩺 MedCore-AI (Pakistan)")
st.caption("AI Health Assistant | Emergency: 1122 | Voice Enabled | PDF Reports")

# Sidebar
with st.sidebar:
    st.header("Upload Data")
    uploaded_file = st.file_uploader("X-Ray / Lab Report", type=["jpg", "png", "pdf"])
    st.info("ℹ️ Note: Voice play karne ke liye response ke baad audio player check karein.")

# Initialize Chat
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_response" not in st.session_state:
    st.session_state.last_response = None

# Display History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
user_input = st.chat_input("Apni alamaat likhein (e.g., seenay main dard hai)...")

if user_input:
    # 1. User Message Display
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Emergency Check (Immediate UI Feedback)
    is_emergency = check_emergency(user_input)
    if is_emergency:
        st.error("🚨 EMERGENCY DETECTED! (High Risk Keywords Found)")
        st.markdown("""
            <div style="background-color:#ffcccc; padding:15px; border-radius:10px; border:2px solid red;">
                <h3 style="color:red; margin:0;">🚑 CALL 1122 IMMEDIATELY</h3>
                <p>You have mentioned symptoms that require urgent attention in Pakistan.</p>
            </div>
        """, unsafe_allow_html=True)

    # 3. Prepare AI Inputs
    inputs = [user_input]
    if uploaded_file:
        try:
            image = Image.open(uploaded_file)
            inputs.append(image)
            st.sidebar.image(image, caption="Uploaded Scan")
        except:
            st.warning("PDF parsing is complex, strictly using text analysis for now.")

    # 4. Generate AI Response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing symptoms & Guidelines..."):
            try:
                response = model.generate_content(inputs)
                bot_text = response.text
                
                # Show Text
                st.markdown(bot_text)
                st.session_state.messages.append({"role": "assistant", "content": bot_text})
                st.session_state.last_response = bot_text
                
                # --- AUDIO GENERATION ---
                audio_path = text_to_speech(bot_text)
                st.audio(audio_path, format='audio/mp3')

            except Exception as e:
                st.error(f"Error: {e}")

# --- 5. PDF DOWNLOAD SECTION ---
if st.session_state.last_response:
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.write("📥 **Save Consultation Record**")
    with col2:
        # Generate PDF bytes
        pdf_bytes = create_pdf(st.session_state.messages[-2]['content'], st.session_state.last_response)
        
        st.download_button(
            label="📄 Download Medical Report (PDF)",
            data=pdf_bytes,
            file_name="MedCore_Report.pdf",
            mime="application/pdf"
        )
