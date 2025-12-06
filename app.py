import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from gtts import gTTS
from streamlit_option_menu import option_menu
from PIL import Image
import io
import datetime
import plotly.graph_objects as go

# --- CONFIGURATION & PAGE SETUP ---
st.set_page_config(
    page_title="Sehat Sahulat Pro - AI Medical Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR ANIMATIONS & UI ---
st.markdown("""
<style>
    /* Fade In Animation */
    .main { animation: fadeIn 1.0s ease-in-out; }
    @keyframes fadeIn { 0% { opacity: 0; } 100% { opacity: 1; } }
    
    /* Chat Bubbles */
    .stChatMessage { border-radius: 15px; border: 1px solid #e0e0e0; }
    
    /* Ticker Animation for News */
    .ticker-wrap {
        width: 100%; overflow: hidden; background-color: #d1ecf1; color: #0c5460; padding: 10px; border-radius: 5px; margin-bottom: 20px;
    }
    .ticker { display: inline-block; white-space: nowrap; animation: ticker 30s linear infinite; }
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    
    /* Buttons */
    div.stButton > button { border-radius: 20px; background: linear-gradient(to right, #00c6ff, #0072ff); color: white; border: none; }
    div.stButton > button:hover { transform: scale(1.02); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR SETUP & BMI CALCULATOR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063176.png", width=80)
    st.title("🏥 Sehat Sahulat Pro")
    
    # API Key Input
    api_key = st.text_input("🔑 Google Gemini API Key:", type="password")
    
    # Language Toggle
    language = st.radio("🌐 Language / Zaban:", ["English", "Urdu / Roman Urdu"], horizontal=True)
    
    st.markdown("---")
    
    # FEATURE 1: BMI CALCULATOR
    st.subheader("⚖️ BMI Calculator")
    weight = st.number_input("Weight (kg)", 0, 200, 70)
    height = st.number_input("Height (cm)", 0, 250, 170)
    
    if height > 0:
        bmi = weight / ((height/100)**2)
        st.metric("Your BMI", f"{bmi:.1f}")
        
        # Visual Gauge for BMI
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = bmi,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Health Status"},
            gauge = {
                'axis': {'range': [10, 40]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [10, 18.5], 'color': "lightblue"},
                    {'range': [18.5, 25], 'color': "green"},
                    {'range': [25, 30], 'color': "orange"},
                    {'range': [30, 40], 'color': "red"}],
            }
        ))
        fig.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)

    # Privacy Toggle
    incognito = st.toggle("🕵️ Incognito Mode (Don't Save Chat)")

# --- SESSION STATE ---
if "history" not in st.session_state:
    st.session_state.history = []
if "user_info" not in st.session_state:
    st.session_state.user_info = {"name": "Guest", "age": "--", "gender": "--"}

# --- HELPER FUNCTIONS ---
def get_gemini_response(prompt, image=None, mode="normal"):
    if not api_key:
        return "⚠️ Please enter your API Key in the sidebar first."
    
    genai.configure(api_key=api_key)
    
    # Dynamic System Instructions
    base_instruction = f"""
    You are 'Sehat Sahulat', a top-tier Medical AI Assistant.
    Language: {language}.
    User Profile: Name: {st.session_state.user_info['name']}, Age: {st.session_state.user_info['age']}.
    
    STRICT RULES:
    1. ONLY answer medical/health queries. Refuse non-medical topics politely.
    2. FORMATTING: Use Bullet points, Bold text for emphasis.
    3. DIET PLANS: Always format diet plans as a Markdown Table.
    4. MEDICINE: If suggesting generic meds, always add a disclaimer: "Consult a real doctor before use."
    5. EMERGENCY: If symptoms seem critical (heart attack, severe bleeding), tell them to call 1122 immediately.
    """
    
    if mode == "drug_checker":
        base_instruction += "\nTASK: Analyze the interaction between these drugs. Be concise and warn about side effects."
    
    model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=base_instruction)
    
    try:
        if image:
            response = model.generate_content([prompt, image])
        else:
            response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Connection Error: {str(e)}"

def generate_pdf(chat_history):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Sehat Sahulat Pro - Medical Report", ln=True, align='C')
    pdf.ln(10)
    for role, text in chat_history:
        safe_text = text.encode('latin-1', 'replace').decode('latin-1')
        prefix = "Patient: " if role == "user" else "Dr. AI: "
        pdf.multi_cell(0, 10, txt=prefix + safe_text)
        pdf.ln(2)
    return pdf.output(dest="S").encode("latin-1")

# --- NEWS TICKER (FEATURE 10) ---
st.markdown("""
<div class="ticker-wrap">
<div class="ticker">
💡 Health Tip: Drink at least 8 glasses of water daily. | 🍎 Eat an apple a day for better immunity. | 🏃‍♂️ Walk 30 mins daily for heart health. | 🚑 For Emergencies in Pakistan, Dial 1122.
</div></div>
""", unsafe_allow_html=True)

# --- NAVIGATION ---
selected = option_menu(
    menu_title=None,
    options=["Consultation", "Drug Checker", "Mental Health", "Hospitals Map", "Tools"],
    icons=["chat-dots", "capsule", "heart-pulse", "geo-alt", "gear"],
    default_index=0,
    orientation="horizontal",
)

# --- TAB 1: CONSULTATION (MAIN CHAT) ---
if selected == "Consultation":
    
    # FEATURE 7: SYMPTOM CHIPS
    st.write("###### Quick Symptoms:")
    cols = st.columns(6)
    symptoms = ["Fever 🤒", "Headache 🤕", "Flu 🤧", "Stomach Pain 🤢", "Diabetes 🍬", "Skin Rash 🖐️"]
    clicked_symptom = None
    for i, sym in enumerate(symptoms):
        if cols[i].button(sym):
            clicked_symptom = sym

    # Chat Interface
    chat_container = st.container()
    
    # Display History
    with chat_container:
        for role, text in st.session_state.history:
            with st.chat_message(role):
                st.markdown(text)

    # Input Area
    with st.container():
        # FEATURE 4: VOICE INPUT (Using Streamlit Audio Input if available, fallback to text)
        col_txt, col_mic = st.columns([8, 1])
        
        # File Uploader in Expander
        with st.expander("📎 Upload Report / Image"):
            uploaded_file = st.file_uploader("Upload X-ray, Report, or Skin Image", type=["jpg", "png", "jpeg"])
        
        # User Input
        user_input = st.chat_input("Type your health question here...")
        
        # Logic to handle inputs
        final_prompt = None
        
        if clicked_symptom:
            final_prompt = f"I am feeling {clicked_symptom}. What should I do? Please guide regarding diet and medicine."
        elif user_input:
            final_prompt = user_input

        if final_prompt:
            if not incognito:
                st.session_state.history.append(("user", final_prompt))
            
            with st.chat_message("user"):
                st.markdown(final_prompt)

            # Image Handling
            img_data = None
            if uploaded_file:
                img_data = Image.open(uploaded_file)
                st.image(img_data, width=200)
                final_prompt = "Analyze this medical image/report: " + final_prompt

            with st.spinner("Dr. AI is thinking..."):
                response = get_gemini_response(final_prompt, img_data)
            
            if not incognito:
                st.session_state.history.append(("assistant", response))
            
            with st.chat_message("assistant"):
                st.markdown(response)

# --- TAB 2: DRUG INTERACTION CHECKER (FEATURE 2) ---
if selected == "Drug Checker":
    st.header("💊 Drug Interaction Checker")
    st.info("Check if two medicines are safe to take together.")
    
    c1, c2 = st.columns(2)
    med1 = c1.text_input("Medicine 1 Name")
    med2 = c2.text_input("Medicine 2 Name")
    
    if st.button("Check Safety"):
        if med1 and med2:
            prompt = f"Can I take {med1} and {med2} together? Explain interactions and side effects."
            res = get_gemini_response(prompt, mode="drug_checker")
            st.success("Analysis Result:")
            st.markdown(res)
        else:
            st.warning("Please enter both medicine names.")

# --- TAB 3: MENTAL HEALTH TRACKER (FEATURE 6) ---
if selected == "Mental Health":
    st.header("🧠 Mental Wellness Check")
    
    mood = st.select_slider("How are you feeling today?", options=["Very Sad", "Sad", "Neutral", "Happy", "Very Happy"])
    sleep = st.slider("Hours of sleep last night?", 0, 12, 7)
    stress = st.slider("Stress Level (1-10)", 1, 10, 5)
    
    if st.button("Get Mental Health Advice"):
        prompt = f"User Mood: {mood}, Sleep: {sleep} hours, Stress Level: {stress}/10. Give 3 short tips to improve mental health."
        res = get_gemini_response(prompt)
        st.markdown(res)

# --- TAB 4: HOSPITALS MAP (FEATURE 3) ---
if selected == "Hospitals Map":
    st.header("🏥 Find Nearby Hospitals")
    st.write("Showing hospitals in Pakistan (Default: Islamabad). Enable GPS for precise location in Google Maps.")
    
    # Embedding Google Maps (Centered on Pakistan/Islamabad by default)
    map_html = """
    <iframe src="https://www.google.com/maps/embed?pb=!1m16!1m12!1m3!1d106263.1360098482!2d73.00392657335967!3d33.68442019999999!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!2m1!1shospitals%20near%20me!5e0!3m2!1sen!2s!4v1700000000000!5m2!1sen!2s" 
    width="100%" height="450" style="border:0;" allowfullscreen="" loading="lazy"></iframe>
    """
    st.components.v1.html(map_html, height=450)

# --- TAB 5: TOOLS & SETTINGS ---
if selected == "Tools":
    st.header("⚙️ User Profile & Tools")
    
    # Profile Update
    with st.expander("📝 Update Profile Details", expanded=True):
        n = st.text_input("Name", st.session_state.user_info['name'])
        a = st.text_input("Age", st.session_state.user_info['age'])
        if st.button("Save Profile"):
            st.session_state.user_info['name'] = n
            st.session_state.user_info['age'] = a
            st.success("Saved!")

    # Download Report
    st.subheader("📄 Export Data")
    if st.session_state.history:
        pdf_data = generate_pdf(st.session_state.history)
        st.download_button("Download Chat as PDF", pdf_data, file_name="Medical_Report.pdf", mime="application/pdf")
    else:
        st.caption("No chat history to export yet.")
        
    # Emergency SOS (Feature 9)
    st.markdown("---")
    st.markdown("### 🆘 Emergency Zone")
    if st.button("🚨 I NEED URGENT HELP"):
        st.error("CALLING EMERGENCY SERVICES (Simulated)...")
        st.markdown("""
        **Pakistan Emergency Numbers:**
        * 🚑 **1122** (Rescue/Ambulance)
        * 🚓 **15** (Police)
        * 🏥 **1166** (Sehat Tahaffuz)
        """)
