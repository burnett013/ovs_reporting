# Catalog Parser App

This is a **Streamlit-based web application** for parsing **graduate and undergraduate catalogs**, extracting programs, graduate certificates, credit hours, and generating a **VA-ready Excel report**.  

It processes **PDF catalogs**, applies approval logic against last year’s data, and outputs a final report.

---

## Features

- Parse **Graduate** & **Undergraduate** catalog PDFs  
- Detect **Majors**, **Graduate Certificates**, and credit hour requirements  
- Classify credentials (Masters, Doctorate, Graduate Certificate)  
- Extract additional info like modality, license prep, and concentrations  
- Compare against **last year’s VA Excel file**  
- Generate a downloadable **Excel report**

---

## Tech Stack

- [Streamlit](https://streamlit.io/)  
- [Pandas](https://pandas.pydata.org/)  
- [PyPDF2](https://pypi.org/project/PyPDF2/)  
- [pdfplumber](https://pypi.org/project/pdfplumber/)  
- [openpyxl](https://pypi.org/project/openpyxl/)  

---

## Project Structure
frontend/
|----- app.py # Main Streamlit entry point
|----- app_params.py # App metadata
|----- requirements.txt # Project dependencies
|----- README.md # This file
|
|----- catalog_parser/ # Graduate/Undergrad parsing logic
|----- page_handler/ # Streamlit pages
|----- utils/ # Approval logic & formatting helpers
|----- upl_file_bunker/ # Generated reports & uploaded files
|----- test_files/ # Sample PDFs & Excel files

---

## Getting Started

### 2. Clone this repository

```bash
git clone <your_repo_url> # ------ ADD THIS
cd frontend
```
---

### 3. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
##### - OR - 
.venv\Scripts\activate           # Windows

### Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run the app
streamlit run app.py

It will open in your default browser at:
http://localhost:8501

	1.	Select the academic year from the dropdown
	2.	Upload the required files:
	    •	Graduate Catalog PDF (currently core)
	    •	Undergraduate Catalog PDF
	    •	Last year’s VA Excel file
	3.	Click Generate Report
	4.	Download the generated Excel report

🐳 Docker (Coming Soon)
Once Docker is added, you’ll be able to build and run:
docker build -t catalog-parser .
docker run -p 8501:8501 catalog-parser


Author

Crafted with ❤️ by James A. Burnett
Office of Veteran Success
University of South Florida