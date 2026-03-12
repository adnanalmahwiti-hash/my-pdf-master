import streamlit as st
from moviepy.editor import VideoFileClip
from docx import Document
import fitz
from io import BytesIO
import os

def convert_video(uploaded_file, target_format):
    """Converts video files (e.g., MOV to MP4) using moviepy."""
    # Save temp file because moviepy needs a path, not just bytes
    with open("temp_video", "wb") as f:
        f.write(uploaded_file.read())
    
    clip = VideoFileClip("temp_video")
    output_filename = f"converted_video.{target_format.lower()}"
    
    # Process conversion
    if target_format.lower() == "mp4":
        clip.write_videofile(output_filename, codec="libx264")
    elif target_format.lower() == "gif":
        clip.write_gif(output_filename, fps=10)
    
    with open(output_filename, "rb") as f:
        data = f.read()
    
    # Cleanup
    clip.close()
    os.remove("temp_video")
    os.remove(output_filename)
    
    return data

def pdf_to_word(pdf_bytes):
    """Extracts text from PDF and builds a .docx file."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    word_doc = Document()
    
    for page in doc:
        text = page.get_text()
        word_doc.add_paragraph(text)
        word_doc.add_page_break()
    
    out_io = BytesIO()
    word_doc.save(out_io)
    return out_io.getvalue()
