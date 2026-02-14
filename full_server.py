
from flask import Flask, request, jsonify
import datetime
from dataclasses import asdict
from classes import Household
from persistent_storage import (
    Load_cache_household,
    Save_cache_households,
    Save_cache_merchants,
    load_merchants,
    append_redemptions_hourly,
    read_redeem_rows,
)

app = Flask(__name__)

household_jsons = "households.json"
household_cache = {}

claim_voucher_package = {
    "May2025": {"2": 50, "5": 20, "10": 30},
    "Jan2026": {"2": 30, "5": 18, "10": 15},
}

raw_data = Load_cache_household(household_jsons) or {}
for household_id, data in raw_data.items():
    household_cache[household_id] = Household(
        Household_ID=data["Household_ID"],
        Postal_Code=data["Postal_Code"],
        Unit_No=data["Unit_No"],
        Registration_Date=data["Registration_Date"],
        Claimed=data["Claimed"],
        Voucher=data["Voucher"],
        Voucher_Code_Seq=data.get("Voucher_Code_Seq", 1),
    )

# Merchant storage & cache
merchant_txt_path = "merchant.csv"

merchant_columns = [
    "Merchant_ID",
    "Merchant_Name",
    "UEN",
    "Bank_Name",
    "Bank_Code",
    "Branch_Code",
    "Account_Number",
    "Account_Holder_Name",
    "Registration_Date",
    "Status",
]

bank_map = {
    "DBS Bank Ltd": {"Bank_Code": "7171", "Branch_Code": "001"},
    "OCBC Bank": {"Bank_Code": "7339", "Branch_Code": "501"},
    "United Overseas Bank": {"Bank_Code": "7761", "Branch_Code": "001"},
    "Maybank Singapore": {"Bank_Code": "7091", "Branch_Code": "001"},
    "Standard Chartered Bank": {"Bank_Code": "7302", "Branch_Code": "001"},
    "HSBC Singapore": {"Bank_Code": "7375", "Branch_Code": "146"},
    "POSB Bank": {"Bank_Code": "7171", "Branch_Code": "081"},
    "Citibank Singapore": {"Bank_Code": "9465", "Branch_Code": "001"},
    "RHB Bank Berhad": {"Bank_Code": "7083", "Branch_Code": "001"},
    "Bank of China": {"Bank_Code": "7012", "Branch_Code": "001"},
}

merchant_cache = {}
merchant_cache.update(load_merchants(merchant_txt_path))

# Redemption columns
redeem_columns = [
    "Transaction_ID",
    "Household_ID",
    "Merchant_ID",
    "Transaction_Date_Time",
    "Voucher_Code",
    "Denomination_Used",
    "Amount_Redeemed",
    "Payment_Status",
    "Remarks",
]


def next_merchant_id(cache):
    next_number = 1
    for merchant_id in cache.keys():
        mid = str(merchant_id).strip().upper()
        if mid.startswith("M") and mid[1:].isdecimal():
            n = int(mid[1:]) + 1
            if n > next_number:
                next_number = n
    return "M" + str(next_number).zfill(3)


def next_transaction_id(completed_transaction):
    next_num = 1001
    for tid0 in completed_transaction.keys():
        tid = str(tid0).strip().upper()
        if tid.startswith("TX") and tid[2:].isdecimal():
            n = int(tid[2:]) + 1
            if n > next_num:
                next_num = n
    return "TX" + str(next_num)


completed_transaction = {}
for row in read_redeem_rows() or []:
    transaction_id = row.get("Transaction_ID") or ""
    transaction_id = str(transaction_id).strip().upper()
    if transaction_id.startswith("TX") and transaction_id[2:].isdecimal():
        completed_transaction[transaction_id] = True


def parse_filter_date():
    date_str = (request.args.get("date") or "").strip()
    if not date_str:
        return datetime.date.today()
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return datetime.date.today()


def same_day_from_tx_time(tx_time_str, target_date):
    # tx_time_str: "YYYY-MM-DD-HHMMSS"
    if not tx_time_str or len(tx_time_str) < 10:
        return False
    return tx_time_str[:10] == target_date.strftime("%Y-%m-%d")


