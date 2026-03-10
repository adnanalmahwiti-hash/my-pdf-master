import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageOps
import os
import time
from io import BytesIO
from datetime import datetime
import threading

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="PDF Master: Elite Web", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .stAlert { border-radius: 10px; }
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; height: 2.2em; font-size: 14px;}
    .stDownloadButton>button { background-color: #007bff; color: white; border-radius: 8px; width: 100%; }
    [data-testid="stHorizontalBlock"] { gap: 0.5rem !important; }
    .stImage > img { border-radius: 12px; border: 1px solid #ddd; object-fit: cover; aspect-ratio: 1 / 1; position: relative; z-index: 1; }
    
    div[data-testid="stColumn"] > div > div > div > div[data-testid="stHorizontalBlock"] {
        margin-top: -50px; position: relative; z-index: 10; padding: 0 10px;
    }
    div[data-testid="stColumn"] button {
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #333 !important; border: 1px solid #ccc !important; box-shadow: 0px 2px 5px rgba(0,0,0,0.2);
    }
    .file-name-text { font-size: 10px; text-align: center; color: #888; margin-top: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION STATE (The Cookie Fix) ---
# We use a 'session_id' to force a hard reset of all widgets if things get buggy
if 'rotation_states' not in st.session_state: st.session_state.rotation_states = {}
if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0

def hard_reset():
    """Wipes session data to clear 'stale' browser cookie interference."""
    for key in list(st.session_state.keys()):
        if key != 'uploader_key':
            del st.session_state[key]
    st.session_state.rotation_states = {}
    st.session_state.uploader_key += 1
    st.rerun()

# --- 3. HELPERS ---
def get_thumbnail(file_bytes, ext, manual_rot=0):
    try:
        if ext == "pdf":
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(0.1, 0.1)) # Extra light for mobile
            img = Image.open(BytesIO(pix.tobytes()))
            doc.close()
        else:
            img = Image.open(BytesIO(file_bytes))
        
        if manual_rot != 0: img = img.rotate(-manual_rot, expand=True)
        return ImageOps.fit(img, (180, 180), Image.Resampling.LANCZOS)
    except: return None

# --- 4. CORE ENGINES ---
def process_universal_merger(uploaded_files, password=None, rotations={}):
    res = fitz.open() 
    total_in = 0
    progress_bar = st.progress(0)
    
    for idx, f in enumerate(uploaded_files):
        f.seek(0); fb = f.read(); total_in += len(fb)
        ext = f.name.split('.')[-1].lower()
        rot = rotations.get(f.name, 0)
        
        if ext == "pdf":
            with fitz.open(stream=fb, filetype="pdf") as m:
                if rot != 0:
                    for page in m: page.set_rotation((page.rotation + rot) % 360)
                res.insert_pdf(m)
        else:
            img = Image.open(BytesIO(fb)).convert("RGB")
            if rot != 0: img = img.rotate(-rot, expand=True)
            img_io = BytesIO()
            img.save(img_io, format='JPEG', quality=75)
            img_pdf_data = fitz.open("jpg", img_io.getvalue()).convert_to_pdf()
            with fitz.open("pdf", img_pdf_data) as img_doc:
                res.insert_pdf(img_doc)
        progress_bar.progress((idx + 1) / len(uploaded_files))
    
    out = BytesIO()
    if password: res.save(out, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw=password, owner_pw=password)
    else: res.save(out, garbage=4, deflate=True)
    
    final_data = out.getvalue()
    res.close()
    progress_bar.empty()
    return final_data

# --- 5. INTERFACE ---
st.sidebar.title("🛠️ Elite Suite Menu")
app_mode = st.sidebar.selectbox("Category", ["🔄 Converter", "📉 Reducer", "📜 History"])

if app_mode == "🔄 Converter":
    col_up, col_clr = st.columns([5, 1])
    with col_clr:
        st.write("###") 
        if st.button("🗑️ Reset App", help="Clears cookies/cache and resets uploader"):
            hard_reset()
    
    # Use the uploader_key to force the widget to re-render from scratch
    files = st.file_uploader("Upload PDF or Images", type=["pdf", "jpg", "png", "jpeg"], 
                             accept_multiple_files=True, 
                             key=f"up_{st.session_state.uploader_key}")

    if files:
        st.subheader(f"🖼️ Gallery ({len(files)} files)")
        grid = st.columns(6)
        for idx, f in enumerate(files):
            if f.name not in st.session_state.rotation_states: 
                st.session_state.rotation_states[f.name] = 0
            
            f.seek(0)
            f_bytes = f.read()
            ext = f.name.split('.')[-1].lower()
            thumb = get_thumbnail(f_bytes, ext, st.session_state.rotation_states[f.name])
            
            with grid[idx % 6]:
                if thumb: st.image(thumb, width="stretch")
                c1, c2 = st.columns(2)
                # Unique keys including idx and uploader_key to prevent cookie collisions
                if c1.button("🔄", key=f"r_{st.session_state.uploader_key}_{idx}"):
                    st.session_state.rotation_states[f.name] = (st.session_state.rotation_states[f.name] + 90) % 360; st.rerun()
                if c2.button("✖", key=f"x_{st.session_state.uploader_key}_{idx}"):
                    st.session_state.rotation_states[f.name] = 0; st.rerun()
                st.markdown(f'<p class="file-name-text">{f.name}</p>', unsafe_allow_html=True)
        
        st.divider()
        pass_val = st.text_input("Password (Optional)", type="password")
        if st.button("EXECUTE MERGE"):
            data = process_universal_merger(files, password=pass_val, rotations=st.session_state.rotation_states)
            st.download_button("📥 Download PDF", data=data, file_name="merged_result.pdf")