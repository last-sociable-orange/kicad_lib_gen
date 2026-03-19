# Agent Guidelines for kicad_lib_gen

This document provides essential information for agentic coding agents working in this repository.

## 1. Build, Lint, Test Commands

### Quick Start
- **Install dependencies:** `uv sync`
- **Run any script:** `uv run <script.py>`

### Main CLI Tools
- **Digikey Authentication:** `uv run digikey_auth.py --user <client_id> --secret <client_secret> [--output .token]`
- **Digikey Search:** `uv run digikey_search.py "<keywords>" [--limit N] [--offset N]`
- **KiCad CIP (main tool):** `uv run kicad_cip.py -k "<keywords>"` or `uv run kicad_cip.py -f <csv_file>`

### Running Individual Components
These are Python scripts with argument parsing; there is no separate build step. Use `uv run` to execute any `.py` file.

### Linting & Type Checking
This project does not currently use `ruff`, `mypy`, `black`, or similar tools. The codebase is formatted with basic PEP 8 style (4-space indentation, double quotes for strings). No formal type checking beyond what's in the code.

## 2. Code Style Guidelines

### Imports
- Standard library imports first, then third-party, then local
- Group related imports (e.g., `import os`, `import sys` together)
- Example:
  ```python
  import argparse
  import csv
  import json
  import logging
  import os
  import sys
  from dataclasses import dataclass, field
  ```

### Formatting
- Indentation: 4 spaces (no tabs)
- Max line length: ~100 characters (comfortably readable)
- Blank lines: separate logical sections and class definitions
- String quoting: Use double quotes `"` for strings consistently
- Multi-line strings: Use triple double-quotes `"""`

### Types
- Python 3.13+ type hints expected for function signatures and complex variables
- Use `list[str]`, `dict[str, Any]`, `None | str` (not `Optional`, `Union`)
- Prefer explicit types for function parameters and return values
- Dataclasses used for structured data (e.g., `ProductInfoBase`, `ProductInfo`)

### Naming Conventions
- Files: `snake_case.py`
- Classes: `PascalCase` (e.g., `ProductDb`, `ProductInfo`)
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE` (e.g., `AUTHORIZATION_BASE_URL`)
- Private/internal functions: prefix with single underscore if not part of public API (not heavily used currently)

### Error Handling
- Use `try/except` for anticipated failure modes (file I/O, network, parsing)
- Log errors with `logging.error()` before raising or exiting
- For user-facing errors, print to `sys.stderr` and `sys.exit(1)` in CLI tools
- For unexpected errors, log and re-raise to allow upstream handling
- Raise specific exceptions (`FileNotFoundError`, `ValueError`) where appropriate

### Database & SQL
- Uses SQLite3 with manual SQL strings; always use parameterized queries where possible to avoid injection
- Table/column names follow exact casing from legacy schema; do not change
- `INSERT OR REPLACE` used for upsert operations

### CLI Arguments
- Use `argparse` with mutually exclusive groups for alternative input modes
- Provide both short (`-k`) and long (`--keywords`) flags
- Include helpful `help` strings
- Required arguments marked with `required=True`

### Prompts & User Interaction
- When using `prompt_toolkit`, provide auto-completion (`WordCompleter`) for known values (symbols, footprints)
- Default values should be sensible (e.g., `default='1'` for selection, `default='n'` for overwrite)
- Handle `KeyboardInterrupt` gracefully with clear exit message

## 3. Project-Specific Notes

### Digikey API Integration
- Tokens stored in `.token` file (JSON) with keys: `client_id`, `client_secret`, `access_token`, `refresh_token`, `expires_by`, `refresh_token_expires_by`
- Access tokens expire; automatic refresh logic checks expiry and updates `.token` file
- If refresh token expires, user must re-run `digikey_auth.py`

### KiCad CIP Workflow
- Database file: `components.db` (SQLite) with table `components`
- Symbol and footprint fields: `KicadSymbolLibrary`, `KicadFootprintLibrary`
- Standard symbols/footprints: prefix with `Standard:` (e.g., `Standard:R`)
- CSV batch mode: header line required with exactly 3 columns; auto-fills symbol/footprint if exactly 1 search result; fails if 0 or >1 results

### File Locations & Conventions
- `.token` - authentication token (user-generated, not in git)
- `components.db` - SQLite database (typically in `Library/` folder of KiCad project)
- `components_db.kicad_dbl` - ODBC config file for KiCad CIP integration (provided externally)
- `uv.lock` - dependency lock file (committed)

## 4. Dependencies

From `pyproject.toml`:
- `prompt-toolkit>=3.0.52`
- `requests-oauthlib>=2.0.0`

Python >= 3.13 required.

## 5. Testing Strategy

No automated tests exist. Manual testing approach:
1. Run `digikey_auth.py` to obtain token (requires Digikey developer account)
2. Use `digikey_search.py` to validate API connectivity
3. Run `kicad_cip.py` in interactive mode to verify database operations
4. For batch mode, create a CSV with known good MPNs and verify auto-insert

## 6. Known Issues & Pitfalls

- The `digikey_search.py` module expects `.token` in current working directory; if missing, raises `FileNotFoundError` with guidance.
- `kicad_cip.py` batch mode is strict: requires exactly one search result for each CSV row; otherwise exits with error (no partial processing).
- Fragment fields (Param01-32, Value01-32) support up to 32 parameters; excess are truncated.
- Symbol/footprint auto-completion only includes entries already in database; new values must be typed manually until added.

## 7. Git Workflow

- Main branch: `main`
- Commit messages: Use imperative mood, concise (`feat:`, `fix:`, `docs:` prefixes optional but encouraged)
- Do not commit `.token` or `components.db` (already in `.gitignore`)

## 8. External Resources

- Digikey Developer Portal: https://developer.digikey.com/
- KiCad documentation: https://docs.kicad.org/
- README.md provides end-user workflow guide

---

**Last updated:** 2025-03-18 (based on commit 0450a03)