# API 1: Register household
@app.route("/api/household_registration", methods=["POST"])
def create_household():
    data = request.get_json(silent=True) or {}
    postal_code = (data.get("postal_code") or "").strip()
    unit_no = (data.get("unit_no") or "").strip()

    if not postal_code or not unit_no:
        return jsonify({"ok": False, "message": "postal_code, unit_no are required"}), 400

    unit_id = unit_no.replace("-", "")
    household_id = f"H{postal_code}{unit_id}"

    if household_id in household_cache:
        return jsonify({"ok": False, "message": "Household already exists"}), 409

    new_household = Household(
        Household_ID=household_id,
        Postal_Code=postal_code,
        Unit_No=unit_no,
        Registration_Date=datetime.datetime.now().strftime("%Y-%m-%d"),
        Claimed={"May2025": False, "Jan2026": False},
        Voucher={
            "May2025": {"2": 0, "5": 0, "10": 0},
            "Jan2026": {"2": 0, "5": 0, "10": 0},
        },
        Voucher_Code_Seq=1,
    )

    household_cache[household_id] = new_household
    raw_data[household_id] = asdict(new_household)
    Save_cache_households(household_jsons, raw_data)

    return jsonify({"ok": True, "household_id": household_id, "status": "successfully registered"}), 201


# API 2: Merchant registration
@app.route("/api/merchants", methods=["GET", "POST"])
def api_merchant():
    if request.method == "GET":
        return jsonify({"ok": True, "count": len(merchant_cache), "merchants": merchant_cache}), 200

    data = request.get_json(silent=True) or {}
    required_fields = ["merchant_name", "uen", "bank_name", "account_number", "account_holder_name"]
    for field in required_fields:
        if not str(data.get(field) or "").strip():
            return jsonify({"ok": False, "message": f"{field} is required"}), 400

    merchant_name = data["merchant_name"].strip()
    uen = data["uen"].strip()
    bank_name = data["bank_name"].strip()
    account_number = data["account_number"].strip()
    account_holder_name = data["account_holder_name"].strip()

    if bank_name not in bank_map:
        return jsonify({"ok": False, "message": "bank_name not found", "bank_name_received": bank_name}), 400

    bank_code = bank_map[bank_name]["Bank_Code"]
    branch_code = bank_map[bank_name]["Branch_Code"]

    merchant_id = next_merchant_id(merchant_cache)
    registration_date = datetime.datetime.now().strftime("%Y-%m-%d")

    merchant_data = {
        "Merchant_ID": merchant_id,
        "Merchant_Name": merchant_name,
        "UEN": uen,
        "Bank_Name": bank_name,
        "Bank_Code": bank_code,
        "Branch_Code": branch_code,
        "Account_Number": account_number,
        "Account_Holder_Name": account_holder_name,
        "Registration_Date": registration_date,
        "Status": "Active",
    }

    merchant_cache[merchant_id] = merchant_data
    Save_cache_merchants(merchant_txt_path, merchant_columns, merchant_data)

    return jsonify({"ok": True, "merchant": merchant_data, "status": "Registration Successful"}), 201


# API 3: balance extraction
@app.route("/api/<household_id>/balance", methods=["GET", "POST"])
def balance_or_claim(household_id):
    household_id = household_id.strip().upper()
    if household_id not in household_cache:
        return jsonify({"ok": False, "message": "Household not found"}), 404

    household = household_cache[household_id]

    total_remaining_value = Household.household_total_balance(household)
    message = f"Balance returned. Remaining balance: ${total_remaining_value}."

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        tranche_name = str(data.get("tranche") or "").strip()

        if tranche_name not in claim_voucher_package:
            return jsonify({"ok": False, "message": "Invalid tranche"}), 400

        if household.Claimed.get(tranche_name, False):
            message = "Vouchers Already claimed"
        else:
            claim_counts = claim_voucher_package[tranche_name]
            household.Voucher[tranche_name]["2"] += claim_counts["2"]
            household.Voucher[tranche_name]["5"] += claim_counts["5"]
            household.Voucher[tranche_name]["10"] += claim_counts["10"]
            household.Claimed[tranche_name] = True
            message = f"You have successfully claimed the voucher for {tranche_name}"
            raw_data[household_id] = asdict(household)
            Save_cache_households(household_jsons, raw_data)

        total_remaining_value = Household.household_total_balance(household)
        message = f"{message}. Remaining balance: ${total_remaining_value}."

    return jsonify(
        {
            "ok": True,
            "household_id": household.Household_ID,
            "claimed_status": household.Claimed,
            "voucher_balance": household.Voucher,
            "total_remaining_value": total_remaining_value,
            "message": message,
        }
    ), 200


