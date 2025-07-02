# parser/gr_parser.py
import pdfplumber
import pandas as pd
import re
from pathlib import Path
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pytesseract
from openpyxl.utils import get_column_letter
from openpyxl import load_workbook

DEGREE_SUFFIXES = [
    "M\\.S\\.", "M\\.A\\.", "Ph\\.D\\.", "M\\.F\\.A\\.", "Au\\.D\\.", "Ed\\.D\\.", "Ed\\.S\\.", "M\\.B\\.A\\.",
    "D\\.B\\.A\\.", "D\\.N\\.P\\.", "M\\.P\\.A\\.", "M\\.S\\.A\\.A\\.", "M\\.S\\.Ch\\.", "M\\.S\\.B\\.C\\.B\\.",
    "M\\.S\\.B\\.", "M\\.S\\.C\\.S\\.", "M\\.S\\.C\\.P\\.", "M\\.S\\.E\\.M\\.", "M\\.S\\.E\\.E\\.", "M\\.S\\.M\\.E\\.",
    "M\\.S\\.C\\.Y\\.S\\.", "M\\.S\\.D\\.I\\.", "M\\.U\\.C\\.D\\.", "M\\.U\\.R\\.P\\.", "M\\.P\\.H\\.", "M\\.Arch\\.",
    "M\\.S\\.B\\.E\\.", "M\\.S\\.C\\.E\\.", "M\\.E\\.d\\.", "M\\.A\\.T\\.", "M\\.S\\.E\\.V\\.", "M\\.H\\.A\\.",
    "M\\.S\\.H\\.I\\.", "M\\.S\\.I\\.E\\.", "M\\.S\\.M\\.", "M\\.S\\.M\\.S\\.E\\.", "M\\.D\\.", "M\\.M\\.",
    "M\\.S\\.N\\.", "Pharm\\.D\\.", "D\\.P\\.T\\.", "M\\.P\\.A\\.S\\.", "Dr\\.P\\.H\\.", "M\\.S\\.P\\.H\\.",
    "M\\.S\\.W\\.", "M\\.S\\.M\\.S\\."
]

DEGREE_PATTERN = "|".join(DEGREE_SUFFIXES)

MAJOR_REGEX = re.compile(rf"^(.*?)\s*,?\s*({DEGREE_PATTERN})\s*\.{{3,}}\s*(\d+)$")
GC_REGEX = re.compile(r"([\w:()&’'\/,\-.\s]*?Graduate Certificate)\s*\.{3,}\s*(\d{3,4})")

def extract_pdf_lines(pdf_toc: Path) -> list:
    with pdfplumber.open(str(pdf_toc)) as pdf:
        lines = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.extend(text.splitlines())
        return lines

def extract_majors(toc_lines: list) -> list:
    majors = []
    for line in toc_lines:
        line = line.strip()
        match = MAJOR_REGEX.match(line)
        if match:
            prefix = match.group(1).strip()
            credential = match.group(2).strip()
            program = f"{prefix}M.S." if prefix.endswith("M.S.") and credential == "M.S." else f"{prefix}, {credential}"
            page = int(match.group(3))
            majors.append((program, page))
        else:
            continue
    return majors

def add_manual_majors(majors: list) -> list:
    manual_entries = [
        ("Business Administration, D.B.A.", 223),
        ("Criminology, Ph.D.", 323),
        ("Curriculum and Instruction, M.Ed.", 332),
        ("Educational Leadership, M.Ed.", 374),
        ("Social Work, M.S.W.", 720)
    ]
    existing_programs = set(prog for prog, _ in majors)
    for prog, page in manual_entries:
        if prog not in existing_programs:
            majors.append((prog, page))
    return majors

def merge_wrapped_lines(lines: list) -> list:
    cleaned = []
    buffer = ""
    for line in lines:
        line = line.strip()
        if re.search(r"\.{3,}\s*\d{3,4}$", line):
            buffer += " " + line
            cleaned.append(buffer.strip())
            buffer = ""
        else:
            buffer += " " + line
    if buffer.strip():
        cleaned.append(buffer.strip())
    return cleaned

def extract_gcs(lines: list) -> list:
    gc_candidates = []
    for line in lines:
        cleaned = re.sub(r"^2024-2025 USF Graduate Catalog [xivl]+\s+", "", line)
        if "Graduate Certificate" in cleaned:
            gc_candidates.append(cleaned.strip())

    gcs = []
    for line in gc_candidates:
        match = GC_REGEX.search(line)
        if match:
            program = match.group(1).strip()
            page = int(match.group(2))
            if page <= 981:
                gcs.append((program, page))
    return gcs

def build_toc(pdf_toc: Path) -> pd.DataFrame:
    toc_lines = extract_pdf_lines(pdf_toc)
    majors = extract_majors(toc_lines)
    majors = add_manual_majors(majors)
    cleaned_lines = merge_wrapped_lines(toc_lines)
    gcs = extract_gcs(cleaned_lines)
    all_programs = majors + gcs
    return pd.DataFrame(all_programs, columns=["Program Name", "Page Number"])

def export_to_excel(programs: list, output_path: Path):
    df = pd.DataFrame(programs, columns=["Program Name", "Page Number"])
    df.to_excel(output_path, index=False)

def modality(text):
    t = text.lower()
    return "Online" if "online" in t else "Hybrid" if "hybrid" in t else "Campus"

def has_license_prep(lines: list) -> str:
    text = " ".join(lines).lower()
    keywords = [
        "state-approved program", "leads to certification", "eligible for teacher certification",
        "teacher preparation program", "florida teacher certification exam",
        "eligible for the endorsements", "licensure", "professional certification",
        "meets certification requirements"
    ]
    return "Yes" if any(k in text for k in keywords) else "No"

