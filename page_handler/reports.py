# reports.py
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
    grad_toc_pdf = st.file_uploader("Graduate Table of Contents PDF", type="pdf")
    ug_catalog_pdf = st.file_uploader("Undergraduate Catalog PDF", type="pdf")
    last_year_xlsx = st.file_uploader("Last Year's VA Excel File (.xlsx)", type=["xlsx"])

    # === Step 3: Generate report ===
    if st.button("Generate Report"):
        if all([grad_catalog_pdf, grad_toc_pdf, ug_catalog_pdf, last_year_xlsx]):
            with st.spinner("Hang on while greatness is made..."):
                # Step 1: Combine UG and GR
                combined_df, _ = combine_catalogs(
                    grad_catalog_pdf,
                    grad_toc_pdf,
                    ug_catalog_pdf,
                    output_name=output_filename
                )

                # Step 2: Load last year's Excel and apply approval logic
                last_year_df = pd.read_excel(last_year_xlsx)
                final_df = apply_approval_logic(combined_df, last_year_df)

                # Step 3: Save final report
                final_path = f"upl_file_bunker/{output_filename}"
                final_df.to_excel(final_path, index=False)

                st.success("Report generated successfully!")

                with open(final_path, "rb") as f:
                    st.download_button("Download Report", f, file_name=output_filename)
        else:
            st.warning("Please upload **all** required files before generating the report.")