# API 4: Redemption
@app.route("/api/<household_id>/redeem", methods=["POST"])
def redeem(household_id):
    household_id = household_id.strip().upper()
    if household_id not in household_cache:
        return jsonify({"ok": False, "message": "Household not found"}), 404

    household = household_cache[household_id]
    data = request.get_json(silent=True) or {}

    merchant_name = str(data.get("merchant_name") or "").strip()
    if not merchant_name:
        return jsonify({"ok": False, "message": "merchant name is required"}), 400

    # find merchant id from merchant name
    merchant_id = ""
    target_name = merchant_name.lower()
    for mid, m in merchant_cache.items():
        cached_name = str(m.get("Merchant_Name", "")).strip().lower()
        if cached_name == target_name:
            merchant_id = str(mid).strip().upper()
            break
    if not merchant_id:
        return jsonify({"ok": False, "message": "Merchant not found by merchant name"}), 404

    transaction_id = next_transaction_id(completed_transaction)
    if transaction_id in completed_transaction:
        return jsonify({"ok": False, "message": "This transaction id is already completed"}), 400

    tranche = str(data.get("tranche") or "").strip()
    use = data.get("use") or {}

    if tranche not in household.Voucher:
        return jsonify({"ok": False, "message": "Invalid tranche"}), 400

    try:
        u2 = int(use.get("2", 0))
        u5 = int(use.get("5", 0))
        u10 = int(use.get("10", 0))
    except Exception:
        return jsonify({"ok": False, "message": "use counts must be integers"}), 400

    if u2 < 0 or u5 < 0 or u10 < 0:
        return jsonify({"ok": False, "message": "use counts cannot be negative"}), 400
    if u2 == 0 and u5 == 0 and u10 == 0:
        return jsonify({"ok": False, "message": "No vouchers selected"}), 400

    available2 = int(household.Voucher[tranche]["2"])
    available5 = int(household.Voucher[tranche]["5"])
    available10 = int(household.Voucher[tranche]["10"])

    if available2 < u2 or available5 < u5 or available10 < u10:
        return jsonify({"ok": False, "message": "Insufficient vouchers at confirmation"}), 400

    # deduct vouchers
    household.Voucher[tranche]["2"] = available2 - u2
    household.Voucher[tranche]["5"] = available5 - u5
    household.Voucher[tranche]["10"] = available10 - u10

    transaction_time = datetime.datetime.now()
    tx_time_str = transaction_time.strftime("%Y-%m-%d-%H%M%S")

    total_used = u2 + u5 + u10
    total_tx_amount = 2 * u2 + 5 * u5 + 10 * u10

    rows = []
    seq = int(household.Voucher_Code_Seq)
    serial = 1

    denom_list = [(u2, "$2.00"), (u5, "$5.00"), (u10, "$10.00")]
    for count, denom_label in denom_list:
        for _ in range(count):
            is_last = (serial == total_used)
            remarks = "Final denomination used" if is_last else serial

            rows.append(
                {
                    "Transaction_ID": transaction_id,
                    "Household_ID": household_id,
                    "Merchant_ID": merchant_id,
                    "Transaction_Date_Time": tx_time_str,
                    "Voucher_Code": "V" + str(seq).zfill(7),
                    "Denomination_Used": denom_label,
                    "Amount_Redeemed": f"${total_tx_amount:.2f}",
                    "Payment_Status": "Completed",
                    "Remarks": remarks,
                }
            )
            seq += 1
            serial += 1

    append_redemptions_hourly(transaction_time, redeem_columns, rows)

    household.Voucher_Code_Seq = seq
    raw_data[household_id] = asdict(household)
    Save_cache_households(household_jsons, raw_data)

    completed_transaction[transaction_id] = True

    return jsonify(
        {
            "ok": True,
            "message": "Transaction completed",
            "transaction_id": transaction_id,
            "completed_at": transaction_time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    ), 200


# API 5: Dashboard data (date + window)
@app.route("/api/dashboard_data", methods=["GET"])
def dashboard_data():
    target_date = parse_filter_date()  # end date (inclusive)

    raw_window = (request.args.get("window") or "").strip()
    if raw_window:
        try:
            window_days = int(raw_window)
        except ValueError:
            window_days = 7
    else:
        window_days = 7

    allowed = {1, 3, 7}
    if window_days not in allowed:
        window_days = 7

    # window date set: target_date back N-1 days
    selected_set = set()
    i = 0
    while i < window_days:
        d = (target_date - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        selected_set.add(d)
        i += 1

    # all-time
    total_households = len(household_cache)
    total_merchants = len(merchant_cache)

    claimed_may = 0
    claimed_jan = 0
    for h in household_cache.values():
        if h.Claimed.get("May2025"):
            claimed_may += 1
        if h.Claimed.get("Jan2026"):
            claimed_jan += 1

    redeem_rows = read_redeem_rows() or []

    denom_value_map = {"$2.00": 2.0, "$5.00": 5.0, "$10.00": 10.0}

    # window totals + merchant rank
    total_redeemed_value = 0.0
    transaction_ids = set()
    merchant_tx_count = {}
    merchant_tx_value = {}

    for row in redeem_rows:
        tx_dt_str = (row.get("Transaction_Date_Time") or "").strip()
        if len(tx_dt_str) < 10:
            continue

        day_str = tx_dt_str[:10]
        if day_str not in selected_set:
            continue

        tx_id = (row.get("Transaction_ID") or "").strip()
        if tx_id:
            transaction_ids.add(tx_id)

        mid = (row.get("Merchant_ID") or "").strip()
        if mid:
            merchant_tx_count[mid] = merchant_tx_count.get(mid, 0) + 1

        denom = (row.get("Denomination_Used") or "").strip()
        v = denom_value_map.get(denom, 0.0)
        total_redeemed_value += v
        if mid:
            merchant_tx_value[mid] = merchant_tx_value.get(mid, 0.0) + v

    # merchant summary sorted by voucher count
    merchant_summary = []

    def sort_by_count(item):
        return item[1]

    sorted_items = sorted(merchant_tx_count.items(), key=sort_by_count, reverse=True)

    for mid, count in sorted_items:
        m = merchant_cache.get(mid, {})
        merchant_summary.append(
            {
                "merchant_id": mid,
                "merchant_name": m.get("Merchant_Name", mid),
                "voucher_count": count,
                "total_value": merchant_tx_value.get(mid, 0.0),
            }
        )

    # hourly (single-day) + hourly value
    hour_count_map = {h: 0 for h in range(24)}
    hour_value_map = {h: 0.0 for h in range(24)}

    for row in redeem_rows:
        tx_dt_str = (row.get("Transaction_Date_Time") or "").strip()
        if not same_day_from_tx_time(tx_dt_str, target_date):
            continue

        parts = tx_dt_str.split("-")
        if len(parts) >= 4 and len(parts[3]) >= 2:
            hh_str = parts[3][:2]
            if hh_str.isdecimal():
                hh = int(hh_str)
                if 0 <= hh <= 23:
                    hour_count_map[hh] += 1

                    denom = (row.get("Denomination_Used") or "").strip()
                    v = denom_value_map.get(denom, 0.0)
                    hour_value_map[hh] += v

    hourly_volume = []
    h = 0
    while h < 24:
        hourly_volume.append(
            {
                "hour": f"{h:02d}",
                "count": hour_count_map[h],
                "value": hour_value_map[h],  # ✅ new hourly value
            }
        )
        h += 1

    return jsonify(
        {
            "ok": True,

            # all-time
            "total_households": total_households,
            "total_merchants": total_merchants,
            "claimed_may2025": claimed_may,
            "claimed_jan2026": claimed_jan,

            # window
            "total_transactions": len(transaction_ids),
            "total_redeemed_value": total_redeemed_value,
            "merchant_summary": merchant_summary,

            # single-day
            "hourly_volume": hourly_volume,

            # meta
            "window_days": window_days,
            "end_date": target_date.strftime("%Y-%m-%d"),
        }
    ), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
