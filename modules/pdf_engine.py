from docx import Document
import fitz
from PIL import Image
from io import BytesIO
import streamlit as st

def process_universal_merger(uploaded_files, password=None, rotations={}):
    res = fitz.open()
    for idx, f in enumerate(uploaded_files):
        f.seek(0); fb = f.read()
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
            img.save(img_io, format='JPEG', quality=85)
            img_pdf_data = fitz.open("jpg", img_io.getvalue()).convert_to_pdf()
            with fitz.open("pdf", img_pdf_data) as img_doc: res.insert_pdf(img_doc)
    
    out = BytesIO()
    if password: res.save(out, encryption=fitz.PDF_ENCRYPT_AES_256, user_pw=password, owner_pw=password)
    else: res.save(out, garbage=4, deflate=True)
    res.close()
    return out.getvalue()

def process_reducer(uploaded_files, deep=True):
    results = []
    for f in uploaded_files:
        f.seek(0)
        doc = fitz.open(stream=f.read(), filetype="pdf")
        out_pdf = BytesIO()
        if deep:
            new_doc = fitz.open()
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
                new_page.insert_image(page.rect, stream=pix.tobytes("jpg", jpg_quality=60))
            new_doc.save(out_pdf, garbage=4, deflate=True); new_doc.close()
        else: 
            doc.save(out_pdf, garbage=4, deflate=True)
        results.append({"name": f"opt_{f.name}", "data": out_pdf.getvalue()})
        doc.close()
    return results

def process_ico_maker(uploaded_files):
    results = []
    for f in uploaded_files:
        img = Image.open(f)
        out = BytesIO()
        img.save(out, format='ICO', sizes=[(32,32), (64,64), (256,256)])
        results.append({"name": f.name.split('.')[0] + ".ico", "data": out.getvalue()})
    return results

def pdf_to_word(pdf_bytes):
    """Extracts text from PDF and builds a .docx file."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    word_doc = Document()
    
    for page in doc:
        text = page.get_text("text")
        word_doc.add_paragraph(text)
        word_doc.add_page_break()
    
    out_io = BytesIO()
    word_doc.save(out_io)
    doc.close()
    return out_io.getvalue()
