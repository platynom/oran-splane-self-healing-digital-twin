# Project Environment

This project uses project-local Python packages in `.project-python/site-packages`.

Note: Windows application-control policy blocked creating a traditional `.venv` executable environment on this machine. The workaround is still isolated for this project: packages are installed into `.project-python/site-packages` and loaded with `PYTHONPATH`.

## Create / Refresh

```powershell
$py = "C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
New-Item -ItemType Directory -Force -Path .project-python\site-packages
& $py -m pip install --target .project-python\site-packages -r requirements.txt
```

Use the same bundled Python executable for running scripts, with `PYTHONPATH` pointed at the project-local package directory.

```powershell
$env:PYTHONPATH = "$PWD\.project-python\site-packages"
& "C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" --version
```

## Useful Commands

Render visual page sheets for the priority PDFs:

```powershell
$env:PYTHONPATH = "$PWD\.project-python\site-packages"
& "C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" tools\render_pdf_review.py literature-survey\papers\priority --pattern "P_*.pdf"
```

Build a CSV inventory of all literature PDFs:

```powershell
$env:PYTHONPATH = "$PWD\.project-python\site-packages"
& "C:\Users\Admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" tools\build_literature_inventory.py
```

## Installed Tooling

- `PyMuPDF`: render PDF pages, extract text, metadata, figures/tables indicators.
- `pypdf`: lightweight PDF text and metadata workflows.
- `pdfplumber`: table/text extraction when layout matters.
- `pillow`: image/contact sheet generation.
- `pandas` + `openpyxl`: optional literature matrices and Excel exports.
- `python-docx`: later conversion of survey notes into Word format.
- `rich`: optional readable terminal output.

The checked-in scripts avoid optional dependencies where possible, so the core PDF workflow only needs PyMuPDF and Pillow.
