import streamlit as st
from moviepy.editor import VideoFileClip
import fitz
from io import BytesIO
import os
import tempfile

def convert_video(uploaded_file, target_format):
    """Processes video conversion using temporary file streams."""
    # Create a persistent temp file for moviepy to read
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tfile:
        tfile.write(uploaded_file.read())
        temp_path = tfile.name

    try:
        clip = VideoFileClip(temp_path)
        output_path = temp_path + f".{target_format.lower()}"
        
        if target_format.lower() == "mp4":
            clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
        elif target_format.lower() == "gif":
            clip.write_gif(output_path, fps=10)
            
        with open(output_path, "rb") as f:
            data = f.read()
            
        clip.close()
        return data
    finally:
        # Cleanup temp files regardless of success or failure
        if os.path.exists(temp_path): os.remove(temp_path)
        if 'output_path' in locals() and os.path.exists(output_path): os.remove(output_path)
