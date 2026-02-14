# Sample Data

This directory contains sample data files for testing and development.

## Files

| File | Description |
|------|-------------|
| `households.json` | 3 sample households: one with full vouchers, one partially redeemed, one unclaimed |
| `merchant.csv` | 3 realistic Singapore merchants with different bank accounts |

## Usage

Copy sample data to the project root to use with the server:

```bash
# Using Make
make seed

# Manual
cp data/samples/households.json households.json
cp data/samples/merchant.csv merchant.csv
```

Then start the server with `python full_server.py` — it will pick up the data automatically.

> **Note:** The server generates these files at runtime too, so sample data is optional. It's useful for starting with a pre-populated state.
