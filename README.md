<p align="center">
  <h1 align="center">CDC Voucher Management System</h1>
  <p align="center">
    A full-stack voucher distribution and redemption system for Singapore's Community Development Council (CDC) voucher scheme.
    <br />
    Built with Flask + Flet as part of NTU AN6007 Advanced Programming.
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.0-green?logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/Flet-0.21-purple" alt="Flet">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-yellow" alt="License"></a>
  <a href="https://github.com/riffarhan/CDC-Voucher-System/commits/main"><img src="https://img.shields.io/github/last-commit/riffarhan/CDC-Voucher-System" alt="Last Commit"></a>
</p>

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Screenshots](#screenshots)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Sample Data](#sample-data)
- [Voucher Tranches](#voucher-tranches)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Features

### Household Portal (`flet_household.py`)
- Register new households with postal code and unit number
- Claim voucher packages across multiple tranches
- View real-time voucher balance with denomination breakdown
- Redeem vouchers at participating merchants with live search
- Visual bar charts showing voucher usage history

### Merchant Portal (`flet_merchant.py`)
- Register new merchants with UEN and bank details
- Auto-lookup bank codes for 10 major Singapore banks (DBS, OCBC, UOB, Maybank, etc.)
- Process voucher redemption transactions
- View full transaction history with timestamps

### Analytics Dashboard (`flet_dashboard.py`)
- Real-time statistics: total households, merchants, and redemption volume
- Bar chart visualizations for voucher distribution and redemption trends
- Aggregate data across all tranches and denominations

## Architecture

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Household   │   │   Merchant   │   │  Dashboard   │
│   Flet UI    │   │   Flet UI    │   │   Flet UI    │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                   │
       └──────────┬───────┴───────────────────┘
                  │  HTTP REST API
           ┌──────┴───────┐
           │  Flask Server │
           │  (Port 5000)  │
           └──────┬───────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
 households.json  merchant.csv  Redeem*.csv
```

| Layer | Technology | Description |
|-------|-----------|-------------|
| **Backend** | Flask | REST API server on port 5000 |
| **Frontend** | Flet | Three native desktop applications |
| **Storage** | File-based | JSON for households, CSV for merchants & transactions |

## Screenshots

> *Coming soon — screenshots of the Household, Merchant, and Dashboard portals.*

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/riffarhan/CDC-Voucher-System.git
cd CDC-Voucher-System

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
make install
# or: pip install -r requirements.txt
```

### Running

**Option 1: Using Make (recommended)**

```bash
make server      # Start Flask API (terminal 1)
make household   # Launch Household portal (terminal 2)
make merchant    # Launch Merchant portal (terminal 3)
make dashboard   # Launch Analytics dashboard (terminal 4)
```

**Option 2: Manual**

```bash
# Terminal 1 — start the backend
python full_server.py

# Terminal 2–4 — launch any client
python flet_household.py
python flet_merchant.py
python flet_dashboard.py
```

Run `make help` to see all available commands.

## API Reference

All endpoints are served at `http://localhost:5000`.

### Register a Household

```
POST /api/household_registration
```

<details>
<summary>Example</summary>

```bash
curl -X POST http://localhost:5000/api/household_registration \
  -H "Content-Type: application/json" \
  -d '{"Postal_Code": "520123", "Unit_No": "12-345"}'
```

**Response:**
```json
{
  "status": "success",
  "Household_ID": "H001",
  "message": "Household registered successfully"
}
```

</details>

### List / Register Merchants

```
GET  /api/merchants          # List all merchants
POST /api/merchants          # Register a new merchant
```

<details>
<summary>Example — register a merchant</summary>

```bash
curl -X POST http://localhost:5000/api/merchants \
  -H "Content-Type: application/json" \
  -d '{
    "Merchant_Name": "FairPrice Xpress",
    "UEN": "200601234A",
    "Bank_Name": "DBS Bank Ltd",
    "Account_Number": "1234567890",
    "Account_Holder_Name": "NTUC FairPrice"
  }'
```

**Response:**
```json
{
  "status": "success",
  "Merchant_ID": "M001",
  "message": "Merchant registered successfully"
}
```

</details>

### Get Balance / Claim Vouchers

```
GET  /api/<household_id>/balance   # Get voucher balance
POST /api/<household_id>/balance   # Claim a voucher package
```

<details>
<summary>Example — claim vouchers</summary>

```bash
curl -X POST http://localhost:5000/api/H001/balance \
  -H "Content-Type: application/json" \
  -d '{"package": "May2025"}'
```

**Response:**
```json
{
  "status": "success",
  "Voucher": {"2": 50, "5": 20, "10": 30},
  "message": "Vouchers claimed successfully"
}
```

</details>

### Redeem Vouchers

```
POST /api/<household_id>/redeem
```

<details>
<summary>Example</summary>

```bash
curl -X POST http://localhost:5000/api/H001/redeem \
  -H "Content-Type: application/json" \
  -d '{"Merchant_ID": "M001", "denomination": "5", "quantity": 2}'
```

**Response:**
```json
{
  "status": "success",
  "amount_redeemed": 10,
  "remaining_balance": {"2": 50, "5": 18, "10": 30}
}
```

</details>

### Dashboard Data

```
GET /api/dashboard_data
```

<details>
<summary>Example</summary>

```bash
curl http://localhost:5000/api/dashboard_data
```

**Response:**
```json
{
  "total_households": 5,
  "total_merchants": 3,
  "total_redemptions": 12,
  "redemption_data": [...]
}
```

</details>

## Sample Data

Pre-built sample data is included in `data/samples/` for testing:

```bash
make seed   # Copies sample data to project root
```

This populates the system with 3 households (unclaimed, partially redeemed, fully claimed) and 3 Singapore merchants. See [`data/samples/README.md`](data/samples/README.md) for details.

## Voucher Tranches

| Tranche | $2 Vouchers | $5 Vouchers | $10 Vouchers | Total Value |
|---------|-------------|-------------|--------------|-------------|
| May 2025 | 50 | 20 | 30 | $500 |
| Jan 2026 | 30 | 18 | 15 | $300 |

## Project Structure

```
CDC-Voucher-System/
├── .editorconfig              # Editor settings (indent, encoding)
├── data/
│   └── samples/
│       ├── README.md          # Sample data documentation
│       ├── households.json    # Sample households
│       └── merchant.csv       # Sample merchants
├── full_server.py             # Flask REST API server
├── flet_household.py          # Household desktop UI (Flet)
├── flet_merchant.py           # Merchant desktop UI (Flet)
├── flet_dashboard.py          # Analytics dashboard UI (Flet)
├── classes.py                 # Household dataclass
├── persistent_storage.py      # File I/O utilities (JSON + CSV)
├── requirements.txt           # Python dependencies
├── Makefile                   # Developer convenience commands
├── CHANGELOG.md               # Release history
├── LICENSE                    # MIT License
└── README.md                  # This file
```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ModuleNotFoundError: flet_charts` | Missing dependency | Run `pip install -r requirements.txt` (includes `flet-charts`) |
| `ConnectionRefusedError` on client launch | Server not running | Start the server first: `make server` or `python full_server.py` |
| Port 5000 already in use | Another process on port 5000 | Kill the process: `lsof -ti:5000 \| xargs kill` (macOS/Linux) |
| Flet window doesn't open | Display/environment issue | Ensure you're not in a headless environment; try `flet --version` |
| `FileNotFoundError` for CSV/JSON | First run, no data files yet | This is normal — the server creates files on first write. Or run `make seed` |
| Stale data after restart | Cached data from previous session | Run `make clean` then `make seed` for a fresh start |

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **NTU AN6007** — Advanced Programming course, Nanyang Technological University
- **Singapore CDC** — Inspiration from the real Community Development Council voucher scheme
- **[Flask](https://flask.palletsprojects.com/)** and **[Flet](https://flet.dev/)** — The frameworks that power this project
