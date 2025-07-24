# parser/gr_parser.py
import pandas as pd
import streamlit as st
import re
from pathlib import Path
from PyPDF2 import PdfReader
import pdfplumber
from openpyxl.utils import get_column_letter
from openpyxl import load_workbook

# Global Constraints
OFFSET = 51  # skip Roman numeral pages

DEGREE_SUFFIXES = [
    "M\\.S\\.", "M\\.A\\.", "Ph\\.D\\.", "M\\.F\\.A\\.", "Au\\.D\\.", "Ed\\.D\\.", "Ed\\.S\\.", "M\\.B\\.A\\.",
    "D\\.B\\.A\\.", "D\\.N\\.P\\.", "M\\.P\\.A\\.", "M\\.S\\.A\\.A\\.", "M\\.S\\.Ch\\.", "M\\.S\\.B\\.C\\.B\\.",
    "M\\.S\\.B\\.", "M\\.S\\.C\\.S\\.", "M\\.S\\.C\\.P\\.", "M\\.S\\.E\\.M\\.", "M\\.S\\.E\\.E\\.", "M\\.S\\.M\\.E\\.",
    "M\\.S\\.C\\.Y\\.S\\.", "M\\.S\\.D\\.I\\.", "M\\.U\\.C\\.D\\.", "M\\.U\\.R\\.P\\.", "M\\.P\\.H\\.", "M\\.Arch\\.",
    "M\\.S\\.B\\.E\\.", "M\\.S\\.C\\.E\\.", "M\\.E\\.d\\.", "M\\.A\\.T\\.", "M\\.S\\.E\\.V\\.", "M\\.H\\.A\\.",
    "M\\.S\\.H\\.I\\.", "M\\.S\\.I\\.E\\.", "M\\.S\\.M\\.", "M\\.S\\.M\\.S\\.E\\.", "M\\.D\\.", "M\\.M\\.",
    "M\\.S\\.N\\.", "Pharm\\.D\\.", "D\\.P\\.T\\.", "M\\.P\\.A\\.S\\.", "Dr\\.P\\.H\\.", "M\\.S\\.P\\.H\\.",
    "M\\.S\\.W\\.", "M\\.S\\.M\\.S\\.","M\\.?S\\.?", "M\\.?A\\.?", "Ph\\.?D\\.?", "M\\.?F\\.?A\\.?", "Au\\.?D\\.?", "Ed\\.?D\\.?", "Ed\\.?S\\.?", "M\\.?B\\.?A\\.?", "D\\.?B\\.?A\\.?", "D\\.?N\\.?P\\.?", "M\\.?P\\.?A\\.?", "M\\.?P\\.?H\\.?", "M\\.?E\\.?d\\.?", "M\\.?S\\.?W\\.?", "Dr\\.?P\\.?H\\.?", "Pharm\\.?D\\.?", "M\\.?S\\.?N\\.?", "M\\.?M\\.?", "M\\.?A\\.?T\\.?"
]

STOP_PHRASES = [
    "also offered", "major shares", "concentration under", "elective", "internship", "comprehensive exam", "PHC",
    "view requirements", "usf is", "usf administration", "graduate studies senior", "college deans", "egad",
    "graduate majors with", "students establish a", "summer 4", "integrated learning experience", "completion",
    "time limit", "certificate contacts", "policies", "admissions and process", "curriculum requirements",
    "refer to", "graduate course", "president", "prasant", "assistant dean", "policy", "office of graduate",
    "majors, concentrations", "by degree type", "chancellor", "6000", "students must", "(a -z)", 
    "usf is a place where you can challenge yourself"
]

DEGREE_PATTERN = "|".join(DEGREE_SUFFIXES)
MAJOR_REGEX = re.compile(rf"^([A-Z][\w\s&/-]+),\s*({DEGREE_PATTERN})\.?$", re.IGNORECASE)
GC_REGEX = re.compile(r"([\w:()&’'\/,\-.\s]*?Graduate Certificate)\s*\.{3,}\s*(\d{3,4})")

# Extract raw lines from PDF
def extract_catalog_lines(pdf_path: Path) -> list:
    with pdfplumber.open(str(pdf_path)) as pdf:
        lines = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.extend(text.splitlines())
        return lines

# Fix broken wrapped lines
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

