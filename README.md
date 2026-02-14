# CDC Voucher Management System

A voucher distribution and redemption management system built for Singapore's Community Development Council (CDC) voucher scheme. Developed as part of NTU AN6007 Advanced Programming.

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

**Backend:** Flask REST API (`full_server.py`)
**Frontend:** Three Flet desktop applications for households, merchants, and analytics
**Storage:** File-based (JSON + CSV)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/household_registration` | Register a new household |
| GET/POST | `/api/merchants` | List or register merchants |
| GET/POST | `/api/<household_id>/balance` | Get balance or claim vouchers |
| POST | `/api/<household_id>/redeem` | Redeem vouchers at a merchant |
| GET | `/api/dashboard_data` | Retrieve analytics data |

## Setup

### Prerequisites
- Python 3.10+

### Installation

```bash
git clone https://github.com/riffarhan/CDC-Voucher-System.git
cd CDC-Voucher-System
pip install -r requirements.txt
```

### Running

1. Start the backend server:
```bash
python full_server.py
```

2. In separate terminals, launch any of the client applications:
```bash
python flet_household.py    # Household portal
python flet_merchant.py     # Merchant portal
python flet_dashboard.py    # Analytics dashboard
```

## Voucher Tranches

| Tranche | $2 Vouchers | $5 Vouchers | $10 Vouchers | Total Value |
|---------|-------------|-------------|--------------|-------------|
| May 2025 | 50 | 20 | 30 | $500 |
| Jan 2026 | 30 | 18 | 15 | $300 |

## Project Structure

```
├── full_server.py          # Flask API server
├── flet_household.py       # Household desktop UI
├── flet_merchant.py        # Merchant desktop UI
├── flet_dashboard.py       # Analytics dashboard UI
├── classes.py              # Household dataclass
├── persistent_storage.py   # File I/O utilities
├── requirements.txt        # Python dependencies
└── README.md
```

## Team

NTU AN6007 Advanced Programming - Group Project
