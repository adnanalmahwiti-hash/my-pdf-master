import streamlit as st

def apply_custom_css():
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
