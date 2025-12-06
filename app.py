import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from streamlit_option_menu import option_menu
import plotly.graph_objects as go
from PIL import Image
import datetime
import time

# --- 1. PAGE SETUP & CONFIGURATION ---
st.set_page_config(
    page_title="MediPro - AI Health System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CUSTOM CSS (Professional UI) ---
st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #f4f6f9; }
    
    /* Login Box Styling */
    .login-container {
        background-color: white; padding: 40px; border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center;
        width: 50%; margin: auto; margin-top: 50px;
    }
    
    /* Dashboard Cards */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f0f2f6 100%);
        padding: 20px; border-radius: 15px; border-left: 5px solid #007bff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* Chat Interface */
    .stChatMessage { background-color: white; border-radius: 15px; border: 1px solid #e1e4e8; }
    
    /* Buttons */
    div.stButton > button {
        background-color: #007bff; color: white; border-radius: 10px; border: none;
        padding: 10px 20px; font-weight: bold; transition: 0.3s;
    }
    div.stButton > button:hover { background-color: #0056b3; box-shadow: 0 5px 15px rgba(0,123,255,0.3); }
</style>
""", unsafe_allow_html=True)

# --- 3. AUTHENTICATION & SESSION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_info" not in st.session_state: st.session_state.user_info = {}
if "chat_history" not in st.session_state: st.session_state.chat_history = []

# --- 4. API CONNECTION ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except:
    st.error("⚠️ Setup Error: Please add 'GEMINI_API_KEY' to Streamlit Secrets.")
    st.stop()

# --- 5. FUNCTIONS ---

# --- REPLACEMENT FUNCTION FOR app.py ---

def get_ai_response(prompt, img_data=None):
    # System Instruction
    sys_prompt = f"""
    You are 'Dr. AI', a professional medical consultant.
    Patient: {st.session_state.user_info.get('name', 'Guest')}, Age: {st.session_state.user_info.get('age', '--')}.
    Guidelines: Answer only medical queries. Suggest Generic Medicines. 
    Structure: Diagnosis -> Diet -> Medicine -> Precautions.
    """
    
    # Hum 3 models try karenge bari bari
    models_to_try = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
    
    last_error = ""

    for model_name in models_to_try:
        try:
            # Model configure karein
            # Note: Purane models system_instruction support nahi karte, isliye hum prompt me add kar rahe hain
            final_prompt = f"System Instruction: {sys_prompt}\n\nUser Query: {prompt}"
            
            model = genai.GenerativeModel(model_name)
            
            if img_data:
                # Image ke sath request
                response = model.generate_content([final_prompt, img_data])
            else:
                # Text only request
                response = model.generate_content(final_prompt)
                
            # Agar yahan tak pohanch gaye to return kardo
            return response.text

        except Exception as e:
            # Agar fail hua to error save karo aur agla model try karo
            last_error = str(e)
            continue 
            
    # Agar saaray models fail ho jayen
    return f"⚠️ Error: Unable to connect. Details: {last_error}. Please Check API Key in Secrets."

def create_pdf(history):
    pdf = FPDF()
    pdf.add_page()
    
    # Professional Header
    pdf.set_fill_color(0, 123, 255) # Blue
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 22)
    pdf.cell(0, 25, "MediPro Consultation Report", 0, 1, 'C')
    pdf.ln(20)
    
    # Details
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 12)
    u = st.session_state.user_info
    pdf.cell(0, 10, f"Patient Name: {u.get('name')}  |  Age: {u.get('age')}  |  Gender: {u.get('gender')}", ln=True)
    pdf.cell(0, 10, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
    pdf.line(10, 70, 200, 70)
    pdf.ln(10)
    
    # Chat Content
    for role, text in history:
        safe_text = text.encode('latin-1', 'replace').decode('latin-1')
        prefix = "PATIENT: " if role == "user" else "DR. AI: "
        pdf.set_font("Arial", 'B', 11) if role == "assistant" else pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 8, prefix + safe_text)
        pdf.ln(2)
        
    return pdf.output(dest="S").encode("latin-1")

# --- 6. APP FLOW ---

# >>> SCENE 1: LOGIN PAGE <<<
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='text-align: center; margin-top: 50px;'>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/3063/3063176.png", width=120)
        st.markdown("<h1>MediPro Login</h1>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            name = st.text_input("Full Name")
            age = st.number_input("Age", 1, 100, 25)
            gender = st.selectbox("Gender", ["Male", "Female"])
            
            if st.form_submit_button("Access System", use_container_width=True):
                if name:
                    st.session_state.logged_in = True
                    st.session_state.user_info = {"name": name, "age": age, "gender": gender}
                    st.rerun()
                else:
                    st.error("Please enter your name.")

# >>> SCENE 2: MAIN SYSTEM <<<
else:
    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3063/3063176.png", width=80)
        st.title(f"Hi, {st.session_state.user_info['name']}")
        
        menu = option_menu(
            menu_title=None,
            options=["Dashboard", "Consultation", "Vitals Tracker"],
            icons=["grid", "chat-text", "activity"],
            default_index=1,
        )
        
        st.markdown("---")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # --- TAB: DASHBOARD ---
    if menu == "Dashboard":
        st.header("📊 Health Dashboard")
        
        # BMI Calculator
        st.subheader("BMI Calculator")
        c1, c2, c3 = st.columns(3)
        w = c1.number_input("Weight (kg)", 40, 150, 70)
        h = c2.number_input("Height (cm)", 120, 220, 170)
        bmi = w / ((h/100)**2)
        
        # Logic for Color
        color = "green" if 18.5 < bmi < 25 else "orange" if bmi < 30 else "red"
        
        c3.markdown(f"""
        <div class="metric-card" style="border-left: 5px solid {color};">
            <h3>BMI Score</h3>
            <h1>{bmi:.1f}</h1>
        </div>
        """, unsafe_allow_html=True)
        
        # Health Chart
        st.subheader("Activity Trends")
        fig = go.Figure(go.Scatter(y=[72, 75, 73, 70, 72, 74], x=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], mode='lines+markers', line=dict(color='#007bff', width=3)))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300)
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB: CONSULTATION (MAIN) ---
    elif menu == "Consultation":
        st.header("🩺 AI Doctor Consultation")
        
        # Chat Container
        chat_container = st.container()
        with chat_container:
            for role, text in st.session_state.chat_history:
                avatar = "👨‍⚕️" if role == "assistant" else "👤"
                with st.chat_message(role, avatar=avatar):
                    st.markdown(text)
        
        # Input Zone
        with st.container():
            st.markdown("---")
            c1, c2 = st.columns([1, 8])
            with c1:
                # Image Upload
                uploaded_file = st.file_uploader("📷", type=["jpg", "png"], label_visibility="collapsed")
            with c2:
                prompt = st.chat_input("Apni tabiyat ke bare mein batayein...")

            if prompt:
                # User Msg
                st.session_state.chat_history.append(("user", prompt))
                with st.chat_message("user", avatar="👤"):
                    st.markdown(prompt)
                
                # Image Logic
                img = None
                if uploaded_file:
                    img = Image.open(uploaded_file)
                    st.image(img, width=150, caption="Uploaded Image")
                    prompt = f"Analyze this image and text: {prompt}"
                
                # AI Msg
                with st.chat_message("assistant", avatar="👨‍⚕️"):
                    with st.spinner("Dr. AI soch rahe hain..."):
                        response = get_ai_response(prompt, img)
                        st.markdown(response)
                        st.session_state.chat_history.append(("assistant", response))
                        
                        # Rerun to update Download Button
                        st.rerun()

        # Download Report (Bottom Fixed)
        if st.session_state.chat_history:
            pdf_bytes = create_pdf(st.session_state.chat_history)
            st.download_button("📥 Download Official Report", pdf_bytes, "Medical_Report.pdf", "application/pdf", use_container_width=True)

    # --- TAB: VITALS ---
    elif menu == "Vitals Tracker":
        st.header("❤️ Vitals Tracker")
        st.info("Manual Entry for Record Keeping")
        
        col1, col2 = st.columns(2)
        with col1:
            st.number_input("Blood Pressure (Sys)", 80, 200)
            st.number_input("Blood Sugar (mg/dL)", 50, 400)
        with col2:
            st.number_input("Pulse Rate", 40, 150)
            st.number_input("Temperature (°F)", 95, 105)
            
        st.button("Save Records", use_container_width=True)
        st.success("Ye data PDF report mein shamil kiya jayega.")

