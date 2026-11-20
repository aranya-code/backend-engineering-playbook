# README

## Overview

The `scripts/` directory contains operational utilities for the Secure File Upload API. These scripts support test-fixture generation, integration testing, and verification of the S3 bucket security configuration.

Test fixtures are generated locally when the fixture-generation utility runs. They are runtime artifacts, not standalone source files committed to the repository. Generate them before running workflows that depend on test data.

## Directory Contents

| File | Purpose |
|---|---|
| `create_test_files.py` | Generates deterministic test fixtures for upload and download testing. |
| `run_integration_tests.py` | Integration-test utility. |
| `verify_bucket_security.py` | S3 bucket security verification utility. |

## Generate Test Fixtures

Run the generator from the project root:

```bash
python scripts/create_test_files.py
```

By default, it creates the following files under `data/test-files/`:

```text
data/
└── test-files/
    ├── sample.txt
    ├── sample.json
    ├── sample.csv
    ├── sample.png
    ├── empty.txt
    ├── large-binary.bin
    └── manifest.json
```

The generated fixtures cover common upload and download scenarios:

| Fixture | Purpose |
|---|---|
| `sample.txt` | Basic text-file upload and download. |
| JSON fixture | JSON content-type and structured metadata testing. |
| `sample.csv` | CSV upload and download testing. |
| `sample.png` | Image-file validation and upload testing. |
| `empty.txt` | Empty-file validation. |
| `large-binary.bin` | Large-file transfer testing. Defaults to 5 MiB. |
| JSON manifest | Records generated fixture filenames, sizes, and extensions. |

The JSON fixture and manifest are created by the generator. They should not be expected to exist in a fresh checkout before fixture generation.

The generator does not overwrite existing files by default. If a destination file already exists, generation fails and instructs you to use `--force`.

### Generator Options

| Option | Default | Description |
|---|---|---|
| `--output-dir` | `data/test-files` | Destination directory for generated fixtures. |
| `--large-size-mib` | `5` | Size of the generated binary fixture in MiB. Valid range: 1–1024. |
| `--force` | Disabled | Allow existing generated files to be overwritten. |
| `--verbose` | Disabled | Enable detailed logging. |

Generate fixtures in a custom directory:

```bash
python scripts/create_test_files.py \
  --output-dir data/custom-test-files
```

Generate a larger binary fixture:

```bash
python scripts/create_test_files.py --large-size-mib 25
```

Regenerate existing fixtures intentionally:

```bash
python scripts/create_test_files.py --force
```

Enable detailed logging:

```bash
python scripts/create_test_files.py --verbose
```

### Generated Manifest

After generating the fixture files, the utility creates a JSON manifest containing a description and a `files` array. Each entry records the generated file's name, byte size, and extension.

Example structure:

```json
{
  "description": "Generated test fixtures for the Secure File Upload API.",
  "files": [
    {
      "filename": "sample.json",
      "size_bytes": 250,
      "extension": ".json"
    }
  ]
}
```

The example illustrates the manifest structure. Actual file sizes and entries depend on the generated fixtures and configured binary size.

## Integration Testing

The project includes `run_integration_tests.py` for integration testing. Run it from the project root after reviewing its command-line options and prerequisites:

```bash
python scripts/run_integration_tests.py --help
```

Integration tests may require an appropriately configured S3 environment. Use a non-production bucket and test credentials with only the permissions required by the test workflow.

## Bucket Security Verification

The project includes `verify_bucket_security.py` for checking the S3 bucket security configuration. Inspect its supported options before execution:

```bash
python scripts/verify_bucket_security.py --help
```

Run security verification only with the intended AWS account, Region, and bucket configuration. Ensure the active AWS identity has the read permissions required by the checks.

## Operational Considerations

- Run scripts from the project root unless their implementation explicitly supports another working directory.
- Generate test fixtures before running workflows that depend on them.
- Keep generated fixtures out of production data locations.
- Do not place credentials or sensitive customer data in test fixtures.
- Use `--force` only when replacing generated files is intentional.
- Treat `large-binary.bin` as a local test artifact; avoid committing it unless the repository explicitly requires it.
- Use a dedicated non-production S3 bucket for integration testing.
- Review AWS account, Region, and bucket settings before running any utility that interacts with AWS.
- Remove generated test files when they are no longer required:

```bash
rm -rf data/test-files
```

## Key Takeaways

- Test fixtures are generated locally; they are not required to exist in a fresh repository checkout.
- The default fixture output directory is `data/test-files/`.
- Existing generated files are protected from accidental overwrite unless `--force` is supplied.
- Run integration and security utilities only against an explicitly configured non-production AWS environment.
- Keep generated test data, AWS credentials, and production data isolated.