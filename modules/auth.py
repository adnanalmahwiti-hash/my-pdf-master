# --- 1. SECURITY GATE ---
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        # This looks for a variable named 'password' in your Streamlit Cloud Secrets
        if st.session_state["password_input"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]  # Clean up memory
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First-time visit: Show login screen
        st.title("🔐 Elite Suite Access")
        st.text_input("Enter Access Key", type="password", on_change=password_entered, key="password_input")
        st.info("Authorized Personnel Only.")
        return False
    elif not st.session_state["password_correct"]:
        # Wrong password
        st.title("🔐 Elite Suite Access")
        st.text_input("Enter Access Key", type="password", on_change=password_entered, key="password_input")
        st.error("🚫 Access Denied: Invalid Key")
        return False
    else:
        # Password is correct
        return True

# If password check fails, stop the script here
if not check_password():
    st.stop()
