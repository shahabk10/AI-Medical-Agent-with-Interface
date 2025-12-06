import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from fpdf import FPDF
from PIL import Image
import io
import re

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Pak-Medical AI Agent", page_icon="🇵🇰", layout="centered")

# --- SIDEBAR & API KEY SETUP ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063176.png", width=100)
    st.title("⚙️ Settings")
    
    # User can paste API Key here directly
    api_key = st.text_input("Enter Gemini API Key:", type="password")
    
    st.markdown("---")
    st.warning("🚑 **Emergency? Call 1122**")
    st.info("Features:\n- Voice Response 🗣️\n- PDF Report 📄\n- Emergency Alert 🚨")

# --- SETUP GEMINI ---
if api_key:
    genai.configure(api_key=api_key)
else:
    st.warning("⚠️ Please enter your Gemini API Key in the sidebar to start.")
    st.stop()

# --- SYSTEM PROMPT (STRICT) ---
SYSTEM_PROMPT = """
You are a 'Medical AI Assistant' for Pakistan. 
You act as a primary triage agent. 
RULES:
1. If user mentions 'Heart Attack', 'Chest Pain', 'Bleeding', 'Accident', 'Suicide' -> START with "🚨 EMERGENCY: CALL 1122 IMMEDIATELY."
2. Output plain text with Markdown.
3. Keep answers concise (under 200 words unless detailed report asked).
4. No Prescriptions (Meds). Only Lifestyle & Triage.
5. Language: Roman Urdu or English (Match User).
6. Use clear headings: [Analysis], [Precautions], [Next Steps].
"""

model = genai.GenerativeModel('gemini-1.5-flash', system_instruction=SYSTEM_PROMPT)

# --- HELPER FUNCTIONS ---

def get_audio_bytes(text):
    """Converts text to audio bytes to avoid file permission errors"""
    try:
        # Remove markdown symbols for clear speech
        clean_text = text.replace("*", "").replace("#", "").replace("-", "")
        tts = gTTS(text=clean_text, lang='en', tld='com')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        return mp3_fp
    except Exception as e:
        return None

def create_clean_pdf(user_text, ai_text):
    """Generates a simple PDF report"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Title
    pdf.set_font("Arial", style="B", size=16)
    pdf.cell(200, 10, txt="Medical AI Consultation Report", ln=True, align='C')
    pdf.ln(10)
    
    # Emergency Note
    pdf.set_font("Arial", style="B", size=10)
    pdf.set_text_color(255, 0, 0)
    pdf.cell(0, 10, txt="EMERGENCY: In Pakistan, Call 1122 for urgent help.", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # Sanitizing text (removing emojis/special chars that crash PDF)
    def clean_str(s):
        return s.encode('latin-1', 'ignore').decode('latin-1')

    # User Section
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 10, txt="Patient Symptoms:", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 10, txt=clean_str(user_text))
    pdf.ln(5)
    
    # AI Section
    pdf.set_font("Arial", style="B", size=12)
    pdf.cell(0, 10, txt="AI Assessment:", ln=True)
    pdf.set_font("Arial", size=10)
    # Remove markdown stars for PDF
    clean_ai = ai_text.replace("*", "").replace("#", "") 
    pdf.multi_cell(0, 8, txt=clean_str(clean_ai))
    
    return pdf.output(dest='S').encode('latin-1')

def check_emergency_keywords(text):
    danger_words = ["heart attack", "chest pain", "dard", "accident", "suicide", "khoon", "bleeding", "mar jaonga", "zehar"]
    for word in danger_words:
        if word in text.lower():
            return True
    return False

# --- MAIN APP INTERFACE ---

st.title("🩺 Pak-Health AI Agent")
st.markdown("Your 24/7 AI Health Companion (Beta)")

# Session State for History
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display Chat History
for role, text in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(text)

# User Input Area
user_query = st.chat_input("Apni tabiyat ke baray main batayein...")

if user_query:
    # 1. Display User Message
    st.session_state.chat_history.append(("user", user_query))
    with st.chat_message("user"):
        st.markdown(user_query)
    
    # 2. Emergency Check (Frontend)
    if check_emergency_keywords(user_query):
        st.error("🚨 EMERGENCY DETECTED! PLEASE DIAL 1122 IMMEDIATELY.")
    
    # 3. Generate Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        with st.spinner("Analyzing Medical Data..."):
            try:
                # Call Gemini
                response = model.generate_content(user_query)
                full_response = response.text
                message_placeholder.markdown(full_response)
                
                # Update History
                st.session_state.chat_history.append(("assistant", full_response))
                
            except Exception as e:
                st.error(f"Error connecting to AI: {e}")
                full_response = "Sorry, error occurred."

    # 4. Features Section (Audio & PDF) - Show ONLY after response
    if full_response and full_response != "Sorry, error occurred.":
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        # Audio Feature
        with col1:
            st.subheader("🔊 Listen")
            audio_bytes = get_audio_bytes(full_response)
            if audio_bytes:
                st.audio(audio_bytes, format='audio/mp3')
            else:
                st.warning("Audio generation failed.")
        
        # PDF Feature
        with col2:
            st.subheader("📄 Report")
            try:
                pdf_data = create_clean_pdf(user_query, full_response)
                st.download_button(
                    label="Download Medical Report",
                    data=pdf_data,
                    file_name="Medical_Report.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error("PDF text format not supported.")
