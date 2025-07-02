# app.py
import streamlit as st
from page_handler import home, reports

# Set basic config
st.set_page_config(page_title="Entry Portal", layout="wide")

# Page routing logic
PAGES = {
    "Home": home,
    "Reports": reports,
}
# Sidebar Navigation
st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))

# Render the pages
PAGES[selection].show()