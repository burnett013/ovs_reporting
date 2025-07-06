# utils/approval_logic.py
import pandas as pd
import re
from utils.formatting import format_program_name

# Define a constant that represents the current academic term
CURRENT_TERM = "Fall 2025"

#     # Apply manual replacements (case-insensitive)
#     for pattern, replacement in replacements.items():
#         name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)

#     # Handle title casing BEFORE the comma (program part only)
#     if ',' in name:
#         base, after_comma = name.split(',', 1)
#         base = base.title()
#         after_comma = after_comma.strip()

#         # Capitalize credential if it is short (e.g., M.A., M.S., Ph.D.)
#         # And title-case anything that comes after (e.g., concentrations)
#         parts = after_comma.split(' ', 1)
#         credential = parts[0].upper()
#         rest = parts[1].title() if len(parts) > 1 else ""

#         formatted = f"{base}, {credential}"
#         if rest:
#             formatted += f" {rest}"
#         return formatted
#     else:
#         return name.title()
    
# This function applies logic to determine the approval status of academic programs
# It compares this year's program list to last year's to detect changes, like new or removed programs
def apply_approval_logic(this_year_df: pd.DataFrame, last_year_df: pd.DataFrame) -> pd.DataFrame:
    # make sure accreditation column matches last year's header
    this_year_df.rename(columns={"Accredited": "Accredited? Yes or No"}, inplace=True)
    this_year_df.rename(columns={
        "Accredited": "Accredited? Yes or No",
        "License Prep": "State License or Cert Prep?    Yes or No"
    }, inplace=True)

    # ---------------------------
    # Normalize Program Names
    # ---------------------------
    # Convert program names to lowercase, strip leading/trailing spaces
    this_year_df["Program Name"] = this_year_df["Program Name"].str.strip().str.lower()
    last_year_df["Program Name"] = last_year_df["Program Name"].str.strip().str.lower()

    # ---------------------------
    # Merge This Year with Last Year’s Data
    # ---------------------------
    # If a match is found, we pull the Effective Date from last year. If there’s no match, that row is still kept — but the date is blank (NaN).
    # Rename last year's 'Effective Date' to avoid collision and ensure consistency
    last_year_df_renamed = last_year_df.rename(columns={"Effective Date": "Effective Date_last"})

    # Merge explicitly using renamed column
    merged = this_year_df.merge(
        last_year_df_renamed[["Program Name", "Effective Date_last"]],
        on="Program Name",
        how="left"
    )

    # ---------------------------
    # Determine the Approval Status for Each Program
    # ---------------------------

    # Helper function to assign the School Reported Approval Status
    def assign_status(row):
        comment = str(row.get("Comments", "")).lower() # Get the Comments field (if present), convert to lowercase
        if pd.isna(row["Effective Date_last"]): # If there's no effective date from last year, it means this is a new program
            return "New"
        elif "teach out" in comment or "withdrawn" in comment:  # Special cases that require human review
            return "Manual Review"
        else:
            return "Still Approved" # Default case for continuing programs

    # Helper function to assign the Effective Date
    def assign_effective_date(row):
        # If it's a new program, use the current term
        if row["School Reported Approval Status"] == "New":
            return CURRENT_TERM
        # If this year's and last year's effective dates are the same, keep this year's
        elif row.get("Effective Date") == row.get("Effective Date_last"):
            return row.get("Effective Date")
        # If they're different, still keep this year's (assuming it's more up to date)
        elif pd.notna(row.get("Effective Date")):
            return row.get("Effective Date")
        # Fall back to last year's if this year's is missing
        else:
            return row.get("Effective Date_last")
        
    # Assign approval status BEFORE using it in assign_effective_date
    merged["School Reported Approval Status"] = merged.apply(assign_status, axis=1)
    merged["Effective Date"] = merged.apply(assign_effective_date, axis=1)

    # Drop the old column
    if "Effective Date_last" in merged.columns:
        merged.drop(columns=["Effective Date_last"], inplace=True)

    # ---------------------------
    # Find Removed Programs
    # ---------------------------
    # Present last year, not this year
    removed_programs = last_year_df[~last_year_df["Program Name"].isin(this_year_df["Program Name"])].copy()

    # Mark these programs for manual review
    removed_programs["School Reported Approval Status"] = "Manual Review"
    # Note: we keep their original Effective Date as-is (already in the dataframe)

    # ---------------------------
    # Combine the Datasets
    # ---------------------------
    # Combine this year's processed programs with the removed programs from last year
    final_df = pd.concat([merged, removed_programs], ignore_index=True)
    final_df["Program Name"] = final_df["Program Name"].apply(format_program_name)

    def assign_catalog_name(row):
        status = row["School Reported Approval Status"]
        level = str(row.get("Educational Objective", "")).strip().lower()
        
        # Determine which catalog
        
    # Prioritize the more specific phrase first
        if "graduate certificate" in level:
            catalog_this_year = "USF Graduate Catalog 2024-2025"
        elif "bachelor" in level or level == "certificate":
            catalog_this_year = "USF Undergraduate Catalog 2024-2025"
        else:
            catalog_this_year = "USF Graduate Catalog 2024-2025"

        if status == "New":
            return catalog_this_year
        elif status == "Still Approved":
            return catalog_this_year
        elif status == "Name Change":
            return catalog_this_year
        elif status == "Teach Out Phase":
            return row.get("Catalog Name_last")  # from last year's file
        else:
            return ""

    # Apply catalog logic to the full, combined DataFrame
    final_df["Catalog or Publication Name along with Number (if more than one is listed above)"] = final_df.apply(assign_catalog_name, axis=1)

    # ---------------------------
    # Optional - Add a Visual Flag
    # ---------------------------
    # Add a column called "Flag" with a yellow box emoji for rows needing manual review
    final_df["Flag"] = final_df["School Reported Approval Status"].apply(
        lambda x: "🟨 Manual Review" if x == "Manual Review" else ""
    )

    # Return the completed dataset with approval statuses and effective dates
    return final_df