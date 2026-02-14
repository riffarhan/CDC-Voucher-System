import requests
import flet as ft
from datetime import datetime

base_url = "http://127.0.0.1:5000"

# Design System
MERCHANT_GREEN_DARK = "#1B4332"
MERCHANT_GREEN_MED = "#2D6A4F"
MERCHANT_GREEN_ACCENT = "#40916C"
GREY_BG = "#F5F5F5"
GREY_BORDER = "#E0E0E0"
GREY_TEXT = "#666666"
TEXT_DARK = "#1A1A1A"


def _call_api(method, path, data=None):
    url = base_url + path
    methods = method.strip().upper()

    try:
        if methods == "GET":
            response = requests.get(url)
        elif methods == "POST":
            response = requests.post(url, json=data or {})
        else:
            return 0, {"ok": False, "message": f"Unsupported method: {method}"}
    except Exception as e:
        return 0, {"ok": False, "message": f"Network error: {e}"}

    try:
        data = response.json()
    except Exception:
        data = {"ok": False, "message": "Non-JSON response from server"}
    return response.status_code, data


def _store_badge():
    """Green store icon badge."""
    return ft.Container(
        content=ft.Icon(ft.Icons.STORE, size=16, color=ft.Colors.WHITE),
        bgcolor=MERCHANT_GREEN_ACCENT,
        border_radius=4,
        padding=ft.Padding.all(4),
    )