def classify_credential(abbrev):
    ab = re.sub(r"[^\w]", "", abbrev).upper()
    if any(x in ab for x in ["PHD", "DBA", "EDD", "DRPH", "DNP", "DPT", "AUD", "PHARMD", "MD", "EDS"]):
        return "Doctorate"
    elif ab.startswith("M") and not ab.startswith("MD"):
        return "Master's"
    elif "CERT" in ab:
        return "Graduate Certificate"
    else:
        return "Other"

def detect_concentration(text):
    context_phrase = "major contacts, deadlines, and delivery information"
    concentration_phrase = "concentration"
    text_lower = text.lower()
    if context_phrase in text_lower:
        context_index = text_lower.find(context_phrase)
        concentration_index = text_lower.find(concentration_phrase, context_index + 1)
        return "Yes" if concentration_index != -1 else "No"
    return "No"

def get_hour_patterns() -> list[str]:
    return [
        r"total\s+minimum\s+hours\s*[:-–]?\s*([0-9]{1,3})",
        r"program\s+minimum\s+credit\s+hours\s*[:-–]?\s*([0-9]{1,3})",
        r"minimum\s+program\s+hours\s*[:-–]?\s*([0-9]{1,3})",
        r"total\s+minimum[^0-9]*([0-9]{1,3})\s*(credit|cr)\s*hours?",
        r"minimum\s+hours\s*[:-–]?\s*([0-9]{1,3})",
        r"total\s+minimum\s+required\s+hours\s*[-–:]\s*(\d{1,3})\s+hours\s+beyond",
        r"total\s+minimum\s+hours\s*[-–:]?\s*([0-9]{1,3})\s+hours?",
        r"total\s+minimum\s+hours\s*[-–:]?\s*([0-9]{1,3})",
        r"total\s+minimum\s+hours\s*[:-–]?\s*([0-9]{1,3})\s+credit\s+hours",
        r"Curriculum\s+Requirements\s*\(\s*([0-9]{1,3})\s*Credit\s+Hours\s*\)",
        r"Curriculum\s+Requirements[^0-9]*([0-9]{1,3})\s*Credit\s+Hours?",
        r"([0-9]{1,3})\s*credit\s+hours?\b",
        r"([0-9]{1,3})\s*credits?\b"
    ]

def find_hours(text: str) -> int | None:
    text_lower = text.lower()
    bach_match = re.search(r"(\d{2,3})\s+(?:credit|hours|minimum)?\s*\(post[-\s]?bachelor", text_lower)
    if bach_match:
        return int(bach_match.group(1))
    beyond_ma = re.search(r"total\s+minimum\s+required\s+hours\s*[-–:]\s*(\d{1,3})\s+hours\s+beyond", text_lower)
    if beyond_ma:
        return int(beyond_ma.group(1))
    for pat in get_hour_patterns():
        m = re.search(pat, text_lower, flags=re.I)
        if m:
            return int(m.group(1))
    return None

def grab_text(reader: PdfReader, page_number: int, range_len: int = 1) -> tuple[str, list[str]]:
    parts = []
    for p in range(page_number - 1, page_number - 1 + range_len + 1):
        if 0 <= p < len(reader.pages):
            parts.append(reader.pages[p].extract_text() or "")
    full_text = "\n".join(parts)
    return full_text, full_text.splitlines()

def build_records(pdf_path: Path, toc_df: pd.DataFrame) -> pd.DataFrame:
    df = toc_df.copy()
    df = df.rename(columns={"Program Name": "Program", "Page Number": "Page Number"})
    df["Page Number"] = df["Page Number"].astype(int)
    reader = PdfReader(pdf_path)
    rows = []
    for program, page_number in df.itertuples(index=False):
        text, lines = grab_text(reader, page_number, range_len=2)
        hours = find_hours(text)
        credential = program.split(",")[-1].strip()
        is_cert = "CERT" in credential.upper()
        concentration_status = "No" if is_cert else detect_concentration(text)
        edu_obj = "Graduate Certificate" if is_cert else classify_credential(credential)
        if concentration_status == "Yes":
            prog_type = "Concentration"
        elif concentration_status == "No" and edu_obj in ["Master's", "Doctorate"]:
            prog_type = "Major"
        elif concentration_status == "No" and edu_obj == "Graduate Certificate":
            prog_type = "Graduate Certificate"
        else:
            prog_type = "Other"
        rows.append({
            "Program Name": program,
            "Accredited": "No" if re.search(r"not accredited", text, flags=re.I) else "Yes",
            "Educational Objective": edu_obj,
            "Concentrations? Yes or No": concentration_status,
            "Total Credit Hours in Program": hours,
            "Program Length Measurement": "Semester",
            "Full-Time Enrollment": 9,
            "Page Number": page_number,
            "License Prep": has_license_prep(lines),
            "Modality": modality(text),
            "Type": prog_type,
        })
    return pd.DataFrame(rows)

# def apply_column_formatting(writer):
#     ws = writer.book.active
#     column_widths = {
#         "A": 10, "B": 50, "C": 15, "D": 25, "E": 25, "F": 30, "G": 15,
#         "H": 20, "I": 25, "J": 15, "K": 30, "L": 12, "M": 15, "N": 12, "O": 20
#     }
#     for col_letter, width in column_widths.items():
#         ws.column_dimensions[col_letter].width = width

def run_gr_parser(core_pdf: str, toc_pdf: str) -> pd.DataFrame:
    toc_df = build_toc(Path(toc_pdf))
    return build_records(Path(core_pdf), toc_df)