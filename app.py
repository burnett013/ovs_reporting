# app.py
'''
Main entry point for Streamlit
'''
import streamlit as st
from page_handler import home, cat_report, comp_report

# Set basic config
st.set_page_config(page_title="Entry Portal", layout="wide")

# Page routing logic
PAGES = {
    "Home": home,
    "Catalog Report": cat_report,
    "Comparison Report": comp_report
}
# Sidebar Navigation
st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))

# Render the pages
PAGES[selection].show()