def main(page: ft.Page):
    page.title = "CDC Voucher System (Merchant)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window.width = 400
    page.window.height = 800
    page.window.resizable = False
    page.bgcolor = GREY_BG

    session = {"merchant_id": None, "merchant_name": None, "view": "merchant_start"}
    message_text = ft.Text("", size=12, color=ft.Colors.RED)

    field_label_map = {
        "merchant_name": "Merchant Name",
        "uen": "UEN",
        "bank_name": "Bank Name",
        "account_number": "Account Number",
        "account_holder_name": "Account Holder Name",
    }

    def set_message(msg="", ok=False):
        message_text.value = msg or ""
        message_text.color = ft.Colors.GREEN if ok else ft.Colors.RED
        page.update()

    def navigate(view_name):
        message_text.value = ""
        session["view"] = view_name
        render()


    # View 1: Start / Register / Login

    def view_merchant_start():
        merchant_name_input = ft.TextField(
            label="Merchant Name",
            prefix_icon=ft.Icons.STORE,
            border_radius=8,
            filled=True,
            fill_color=ft.Colors.WHITE,
        )
        uen_input = ft.TextField(
            label="UEN",
            prefix_icon=ft.Icons.BADGE,
            border_radius=8,
            filled=True,
            fill_color=ft.Colors.WHITE,
        )
        # user choose bank names
        bank_name_dropdown = ft.Dropdown(
            label="Bank Name",
            border_radius=8,
            filled=True,
            fill_color=ft.Colors.WHITE,
            options=[
                ft.dropdown.Option(key="DBS Bank Ltd", text="DBS Bank Ltd"),
                ft.dropdown.Option(key="OCBC Bank", text="OCBC Bank"),
                ft.dropdown.Option(key="United Overseas Bank", text="United Overseas Bank"),
                ft.dropdown.Option(key="Maybank Singapore", text="Maybank Singapore"),
                ft.dropdown.Option(key="Standard Chartered Bank", text="Standard Chartered Bank"),
                ft.dropdown.Option(key="HSBC Singapore", text="HSBC Singapore"),
                ft.dropdown.Option(key="POSB Bank", text="POSB Bank"),
                ft.dropdown.Option(key="Citibank Singapore", text="Citibank Singapore"),
                ft.dropdown.Option(key="RHB Bank Berhad", text="RHB Bank Berhad"),
                ft.dropdown.Option(key="Bank of China", text="Bank of China"),
            ],
        )

        bank_name_field = ft.Row(
        controls=[ft.Icon(ft.Icons.ACCOUNT_BALANCE),bank_name_dropdown],vertical_alignment=ft.CrossAxisAlignment.CENTER
                       )

        account_number_input = ft.TextField(
            label="Account Number",
            prefix_icon=ft.Icons.CREDIT_CARD,
            border_radius=8,
            filled=True,
            fill_color=ft.Colors.WHITE,
        )
        account_holder_input = ft.TextField(
            label="Account Holder Name",
            prefix_icon=ft.Icons.PERSON,
            border_radius=8,
            filled=True,
            fill_color=ft.Colors.WHITE,
        )

        existing_merchant_id_input = ft.TextField(
            label="Merchant ID",
            hint_text="e.g., M001",
            prefix_icon=ft.Icons.BADGE,
            border_radius=8,
            filled=True,
            fill_color=ft.Colors.WHITE,
        )
        # merchant registration
        def register_merchant(e):
            set_message("")
            payload = {
                "merchant_name": (merchant_name_input.value or "").strip(),
                "uen": (uen_input.value or "").strip(),
                "bank_name": (bank_name_dropdown.value or "").strip(),
                "account_number": (account_number_input.value or "").strip(),
                "account_holder_name": (account_holder_input.value or "").strip(),
            }
            for k in ["merchant_name", "uen", "bank_name", "account_number", "account_holder_name"]:
                if not payload.get(k):
                    friendly = field_label_map.get(k, k)
                    set_message(f"{friendly} is required", ok=False)
                    return
            # call merchant api
            status_code, data = _call_api("POST", "/api/merchants", payload)
            if status_code == 201 and data.get("ok"):
                merchant = data.get("merchant") or {}
                session["merchant_id"] = merchant.get("Merchant_ID")
                session["merchant_name"] = merchant.get("Merchant_Name")
                set_message(f"Registered: {session['merchant_id']}", ok=True)
                navigate("merchant_confirm")
            else:
                set_message(data.get("message", f"Error ({status_code})"), ok=False)

    # open existing merchant portal
        def open_existing(e):
            set_message("")
            mid = (existing_merchant_id_input.value or "").strip().upper()
            if not mid:
                set_message("Enter a Merchant ID", ok=False)
                return

            status_code, data = _call_api("GET", "/api/merchants")
            if status_code != 200 or not data.get("ok"):
                set_message(data.get("message", f"Error ({status_code})"), ok=False)
                return

            merchants = data.get("merchants") or {}
            m = merchants.get(mid)
            if not m:
                set_message("Merchant ID not found on server.", ok=False)
                return

            session["merchant_id"] = mid
            session["merchant_name"] = str(m.get("Merchant_Name", "")).strip()
            set_message(f"Opened: {mid}", ok=True)
            navigate("merchant_confirm")

        # Header
        header_bar = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [_store_badge(), ft.Text("CDC Merchant", size=14, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500)],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Text(
                        "Merchant Portal",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                    ),
                    ft.Text(
                        "Register or access your merchant account",
                        size=12,
                        color=ft.Colors.WHITE70,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            bgcolor=MERCHANT_GREEN_DARK,
            padding=ft.Padding.symmetric(horizontal=20, vertical=18),
            alignment=ft.Alignment.CENTER,
        )

        message_bar = ft.Container(
            padding=ft.Padding.only(left=15, right=15, top=8),
            content=message_text,
        )

        # Register card
        register_section = ft.Container(
            content=ft.Column(
                [
                    ft.Text("New Merchant Registration", size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                    ft.Text("Enter your business details", size=12, color=GREY_TEXT),
                    ft.Container(height=10),
                    merchant_name_input,
                    uen_input,
                    bank_name_field,
                    account_number_input,
                    account_holder_input,
                    ft.Container(height=14),
                    ft.Button(
                        "Register",
                        icon=ft.Icons.STORE,
                        on_click=register_merchant,
                        width=350,
                        height=48,
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=MERCHANT_GREEN_DARK,
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=18,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
        )

        # Open existing card
        existing_section = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Open Existing Account", size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                    ft.Container(height=10),
                    existing_merchant_id_input,
                    ft.Container(height=14),
                    ft.OutlinedButton(
                        "Open Confirm Screen",
                        on_click=open_existing,
                        width=350,
                        height=48,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            padding=18,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
        )

        page_body = ft.Column(
            [
                header_bar,
                ft.Container(
                    content=ft.Column(
                        [
                            message_bar,
                            ft.Container(height=18),
                            register_section,
                            ft.Container(height=16),
                            existing_section,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        scroll=ft.ScrollMode.AUTO,
                        spacing=0,
                    ),
                    padding=ft.Padding.only(left=15, right=15),
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

        return ft.Container(content=page_body, padding=0, expand=True)


    # View 2: Paste & Confirm
   
    def view_merchant_confirm():
        mid = session.get("merchant_id")
        mname = session.get("merchant_name")

        if not mid:
            navigate("merchant_start")
            return ft.Container()

        request_box = ft.TextField(
            label="Paste Payment Request from Household app",
            value="",
            multiline=True,
            read_only=False,
            min_lines=7,
            max_lines=10,
            border_radius=8,
            focused_border_color=MERCHANT_GREEN_ACCENT,
        )

        summary_text = ft.Text("Paste request, then confirm redemption.", size=12, color=GREY_TEXT)

        def back(e):
            navigate("merchant_start")

        def clear(e):
            request_box.value = ""
            summary_text.value = "Paste request, then confirm redemption."
            set_message("", ok=True)
            page.update()
    # parse request sentence
        def confirm(e):
            raw = (request_box.value).strip()
            try:
                lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
                hid = lines[0].split("Household", 1)[1].replace(".", "").strip().upper()
                tranche_label = lines[1].split(":", 1)[1].replace(".", "").strip()

                label_to_key = {"May 2025": "May2025", "Jan 2026": "Jan2026"}
                tranche = label_to_key.get(tranche_label, tranche_label.replace(" ", ""))

                use_line = lines[2].replace("Use vouchers:", "").replace(".", "").strip()
                parts = [p.strip() for p in use_line.split(",") if p.strip()]
                use = {"2": 0, "5": 0, "10": 0}
                for p in parts:
                    left_right = [x.strip() for x in p.split("x")]
                    denom = left_right[0].replace("$", "").strip()
                    val = int(left_right[1])
                    if denom in use:
                        use[denom] = val

                txid = f"{mid}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            except Exception:
                set_message("Cannot read request. Please paste the full request again.", ok=False)
                return

            payload = {
                "action": "confirm",
                "merchant_name": mname,
                "transaction_id": txid,
                "tranche": tranche,
                "use": use,
            }
        # call redemption api
            status_code, data = _call_api("POST", f"/api/{hid}/redeem", payload)
            if status_code == 200 and data.get("ok"):
                set_message("Confirmed. Household balance deducted.", ok=True)
                summary_text.value = f"Redemption confirmed for {hid}"
                request_box.value = ""
                page.update()
            else:
                set_message(data.get("message", f"Error ({status_code})"), ok=False)

        # Header
        header_bar = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=back, icon_color=ft.Colors.WHITE),
                    ft.Column(
                        [
                            ft.Text("Confirm Redemption", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                            ft.Text(f"{mid} - {mname}", size=10, color=ft.Colors.WHITE70),
                        ],
                        spacing=2,
                    ),
                    ft.IconButton(icon=ft.Icons.CLEAR_ALL, on_click=clear, icon_color=ft.Colors.WHITE, tooltip="Clear"),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor=MERCHANT_GREEN_DARK,
            padding=12,
        )

        message_bar = ft.Container(
            padding=ft.padding.only(left=15, right=15, top=8),
            content=message_text,
        )

        # Instruction card
        instruction_card = ft.Container(
            content=ft.Column(
                [
                    ft.Text("How to process", size=14, weight=ft.FontWeight.BOLD, color=MERCHANT_GREEN_DARK),
                    ft.Container(height=6),
                    ft.Text("1. Household generates a payment request", size=12, color=TEXT_DARK),
                    ft.Text("2. Paste the request in the box below", size=12, color=TEXT_DARK),
                    ft.Text("3. Tap Confirm Redemption to process", size=12, color=TEXT_DARK),
                ],
                spacing=2,
            ),
            padding=14,
            border_radius=10,
            bgcolor="#E8F5E9",
        )

        # Paste & confirm card
        confirm_card = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Payment Request", size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                    ft.Container(height=8),
                    request_box,
                    ft.Container(height=12),
                    ft.ElevatedButton(
                        "Confirm Redemption",
                        icon=ft.Icons.CHECK_CIRCLE,
                        on_click=confirm,
                        width=350,
                        height=48,
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=MERCHANT_GREEN_DARK,
                            shape=ft.RoundedRectangleBorder(radius=8),
                        ),
                    ),
                    ft.Container(height=8),
                    summary_text,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            padding=18,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
        )

        body = ft.Column(
            [
                header_bar,
                ft.Container(
                    content=ft.Column(
                        [
                            message_bar,
                            ft.Container(height=12),
                            instruction_card,
                            ft.Container(height=12),
                            confirm_card,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        scroll=ft.ScrollMode.AUTO,
                        spacing=0,
                    ),
                    padding=ft.padding.only(left=15, right=15),
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

        return ft.Container(content=body, padding=0, expand=True)

    def render():
        page.controls.clear()
        view_name = session.get("view")

        if view_name == "merchant_start":
            page.add(view_merchant_start())
        elif view_name == "merchant_confirm":
            page.add(view_merchant_confirm())
        else:
            page.add(view_merchant_start())

        page.update()

    render()


if __name__ == "__main__":
    ft.run(main)
