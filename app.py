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
        content = msg["content"].encode('latin-1', 'replace').decode('latin-1')
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(17, 87, 64) if role == "AI DOCTOR" else pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 6, f"{role}:", 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(0)
        pdf.multi_cell(0, 6, content)
        pdf.ln(3)
    return pdf.output(dest='S').encode('latin-1')

def generate_doctor_email(chat_history):
    # Model Updated to specific version to avoid 404
    model = genai.GenerativeModel('gemini-1.5-flash-001')
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in chat_history])
    prompt = f"""
    Write a formal appointment request email to a Doctor in Pakistan based on this chat.
    History: {history_text}
    Format: Subject, Dear Doctor, Body (Symptoms in English), Sincerely.
    """
    response = model.generate_content(prompt)
    return response.text

# --- 4. CORE INTELLIGENCE (PAKISTAN CONTEXT) ---

def process_input(prompt, image=None):
    # Emergency Check
    if prompt:
        emergency_keywords = ["chest pain", "heart attack", "cant breathe", "saans", "khoon", "bleeding", "dengue", "accident"]
        if any(word in prompt.lower() for word in emergency_keywords):
            return "🚨 **EMERGENCY ALERT:** Yeh serious lag raha hai. AI ko chorein aur **1122** par call karein ya foran Hospital Emergency mein jayein."

    # FIX: Using 'gemini-1.5-flash-001' instead of generic tag to prevent 404
    model = genai.GenerativeModel('gemini-1.5-flash-001')
    
    system_instruction = """
    You are a polite AI Health Assistant for Pakistan.
    1. Language: Use English mixed with simple Roman Urdu (e.g., "Take medicine pani ke sath").
    2. Medicines: Recommend common Pakistani brands (Panadol, Brufen, Gravinate, ORS).
    3. Warning: If high fever, suggest CBC Test for Dengue/Malaria.
    4. Disclaimer: Always say "Please Doctor se check karwayein".
    """
    content = [system_instruction]
    if image:
        content.append(image)
        content.append("Analyze this medical image/report and provide feedback.")
    if prompt:
        content.append(f"User Query: {prompt}")
    
    try:
        response = model.generate_content(content)
        return response.text
    except Exception as e:
        return f"System Error: {e}"

# --- 5. UI LAYOUT ---

# A. SIDEBAR
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/206/206856.png", width=60)
    st.title("Sehat Sahulat")

    # BMI Calculator
    with st.expander("⚖️ BMI Calculator (Sehat Check)", expanded=False):
        weight = st.number_input("Wazan (Weight kg)", min_value=10, max_value=200, value=70)
        height = st.number_input("Qad (Height cm)", min_value=50, max_value=250, value=170)
        if st.button("Calculate Karein"):
            height_m = height / 100
            bmi = round(weight / (height_m ** 2), 1)
            if bmi < 18.5: status, color = "Kamzor (Underweight)", "orange"
            elif 18.5 <= bmi < 24.9: status, color = "Fit (Healthy)", "green"
            elif 25 <= bmi < 29.9: status, color = "Motaapa (Overweight)", "orange"
            else: status, color = "Boht Motaapa (Obese)", "red"
            st.markdown(f"### BMI: :{color}[{bmi}]")
            st.markdown(f"**Status: {status}**")

    # Emergency Numbers
    with st.expander("🚑 Emergency Numbers", expanded=True):
        st.error("📞 **1122**: Rescue & Ambulance")
        st.warning("📞 **15**: Police")
        st.info("📞 **1166**: Polio Helpline")

    st.markdown("---")
    
    uploaded_file = st.file_uploader("Nuskha (Prescription) ya Alamat", type=["jpg", "png", "jpeg"])
    
    if st.button("📄 Report Download Karein"):
        if len(st.session_state.messages) > 1:
            pdf_bytes = create_pdf(st.session_state.messages)
            st.download_button("⬇️ Save PDF", pdf_bytes, "Sehat_Report.pdf", "application/pdf")

    if st.button("📧 Email Likhwain"):
        if len(st.session_state.messages) > 2:
            email_draft = generate_doctor_email(st.session_state.messages)
            st.session_state['email_draft'] = email_draft
            
    if 'email_draft' in st.session_state:
        st.text_area("Email Copy Karein:", value=st.session_state['email_draft'], height=150)

    st.markdown("---")
    if st.button("🔄 Nayi Chat Shuru Karein"):
        st.session_state.messages = []
        st.session_state.chat_phase = "onboarding"
        if 'email_draft' in st.session_state: del st.session_state['email_draft']
        st.rerun()

# B. MAIN CHAT AREA
st.title("🏥 Pak AI Health Assistant")
st.caption("AI Doctor • Roman Urdu Support • Pakistani Medicines")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "EMERGENCY" in message["content"]:
             st.markdown(f'<div class="warning-box">{message["content"]}</div>', unsafe_allow_html=True)
        else:
             st.markdown(message["content"])

# C. INPUT AREA
prompt = st.chat_input("Apni tabiyat ke bare mein batayein...")

if prompt:
    # User Msg
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Image Handling
    image_data = None
    if uploaded_file:
        image_data = Image.open(uploaded_file)
        if "image_processed" not in st.session_state: 
             st.toast("Tasveer upload ho gayi hai", icon="📸")
             st.session_state.image_processed = True

    # AI Processing
    with st.chat_message("assistant"):
        with st.spinner("AI soch raha hai..."):
            
            # Onboarding Phase
            if st.session_state.chat_phase == "onboarding":
                response_text = f"Shukriya. Aapki details note kar li gayi hain: **{prompt}**.\n\nAb batayein aapko kya masla hai? (Aap Roman Urdu mein likh sakte hain)."
                st.session_state.chat_phase = "consultation"
            else:
                response_text = process_input(prompt, image_data)

            # Display
            if "EMERGENCY" in response_text:
                st.markdown(f'<div class="warning-box">{response_text}</div>', unsafe_allow_html=True)
            else:
                st.markdown(response_text)

    # Save
    st.session_state.messages.append({"role": "assistant", "content": response_text})
