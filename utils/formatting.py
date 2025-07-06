# utils/formatting.py
import re
from openpyxl import load_workbook
from pathlib import Path

# ---------------------------
# Normalize text case for known terms
# ---------------------------
def normalize_text_case(text: str) -> str:
    if not isinstance(text, str):
        return text

    # Core replacements
    corrections = {
        r"\bph\.d\.\b": "Ph.D.",
        r"\bPH\.D\.\b": "Ph.D.",  # or just rely on flags=re.IGNORECASE
        r"ed\.s\.": "Ed.S.",
        r"ed\.d\.": "Ed.D.",
        r"au\.d\.": "Au.D.",
        r"m\.arch\.": "M.Arch.",
        r"m\.ed\.": "M.Ed.",
        r"m\.a\.t\.": "M.A.T.",
        r"m\.s\.n": "MSN",
        r"b\.s\.n": "BSN",
        r"pharm\.d\.": "Pharm.D.",
        r"dr\.p\.h\.": "Dr.P.H.",
        r"m\.s\.a\.a\.": "M.S.A.A.",
        r"m\.s\.b\.": "M.S.B.",
        r"m\.s\.b\.e\.": "M.S.B.E.",
        r"m\.s\.b\.c\.b\.": "M.S.B.C.B.",
        r"m\.s\.c\.e\.": "M.S.C.E.",
        r"m\.s\.c\.h\.": "M.S.C.H.",

        r"\besol\b": "ESOL",
        r"\brotc\b": "ROTC",
        r"\btesla\b": "TESLA",
        r"\bwoment['’]s\b": "Women's",
        r"\bwomen['’]s\b": "Women's",
        r"\bwith\b": "with",
        r"\bof\b": "of",
        r"\bcaribbean\b": "Caribbean",
    }

    for pattern, repl in corrections.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    # Smart quote fix (e.g. Master’S → Master’s)
    text = text.replace("’S", "'s").replace("’", "'")

    # Lowercase ALL-CAPS phrases after comma or parentheses, then fix casing
    def smart_fix(match):
        part = match.group(1)
        return ', ' + part.title()

    text = re.sub(r",\s*([A-Z\s\-]+)", smart_fix, text)

    return text.strip()

# ---------------------------
# Format program name with title casing
# ---------------------------
def format_program_name(name: str) -> str:
    if not isinstance(name, str):
        return name

    print(f"\n🟡 Raw input: {name}")  # ← Add this line

    name = normalize_text_case(name).strip()

    if ',' in name:
        base, after_comma = name.split(',', 1)
        base = normalize_text_case(base.title())
        after_comma = after_comma.strip()

        parts = after_comma.split(' ', 1)
        credential = normalize_text_case(parts[0])
        rest = normalize_text_case(parts[1]) if len(parts) > 1 else ""

        formatted = f"{base}, {credential}" + (f" {rest}" if rest else "")
    else:
        formatted = normalize_text_case(name.title())

    print(f"✅ Final formatted: {formatted}")  # ← Add this line
    return formatted

# ---------------------------
# Excel reload (placeholder for future features)
# ---------------------------
def apply_final_formatting(file_path: str | Path, worksheet_name: str = "Sheet1"):
    file_path = Path(file_path)
    wb = load_workbook(file_path)
    wb.save(file_path)