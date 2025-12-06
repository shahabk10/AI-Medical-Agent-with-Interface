import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
from streamlit_option_menu import option_menu
import plotly.graph_objects as go
import datetime

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="MediCore AI - Premium Health Agent",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SECURE API CONNECTION ---
try:
    # Agar Secrets setup nahi hain to error handle karein
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    # Fallback for first run (Instruction for User)
    st.warning("⚠️ API Key Missing! Please add 'GEMINI_API_KEY' to Streamlit Secrets.")
    st.stop()

# --- 3. PREMIUM UI CSS (GLASSMORPHISM) ---
st.markdown("""
<style>
    /* Background & Main Theme */
    .stApp { background-color: #f8f9fa; }
    
    /* Card Styling */
    .css-card {
        border-radius: 20px;
        padding: 25px;
        background-color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #001f3f; color: white; }
    
    /* Buttons */
    .stButton>button {
        border-radius: 12px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; padding: 10px 24px; font-weight: bold;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(0,0,0,0.2); }
    
    /* Input Fields */
    .stTextInput>div>div>input { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 4. SESSION STATE ---
if "history" not in st.session_state: st.session_state.history = []
if "user_data" not in st.session_state: 
    st.session_state.user_data = {"name": "Guest User", "age": 25, "gender": "Male", "weight": 70, "height": 175}

def get_ai_response(prompt, system_instruction):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system_instruction)
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        model = genai.GenerativeModel("gemini-pro")
        return model.generate_content(f"{system_instruction}\n\nQuery: {prompt}").text

def generate_professional_pdf(history, user_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(36, 59, 85)
    pdf.rect(0, 0, 210, 40, 'F')
    pdf.set_font("Arial", 'B', 24)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 20, "MediCore AI Medical Report", 0, 1, 'C')
    pdf.ln(20)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 10, f"Patient: {user_data['name']} | Date: {datetime.datetime.now().strftime('%Y-%m-%d')}")
    pdf.line(10, 60, 200, 60)
    pdf.ln(10)
    for role, text in history:
        safe_text = text.encode('latin-1', 'replace').decode('latin-1')
        prefix = "PATIENT: " if role == "user" else "DOCTOR AI: "
        pdf.set_font("Arial", 'B', 11) if role == "assistant" else pdf.set_font("Arial", '', 11)
        pdf.multi_cell(0, 6, prefix + safe_text)
        pdf.ln(2)
    return pdf.output(dest="S").encode("latin-1")

# --- 5. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4228/4228730.png", width=80)
    st.markdown("### MediCore AI")
    
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "AI Doctor Chat", "Medicine Info", "Lab Planner", "Settings"],
        icons=["speedometer2", "chat-square-heart", "capsule", "clipboard-pulse", "gear"],
        default_index=1,
    )
    
    st.markdown("---")
    if st.button("🚨 EMERGENCY SOS", type="primary"):
        st.error("🚑 Emergency Protocol Initiated! Dialing 1122...")

# --- 6. MAIN CONTENT ---

# >>>> PAGE: DASHBOARD <<<<
if selected == "Dashboard":
    st.markdown("## 📊 Patient Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Status", "Healthy", "Active")
    col2.metric("BMI", f"{st.session_state.user_data['weight'] / ((st.session_state.user_data['height']/100)**2):.1f}")
    col3.metric("Last Checkup", "Today")
    
    fig = go.Figure(go.Scatter(x=['W1', 'W2', 'W3', 'W4'], y=[72, 70, 71, 72], mode='lines+markers', name='Heart Rate'))
    fig.update_layout(title="Heart Rate Trends", height=300)
    st.plotly_chart(fig, use_container_width=True)

# >>>> PAGE: AI DOCTOR CHAT <<<<
if selected == "AI Doctor Chat":
    st.title("🩺 Live Consultation")
    for role, text in st.session_state.history:
        avatar = "👨‍⚕️" if role == "assistant" else "👤"
        with st.chat_message(role, avatar=avatar):
            st.markdown(text)
            
    user_query = st.chat_input("Describe symptoms...")
    if user_query:
        st.session_state.history.append(("user", user_query))
        with st.chat_message("user", avatar="👤"): st.markdown(user_query)
        
        with st.chat_message("assistant", avatar="👨‍⚕️"):
            with st.spinner("Analyzing..."):
                sys = f"You are MediCore AI. Patient: {st.session_state.user_data['name']}. Give diagnosis, remedies, diet (table), and medicine."
                res = get_ai_response(user_query, sys)
                st.markdown(res)
                st.session_state.history.append(("assistant", res))
                st.rerun()

    if st.session_state.history:
        pdf_data = generate_professional_pdf(st.session_state.history, st.session_state.user_data)
        st.download_button("📥 Download Report", pdf_data, "Report.pdf", "application/pdf")

# >>>> PAGE: MEDICINE INFO (NEW FEATURE) <<<<
if selected == "Medicine Info":
    st.markdown("""<div class="css-card"><h2>💊 Medicine Encyclopedia</h2>
    <p>Enter any medicine name to get detailed composition and usage analysis.</p></div>""", unsafe_allow_html=True)
    
    med_name = st.text_input("Enter Medicine Name (e.g., Panadol, Augmentin, Brufen):")
    
    if st.button("Analyze Medicine"):
        if med_name:
            with st.spinner(f"Analyzing composition of {med_name}..."):
                # Special Prompt for Medicine Analysis
                med_prompt = f"""
                Analyze the medicine: '{med_name}'.
                Provide the output in the following STRICT format:
                
                ### 1. Active Ingredients & Mechanism
                * List each active ingredient.
                * For each ingredient, provide a 1-line simple explanation of what it does.
                
                ### 2. Primary Uses
                * List the main diseases/conditions it treats.
                
                ### 3. Safety Check
                * Common Side Effects.
                * Warnings (Pregnancy, Driving, etc).
                
                Note: Be precise. If it's a brand name, find its generic formula.
                """
                
                med_info = get_ai_response(med_prompt, "You are an expert Pharmacist.")
                
                # Display Result in a Card
                st.markdown(f"""
                <div class="css-card">
                    <h3 style="color: #007bff;">🧬 Analysis for: {med_name}</h3>
                    <hr>
                    {med_info}
                </div>
                """, unsafe_allow_html=True)
                
                st.caption("⚠️ Disclaimer: This information is for educational purposes. Always consult a doctor.")
        else:
            st.warning("Please enter a medicine name first.")

# >>>> PAGE: LAB PLANNER <<<<
if selected == "Lab Planner":
    st.header("🔬 Lab Test Recommender")
    sym = st.text_area("Symptoms for Lab Test:")
    if st.button("Get Recommendations") and sym:
        res = get_ai_response(f"Recommend lab tests for: {sym}", "You are a Pathologist.")
        st.success("Recommended Tests:")
        st.markdown(res)

# >>>> PAGE: SETTINGS <<<<
if selected == "Settings":
    st.header("👤 Profile Settings")
    with st.form("p_form"):
        name = st.text_input("Name", st.session_state.user_data['name'])
        if st.form_submit_button("Save"):
            st.session_state.user_data['name'] = name
            st.success("Saved!")
