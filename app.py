import streamlit as st
import google.generativeai as genai
import os
import io
import csv
import json
import uuid
import datetime
import sqlite3
import hashlib
import base64
from PIL import Image
from pypdf import PdfReader
import docx
from dotenv import load_dotenv

# Load local environment variables if present
load_dotenv(override=True)

# Configure Gemini API Key
api_key = os.getenv("GEMINI_API_KEY")
if api_key == "your_gemini_api_key_here" or not api_key:
    api_key = None
else:
    genai.configure(api_key=api_key)

# Dynamically fetch available models based on API key permissions
supported_models = []
default_index = 0
if api_key:
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods and ('gemini' in m.name or 'gemma' in m.name):
                clean_name = m.name.split('/')[-1]
                if any(v in clean_name for v in ["3.5", "2.5", "2.0", "gemini-2-"]):
                    supported_models.append(clean_name)
        supported_models.sort()
        # Find best default model
        for idx, model_name in enumerate(supported_models):
            if "3.5-flash" in model_name:
                default_index = idx
                break
        else:
            for idx, model_name in enumerate(supported_models):
                if "2.5-flash" in model_name:
                    default_index = idx
                    break
            else:
                for idx, model_name in enumerate(supported_models):
                    if "2.0-flash" in model_name:
                        default_index = idx
                        break
    except Exception as e:
        pass

if not supported_models:
    supported_models = [
        "gemini-3.5-flash", 
        "gemini-3.5-pro", 
        "gemini-2.5-flash", 
        "gemini-2.5-pro", 
        "gemini-2.0-flash", 
        "gemini-2.0-pro"
    ]
    default_index = 0

# Load Logo Image & Convert to Base64 for inline HTML rendering
logo_path = "e:/Hackathon/image.jpeg"
logo_image = None
logo_base64 = ""

