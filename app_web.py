import streamlit as st
import os
import time
import zipfile
from io import BytesIO

# Import Custom Modules
from modules.auth import check_password
from modules.ui_styles import apply_custom_css
from modules.pdf_engine import process_universal_merger, process_reducer, process_ico_maker, pdf_to_word
from modules.utils import write_global_log, get_thumbnail
from modules.media_engine import convert_video

# 1. Access Control
if not check_password():
    st.stop()

# 2. Initialize UI & State
apply_custom_css()

if 'rotation_states' not in st.session_state: 
    st.session_state.rotation_states = {}
if 'uploader_key' not in st.session_state: 
    st.session_state.uploader_key = 0

def hard_reset():
    """Triggers a clean wipe of uploader and local cache."""
    st.session_state.rotation_states = {}
    st.session_state.uploader_key += 1
    st.rerun()

# 3. Sidebar Navigation
st.sidebar.title("🚀 Elite Suite")
if st.sidebar.button("🔓 Logout"):
    del st.session_state["password_correct"]
    st.rerun()

app_mode = st.sidebar.selectbox("Choose Category", 
    ["🔄 Converter Mode", "📉 Reducer Mode", "🎬 Media Suite", "📜 Management"])

# --- CONVERTER MODE ---
if app_mode == "🔄 Converter Mode":
    tool = st.radio("Tool", ["Universal Merger", "PDF to Word", "ICO Maker"], horizontal=True)
    
    if tool == "Universal Merger":
        col_up, col_clr = st.columns([5, 1])
        with col_clr:
            st.write("###")
            if st.button("🗑️ Reset"): hard_reset()
            
        files = st.file_uploader("Upload PDF or Images", type=["pdf","jpg","png","jpeg"], 
                                 accept_multiple_files=True, key=f"up_{st.session_state.uploader_key}")
        
        if files:
            st.subheader(f"🖼️ Gallery ({len(files)} files)")
            grid = st.columns(6)
            for idx, f in enumerate(files):
                if f.name not in st.session_state.rotation_states: 
                    st.session_state.rotation_states[f.name] = 0
                
                f.seek(0)
                thumb = get_thumbnail(f.read(), f.name.split('.')[-1].lower(), st.session_state.rotation_states[f.name])
                
                with grid[idx % 6]:
                    if thumb: st.image(thumb, width="stretch")
                    c1, c2 = st.columns(2)
                    if c1.button("🔄", key=f"r_{st.session_state.uploader_key}_{idx}"):
                        st.session_state.rotation_states[f.name] = (st.session_state.rotation_states[f.name] + 90) % 360
                        st.rerun()
                    if c2.button("✖", key=f"x_{st.session_state.uploader_key}_{idx}"):
                        st.session_state.rotation_states[f.name] = 0
                        st.rerun()
                    st.markdown(f'<p class="file-name-text">{f.name}</p>', unsafe_allow_html=True)
            
            st.divider()
            pass_val = st.text_input("Optional PDF Password", type="password")
            if st.button("EXECUTE MERGE"):
                start_t = time.time()
                data = process_universal_merger(files, password=pass_val, rotations=st.session_state.rotation_states)
                dur = time.time() - start_t
                st.download_button("📥 Download PDF", data=data, file_name="merged_result.pdf")
                write_global_log("MERGER", len(files), dur)

    elif tool == "PDF to Word":
        st.subheader("📄 PDF to Word Converter")
        pdf_file = st.file_uploader("Upload PDF", type="pdf", key="p2w_up")
        if pdf_file and st.button("Convert to Word"):
            with st.spinner("Processing..."):
                word_data = pdf_to_word(pdf_file.read())
                st.download_button("📥 Download Word Doc", word_data, f"{pdf_file.name}.docx")
                
    else:
        st.header("Icon Maker (.ICO)")
        ico_files = st.file_uploader("Upload Images", type=["jpg","png","jpeg"], accept_multiple_files=True)
        if ico_files and st.button("CONVERT TO ICO"):
            res_list = process_ico_maker(ico_files)
            for r in res_list:
                st.download_button(f"📥 Download {r['name']}", data=r['data'], file_name=r['name'])

# --- 🎬 MEDIA MODE (New) ---
elif app_mode == "🎬 Media Mode":
    st.header("Video Processing Suite")
    st.subheader("🎥 Video Format Transcoder")
    vid_file = st.file_uploader("Upload Video", type=["mp4", "mov", "avi"], key="v_up")
    target = st.selectbox("Target Format", ["MP4", "GIF"])
    
    if vid_file and st.button("Start Conversion"):
        with st.spinner("Processing video... this may take a moment"):
            vid_data = convert_video(vid_file, target)
            st.download_button(f"📥 Download {target}", vid_data, f"converted.{target.lower()}")

# --- REDUCER MODE ---
elif app_mode == "📉 Reducer Mode":
    st.header("PDF Size Reducer")
    red_files = st.file_uploader("Select PDFs", type="pdf", accept_multiple_files=True)
    
    if red_files:
        comp_mode = st.radio("Compression", ["Standard", "Deep Squeeze"])
        if st.button("START REDUCTION"):
            start_t = time.time()
            processed = process_reducer(red_files, deep=(comp_mode == "Deep Squeeze"))
            dur = time.time() - start_t
            
            # ZIP Feature
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zf:
                for item in processed:
                    zf.writestr(item["name"], item["data"])
            
            st.download_button("📥 Download All as ZIP", data=zip_buffer.getvalue(), file_name="compressed_pdfs.zip")
            
            for item in processed: 
                st.download_button(f"📥 Download {item['name']}", data=item['data'], file_name=item['name'])
            
            write_global_log(comp_mode, len(red_files), dur)

# --- MANAGEMENT ---
elif app_mode == "📜 Management":
    st.header("Audit History")
    if os.path.exists("web_activity_log.txt"):
        with open("web_activity_log.txt", "r") as f:
            st.text_area("Logs", f.read(), height=400)
        if st.button("Clear Log History"):
            os.remove("web_activity_log.txt")
            st.rerun()
    else:
        st.info("No activity recorded yet.")


# --- NEW: MEDIA SUITE ---
if app_mode == "🎬 Media Suite":
    st.header("Media Suite")
    sub_tool = st.tabs(["🎥 Video Converter"])
    

    with sub_tool[1]:
        st.subheader("Video Format Transcoder")
        vid_file = st.file_uploader("Upload Video", type=["mp4", "mov", "avi"], key="v_up")
        target = st.selectbox("Target Format", ["MP4", "GIF"])
        if vid_file and st.button("Start Conversion"):
            with st.spinner("Processing video... this may take a moment"):
                vid_data = convert_video(vid_file, target)
                st.download_button(f"📥 Download {target}", vid_data, f"converted.{target.lower()}")



