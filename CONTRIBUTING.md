# Contributing to CDC Voucher Management System

Thank you for considering contributing! This guide will help you get started.

## How to Contribute

### Reporting Bugs

1. Check [existing issues](https://github.com/riffarhan/CDC-Voucher-System/issues) to avoid duplicates.
2. Open a new issue using the **Bug Report** template.
3. Include steps to reproduce, expected vs actual behavior, and your environment details.

### Suggesting Features

1. Open a new issue using the **Feature Request** template.
2. Describe the problem you're trying to solve and your proposed solution.

### Submitting Pull Requests

1. Fork the repository and create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes and test them locally.
3. Ensure your code follows the project style (see below).
4. Open a PR using the pull request template.
5. Link any related issues in the PR description.

## Development Setup

```bash
# Clone your fork
git clone https://github.com/<your-username>/CDC-Voucher-System.git
cd CDC-Voucher-System

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python full_server.py

# In separate terminals, launch clients
python flet_household.py
python flet_merchant.py
python flet_dashboard.py
```

## Code Style

- **Python**: Follow [PEP 8](https://peps.python.org/pep-0008/).
- **Indentation**: 4 spaces (no tabs).
- **Line length**: 120 characters max.
- **Imports**: Group into standard library, third-party, and local — separated by blank lines.

## Commit Message Format

Use clear, descriptive commit messages:

```
<type>: <short description>

<optional body>
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples:**
- `feat: add voucher expiry date validation`
- `fix: correct balance calculation for partial redemptions`
- `docs: update API reference in README`

## Code of Conduct

Be respectful, constructive, and inclusive. We're all here to learn and build.

## Questions?

Open a [discussion](https://github.com/riffarhan/CDC-Voucher-System/issues) or reach out to the maintainers.