try:
    if os.path.exists(logo_path):
        logo_image = Image.open(logo_path)
        with open(logo_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
            logo_base64 = f"data:image/jpeg;base64,{encoded}"
except Exception as e:
    pass

# App Configuration
st.set_page_config(
    page_title="NexaBot - Multi-Modal AI Document Scanner",
    page_icon=logo_image if logo_image else None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling (Glassmorphism, Dark Theme, Micro-animations)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
    
    /* Global Styles */
    .stApp {
        background: radial-gradient(circle at top right, #1e0b36, #090514 60%);
        color: #e2e8f0;
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #080410 !important;
        border-right: 1px solid rgba(124, 58, 237, 0.15);
    }
    
    /* Custom Headers & Gradients */
    .app-header {
        font-weight: 800;
        background: linear-gradient(135deg, #a78bfa 0%, #38bdf8 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(167, 139, 250, 0.2);
        margin-bottom: 0px;
    }
    .app-subheader {
        color: #94a3b8;
        font-weight: 400;
        margin-top: -10px;
        margin-bottom: 25px;
    }
    
    /* Glassmorphic Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        margin-bottom: 15px;
    }
    .glass-card:hover {
        border-color: rgba(124, 58, 237, 0.4);
        box-shadow: 0 8px 32px 0 rgba(124, 58, 237, 0.15);
        transform: translateY(-2px);
    }
    
    /* Custom File Card */
    .file-card {
        background: rgba(124, 58, 237, 0.05);
        border: 1px solid rgba(124, 58, 237, 0.2);
        border-radius: 12px;
        padding: 12px;
        margin-top: 8px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    /* Status Badge */
    .status-badge {
        padding: 4px 8px;
        border-radius: 8px;
        font-size: 0.8rem;
        font-weight: 600;
        background: rgba(6, 182, 212, 0.15);
        color: #22d3ee;
        border: 1px solid rgba(6, 182, 212, 0.3);
    }
    
    /* Chat Styling */
    div[data-testid="stChatMessage"] {
        background-color: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 16px !important;
        padding: 15px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stChatMessage"]:hover {
        border-color: rgba(124, 58, 237, 0.25) !important;
        background-color: rgba(124, 58, 237, 0.01) !important;
    }
    
    /* Chat Input */
    div[data-testid="stChatInput"] {
        border-radius: 12px !important;
        border: 1px solid rgba(124, 58, 237, 0.2) !important;
        background-color: rgba(15, 10, 28, 0.8) !important;
    }
    
    /* File Uploader styling */
    div[data-testid="stFileUploader"] {
        border: 2px dashed rgba(124, 58, 237, 0.25) !important;
        background-color: rgba(124, 58, 237, 0.02) !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #a78bfa !important;
        background-color: rgba(124, 58, 237, 0.05) !important;
    }
    
    /* Custom buttons */
    .stButton>button {
        background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(124, 58, 237, 0.5) !important;
    }
    
    /* Glow highlights */
    .glow-text {
        text-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
    }
    
    /* Sidebar Column Layout Alignment */
    section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    /* Sidebar Select button styling */
    section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button {
        text-align: left !important;
        width: 100% !important;
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #cbd5e1 !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        font-weight: 500 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        transition: all 0.2s ease !important;
    }
    section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:nth-child(1) .stButton > button:hover {
        background: rgba(124, 58, 237, 0.15) !important;
        border-color: rgba(124, 58, 237, 0.4) !important;
        color: #ffffff !important;
    }
    
    /* Sidebar Delete/Rename button styling */
    section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:nth-child(2) .stButton > button {
        background: transparent !important;
        border: none !important;
        color: #94a3b8 !important;
        box-shadow: none !important;
        font-size: 1.2rem !important;
        padding: 4px 8px !important;
        margin-top: 0px !important;
        width: 100% !important;
        min-width: unset !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease !important;
    }
    section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] > div:nth-child(2) .stButton > button:hover {
        background: rgba(124, 58, 237, 0.15) !important;
        color: #a78bfa !important;
        border-radius: 6px !important;
    }

    /* Compact Attachment Bar above Chat Input */
    div[data-testid="stFileUploader"] {
        border: 1px dashed rgba(124, 58, 237, 0.25) !important;
        background-color: rgba(124, 58, 237, 0.02) !important;
        border-radius: 12px !important;
        padding: 6px 12px !important;
        min-height: 48px !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #a78bfa !important;
        background-color: rgba(124, 58, 237, 0.05) !important;
    }
    div[data-testid="stFileUploader"] section {
        padding: 0 !important;
    }
    div[data-testid="stFileUploader"] label {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Document Parsing Helpers
def extract_text_from_pdf(file_bytes):
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- Page {i+1} ---\n{page_text}"
        return text.strip()
    except Exception as e:
        return f"Error parsing PDF: {str(e)}"

def extract_text_from_docx(file_bytes):
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        text = []
        for para in doc.paragraphs:
            if para.text.strip():
                text.append(para.text)
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip() for cell in row.cells]
                text.append(" | ".join(row_text))
        return "\n".join(text)
    except Exception as e:
        return f"Error parsing DOCX: {str(e)}"

def extract_text_from_csv(file_bytes):
    try:
        decoded = file_bytes.decode('utf-8', errors='ignore')
        reader = csv.reader(io.StringIO(decoded))
        text = []
        for i, row in enumerate(reader):
            if i < 500:  # Restrict to first 500 rows to prevent context blowing up
                text.append(" | ".join(row))
            else:
                text.append("... [CSV truncated due to length] ...")
                break
        return "\n".join(text)
    except Exception as e:
        return f"Error parsing CSV: {str(e)}"

def process_uploaded_file(uploaded_file):
    name = uploaded_file.name
    file_bytes = uploaded_file.read()
    size_kb = len(file_bytes) / 1024
    
    # Reset read pointer
    uploaded_file.seek(0)
    
    file_type = name.split('.')[-1].lower()
    text = ""
    native_part = None
    
    # Parse depending on type
    if file_type == 'txt':
        text = file_bytes.decode('utf-8', errors='ignore')
    elif file_type == 'pdf':
        text = extract_text_from_pdf(file_bytes)
        native_part = {"mime_type": "application/pdf", "data": file_bytes}
    elif file_type == 'docx':
        text = extract_text_from_docx(file_bytes)
    elif file_type == 'csv':
        text = extract_text_from_csv(file_bytes)
    elif file_type in ['png', 'jpg', 'jpeg', 'webp']:
        text = f"[Image File: {name}] - visual parsing supported."
        native_part = {"mime_type": f"image/{'jpeg' if file_type=='jpg' else file_type}", "data": file_bytes}
    else:
        text = f"Unsupported file type: {file_type}"
        
    return {
        "name": name,
        "type": file_type,
        "size": f"{size_kb:.1f} KB",
        "text": text,
        "native_part": native_part,
        "tokens_estimate": len(text.split()) * 1.3  # rough estimate
    }

# Database Setup & Hashing Helpers

DB_FILE = "users.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16).hex()
    pw_hash = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('utf-8'), 
        100000
    ).hex()
    return pw_hash, salt

def register_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        pw_hash, salt = hash_password(password)
        created_at = datetime.datetime.now().isoformat()
        c.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?)", 
            (username.strip(), pw_hash, salt, created_at)
        )
        conn.commit()
        return True, "Registration successful! You can now log in."
    except sqlite3.IntegrityError:
        return False, "Username already exists."
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password_hash, salt FROM users WHERE username = ?", (username.strip(),))
    row = c.fetchone()
    conn.close()
    if row:
        stored_hash, salt = row
        pw_hash, _ = hash_password(password, salt)
        if pw_hash == stored_hash:
            return True
    return False

# Initialize the SQLite Database
init_db()

# Chat History Persistence Helpers

HISTORY_DIR = "chat_histories"
os.makedirs(HISTORY_DIR, exist_ok=True)

def list_chats():
    username = st.session_state.get("username", "default")
    chats = []
    for f in os.listdir(HISTORY_DIR):
        if f.endswith(".json") and f.startswith(f"{username}_"):
            path = os.path.join(HISTORY_DIR, f)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    # Only list chats with messages
                    if data.get("messages"):
                        chats.append(data)
            except Exception:
                pass
    chats.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return chats

def save_chat(session_id, title, messages):
    username = st.session_state.get("username", "default")
    path = os.path.join(HISTORY_DIR, f"{username}_{session_id}.json")
    data = {
        "id": session_id,
        "title": title,
        "messages": messages,
        "updated_at": datetime.datetime.now().isoformat()
    }
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def delete_chat_file(session_id):
    username = st.session_state.get("username", "default")
    path = os.path.join(HISTORY_DIR, f"{username}_{session_id}.json")
    if os.path.exists(path):
        os.remove(path)

# Session State Initialization
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None

if st.session_state["logged_in"]:
    if "uploaded_files" not in st.session_state:
        st.session_state["uploaded_files"] = {}
    if "chat_mode_selection" not in st.session_state:
        st.session_state["chat_mode_selection"] = "Smart Router (Agent)"
    if "chat_input_val" not in st.session_state:
        st.session_state["chat_input_val"] = ""
    if "current_chat_id" not in st.session_state:
        existing_chats = list_chats()
        if existing_chats:
            st.session_state["current_chat_id"] = existing_chats[0]["id"]
            st.session_state["messages"] = existing_chats[0]["messages"]
            st.session_state["chat_title"] = existing_chats[0]["title"]
        else:
            new_id = str(uuid.uuid4())
            st.session_state["current_chat_id"] = new_id
            st.session_state["messages"] = []
            st.session_state["chat_title"] = "New Conversation"
            save_chat(new_id, "New Conversation", [])

# Auth Flow Guard
if not st.session_state["logged_in"]:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
        if logo_base64:
            st.markdown(f"""
            <div class="glass-card" style="text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                <img src="{logo_base64}" style="width: 80px; height: 80px; border-radius: 16px; margin-bottom: 15px; box-shadow: 0 0 20px rgba(124, 58, 237, 0.4); object-fit: cover;">
                <h1 style="margin-bottom:0px; background: linear-gradient(135deg, #a78bfa 0%, #38bdf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.2rem; font-weight: 800;">NexaBot</h1>
                <p style="color: #94a3b8; font-size: 0.95rem; margin-top: 5px;">Multi-Modal AI Document Assistant</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="glass-card" style="text-align: center;">
                <h1 style="margin-bottom:0px; background: linear-gradient(135deg, #a78bfa 0%, #38bdf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">NexaBot</h1>
                <p style="color: #94a3b8; font-size: 0.95rem; margin-top: 5px;">Multi-Modal AI Document Assistant</p>
            </div>
            """, unsafe_allow_html=True)
        
        login_tab, register_tab = st.tabs(["Login", "Register"])
        
        with login_tab:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            u_login = st.text_input("Username", key="u_login_input", placeholder="Enter your username...")
            p_login = st.text_input("Password", type="password", key="p_login_input", placeholder="Enter your password...")
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if st.button("Log In", use_container_width=True):
                if not u_login or not p_login:
                    st.error("Please fill in all fields.")
                else:
                    if authenticate_user(u_login, p_login):
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = u_login.strip()
                        st.toast(f"Welcome back, {u_login}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                        
        with register_tab:
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            u_reg = st.text_input("Choose Username", key="u_reg_input", placeholder="Choose a username...")
            p_reg = st.text_input("Choose Password", type="password", key="p_reg_input", placeholder="Choose a password...")
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            if st.button("Create Account", use_container_width=True):
                if not u_reg or not p_reg:
                    st.error("Please fill in all fields.")
                elif len(u_reg.strip()) < 3:
                    st.error("Username must be at least 3 characters long.")
                elif len(p_reg) < 4:
                    st.error("Password must be at least 4 characters long.")
                else:
                    success, msg = register_user(u_reg, p_reg)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)
    st.stop()

# Sidebar UI
with st.sidebar:
    if logo_base64:
        st.markdown(f"""
        <div style="text-align: center; padding: 10px 0;">
            <img src="{logo_base64}" style="width: 60px; height: 60px; border-radius: 12px; margin-bottom: 10px; box-shadow: 0 0 15px rgba(124, 58, 237, 0.3); object-fit: cover; display: block; margin-left: auto; margin-right: auto;">
            <h2 style='text-align: center; margin-bottom: 0px; font-weight: 700; color: #ffffff; font-size: 1.5rem;'>NexaBot Settings</h2>
            <p style='text-align: center; color: #8b5cf6; font-size: 0.85rem; margin-top: 2px;'>Configure your Multi-Modal Agent</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<h2 style='text-align: center; margin-bottom: 0px;'>Settings</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #8b5cf6; font-size: 0.9rem;'>Configure your Multi-Modal Agent</p>", unsafe_allow_html=True)
    
    # API Key is loaded from .env file
    
    st.markdown("---")

    # Profile Card in Sidebar (Moved up to be visible without scrolling)
    initial_letter = st.session_state['username'][0].upper() if st.session_state.get('username') else 'U'
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 12px; padding: 12px; background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; margin-bottom: 12px;">
        <div style="font-size: 1.4rem; font-weight: 700; color: #ffffff; background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%); border-radius: 50%; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 10px rgba(124, 58, 237, 0.4);">
            {initial_letter}
        </div>
        <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; width: 100%;">
            <strong style="color: #ffffff; font-size: 0.95rem; display: block; overflow: hidden; text-overflow: ellipsis; text-align: left;">{st.session_state['username']}</strong>
            <span style="color: #94a3b8; font-size: 0.75rem; display: block; text-align: left;">Active Profile</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Log Out", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        st.session_state["uploaded_files"] = {}
        st.session_state["messages"] = []
        st.rerun()

    st.markdown("---")
    
    # Conversations Section
    st.markdown("### Conversations")
    if st.button("New Chat Session", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state["current_chat_id"] = new_id
        st.session_state["messages"] = []
        st.session_state["chat_title"] = "New Conversation"
        save_chat(new_id, "New Conversation", [])
        st.rerun()
        
    chats = list_chats()
    for chat_info in chats:
        cid = chat_info["id"]
        title = chat_info["title"]
        active = (cid == st.session_state["current_chat_id"])
        
        if st.session_state.get("renaming_chat_id") == cid:
            # Render rename text input row
            new_title = st.text_input(
                "Rename Chat",
                value=title,
                key=f"rename_input_{cid}",
                label_visibility="collapsed"
            )
            col_save, col_cancel = st.columns([1, 1])
            with col_save:
                if st.button("Save", key=f"save_rename_{cid}"):
                    if new_title.strip():
                        save_chat(cid, new_title.strip(), chat_info["messages"])
                        if cid == st.session_state["current_chat_id"]:
                            st.session_state["chat_title"] = new_title.strip()
                    del st.session_state["renaming_chat_id"]
                    st.rerun()
            with col_cancel:
                if st.button("Cancel", key=f"cancel_rename_{cid}"):
                    del st.session_state["renaming_chat_id"]
                    st.rerun()
        else:
            col_c, col_d = st.columns([5, 1])
            with col_c:
                btn_label = f"{title}"
                if st.button(btn_label, key=f"sel_{cid}", use_container_width=True):
                    st.session_state["current_chat_id"] = cid
                    st.session_state["messages"] = chat_info["messages"]
                    st.session_state["chat_title"] = title
                    st.rerun()
            with col_d:
                # Show X mark to delete
                if st.button("✖", key=f"del_chat_{cid}", help="Delete chat permanently"):
                    delete_chat_file(cid)
                    if cid == st.session_state["current_chat_id"]:
                        del st.session_state["current_chat_id"]
                    st.rerun()
                
    st.markdown("---")
    
    # Model Selection
    model_choice = st.selectbox(
        "Select Brain Model",
        options=supported_models,
        index=default_index,
        help="Dynamically loaded from your Gemini API project permissions."
    )
    
    # Agent Mode
    chat_mode_val = st.radio(
        "AI Agent Routing Mode",
        options=["Smart Router (Agent)", "Document Grounded Chat", "General Chat"],
        key="chat_mode_selection",
        help="Smart Router decides if your question needs document scans. Grounded Chat uses documents for context. General Chat ignores documents."
    )
    st.session_state["chat_mode"] = chat_mode_val
    
    st.markdown("---")
    
    # Document Upload Zone is now placed in the main chat panel as an attachment pin
                    
    # Display list of currently scanned files
    if st.session_state["uploaded_files"]:
        st.markdown("### Scanned Files")
        for filename, info in list(st.session_state["uploaded_files"].items()):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"""
                <div class="file-card">
                    <div>
                        <strong style='font-size:0.9rem;'>{filename}</strong><br>
                        <span style='font-size:0.75rem; color:#94a3b8;'>{info['type'].upper()} • {info['size']}</span>
                    </div>
                    <span class="status-badge">Scanned</span>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
                if st.button("Remove", key=f"del_{filename}", help="Remove from scanner context"):
                    del st.session_state["uploaded_files"][filename]
                    st.rerun()
        
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("Clear All Scanned Files", use_container_width=True):
            st.session_state["uploaded_files"] = {}
            st.rerun()



# Main Panel UI
if not st.session_state["messages"]:
    if logo_base64:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px;">
            <img src="{logo_base64}" style="width: 50px; height: 50px; border-radius: 10px; box-shadow: 0 0 15px rgba(124, 58, 237, 0.4); object-fit: cover;">
            <div>
                <h1 class='app-header' style='margin: 0; line-height: 1.1;'>NexaBot</h1>
                <p class='app-subheader' style='margin: 0; color: #94a3b8; font-weight: 400;'>Next-Gen Multi-Modal AI Document Scanner & Chatbot</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<h1 class='app-header'>NexaBot</h1>", unsafe_allow_html=True)
        st.markdown("<p class='app-subheader'>Next-Gen Multi-Modal AI Document Scanner & Chatbot</p>", unsafe_allow_html=True)

    if not api_key:
        st.warning("**Gemini API Key is missing or using placeholder value.** Please open the `.env` file in the project directory, add your `GEMINI_API_KEY`, and refresh this page.")

    # Quick Action Suggestions
    st.markdown("### Quick Actions & Prompts")
    q_cols = st.columns(3)
    with q_cols[0]:
        if st.button("Summarize Uploaded Documents", use_container_width=True):
            st.session_state["chat_input_val"] = "Provide a comprehensive summary of all uploaded documents, outlining their key findings and details."
            st.rerun()
    with q_cols[1]:
        if st.button("Analyze Structure & Layout", use_container_width=True):
            st.session_state["chat_input_val"] = "What documents have been uploaded? List their file names, sizes, and formats. Summarize their structural outline."
            st.rerun()
    with q_cols[2]:
        if st.button("Ask a General AI Question", use_container_width=True):
            st.session_state["chat_input_val"] = "Explain the concept of Multi-Modal AI Agents and how they differ from text-only models."
            st.rerun()

# Chat Area
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        
# Document Attachment (Pin Style)
if not st.session_state["messages"]:
    st.markdown("##### Attach Documents / Images for Scanning")
    uploaded_files = st.file_uploader(
        "Upload files for scanning",
        type=['pdf', 'docx', 'txt', 'csv', 'png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if uploaded_files:
        for file in uploaded_files:
            if file.name not in st.session_state["uploaded_files"]:
                with st.spinner(f"Scanning {file.name}..."):
                    processed = process_uploaded_file(file)
                    st.session_state["uploaded_files"][file.name] = processed
                    st.toast(f"Successfully scanned {file.name}!")

# User Input Processing
if prompt := st.chat_input("Ask about your documents, analyze images, or query general knowledge...", key="chat_input_val"):
    # Render user message
    st.session_state["messages"].append({"role": "user", "content": prompt})
    
    # Auto-update title if it's the default
    if st.session_state.get("chat_title") == "New Conversation":
        words = prompt.split()
        title = " ".join(words[:4])
        if len(words) > 4:
            title += "..."
        st.session_state["chat_title"] = title
        
    save_chat(st.session_state["current_chat_id"], st.session_state["chat_title"], st.session_state["messages"])
    
    with st.chat_message("user"):
        st.write(prompt)
        
    # Generate Response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        # Verify API Key
        if not api_key:
            response_placeholder.error("Gemini API Key not configured. Please set `GEMINI_API_KEY` in your `.env` file in the project folder and restart the app.")
            st.session_state["messages"].append({"role": "assistant", "content": "Error: Missing Gemini API Key in `.env` file."})
        else:
            with st.spinner("NexaBot is thinking..."):
                try:
                    # Initialize Model
                    model = genai.GenerativeModel(model_choice)
                    
                    # Decide Context usage based on Mode
                    chat_mode = st.session_state["chat_mode"]
                    active_files = st.session_state["uploaded_files"]
                    
                    use_docs = False
                    selected_files_info = []
                    
                    if chat_mode == "Document Grounded Chat":
                        use_docs = True
                    elif chat_mode == "Smart Router (Agent)":
                        # Agent Decider
                        if len(active_files) > 0:
                            # Quick local bypass for greetings/short queries
                            cleaned_prompt = prompt.lower().strip().strip("?!.")
                            greetings = ["hi", "hello", "hey", "hola", "greetings", "howdy", "how are you", "who are you", "what can you do", "help"]
                            is_greeting = any(cleaned_prompt == g or cleaned_prompt.startswith(g + " ") for g in greetings) or len(cleaned_prompt.split()) <= 2
                            
                            if is_greeting:
                                use_docs = False
                                st.write("*Agent Router analysis: `NO` (Detected general greeting/query)*")
                            else:
                                file_names = list(active_files.keys())
                                decision_prompt = f"""
                                You are an orchestrator agent in a document assistant app.
                                The user query is: "{prompt}"
                                
                                We have the following scanned files in context:
                                {file_names}
                                
                                Does this query require scanning the uploaded documents to answer?
                                - For greetings, general questions (e.g., math, science, history), or meta-questions, respond with NO.
                                - Only respond with YES if the query specifically asks about the contents, details, or summaries of the uploaded files.
                                
                                Respond with exactly YES or NO. If YES, list the files that are needed, separated by commas (e.g. YES: doc1.pdf, doc2.png).
                                """
                                decider_model = genai.GenerativeModel(model_choice)
                                decision_res = decider_model.generate_content(decision_prompt).text.strip().upper()
                                
                                st.write(f"*Agent Router analysis: `{decision_res}`*")
                                
                                if "YES" in decision_res:
                                    use_docs = True
                                    # Parse out chosen files if specific files are mentioned, else use all
                                    for name in file_names:
                                        if name.lower() in decision_res.lower() or "YES" == decision_res:
                                            selected_files_info.append(name)
                                    if not selected_files_info:
                                        selected_files_info = file_names
                                else:
                                    use_docs = False
                        else:
                            use_docs = False
                    
                    # Build Gemini Request Content
                    contents = []
                    
                    if use_docs and active_files:
                        files_to_inject = selected_files_info if selected_files_info else list(active_files.keys())
                        
                        document_context = "--- SCANNED DOCUMENTS CONTEXT ---\n"
                        image_or_pdf_parts = []
                        
                        for fname in files_to_inject:
                            file_data = active_files[fname]
                            # If it's a native part (like Image or PDF visual), we can pass it directly to Gemini
                            if file_data["native_part"] is not None:
                                image_or_pdf_parts.append(file_data["native_part"])
                                document_context += f"[Visual File Attached: {fname} (Gemini is reading it natively)]\n"
                            else:
                                document_context += f"\n--- Start Document: {fname} ---\n"
                                document_context += file_data["text"]
                                document_context += f"\n--- End Document: {fname} ---\n"
                                
                        document_context += "\nUse the scanned document details above to answer the user's prompt. If the answer cannot be found in the documents, state that clearly, but try to answer using general reasoning if appropriate."
                        
                        # Set instructions
                        contents.append(document_context)
                        
                        # Add any visual parts (like images or PDF bytes)
                        for part in image_or_pdf_parts:
                            contents.append(part)
                            
                    # Chat History
                    # For a stateful multi-turn conversation, we can supply the past messages.
                    # To prevent context window explosion and keep it simple, we supply the recent history.
                    chat_context = ""
                    if len(st.session_state["messages"]) > 1:
                        chat_context = "--- RECENT CHAT HISTORY ---\n"
                        for prev_msg in st.session_state["messages"][:-1]:
                            chat_context += f"{prev_msg['role'].capitalize()}: {prev_msg['content']}\n"
                        chat_context += "---------------------------\n"
                        contents.append(chat_context)
                    
                    # Add current prompt
                    contents.append(f"User Query: {prompt}")
                    
                    # Inject System Instructions
                    system_instruction = """
                    You are NexaBot, a highly advanced Multi-Modal AI Document Scanner and Chatbot.
                    Your goal is to scan documents, extract information, visual details, text, and answer user queries with high accuracy.
                    - If document context is provided, ground your answers in the document context. Extract tables, keys, and values.
                    - If images/PDFs are attached natively, inspect them carefully. Check charts, layout, diagrams, and handwriting.
                    - Be helpful, concise, and professional. 
                    - Use markdown styling for structure (e.g. bold, bullet points, tables, code blocks).
                    - If the user asks a general query (not about documents), answer it using your general knowledge in a creative, helpful way.
                    """
                    
                    # Run Generation
                    # Set system instruction
                    full_model = genai.GenerativeModel(
                        model_name=model_choice,
                        system_instruction=system_instruction
                    )
                    
                    response = full_model.generate_content(contents)
                    
                    # Render response
                    response_placeholder.markdown(response.text)
                    st.session_state["messages"].append({"role": "assistant", "content": response.text})
                    save_chat(st.session_state["current_chat_id"], st.session_state["chat_title"], st.session_state["messages"])
                    
                except Exception as e:
                    err_msg = str(e)
                    if "429" in err_msg or "quota" in err_msg.lower():
                        friendly_error = (
                            f"Quota Exceeded for model: {model_choice}\n\n"
                            "You have reached the free tier limits for the current model. "
                            "Please select a different model (such as Gemini 2.5 Flash, Gemini 2.5 Pro, or Gemini 2 Flash) in the Settings sidebar to continue chatting without delay!"
                        )
                        response_placeholder.warning(friendly_error)
                        st.session_state["messages"].append({"role": "assistant", "content": friendly_error})
                    else:
                        response_placeholder.error(f"Error calling Gemini API: {err_msg}")
                        st.session_state["messages"].append({"role": "assistant", "content": f"An error occurred: {err_msg}"})
                    save_chat(st.session_state["current_chat_id"], st.session_state["chat_title"], st.session_state["messages"])

# Clear Chat History Button
if st.session_state["messages"]:
    st.sidebar.markdown("---")
    if st.sidebar.button("Clear Messages in Active Chat"):
        st.session_state["messages"] = []
        save_chat(st.session_state["current_chat_id"], st.session_state["chat_title"], [])
        st.rerun()
