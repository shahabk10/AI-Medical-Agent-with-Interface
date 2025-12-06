import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from PIL import Image
import os

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Pak AI Health Assistant",
    page_icon="🇵🇰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Pakistan Green Theme
st.markdown("""
<style>
    .stButton>button {
        background-color: #115740; /* Pakistan Green */
        color: white;
        border-radius: 8px;
        height: 45px;
        width: 100%;
        font-weight: bold;
    }
    .warning-box {
        background-color: #ffebee;
        color: #c62828;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #c62828;
        font-weight: bold;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SETUP & MEMORY ---

# Load API Key
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    else:
        st.error("⚠️ API Key missing! Set GEMINI_API_KEY in Streamlit Secrets.")
except Exception as e:
    st.error(f"Config Error: {e}")

# Initialize History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Assalam-o-Alaikum! 🇵🇰\nMain aapka AI Health Assistant hoon. Shuru karne ke liye apna **Naam** aur **Umar (Age)** batayein."}
    ]
if "chat_phase" not in st.session_state:
    st.session_state.chat_phase = "onboarding"

# --- 3. HELPER FUNCTIONS ---

class MedicalReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'PAKISTAN DIGITAL HEALTH CLINIC', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'AI Consultation Summary Report', 0, 1, 'C')
        self.line(10, 30, 200, 30)
        self.ln(20)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, 'Note: Yeh report AI ne banayi hai. Asli Doctor se ruju karein.', 0, 0, 'C')

def create_pdf(chat_history):
    pdf = MedicalReport()
    pdf.add_page()
    pdf.set_font('Arial', '', 11)
    for msg in chat_history:
        role = "PATIENT" if msg["role"] == "user" else "AI DOCTOR"
        # Fix encoding issues
        content = str(msg["content"]).encode('latin-1', 'replace').decode('latin-1')
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(17, 87, 64) if role == "AI DOCTOR" else pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 6, f"{role}:", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(0)
        pdf.multi_cell(0, 6, content)
        pdf.ln(3)
    return pdf.output(dest='S').encode('latin-1')

def generate_doctor_email(chat_history):
    # Try Flash first, fallback to Pro
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        model = genai.GenerativeModel('gemini-pro')
        
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history])
    prompt = f"""
    Write a formal appointment request email to a Doctor in Pakistan based on this chat.
    History: {history_text}
    Format: Subject, Dear Doctor, Body (Symptoms in English), Sincerely.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "Email generation failed due to model error."

# --- 4. CORE INTELLIGENCE (ROBUST FIX) ---

def process_input(prompt, image=None):
    # Emergency Check
    if prompt:
        emergency_keywords = ["chest pain", "heart attack", "cant breathe", "saans", "khoon", "bleeding", "dengue", "accident"]
        if any(word in prompt.lower() for word in emergency_keywords):
            return "🚨 **EMERGENCY ALERT:** Yeh serious lag raha hai. AI ko chorein aur **1122** par call karein."

    # --- SMART MODEL SELECTION ---
    # Hum pehle 'Flash' try karenge, agar wo 404 dega to 'Pro' use karenge
    target_model = 'gemini-1.5-flash'
    
    # System Instructions
    system_instruction = """
    You are a polite AI Health Assistant for Pakistan.
    1. Language: English mixed with simple Roman Urdu.
    2. Medicines: Suggest Panadol, Brufen, ORS, etc.
    3. Disclaimer: Always say "Doctor se check karwayein".
    """
    
    content = [system_instruction]
    
    if image:
        content.append(image)
        content.append("Analyze this medical image/report and provide feedback.")
    if prompt:
        content.append(f"User Query: {prompt}")

    try:
        # Koshish 1: Latest Model
        model = genai.GenerativeModel(target_model)
        response = model.generate_content(content)
        return response.text
        
    except Exception as e:
        # Agar 404 ya koi error aaya, to ye block chalega
        error_msg = str(e)
        if "404" in error_msg or "not found" in error_msg:
            try:
                # Koshish 2: Old Reliable Model (Fallback)
                fallback_model = 'gemini-pro'
                # Note: gemini-pro images support nahi karta, isliye agar image hai to warning denge
                if image:
                    return "⚠️ Error: Aapka system purane model par chal raha hai jo Images support nahi karta. Please sirf Text use karein."
                
                model = genai.GenerativeModel(fallback_model)
                # Fallback mein system instruction direct prompt mein add karte hain
                full_prompt = system_instruction + "\n\n" + prompt
                response = model.generate_content(full_prompt)
                return response.text
            except Exception as e2:
                return f"System Critical Error: {e2}"
        else:
            return f"Error: {e}"

# --- 5. UI LAYOUT ---

# A. SIDEBAR
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/206/206856.png", width=60)
    st.title("Sehat Sahulat")

    with st.expander("⚖️ BMI Calculator", expanded=False):
        weight = st.number_input("Wazan (kg)", 10, 200, 70)
        height = st.number_input("Qad (cm)", 50, 250, 170)
        if st.button("Calculate"):
            bmi = round(weight / ((height/100)**2), 1)
            st.write(f"BMI: {bmi}")

    with st.expander("🚑 Emergency", expanded=True):
        st.error("📞 **1122**: Rescue")
        st.warning("📞 **15**: Police")

    st.markdown("---")
    uploaded_file = st.file_uploader("Nuskha (Image)", type=["jpg", "png", "jpeg"])
    
    if st.button("📄 PDF Download"):
        if len(st.session_state.messages) > 1:
            pdf_bytes = create_pdf(st.session_state.messages)
            st.download_button("⬇️ Save PDF", pdf_bytes, "Sehat_Report.pdf", "application/pdf")

    if st.button("📧 Email Draft"):
        if len(st.session_state.messages) > 2:
            st.session_state['email_draft'] = generate_doctor_email(st.session_state.messages)
            
    if 'email_draft' in st.session_state:
        st.text_area("Email:", value=st.session_state['email_draft'], height=150)

    st.markdown("---")
    if st.button("🔄 Reset Chat"):
        st.session_state.messages = []
        st.session_state.chat_phase = "onboarding"
        st.rerun()

# B. MAIN CHAT
st.title("🏥 Pak AI Health Assistant")
st.caption("Roman Urdu Support • Pakistan Edition")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "EMERGENCY" in message["content"]:
             st.markdown(f'<div class="warning-box">{message["content"]}</div>', unsafe_allow_html=True)
        else:
             st.markdown(message["content"])

# C. INPUT
prompt = st.chat_input("Tabiyat kaisi hai?")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    image_data = None
    if uploaded_file:
        image_data = Image.open(uploaded_file)
        if "image_processed" not in st.session_state: 
             st.toast("Tasveer upload ho gayi", icon="📸")
             st.session_state.image_processed = True

    with st.chat_message("assistant"):
        with st.spinner("AI soch raha hai..."):
            if st.session_state.chat_phase == "onboarding":
                response_text = f"Shukriya. Details note kar li gayi hain: **{prompt}**.\n\nAb batayein kya masla hai?"
                st.session_state.chat_phase = "consultation"
            else:
                response_text = process_input(prompt, image_data)

            if "EMERGENCY" in response_text:
                st.markdown(f'<div class="warning-box">{response_text}</div>', unsafe_allow_html=True)
            else:
                st.markdown(response_text)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
