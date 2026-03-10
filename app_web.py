import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageOps
import os
import time
from io import BytesIO
from datetime import datetime

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="PDF Master: Elite Web", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    .stAlert { border-radius: 10px; }
    .stButton>button { border-radius: 8px; font-weight: bold; width: 100%; height: 2.2em; font-size: 14px;}
    .stDownloadButton>button { background-color: #007bff; color: white; border-radius: 8px; width: 100%; }
    [data-testid="stHorizontalBlock"] { gap: 0.5rem !important; }
    .stImage > img { border-radius: 12px; border: 1px solid #ddd; object-fit: cover; aspect-ratio: 1 / 1; position: relative; z-index: 1; }
    
    /* Overlay Buttons Positioning */
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

# --- 3. HELPERS ---
def write_global_log(tool, count, size_in, size_out, duration):
    log_file = "web_activity_log.txt"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    saved = size_in - size_out
    log_entry = f"[{now}] {tool.upper()} | Files: {count} | Saved: {saved:.2f}MB | {duration:.2f}s\n"
    try:
        with open(log_file, "a") as f: f.write(log_entry)
    except: pass

def get_thumbnail(file_bytes, ext, manual_rot=0):
    try:
        if ext == "pdf":
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
            img = Image.open(BytesIO(pix.tobytes()))
            doc.close()
        else:
            img = Image.open(BytesIO(file_bytes))
        if manual_rot != 0: img = img.rotate(-manual_rot, expand=True)
        return ImageOps.fit(img, (250, 250), Image.Resampling.LANCZOS)
    except: return None

# --- 4. CORE ENGINES ---
def process_reducer(uploaded_files, deep=True):
    results, total_in, total_out = [], 0, 0
    for f in uploaded_files:
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
    return results, total_in/(1024*1024), total_out/(1024*1024)

def process_universal_merger(uploaded_files, password=None, rotations={}):
    res = fitz.open() # Master PDF
    total_in = 0
    for f in uploaded_files:
        f.seek(0); fb = f.read(); total_in += len(fb)
        ext = f.name.split('.')[-1].lower()
        rot = rotations.get(f.name, 0)
        
        if ext == "pdf":
            with fitz.open(stream=fb, filetype="pdf") as m:
                if rot != 0:
                    for page in m: page.set_rotation((page.rotation + rot) % 360)
                res.insert_pdf(m)
        else:
            # Handle Image to PDF conversion
            img = Image.open(BytesIO(fb)).convert("RGB")
            if rot != 0: img = img.rotate(-rot, expand=True)
            img_io = BytesIO()
            img.save(img_io, format='JPEG', quality=85)
            # Create a 1-page PDF from the image bytes
            img_pdf_data = fitz.open("jpg", img_io.getvalue()).convert_to_pdf()
            with fitz.open("pdf", img_pdf_data) as img_doc:
                res.insert_pdf(img_doc)
    
    out = BytesIO()
    if password and len(password) > 0:
        res.save(out, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw=password, owner_pw=password)
    else:
        res.save(out, garbage=4, deflate=True, clean=True)
    
    final_data = out.getvalue()
    res.close()
    return final_data, total_in/(1024*1024), len(final_data)/(1024*1024)

def process_ico_maker(uploaded_files):
    results = []
    for f in uploaded_files:
        img = Image.open(f)
        out = BytesIO()
        img.save(out, format='ICO', sizes=[(32,32), (64,64), (128,128), (256,256)])
        results.append({"name": f.name.split('.')[0] + ".ico", "data": out.getvalue()})
    return results

# --- 5. MAIN INTERFACE ---
st.sidebar.title("🛠️ Tools Menu")
app_mode = st.sidebar.selectbox("Choose a category", ["🔄 Converter Mode", "📉 Reducer Mode", "📜 Management"])

# --- GROUP 1: CONVERTER MODE ---
if app_mode == "🔄 Converter Mode":
    tool_choice = st.radio("Select Tool", ["Universal Merger (PDF/IMG)", "Icon Maker (.ICO)"], horizontal=True)
    
    if tool_choice == "Universal Merger (PDF/IMG)":
        col_up, col_clr = st.columns([5, 1])
        with col_clr:
            st.write("###") 
            if st.button("🗑️ Clear"):
                st.session_state.rotation_states = {}
                st.session_state.uploader_key += 1; st.rerun()
        
        files = st.file_uploader("Upload PDF/Images", type=["pdf", "jpg", "png", "jpeg"], accept_multiple_files=True, key=f"up_{st.session_state.uploader_key}")
        if files:
            st.subheader("🖼️ Square Gallery Editor")
            grid = st.columns(6)
            for idx, f in enumerate(files):
                if f.name not in st.session_state.rotation_states: st.session_state.rotation_states[f.name] = 0
                f.seek(0); thumb = get_thumbnail(f.read(), f.name.split('.')[-1].lower(), st.session_state.rotation_states[f.name])
                with grid[idx % 6]:
                    if thumb: st.image(thumb, width="stretch")
                    c1, c2 = st.columns(2)
                    if c1.button("🔄", key=f"r_{f.name}"):
                        st.session_state.rotation_states[f.name] = (st.session_state.rotation_states[f.name] + 90) % 360; st.rerun()
                    if c2.button("✖", key=f"x_{f.name}"):
                        st.session_state.rotation_states[f.name] = 0; st.rerun()
                    st.markdown(f'<p class="file-name-text">{f.name}</p>', unsafe_allow_html=True)
            
            st.divider()
            pass_val = st.text_input("Optional: Set Password", type="password")
            if st.button("EXECUTE UNIVERSAL MERGE"):
                with st.spinner("Merging documents..."):
                    start_t = time.time()
                    data, s_in, s_out = process_universal_merger(files, password=pass_val, rotations=st.session_state.rotation_states)
                    dur = time.time() - start_t
                    st.download_button("📥 Download PDF", data=data, file_name="merged_output.pdf")
                    st.success(f"Success! Merged in {dur:.2f}s"); write_global_log("MERGER", len(files), s_in, s_out, dur)

    elif tool_choice == "Icon Maker (.ICO)":
        st.header("Icon Maker (.ICO)")
        ico_files = st.file_uploader("Upload Images", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
        if ico_files and st.button("CONVERT TO ICO"):
            results = process_ico_maker(ico_files)
            for res in results: st.download_button(f"📥 Download {res['name']}", data=res['data'], file_name=res['name'])

# --- GROUP 2: REDUCER MODE ---
elif app_mode == "📉 Reducer Mode":
    st.header("PDF Size Reducer")
    red_files = st.file_uploader("Select PDFs", type="pdf", accept_multiple_files=True, key="red_up")
    if red_files:
        comp_mode = st.radio("Compression Level", ["Standard", "Deep Squeeze"])
        if st.button("START REDUCTION"):
            start_t = time.time()
            processed, s_in, s_out = process_reducer(red_files, deep=(comp_mode == "Deep Squeeze"))
            dur = time.time() - start_t
            st.success(f"Compressed! Saved {(s_in - s_out):.2f} MB")
            for item in processed: st.download_button(f"📥 Download {item['name']}", data=item['data'], file_name=f"opt_{item['name']}")
            write_global_log(comp_mode, len(red_files), s_in, s_out, dur)

# --- GROUP 3: MANAGEMENT ---
elif app_mode == "📜 Management":
    st.header("Audit & History")
    if os.path.exists("web_activity_log.txt"):
        with open("web_activity_log.txt", "r") as f: st.text_area("Activity History", f.read(), height=500)
        if st.button("Clear Log History"): 
            try: os.remove("web_activity_log.txt"); st.rerun()
            except: st.error("Could not clear log.")
    else: st.info("No activity recorded yet.")