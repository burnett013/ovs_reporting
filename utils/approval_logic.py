# utils/approval_logic.py
import pandas as pd
from utils.formatting import format_program_name

CURRENT_TERM = "Fall 2025"

def apply_approval_logic(this_year_df: pd.DataFrame, last_year_df: pd.DataFrame) -> pd.DataFrame:
    # Rename columns to match last year's headers
    this_year_df.rename(columns={
        "Accredited": "Accredited? Yes or No",
        "License Prep": "State License or Cert Prep?    Yes or No"
    }, inplace=True)

    # ---------------------------
    # Normalize Program Names for Matching Only
    # ---------------------------
    this_year_df["Program Name Clean"] = this_year_df["Program Name"].str.strip().str.lower()
    last_year_df["Program Name Clean"] = last_year_df["Program Name"].str.strip().str.lower()

    # ---------------------------
    # Merge This Year with Last Year’s Data
    # ---------------------------
    last_year_df_renamed = last_year_df.rename(columns={"Effective Date": "Effective Date_last"})

    merged = this_year_df.merge(
        last_year_df_renamed[["Program Name Clean", "Effective Date_last"]],
        on="Program Name Clean",
        how="left"
    )

    # Drop helper column
    merged.drop(columns=["Program Name Clean"], inplace=True)

    # Format final program name
    merged["Program Name"] = merged["Program Name"].apply(format_program_name)

    # ---------------------------
    # Assign Approval Status
    # ---------------------------
    def assign_status(row):
        comment = str(row.get("Comments", "")).lower()
        if pd.isna(row["Effective Date_last"]):
            return "New"
        elif "teach out" in comment or "withdrawn" in comment:
            return "Manual Review"
        else:
            return "Still Approved"

    def assign_effective_date(row):
        if row["School Reported Approval Status"] == "New":
            return CURRENT_TERM
        elif row.get("Effective Date") == row.get("Effective Date_last"):
            return row.get("Effective Date")
        elif pd.notna(row.get("Effective Date")):
            return row.get("Effective Date")
        else:
            return row.get("Effective Date_last")

    merged["School Reported Approval Status"] = merged.apply(assign_status, axis=1)
    merged["Effective Date"] = merged.apply(assign_effective_date, axis=1)

    if "Effective Date_last" in merged.columns:
        merged.drop(columns=["Effective Date_last"], inplace=True)

    # ---------------------------
    # Find Removed Programs
    # ---------------------------
    removed_programs = last_year_df[
        ~last_year_df["Program Name Clean"].isin(this_year_df["Program Name Clean"])
    ].copy()

    removed_programs["Program Name"] = removed_programs["Program Name"].apply(format_program_name)
    removed_programs["School Reported Approval Status"] = "Manual Review"

    # ---------------------------
    # Combine and Final Format
    # ---------------------------
    final_df = pd.concat([merged, removed_programs], ignore_index=True)
    final_df["Program Name"] = final_df["Program Name"].apply(format_program_name)

    # ---------------------------
    # Assign Catalog Name
    # ---------------------------
    def assign_catalog_name(row):
        status = row["School Reported Approval Status"]
        level = str(row.get("Educational Objective", "")).strip().lower()

        if "graduate certificate" in level:
            catalog_this_year = "USF Graduate Catalog 2024-2025"
        elif "bachelor" in level or level == "certificate":
            catalog_this_year = "USF Undergraduate Catalog 2024-2025"
        else:
            catalog_this_year = "USF Graduate Catalog 2024-2025"

        if status in ["New", "Still Approved", "Name Change"]:
            return catalog_this_year
        elif status == "Teach Out Phase":
            return row.get("Catalog Name_last")
        else:
            return ""

    final_df["Catalog or Publication Name along with Number (if more than one is listed above)"] = final_df.apply(assign_catalog_name, axis=1)

    # Add a flag for manual review
    final_df["Flag"] = final_df["School Reported Approval Status"].apply(
        lambda x: "🟨 Manual Review" if x == "Manual Review" else ""
    )

    return final_df