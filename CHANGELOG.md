# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2025-05-01

### Added

- **Flask REST API** (`full_server.py`) with endpoints for household registration, merchant management, voucher claiming, voucher redemption, and dashboard analytics.
- **Household Portal** (`flet_household.py`) — Flet desktop app for residents to register, view voucher balances, and redeem vouchers at participating merchants.
- **Merchant Portal** (`flet_merchant.py`) — Flet desktop app for merchants to register, process voucher redemptions, and view transaction history.
- **Analytics Dashboard** (`flet_dashboard.py`) — Flet desktop app with bar charts and statistics for monitoring voucher distribution and redemption across the scheme.
- **Data classes** (`classes.py`) — `Household` dataclass for structured data representation.
- **Persistent storage** (`persistent_storage.py`) — File-based I/O utilities for JSON and CSV data.
- **Two voucher tranches**: May 2025 ($500) and January 2026 ($300) with $2, $5, and $10 denominations.
