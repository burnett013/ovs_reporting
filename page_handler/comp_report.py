# comparison.py
import streamlit as st
import pandas as pd


def find_program_column(columns):
    for col in columns:
        if "program" in col.lower() and "name" in col.lower():
            return col
    return None

def compare_reports(df_old: pd.DataFrame, df_new: pd.DataFrame):
    """
    Compare two catalog reports and identify:
      - Added programs (in new, not in old)
      - Removed programs (in old, not in new)
      - Changed programs (same program but different attributes)
    """

    # ✅ Try to find the right key column in both files
    col_old = find_program_column(df_old.columns)
    col_new = find_program_column(df_new.columns)

    # ✅ Debug info: show what columns were found
    st.write("Detected columns in OLD report:", list(df_old.columns))
    st.write("Detected columns in NEW report:", list(df_new.columns))
    st.write("Auto-detected key columns:", col_old, col_new)

    # ✅ Handle case where the column isn't found
    if not col_old or not col_new:
        st.error(
            "❌ Could not find a 'Program Name' column in one of the reports!\n\n"
            f"Old report columns: {list(df_old.columns)}\n"
            f"New report columns: {list(df_new.columns)}"
        )
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # ✅ Now safely use the detected columns
    old_names = set(df_old[col_old])
    new_names = set(df_new[col_new])

    # --- Find Added ---
    added = df_new[df_new[col_new].isin(new_names - old_names)]

    # --- Find Removed ---
    removed = df_old[df_old[col_old].isin(old_names - new_names)]

    # --- Find Changed ---
    common = old_names.intersection(new_names)
    df_common_old = df_old[df_old[col_old].isin(common)].set_index(col_old)
    df_common_new = df_new[df_new[col_new].isin(common)].set_index(col_new)

    changed_rows = []
    for program in common:
        old_row = df_common_old.loc[program]
        new_row = df_common_new.loc[program]

        if not old_row.equals(new_row):
            diff = pd.concat([old_row, new_row], axis=1)
            diff.columns = ["Old", "New"]
            diff.insert(0, "Program Name", program)
            changed_rows.append(diff.reset_index())

    changed = pd.concat(changed_rows, ignore_index=True) if changed_rows else pd.DataFrame()

    return added, removed, changed

def show():
    st.title("Year-to-Year Comparison Report")

    st.subheader("Upload Two Reports to Compare")
    st.caption("Upload two previously generated catalog reports (XLSX) to see what was added, removed, or changed.")

    report_old = st.file_uploader("Upload Report :one:", type=["xlsx"], key="old_report")
    report_new = st.file_uploader("Upload Report :two:", type=["xlsx"], key="new_report")

    # === Ask for sheet name ===
    sheet_name = st.text_input(
        "Enter the **sheet name** where the data is located",
        value="Sheet1"  # default
    )

    # === Ask for first row number ===
    first_row_number = st.number_input(
        "Enter the **row number where data begins**",
        min_value=1,
        value=5,  # default row number
        step=1
    )

    # Calculate how many rows to skip for pd.read_excel
    skiprows_count = first_row_number - 1 if first_row_number > 1 else 0


    if st.button("Compare Reports"):
        if report_old and report_new:
            with st.spinner("Comparing reports..."):

                # ✅ Load dataframes using user-defined sheet + skiprows
                try:
                    df_old = pd.read_excel(
                        report_old,
                        sheet_name=sheet_name,
                        skiprows=skiprows_count
                    )
                    df_new = pd.read_excel(
                        report_new,
                        sheet_name=sheet_name,
                        skiprows=skiprows_count
                    )
                except Exception as e:
                    st.error(f"❌ Error reading Excel files: {e}")
                    return

                # ✅ Compare
                added, removed, changed = compare_reports(df_old, df_new)

                # ✅ Show results
                st.success("✅ Comparison Complete!")

                st.write("### :heavy_plus_sign: Added Programs")
                st.dataframe(added if not added.empty else pd.DataFrame({"Result": ["No new programs"]}))

                st.write("### :heavy_minus_sign: Removed Programs")
                st.dataframe(removed if not removed.empty else pd.DataFrame({"Result": ["No removed programs"]}))

                st.write("### 🔄 Changed Programs")
                if not changed.empty:
                    st.write(changed)
                else:
                    st.info("No changed programs detected.")
        else:
            st.warning("⚠️ Please upload **both reports** to run the comparison.")