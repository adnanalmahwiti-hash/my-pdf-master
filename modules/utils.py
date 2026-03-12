import streamlit as st
import fitz
from PIL import Image, ImageOps
from io import BytesIO
import os
import threading
from datetime import datetime

lock = threading.Lock()

def write_global_log(tool, count, duration):
    log_file = "web_activity_log.txt"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{now}] {tool.upper()} | Files: {count} | Took: {duration:.2f}s\n"
    with lock:
        try:
            with open(log_file, "a") as f: f.write(log_entry)
        except: pass

def get_thumbnail(file_bytes, ext, manual_rot=0):
    try:
        if ext == "pdf":
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            pix = doc[0].get_pixmap(matrix=fitz.Matrix(0.1, 0.1))
            img = Image.open(BytesIO(pix.tobytes()))
            doc.close()
        else:
            img = Image.open(BytesIO(file_bytes))
        if manual_rot != 0: img = img.rotate(-manual_rot, expand=True)
        return ImageOps.fit(img, (180, 180), Image.Resampling.LANCZOS)
    except: return None
