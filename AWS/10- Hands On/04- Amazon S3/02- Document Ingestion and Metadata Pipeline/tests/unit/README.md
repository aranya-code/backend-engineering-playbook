# README

## Overview

This directory contains unit tests for the Document Ingestion and Metadata Pipeline's processing components.

Unit tests verify the behavior of individual processing modules in isolation. They validate document parsing, content extraction, metadata handling, input validation, and failure handling without requiring AWS resources.

The tests focus on the document processor, which receives document bytes and metadata from the ingestion workflow and extracts processable content from supported document formats.

## Directory Structure

```text
tests/
└── unit/
    ├── README.md
    ├── test_document_processor.py
    ├── test_document_validator.py
    └── test_metadata_extractor.py
```

| File | Responsibility |
|---|---|
| `test_document_processor.py` | Tests document content processing and extraction across supported formats. |
| `test_document_validator.py` | Tests filename, MIME type, file size, and file signature validation. |
| `test_metadata_extractor.py` | Tests document metadata extraction from supported formats. |

## Testing Scope

Unit tests should validate application behavior independently of AWS infrastructure.

| Component | What to verify |
|---|---|
| Document processor | Text and structured content extraction, supported formats, malformed documents, and processing failures. |
| Document validator | Allowed extensions, MIME type consistency, filename safety, size limits, and file signatures. |
| Metadata extractor | Metadata extraction, format-specific properties, invalid input handling, and unsupported formats. |

Tests should cover both successful processing and expected failure conditions.

## Prerequisites

Install the project dependencies from the project root:

```bash
python -m pip install -r requirements.txt
```

Ensure the Python environment includes:

- Python 3.10 or later.
- pytest.
- pypdf.
- python-docx.
- openpyxl.
- python-magic where required by the implementation.

Run commands from the project root so that the `src` package is importable.

If the project uses a `src`-based import layout, configure the project or test environment accordingly. For example:

```bash
export PYTHONPATH=src
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH = "src"
```

## Running Unit Tests

Run all unit tests:

```bash
pytest tests/unit/ -v
```

Run a specific test module:

```bash
pytest tests/unit/test_document_processor.py -v
pytest tests/unit/test_document_validator.py -v
pytest tests/unit/test_metadata_extractor.py -v
```

Run a specific test class or test case:

```bash
pytest tests/unit/test_document_processor.py::TestPDFProcessing -v
```

Run tests with coverage:

```bash
pytest tests/unit/ \
    --cov=src \
    --cov-report=term-missing
```

On Windows PowerShell, use the same command on one line:

```powershell
pytest tests/unit/ --cov=src --cov-report=term-missing
```

## Test Data and Isolation

Prefer creating small, deterministic documents directly in test fixtures rather than depending on external files or AWS resources.

Examples include:

- In-memory PDF documents using `pypdf`.
- DOCX documents generated with `python-docx`.
- XLSX workbooks generated with `openpyxl`.
- UTF-8 text and CSV content stored as bytes.

Use temporary files only when the behavior under test requires filesystem interaction.

Tests should:

- Avoid real AWS API calls.
- Avoid hardcoded credentials or account-specific configuration.
- Avoid depending on external network services.
- Use deterministic input data.
- Verify observable behavior rather than implementation details.
- Keep test fixtures isolated between test cases.

For AWS-dependent components, inject clients or dependencies and use mocks or Moto where appropriate. Keep AWS integration behavior separate from pure document-processing tests.

## Testing Standards

### Assertions

Prefer assertions against the documented result structure and exact expected values.

For example:

```python
assert result["status"] == "COMPLETED"
assert result["filename"] == "report.pdf"
```

Use the actual result schema defined by the implementation.

Avoid weak assertions such as checking only that a result is truthy or converting an entire result to a string to search for expected values. Such assertions can pass even when the output structure is incorrect.

### Exception Handling

Assert specific exception types and meaningful error behavior.

```python
with pytest.raises(ValueError):
    processor.process_document(
        document=b"invalid content",
        metadata={},
        filename="report.pdf",
        content_type="application/pdf",
    )
```

Use the exception contract defined by the component. Avoid broad exception tuples unless multiple exception types are explicitly part of the public contract.

### Test Coverage

Include tests for:

- Valid documents across supported formats.
- Empty and malformed document content.
- Unsupported file formats.
- Invalid filenames and content types.
- Missing or invalid metadata.
- Unicode and special characters.
- Multiple worksheets and CSV edge cases where applicable.
- Parser failures and unexpected input conditions.
- Input immutability where the component promises not to mutate caller-owned data.

## Quality Checks

Run Ruff against the unit test directory:

```bash
ruff check tests/unit/
```

Check formatting:

```bash
ruff format --check tests/unit/
```

Run static type checking when the project configuration supports it:

```bash
mypy src/
```

Resolve test failures and static-analysis findings before merging changes.

## Key Takeaways

- Unit tests validate document-processing behavior without requiring deployed AWS resources.
- Generate deterministic document fixtures in memory to keep tests reproducible.
- Assert exact output structures and specific exception contracts rather than relying on weak assertions.
- Keep document parsing, validation, metadata extraction, and AWS integration concerns independently testable.
- Run pytest, coverage, Ruff, and applicable static-analysis checks before merging changes.