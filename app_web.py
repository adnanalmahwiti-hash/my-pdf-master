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

# --- 2. SESSION STATE ---
if 'rotation_states' not in st.session_state: st.session_state.rotation_states = {}
if 'uploader_key' not in st.session_state: st.session_state.uploader_key = 0

# --- 3. THREAD-SAFE LOGGING ---
lock = threading.Lock()
def write_global_log(tool, count, size_in, size_out, duration):
    log_file = "web_activity_log.txt"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    saved = size_in - size_out
    log_entry = f"[{now}] {tool.upper()} | Files: {count} | Saved: {saved:.2f}MB | {duration:.2f}s\n"
    with lock:
        try:
            with open(log_file, "a") as f: f.write(log_entry)
        except: pass

# --- 4. HELPERS ---
def get_thumbnail(file_bytes, ext, manual_rot=0):
    try:
        if ext == "pdf":
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(0.15, 0.15))
            img = Image.open(BytesIO(pix.tobytes()))
            doc.close()
        else:
            img = Image.open(BytesIO(file_bytes))
        if manual_rot != 0: img = img.rotate(-manual_rot, expand=True)
        return ImageOps.fit(img, (200, 200), Image.Resampling.LANCZOS)
    except: return None

# --- 5. CORE ENGINES ---
def process_universal_merger(uploaded_files, password=None, rotations={}):
    res = fitz.open() 
    total_in = 0
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, f in enumerate(uploaded_files):
        status_text.text(f"Processing: {f.name}...")
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
            img.save(img_io, format='JPEG', quality=80)
            img_pdf_bytes = fitz.open("jpg", img_io.getvalue()).convert_to_pdf()
            with fitz.open("pdf", img_pdf_bytes) as img_doc:
                res.insert_pdf(img_doc)
        progress_bar.progress((idx + 1) / len(uploaded_files))
    
    out = BytesIO()
    if password: res.save(out, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw=password, owner_pw=password)
    else: res.save(out, garbage=4, deflate=True)
    
    final_data = out.getvalue()
    res.close()
    progress_bar.empty()
    status_text.empty()
    return final_data, total_in/(1024*1024), len(final_data)/(1024*1024)

def process_reducer(uploaded_files, deep=True):
    results, total_in, total_out = [], 0, 0
    progress_bar = st.progress(0)
    for idx, f in enumerate(uploaded_files):
        fb = f.read(); total_in += len(fb)
        doc = fitz.open(stream=fb, filetype="pdf")
        out_pdf = BytesIO()
        if deep:
            new_doc = fitz.open()
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
                new_page.insert_image(page.rect, stream=pix.tobytes("jpg", jpg_quality=60))
            new_doc.save(out_pdf, garbage=4, deflate=True); new_doc.close()
        else: doc.save(out_pdf, garbage=4, deflate=True)
        doc.close(); data = out_pdf.getvalue(); total_out += len(data)
        results.append({"name": f.name, "data": data})
        progress_bar.progress((idx + 1) / len(uploaded_files))
    progress_bar.empty()
    return results, total_in/(1024*1024), total_out/(1024*1024)

# --- 6. INTERFACE ---
st.sidebar.title("🛠️ Elite Suite Menu")
app_mode = st.sidebar.selectbox("Category", ["🔄 Converter", "📉 Reducer", "🖼️ ICO Maker", "📜 History"])

if app_mode == "🔄 Converter":
    col_up, col_clr = st.columns([5, 1])
    with col_clr:
        st.write("###") 
        if st.button("🗑️ Clear"):
            st.session_state.rotation_states = {}
            st.session_state.uploader_key += 1; st.rerun()
    
    files = st.file_uploader("Upload Files", type=["pdf", "jpg", "png", "jpeg"], accept_multiple_files=True, key=f"up_{st.session_state.uploader_key}")
    if files:
        grid = st.columns(6)
        for idx, f in enumerate(files):
            if f.name not in st.session_state.rotation_states: st.session_state.rotation_states[f.name] = 0
            f.seek(0)
            thumb = get_thumbnail(f.read(), f.name.split('.')[-1].lower(), st.session_state.rotation_states[f.name])
            with grid[idx % 6]:
                if thumb: st.image(thumb, width="stretch")
                c1, c2 = st.columns(2)
                # UNIQUE KEYS GENERATED HERE
                if c1.button("🔄", key=f"rot_{idx}_{f.name}"):
                    st.session_state.rotation_states[f.name] = (st.session_state.rotation_states[f.name] + 90) % 360; st.rerun()
                if c2.button("✖", key=f"res_{idx}_{f.name}"):
                    st.session_state.rotation_states[f.name] = 0; st.rerun()
                st.markdown(f'<p class="file-name-text">{f.name}</p>', unsafe_allow_html=True)
        
        st.divider()
        pass_val = st.text_input("Password (Optional)", type="password")
        if st.button("EXECUTE MERGE"):
            data, s_in, s_out = process_universal_merger(files, password=pass_val, rotations=st.session_state.rotation_states)
            st.download_button("📥 Download PDF", data=data, file_name="merged_result.pdf")
            write_global_log("MERGER", len(files), s_in, s_out, 1.0)

elif app_mode == "📉 Reducer":
    st.header("PDF Reducer")
    red_files = st.file_uploader("Select PDFs", type="pdf", accept_multiple_files=True)
    if red_files:
        mode = st.radio("Mode", ["Standard", "Deep Squeeze"])
        if st.button("START REDUCTION", key="btn_reduce_unique"):
            processed, s_in, s_out = process_reducer(red_files, deep=(mode == "Deep Squeeze"))
            st.success(f"Saved {(s_in - s_out):.2f} MB")
            for item in processed: st.download_button(f"📥 Download {item['name']}", data=item['data'], file_name=f"opt_{item['name']}")

elif app_mode == "🖼️ ICO Maker":
    st.header("ICO Maker")
    ico_files = st.file_uploader("Upload Images", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    if ico_files and st.button("CONVERT TO ICO"):
        for f in ico_files:
            img = Image.open(f)
            buf = BytesIO()
            img.save(buf, format='ICO', sizes=[(32,32), (64,64), (256,256)])
            st.download_button(f"📥 Download {f.name.split('.')[0]}.ico", data=buf.getvalue(), file_name=f"{f.name.split('.')[0]}.ico")

elif app_mode == "📜 History":
    st.header("History")
    if os.path.exists("web_activity_log.txt"):
        with open("web_activity_log.txt", "r") as f: st.text_area("Logs", f.read(), height=400)
    else: st.info("No logs.")