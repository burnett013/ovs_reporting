# page_handler/reports.py
import streamlit as st
import pandas as pd
from catalog_parser.merge import combine_catalogs
from utils.approval_logic import apply_approval_logic

def show():
    st.title("Catalog Report Generator")

    # === Step 1: Academic year selection ===
    academic_year = st.selectbox(
        "Select the current academic year:",
        ["2022-2023", "2023-2024", "2024-2025", "2025-2026"],
        index=2
    )

    # Generate year suffix (e.g., "2425")
    year_suffix = academic_year[2:4] + academic_year[7:]
    output_filename = f"{year_suffix}_Report.xlsx"

    # === Step 2: File uploaders ===
    st.subheader("Upload Required Files")
    grad_catalog_pdf = st.file_uploader("Graduate Catalog PDF", type="pdf")
    ug_catalog_pdf = st.file_uploader("Undergraduate Catalog PDF", type="pdf")

    # === Step 3: Generate Step 1 Report ===
    if st.button("Generate Catalog Report"):
        if all([grad_catalog_pdf, ug_catalog_pdf]):
            with st.spinner("Generating catalog report..."):
                combined_df, combined_path = combine_catalogs(
                    grad_catalog_pdf,
                    ug_catalog_pdf,
                    output_name=output_filename
                )

                st.success("✅ Catalog Report generated successfully!")

                with open(combined_path, "rb") as f:
                    st.download_button("Download Catalog Report", f, file_name=output_filename)

        else:
            st.warning("Please upload **both catalogs** before generating the report.")