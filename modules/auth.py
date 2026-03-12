import streamlit as st

def check_password():
    def password_entered():
        if st.session_state["password_input"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Elite Suite Access")
        st.text_input("Enter Access Key", type="password", on_change=password_entered, key="password_input")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 Elite Suite Access")
        st.text_input("Enter Access Key", type="password", on_change=password_entered, key="password_input")
        st.error("🚫 Access Denied")
        return False
    return True
