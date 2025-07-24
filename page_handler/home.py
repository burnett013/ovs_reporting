# page_handler/home.py
import streamlit as st
from app_params import APP_NAME, VERSION

def show():
    # ---- Hero Section ----------------------------
    st.title(APP_NAME if 'APP_NAME' in globals() else "VA Reporting Automation")
    st.markdown(f"*Version {VERSION}*" if 'VERSION' in globals() else "")

    st.markdown(
        """
        ### Why this app exists  
        Each year the VA requires universities to certify every approved **academic program**.  
        Traditionally this involves:  

        1. **Manually** combing through graduate & undergraduate catalogs
        2. Cross-checking the details with last year’s WEAMS-bound Excel file
        3. Identifying programs that will be **carried over, new, removed, or changed**  
        4. Re-entering the data into a VA-formatted spreadsheet
        5. Submitting the new spreadsheet for VA approval

        This process is slow, error-prone, and ties up staff time that could be spent helping
        student veterans directly.

        **Our goal:** *Automate steps 1 – 3* and pre-populate step 4, so staff only need to review
        edge cases and add a few comments before submission.
        """,
        unsafe_allow_html=True,
    )

    # ---- How It Works --------------------------------------
    with st.expander("🔍  How it works — technical flow", expanded=False):
        st.markdown(
            """
            1. **Upload Files**  
               • Current **Undergrad** & **Graduate** catalog PDFs  
               • Last year’s **VA-certified Excel (WEAMS)** file  

            2. **PDF Parsing** (`pdfplumber`, `PyPDF2`, regex)\
               &nbsp;→ Extract program name, degree, credit hours, modality, page #  

            3. **Data Normalization & Fuzzy Matching** (`pandas`, `rapidfuzz`)\
               &nbsp;→ Compare against last year to detect **New / Removed / Updated** programs  

            4. **Output** \
               • **Excel** — fully formatted for VA upload, legacy columns preserved\
               • *(Optional)* **Word summary** of the changes  

            5. **Review & Submit**\
               Staff add any comments, mark “Contracted Program?” flags, and send to VA.
            """
        )

    # ---- Quick Call-to-Action ---------------------------
    st.success("Ready to get started? Head to the **“Catalog Report”** page or the **Comparison Report** via the sidebar, upload your files, and click **Generate VA Report**.")

    # ---- Footer ------------------------------------------
    st.caption("Built from Texas with ❤️ & Streamlit · USF Office of Veteran Success · 2025")