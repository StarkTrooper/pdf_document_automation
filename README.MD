# PDF Document Automation

A collection of Python utilities designed to automate repetitive editing tasks in existing PDF documents.

This project focuses on **content replacement, selective redaction, and batch document processing**, reducing the need for manual editing while preserving the original document structure whenever possible.

## Features

- **Content replacement:** Locate existing text using reference anchors, remove selected content, and insert updated information.
- **Selective redaction:** Remove targeted text, numerical values, and graphical elements from structured PDF documents.
- **Batch processing:** Process multiple PDF files automatically.
- **Recursive directory traversal:** Discover PDF files across nested folders.
- **Non-destructive workflows:** Save modified documents separately from their originals.
- **Multi-page support:** Process individual pages within multi-page documents.
- **Validation and error handling:** Detect processing failures and verify selected output conditions.

## Technologies

- Python 3.10+
- PyMuPDF
- pathlib
- argparse
- Regular expressions

## Project Structure

```text
pdf_document_automation/
├── scripts/
│   ├── pdf_content_replacement.py
│   └── pdf_selective_redaction.py
├── examples/
├── tests/
├── README.md
├── requirements.txt
└── .gitignore
```

## Installation

Clone the repository:

```bash
git clone https://github.com/StarkTrooper/pdf_document_automation.git
cd pdf_document_automation
```

Create a virtual environment:

```bash
python -m venv .venv
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Utilities

### 1. PDF Content Replacement

`pdf_content_replacement.py`

Locates specific text regions within a PDF using predefined anchors, removes existing content, and inserts replacement text.

Useful for updating standardized fields in documents with consistent layouts.

### 2. PDF Selective Redaction

`pdf_selective_redaction.py`

Removes selected content from structured PDFs using text detection, coordinate-based regions, and document-specific processing rules.

Supports batch processing, multiple pages, and preservation of non-targeted content.

## Usage

The utilities are designed for structured PDF templates. Their configuration and command-line options depend on the processing rules implemented in each script.

Review the configuration before executing a utility against new documents.

For batch processing, the tools accept a root directory containing PDF files and nested folders.

## Limitations

- PDF layouts can vary significantly between document generators.
- Some files require template-specific rules or coordinate adjustments.
- Scanned documents may require additional image-processing or OCR capabilities.
- Automated text validation does not guarantee that every visual element was removed.
- PDF redaction is not a substitute for a comprehensive privacy or security audit.

Always test the utilities on sample documents before processing large collections.

## Privacy and Data Handling

This repository is intended to contain source code and synthetic examples only.

Real invoices, personal information, confidential documents, fiscal records, and production outputs should not be committed to the repository.

## Project Background

Developed as a practical automation project to reduce repetitive manual work involving structured PDF documents.

The project demonstrates Python scripting, file-system automation, PDF manipulation, error handling, and document validation.