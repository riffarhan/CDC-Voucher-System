
from classes import Household
import os,json, csv
from datetime import datetime

# load data from household.json
def Load_cache_household(households_json_path):
    
    if not os.path.exists(households_json_path):
        return

    with open(households_json_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
        return raw_data
    
    

# update new records to json file
def Save_cache_households(households_json_path, save_dict):
    
    with open(households_json_path, "w", encoding="utf-8") as f:
        json.dump(save_dict, f, indent=2)

# load existing merchants into memory

def load_merchants(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return {}
    out = {}
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            mid = (row.get("Merchant_ID")).strip().upper()
            if mid:
                out[mid] = row
    return out

# update merchant.csv records
def Save_cache_merchants(merchants_txt_path, columns, rows):
    file_exists = os.path.exists(merchants_txt_path)
    write_header = (not file_exists) or (os.path.getsize(merchants_txt_path) == 0)

    with open(merchants_txt_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        if write_header:
            writer.writeheader()
        writer.writerow({k: rows[k] for k in columns})

# load redemption.csv files, mainly to track transaction id
def read_redeem_rows():
    rows = []
    for file_name in os.listdir("."):
        if file_name.startswith("Redeem") and file_name.endswith(".csv"):
            
            with open(file_name, "r", newline="") as f:
                for row in csv.DictReader(f):
                    rows.append(row)
    return rows

# append new redemption records
def append_redemptions_hourly(date_time, redeem_columns, rows):
  csv_path = f"Redeem{date_time.strftime('%Y%m%d%H')}.csv"
  file_exists = os.path.exists(csv_path)
  with open(csv_path, "a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=redeem_columns)
    if not file_exists:
      writer.writeheader()
    for r in rows:
      writer.writerow(r)
