# comparison.py
import streamlit as st
import pandas as pd

def compare_reports(df_old: pd.DataFrame, df_new: pd.DataFrame):
    """
    Compare two catalog reports and identify:
      - Added programs (in new, not in old)
      - Removed programs (in old, not in new)
      - Changed programs (same program but different attributes)
    """

    # Use Program Name as the key
    key_col = "Program Name"

    old_names = set(df_old[key_col])
    new_names = set(df_new[key_col])

    # Added = in new but not in old
    added = df_new[df_new[key_col].isin(new_names - old_names)]

    # Removed = in old but not in new
    removed = df_old[df_old[key_col].isin(old_names - new_names)]

    # Potentially changed = same key but differences in columns
    common = old_names.intersection(new_names)
    df_common_old = df_old[df_old[key_col].isin(common)].set_index(key_col)
    df_common_new = df_new[df_new[key_col].isin(common)].set_index(key_col)

    changed_rows = []
    for program in common:
        old_row = df_common_old.loc[program]
        new_row = df_common_new.loc[program]

        # Compare row-wise (excluding NaN-safe equality)
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

    if st.button("Compare Reports"):
        if report_old and report_new:
            with st.spinner("Comparing reports..."):
                # Load dataframes
                df_old = pd.read_excel(report_old)
                df_new = pd.read_excel(report_new)

                # Compare
                added, removed, changed = compare_reports(df_old, df_new)

                # Show results
                st.success("Comparison Complete!")

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
            st.warning("Please upload **both reports** to run the comparison.")