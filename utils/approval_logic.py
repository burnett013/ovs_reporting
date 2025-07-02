# Import the pandas library, which is used for working with data in tables (like Excel)
import pandas as pd

# Define a constant that represents the current academic term
CURRENT_TERM = "Fall 2025"

# This function applies logic to determine the approval status of academic programs
# It compares this year's program list to last year's to detect changes, like new or removed programs
def apply_approval_logic(this_year_df: pd.DataFrame, last_year_df: pd.DataFrame) -> pd.DataFrame:

    # ---------------------------
    # STEP 1: Normalize Program Names
    # ---------------------------
    # Convert all program names to lowercase and strip leading/trailing spaces
    # This helps avoid mismatches due to capitalization or extra spaces
    this_year_df["Program Name"] = this_year_df["Program Name"].str.strip().str.lower()
    last_year_df["Program Name"] = last_year_df["Program Name"].str.strip().str.lower()

    # ---------------------------
    # STEP 2: Merge This Year with Last Year’s Data
    # ---------------------------
    # Join (merge) this year's programs with last year's data based on the program name
    # This brings in the 'Effective Date' from last year if there's a matching program
    # Programs not found in last year’s data will have NaN in 'Effective Date_last'
    merged = this_year_df.merge(
        last_year_df[["Program Name", "Effective Date"]],  # Only bring 'Program Name' and 'Effective Date' columns from last year
        on="Program Name",                                 # Match rows where the 'Program Name' is the same
        how="left",                                        # Keep all rows from this year, even if no match in last year
        suffixes=('', '_last')                             # Rename overlapping columns: 'Effective Date' becomes 'Effective Date_last' from last year
    )

    # ---------------------------
    # STEP 3: Determine the Approval Status for Each Program
    # ---------------------------

    # Helper function to assign the School Reported Approval Status
    def assign_status(row):
        comment = str(row.get("Comments", "")).lower()  # Get the Comments field (if present), convert to lowercase
        if pd.isna(row["Effective Date_last"]):         # If there's no effective date from last year, it means this is a new program
            return "New"
        elif "teach out" in comment or "withdrawn" in comment:  # Special cases that require human review
            return "Manual Review"
        else:
            return "Still Approved"                     # Default case for continuing programs

    # Helper function to assign the Effective Date
    def assign_effective_date(row):
        if row["School Reported Approval Status"] == "New":
            return CURRENT_TERM                         # Use current term for new programs
        else:
            return row["Effective Date_last"]           # Reuse the old effective date for continuing programs

    # Apply the helper functions to each row of the DataFrame
    merged["School Reported Approval Status"] = merged.apply(assign_status, axis=1)
    merged["Effective Date"] = merged.apply(assign_effective_date, axis=1)

    # ---------------------------
    # STEP 4: Find Removed Programs
    # ---------------------------
    # These are programs that existed last year but are not in this year's list
    removed_programs = last_year_df[~last_year_df["Program Name"].isin(this_year_df["Program Name"])].copy()

    # Mark these programs for manual review
    removed_programs["School Reported Approval Status"] = "Manual Review"
    # Note: we keep their original Effective Date as-is (already in the dataframe)

    # ---------------------------
    # STEP 5: Combine the Datasets
    # ---------------------------
    # Combine this year's processed programs with the removed programs from last year
    final_df = pd.concat([merged, removed_programs], ignore_index=True)

    # ---------------------------
    # STEP 6: Optional - Add a Visual Flag
    # ---------------------------
    # Add a column called "Flag" with a yellow box emoji for rows needing manual review
    final_df["Flag"] = final_df["School Reported Approval Status"].apply(
        lambda x: "🟨 Manual Review" if x == "Manual Review" else ""
    )

    # Return the completed dataset with approval statuses and effective dates
    return final_df