# Extract majors
def extract_programs_from_catalog(pdf_path: Path) -> list:
    """
    Extract graduate programs from the catalog while skipping the Roman numeral pages.

    OFFSET is used to skip the initial front matter with Roman numeral page numbering.
    """
    reader = PdfReader(str(pdf_path))
    programs = []

    # Skip the first OFFSET pages (Roman numerals) and only process the numbered section
    for i, page in enumerate(reader.pages[OFFSET:], start=OFFSET):
        text = page.extract_text() or ""
        lines = text.splitlines()

        printed_page_number = None

        # Try to detect the printed page number from the last ~40 lines of the page
        for line in reversed(lines[-40:]):
            if re.fullmatch(r"\d{3,4}", line.strip()):
                num = int(line.strip())
                if 3 <= num <= 761:  # valid major section page range
                    printed_page_number = num
                    break

        # Fallback with pdfplumber if PyPDF2 missed it
        if not printed_page_number:
            with pdfplumber.open(str(pdf_path)) as pdf:
                text_lines = pdf.pages[i].extract_text().splitlines()
                for line in reversed(text_lines[-10:]):
                    try:
                        num = int(line.strip())
                        if 3 <= num <= 761:
                            printed_page_number = num
                            break
                    except ValueError:
                        continue

        # If we still can’t find a printed page number, skip
        if not printed_page_number:
            continue

        # Collect header block for possible program titles
        header_block = []
        for line in lines[:40]:
            stripped = line.strip()
            if stripped == "":
                continue
            if stripped.lower().startswith("college of "):
                break
            header_block.append(stripped)

        # Look for valid program title + degree suffix
        for j in range(len(header_block)):
            for span in range(1, 4):  # check 1-line, 2-line, or 3-line combos
                combo = " ".join(header_block[j:j+span]).replace("•", "").strip()
                combo_lower = combo.lower()
                if any(phrase in combo_lower for phrase in STOP_PHRASES):
                    continue

                match = re.match(rf"^([A-Z].*?),\s*({DEGREE_PATTERN})\.?$", combo)
                if match:
                    program = f"{match.group(1).strip()}, {match.group(2).strip()}"
                    programs.append((program, printed_page_number))
                    break
            else:
                # continue outer loop if inner didn't break
                continue
            # break outer loop if we found a match
            break

    return programs

# Extract graduate certificates
def extract_gcs(pdf_path: Path) -> list:
    """
    Extract graduate certificates from the catalog while skipping the Roman numeral pages.

    OFFSET is used to skip the initial front matter with Roman numeral page numbering.
    """
    reader = PdfReader(str(pdf_path))
    gcs = []

    # Skip the first OFFSET pages (Roman numerals) and only process the numbered section
    for i, page in enumerate(reader.pages[OFFSET:], start=OFFSET):
        text = page.extract_text() or ""
        lines = text.splitlines()

        printed_page_number = None

        # Try to detect the printed page number from the last ~40 lines of the page
        for line in reversed(lines[-40:]):
            try:
                num = int(line.strip())
                if 763 <= num <= 981:  # valid Graduate Certificate section page range
                    printed_page_number = num
                    break
            except ValueError:
                continue

        # Fallback with pdfplumber if PyPDF2 missed it
        if not printed_page_number:
            with pdfplumber.open(str(pdf_path)) as pdf:
                text_lines = pdf.pages[i].extract_text().splitlines()
                for line in reversed(text_lines[-10:]):
                    try:
                        num = int(line.strip())
                        if 763 <= num <= 981:
                            printed_page_number = num
                            break
                    except ValueError:
                        continue

        # If we still can’t find a printed page number, skip
        if not printed_page_number:
            continue

        # Look for Graduate Certificate titles near the top of the page
        found_gc = False
        for j in range(len(lines[:30])):  # scan first ~30 lines for GC titles
            for span in range(1, 4):  # check 1-line, 2-line, or 3-line combos
                combo = " ".join(line.strip() for line in lines[j:j+span])
                combo_clean = combo.replace("•", "").strip()
                combo_lower = combo_clean.lower()

                # Skip lines with known stop phrases
                if any(phrase in combo_lower for phrase in STOP_PHRASES):
                    continue

                # Check if it's a Graduate Certificate title
                if (
                    "graduate certificate" in combo_lower
                    and combo_lower.startswith(tuple("abcdefghijklmnopqrstuvwxyz"))
                    and 3 <= len(combo_clean.split()) <= 22
                ):
                    gcs.append((combo_clean, printed_page_number))
                    found_gc = True
                    break

            if found_gc:
                break

    return gcs
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

def classify_credential(abbrev: str) -> str:
    ab = re.sub(r"[^\w]", "", abbrev).upper()
    if any(x in ab for x in ["CERT", "GRADCERTIFICATE"]):
        return "Grad Cert"
    elif any(x in ab for x in ["PHD", "DBA", "EDD", "EDS", "DRPH", "DNP", "DPT", "AUD", "PHARMD", "MD"]):
        return "Doctorate"
    elif ab.startswith("M") and not ab.startswith("MD"):
        return "Masters"
    else:
        return "Other"

# Build DataFrame
def build_program_dataframe(pdf_path: Path, programs: list[tuple[str, int]]) -> pd.DataFrame:
    reader = PdfReader(str(pdf_path))
    rows = []
    for program_name, page_number in programs:
        text, lines = grab_text(reader, page_number, range_len=2)
        hours = find_hours(text)
        credential = program_name.split(",")[-1].strip()
        is_cert = "CERT" in credential.upper()
        edu_obj = "Grad Cert" if is_cert else classify_credential(credential)
        concentration_status = "No" if is_cert else detect_concentration(text)
        if concentration_status == "Yes":
            prog_type = "Major with Concentration"
        elif is_cert:
            prog_type = "Grad Cert"
        elif edu_obj in ["Masters", "Doctorate"]:
            prog_type = "Major"
        else:
            prog_type = "Other"
        rows.append({
            "Program Name": program_name,
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


# Main Function for Execution
def run_gr_parser(core_pdf: str) -> pd.DataFrame:
    pdf_path = Path(core_pdf)
    majors = extract_programs_from_catalog(pdf_path)
    gcs = extract_gcs(pdf_path)
    all_programs = majors + gcs
    return build_program_dataframe(pdf_path, all_programs)