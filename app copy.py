import streamlit as st
import google.generativeai as genai
import sys
import asyncio
import firebase_admin
from firebase_admin import credentials, firestore
import requests
import json
import re

# -------------- Configuration --------------
st.set_page_config(page_title="KynoHealth Chatbot", page_icon="💬", layout="wide")

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Firebase init
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("firebase_credentials.json")
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Firebase initialization failed: {e}")
        st.stop()

db = firestore.client()

# API Configuration
GEMINI_API_KEY = "AIzaSyDoDT6-pFN_Bq3WLoDczx1zeKcMZrhlmvA"
genai.configure(api_key=GEMINI_API_KEY)

# Model mapping based on user role
MODEL_CONFIG = {
    "free": {
        "name": "gemini-1.5-flash",
        "display": "Gemini 1.5 Flash (Free)"
    },
    "paid": {
        "name": "gemini-2.0-flash", 
        "display": "Gemini 2.0 Flash (Premium)"
    }
}

# -------------- Helper Functions --------------

@st.cache_data(show_spinner=False)
def load_scraped_data():
    try:
        with open("kyno_scraped_data.txt", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        st.error(f"Failed to load scraped data: {e}")
        return ""

def ask_question(question, context, user_role):
    prompt = f"""
Context from KynoHealth website:
{context}

Question: {question}

Answer based on the context above. If not found, say "you are not sure".
Avoid saying "Based on the provided context, it's unclear" or "context in general".
Also provide Email, Phone number, and Address of KynoHealth if relevant.
If no info, say "Contact KynoHealth (email, phone, address) to know more".
"""

    try:
        model_name = MODEL_CONFIG[user_role]["name"]
        gemini_model = genai.GenerativeModel(model_name)
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating response: {e}"

def is_valid_email(email):
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

# -------------- UI Components --------------

def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Login to KynoHealth Chatbot")
        st.markdown("---")

        with st.form("login_form"):
            email = st.text_input("📧 Email", placeholder="Enter your email")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            login_button = st.form_submit_button("Login", use_container_width=True)

            if login_button:
                if not email or not password:
                    st.warning("⚠️ Please enter both email and password.")
                    return

                if not is_valid_email(email):
                    st.warning("⚠️ Please enter a valid email address.")
                    return

                try:
                    with st.spinner("Logging in..."):
                        user_query = db.collection("users").where("email", "==", email).limit(1).get()
                        if user_query:
                            user_doc = user_query[0].to_dict()
                            stored_password = user_doc.get("password", "")
                            if stored_password == password:
                                st.success("✅ Login successful!")
                                st.session_state.user_logged_in = True
                                st.session_state.user_email = email
                                st.session_state.role = user_doc.get("role", "free").lower()
                                st.rerun()
                            else:
                                st.error("❌ Incorrect password.")
                        else:
                            st.error("❌ User not found.")
                except Exception as e:
                    st.error(f"❌ Error checking user: {e}")

def chat_page():
    # Header with user info and model display
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("💬 KynoHealth Chatbot")
        user_role = st.session_state.get("role", "free")
        model_display = MODEL_CONFIG[user_role]["display"]
        
        # Display user info with model being used
        st.markdown(f"""
        **Welcome back, {st.session_state.user_email}**  
        🔹 **Plan:** {user_role.title()}  
        🤖 **AI Model:** {model_display}
        """)
    
    with col2:
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("✅ Logged out successfully!")
            st.rerun()

    st.markdown("---")
    st.markdown("Ask me anything about **KynoHealth** based on their website!")

    # Load context data
    context = load_scraped_data()
    if not context:
        st.warning("⚠️ No context data loaded. Please check kyno_scraped_data.txt file.")

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Handle user input
    user_input = st.chat_input("Ask your question here...")

    if user_input:
        # Add user message to chat
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking... 🤔"):
                answer = ask_question(user_input, context, st.session_state.get("role", "free"))
                st.markdown(answer)

        st.session_state.chat_history.append({"role": "assistant", "content": answer})

def main():
    if "user_logged_in" not in st.session_state:
        st.session_state.user_logged_in = False

    if st.session_state.user_logged_in:
        chat_page()
    else:
        login_page()

if __name__ == "__main__":
    main()