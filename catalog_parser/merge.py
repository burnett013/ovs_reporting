# catalog_parser/merge.py
from pathlib import Path
import pandas as pd
from . import gr_parser, ug_parser

def combine_catalogs(
    grad_pdf,
    ug_pdf,
    output_name: str = "combined_catalog.xlsx"
) -> tuple[pd.DataFrame, str]:
    """
    Merge parsed graduate & undergraduate catalogs.
    Saves the combined output and returns both the dataframe and path.
    """
    storage_dir = Path.cwd() / "upl_file_bunker"
    storage_dir.mkdir(exist_ok=True)

    # ---------- persist uploads ----------
    grad_path = storage_dir / "grad_catalog_upl.pdf"
    ug_path   = storage_dir / "ug_catalog_upl.pdf"

    grad_path.write_bytes(grad_pdf.read())
    ug_path.write_bytes(ug_pdf.read())

    # ---------- parse PDFs ----------
    gr_df = gr_parser.run_gr_parser(str(grad_path))
    ug_df = ug_parser.run_ug_parser(str(ug_path))
    combined_df = pd.concat([gr_df, ug_df], ignore_index=True)

    # ---------- save output ----------
    output_path = storage_dir / output_name
    combined_df.to_excel(output_path, index=False)

    return combined_df, str(output_path)