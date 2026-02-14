import requests
import flet as ft
from flet_charts import BarChart, BarChartGroup, BarChartRod, ChartAxis, ChartAxisLabel

base_url = "http://127.0.0.1:5000"

# Design System
NAVY_DARK = "#1B2A4A"
CDC_RED = "#DB0000"
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
            response = requests.post(url, json=data)
        else:
            return 0, {"ok": False, "message": f"Unsupported method: {method}"}
    except Exception as e:
        return 0, {"ok": False, "message": f"Network error: {e}"}

    try:
        data = response.json()
    except Exception:
        data = {"ok": False, "message": "Non-JSON response from server"}
    return response.status_code, data


def tranche_total(tranche_balance):
    return (
        2 * int(tranche_balance.get("2", 0))
        + 5 * int(tranche_balance.get("5", 0))
        + 10 * int(tranche_balance.get("10", 0))
    )


def build_request_sentence(household_id, tranche_label, use_counts):
    use_2 = int(use_counts.get("2", 0))
    use_5 = int(use_counts.get("5", 0))
    use_10 = int(use_counts.get("10", 0))
    total_amount = 2 * use_2 + 5 * use_5 + 10 * use_10

    lines = [
        f"Please redeem vouchers for Household {household_id}.",
        f"Voucher Tranche: {tranche_label}.",
        f"Use vouchers: $2 x {use_2}, $5 x {use_5}, $10 x {use_10}.",
        f"Total amount: ${total_amount}.",
    ]
    return "\n".join(lines)


def format_address(household_id):
    """Parse household ID like H5229880224 to 'Blk 522988, #02-24'"""
    try:
        raw = household_id.lstrip("Hh")
        postal = raw[:6]
        unit = raw[6:]
        if len(unit) >= 3:
            floor = unit[:2]
            room = unit[2:]
            return f"Blk {postal}, #{floor}-{room}"
        return f"Blk {postal}"
    except Exception:
        return household_id


def _cdc_badge():
    """Red CDC badge used in headers."""
    return ft.Container(
        content=ft.Text("CDC", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
        bgcolor=CDC_RED,
        border_radius=4,
        padding=ft.Padding.symmetric(horizontal=8, vertical=3),
    )


def _header_title_row(badge, label_text):
    """Row with CDC badge + label."""
    return ft.Row(
        [badge, ft.Text(label_text, size=14, color=ft.Colors.WHITE, weight=ft.FontWeight.W_500)],
        spacing=8,
        alignment=ft.MainAxisAlignment.CENTER,
    )


def main(page: ft.Page):
    page.title = "CDC Voucher System (Household)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window.width = 400
    page.window.height = 800
    page.window.resizable = False
    page.bgcolor = GREY_BG
    clipboard = ft.Clipboard()
    

    label_map = {"May2025": "May 2025", "Jan2026": "Jan 2026"}

    session = {
        "household_id": None,
        "view": "household_start",
        "last_balance": None,
        "flash_msg": "",
        "flash_ok": False,
        "tranche_key": "May2025",
    }

    selected_vouchers = {"2": set(), "5": set(), "10": set()}
    message_text = ft.Text("", size=12, color=ft.Colors.RED)

    # helper functions
    
    def set_message(message, ok=False):
        message_text.value = message 
        message_text.color = ft.Colors.GREEN if ok else ft.Colors.RED
        page.update()
    # flash message on next page
    def set_flash(message, ok=False):
        session["flash_msg"] = message 
        session["flash_ok"] = bool(ok)
    # navigate between pages
    def navigate(view_name):
        message_text.value = ""
        session["view"] = view_name
        render()
    # update selected vouchers and total selected
    def update_summary_text(selected_summary):
        c2 = len(selected_vouchers["2"])
        c5 = len(selected_vouchers["5"])
        c10 = len(selected_vouchers["10"])
        total_amount = 2 * c2 + 5 * c5 + 10 * c10
        selected_summary.value = f"${total_amount}"

    def get_balance():
        hid = session.get("household_id")
        if not hid:
            return False

        status_code, data = _call_api("GET", f"/api/{hid}/balance")
        if status_code != 200 or not data.get("ok"):
            set_message(data.get("message", "Household not found"), ok=False)
            return False

        session["last_balance"] = data
        return True

    # View 1: Start / Register / Login

    def view_household_start():
        postal_code_input = ft.TextField(
            label="Postal Code",
            hint_text="e.g., 522988 (6 digits)",
            prefix_icon=ft.Icons.LOCATION_ON,
            border_radius=8,
            filled=True,
            fill_color=ft.Colors.WHITE
        )
        unit_no_input = ft.TextField(
            label="Unit No",
            hint_text="e.g., 02-24",
            prefix_icon=ft.Icons.HOME,
            border_radius=8,
            filled=True,
            fill_color=ft.Colors.WHITE
        )
        existing_household_id_input = ft.TextField(
            label="Household ID",
            hint_text="e.g., H5229880224",
            prefix_icon=ft.Icons.BADGE,
            border_radius=8,
            filled=True,
            fill_color=ft.Colors.WHITE
        )
       # case 1: register new household
        def register_household(e):
            
            if not postal_code_input.value or not unit_no_input.value:
                set_message("Please fill postal code and unit no", ok=False)
                return

            status_code, data = _call_api("POST","/api/household_registration",{"postal_code": postal_code_input.value, "unit_no": unit_no_input.value})

            if status_code == 201 and data.get("ok"):
                session["household_id"] = data.get("household_id")
                set_flash(f"Registered: {session['household_id']}", ok=True)
                navigate("household_dashboard")
            else:
                set_message(data.get("message", f"Error ({status_code})"), ok=False)
    # case 2: open existing account
        def open_existing(e):
            hid = (existing_household_id_input.value).strip()
            if not hid:
                set_message("Enter a Household ID", ok=False)
                return

            session["household_id"] = hid
            set_flash(f"Opened: {hid}", ok=True)
            navigate("household_dashboard")

        def go_analytics(e):
            navigate("analytics")

        # Header
        header_bar = ft.Container(
            content=ft.Column(
                [
                    _header_title_row(_cdc_badge(), "CDC Vouchers"),
                    ft.Text(
                        "Household Portal",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE
                    ),
                    ft.Text(
                        "Register or access your vouchers",
                        size=12,
                        color=ft.Colors.WHITE70
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4
            ),
            bgcolor=NAVY_DARK,
            padding=ft.Padding.symmetric(horizontal=20, vertical=18),
            alignment=ft.Alignment.CENTER
        )

        message_bar = ft.Container(
            padding=ft.Padding.only(left=15, right=15, top=8),
            content=message_text
        )

        # Register card
        register_section = ft.Container(
            content=ft.Column(
                [
                    ft.Text("New Household", size=16, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                    ft.Text("Enter your address", size=12, color=GREY_TEXT),
                    ft.Container(height=10),
                    postal_code_input,
                    ft.Container(height=8),
                    unit_no_input,
                    ft.Container(height=14),
                    ft.Button(
                        "Register",
                        on_click=register_household,
                        width=350,
                        height=48,
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=CDC_RED,
                            shape=ft.RoundedRectangleBorder(radius=8)
                        ),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0
            ),
            padding=18,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK))
        )

        # Open existing card
        existing_section = ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Open Existing Household",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=TEXT_DARK
                    ),
                    ft.Container(height=10),
                    existing_household_id_input,
                    ft.Container(height=14),
                    ft.OutlinedButton(
                        "Open Dashboard",
                        icon=ft.Icons.DASHBOARD,
                        on_click=open_existing,
                        width=350,
                        height=48,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8)
                        ),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            padding=18,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK))
        )

        analytics_button = ft.Container(
            content=ft.TextButton(
                "View Analytics",
                icon=ft.Icons.BAR_CHART,
                on_click=go_analytics,
            ),
            alignment=ft.Alignment.CENTER
        )

    # page layout
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
                            ft.Container(height=16),
                            analytics_button
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        scroll=ft.ScrollMode.AUTO,
                        spacing=0
                    ),
                    padding=ft.Padding.only(left=15, right=15),
                    expand=True
                ),
            ],
            spacing=0,
            expand=True
        )
        return ft.Container(content=page_body, padding=0, expand=True)


    # View 2: Household page

    def view_household_dashboard():
        hid = session.get("household_id")
        if not hid:
            navigate("household_start")
            return ft.Container()

        if not get_balance():
            navigate("household_start")
            return ft.Container()

        last = session.get("last_balance")
        voucher_balance = last.get("voucher_balance") 
        claimed_status = last.get("claimed_status") 
        # State for expand/collapse per denomination
        expanded_denoms = {"2": True, "5": True, "10": True}

        selected_summary = ft.Text("$0", size=36, weight=ft.FontWeight.BOLD, color=TEXT_DARK)
        voucher_panel = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        # request to be generated on household app
        payment_request_box = ft.TextField(
            label="Payment request",
            multiline=True,
            min_lines=4,
            read_only=True,
            text_style=ft.TextStyle(font_family="Courier New", size=12),
            border_radius=8
        )

        payment_request_container = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=18),
                            ft.Text("Request copied to clipboard!", size=12, color=ft.Colors.GREEN, weight=ft.FontWeight.W_500),
                        ],
                        spacing=6,
                    ),
                    ft.Container(height=4),
                    payment_request_box
                ],
                spacing=0
            ),
            visible=False,
            padding=12,
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, GREY_BORDER)
        )

        def on_back(e):
            navigate("household_start")
        # refresh and voucher selection clears
        def on_refresh(e):
            if get_balance():
                selected_vouchers["2"].clear()
                selected_vouchers["5"].clear()
                selected_vouchers["10"].clear()
                set_flash("Balance refreshed.", ok=True)
                navigate("household_dashboard")

        def on_claim(e):
            tranche_key = str(e.control.data).strip()
            if not tranche_key:
                return
            status_code, data = _call_api( "POST", f"/api/{hid}/balance", {"tranche": tranche_key})
            if status_code == 200 and data.get("ok"):
                set_flash(data.get("message", "Claimed"), ok=True)
                selected_vouchers["2"].clear()
                selected_vouchers["5"].clear()
                selected_vouchers["10"].clear()
                session["tranche_key"] = tranche_key
                navigate("household_dashboard")
            else:
                set_message(data.get("message", f"Error ({status_code})"), ok=False)
        # when clicking clear button, all things reset
        def on_clear_selection(e):
            selected_vouchers["2"].clear()
            selected_vouchers["5"].clear()
            selected_vouchers["10"].clear()
            payment_request_box.value = ""
            payment_request_container.visible = False
            update_summary_text(selected_summary)
            render_vouchers()
        # after claiming, pages update to show vouchers
        def on_tranche_tab(e):
          new_key = e.control.data
          if new_key == session["tranche_key"]:
            return

          session["tranche_key"] = new_key

    # reset selection state
          selected_vouchers["2"].clear()
          selected_vouchers["5"].clear()
          selected_vouchers["10"].clear()
          payment_request_box.value = ""
          payment_request_container.visible = False
          navigate("household_dashboard")

        #when user tick/untick vouchers
        def on_voucher_chip_click(e):
            denom, voucher_id = e.control.data
            if voucher_id in selected_vouchers[denom]:
                selected_vouchers[denom].discard(voucher_id)
            else:
                selected_vouchers[denom].add(voucher_id)

            payment_request_box.value = ""
            payment_request_container.visible = False
            update_summary_text(selected_summary)
            render_vouchers()

    # select all
        def on_select_all_change(ev):
            denom = ev.control.data
            tranche_key = session.get("tranche_key") or "May2025"
            tranche_obj = voucher_balance.get(tranche_key)
            available_count = int(tranche_obj.get(denom, 0))

            if ev.control.value:
                for i in range(1, available_count + 1):
                    voucher_id = f"{tranche_key}:{denom}:{i}"
                    selected_vouchers[denom].add(voucher_id)
            else:
                selected_vouchers[denom].clear()

            payment_request_box.value = ""
            payment_request_container.visible = False
            update_summary_text(selected_summary)
            render_vouchers()
        # expand voucher selection window
        def on_toggle_expand(e):
            denom = e.control.data
            expanded_denoms[denom] = not expanded_denoms[denom]
            render_vouchers()
        # genedrate request
        def on_generate_and_copy(e):
            tranche_key = session.get("tranche_key") or "May2025"
            tranche_label = label_map.get(tranche_key, tranche_key)

            is_claimed = bool(claimed_status.get(tranche_key, False))
            if not is_claimed:
                set_message("Claim this tranche first.", ok=False)
                return

            counts = {
                "2": len(selected_vouchers["2"]),
                "5": len(selected_vouchers["5"]),
                "10": len(selected_vouchers["10"]),
            }
            if counts["2"] == 0 and counts["5"] == 0 and counts["10"] == 0:
                set_message("Please select at least 1 voucher.", ok=False)
                return

            payment_request_box.value = build_request_sentence(hid, tranche_label, counts)
            payment_request_container.visible = True
            clipboard.set(payment_request_box.value)
            page.update()
            set_message("Request generated and copied to clipboard!", ok=True)

        def go_analytics(e):
            navigate("analytics")

        # Tranche tab selector
        tranche_tabs_row = ft.Row(spacing=0)

        def build_tranche_tabs():
            tranche_tabs_row.controls.clear()
            for key, label in label_map.items():
                is_active = key == session.get("tranche_key", "May2025")
                tranche_tabs_row.controls.append(
                    ft.Container(
                        content=ft.Text(
                            label,
                            size=13,
                            weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL,
                            color=ft.Colors.WHITE if is_active else GREY_TEXT,
                            text_align=ft.TextAlign.CENTER
                        ),
                        bgcolor=NAVY_DARK if is_active else ft.Colors.WHITE,
                        border=None if is_active else ft.Border.all(1, GREY_BORDER),
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=20, vertical=10),
                        on_click=on_tranche_tab,
                        data=key,
                        expand=True,
                        alignment=ft.Alignment.CENTER
                    )
                )

        build_tranche_tabs()

        # Render voucher chips
        def render_vouchers():
            voucher_panel.controls.clear()

            tranche_key = session.get("tranche_key") or "May2025"
            tranche_obj = voucher_balance.get(tranche_key)
            is_claimed = claimed_status.get(tranche_key, False)
       # claim before redeem
            if not is_claimed:
                payment_request_box.value = ""
                payment_request_container.visible = False
                voucher_panel.controls.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "Please claim this tranche before selecting vouchers.",
                                    size=12,
                                    color=CDC_RED,
                                    text_align=ft.TextAlign.CENTER
                                ),
                                ft.Container(height=8),
                                ft.ElevatedButton(
                                    "Claim Vouchers",
                                    data=tranche_key,
                                    on_click=on_claim,
                                    width=280,
                                    style=ft.ButtonStyle(bgcolor=CDC_RED, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8))
                                ),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER
                        ),
                        padding=16,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=12,
                        border=ft.border.all(1, GREY_BORDER)
                    )
                )
                update_summary_text(selected_summary)
                page.update()
                return

            for denom in ["2", "5", "10"]:
                available_count = int(tranche_obj.get(denom, 0))

                all_selected = available_count > 0 and all(
                    f"{tranche_key}:{denom}:{i}" in selected_vouchers[denom]
                    for i in range(1, available_count + 1)
                )

                is_expanded = expanded_denoms.get(denom, True)

                # Section header
                header_row = ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                f"${denom} Vouchers ({available_count} available)",
                                size=13,
                                weight=ft.FontWeight.W_600,
                                color=TEXT_DARK,
                            ),
                            ft.Row(
                                [
                                    ft.Checkbox(
                                        label="All",
                                        value=all_selected,
                                        data=denom,
                                        on_change=on_select_all_change,
                                        scale=0.85,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.EXPAND_LESS if is_expanded else ft.Icons.EXPAND_MORE,
                                        data=denom,
                                        on_click=on_toggle_expand,
                                        icon_size=20,
                                    )
                                ],
                                spacing=0
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    padding=ft.Padding.only(left=4, right=0, top=4, bottom=0)
                )
                voucher_panel.controls.append(header_row)
               # not enough vouchers
                if available_count <= 0:
                    voucher_panel.controls.append(
                        ft.Container(
                            content=ft.Text("None", size=12, color=GREY_TEXT),
                            padding=ft.padding.only(left=8, bottom=8),
                        )
                    )
                    continue
     
                if not is_expanded:
                    sel_count = len(selected_vouchers[denom])
                    if sel_count > 0:
                        voucher_panel.controls.append(
                            ft.Container(
                                content=ft.Text(f"{sel_count} selected", size=11, color=GREY_TEXT),
                                padding=ft.padding.only(left=8, bottom=8),
                            )
                        )
                    continue

                # Voucher chip grid
                grid = ft.GridView(
                    expand=False,
                    max_extent=170,
                    child_aspect_ratio=2.2,
                    spacing=10,
                    run_spacing=10,
                )

                for i in range(1, available_count + 1):
                    voucher_id = f"{tranche_key}:{denom}:{i}"
                    is_selected = voucher_id in selected_vouchers[denom]

                    chip = ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(
                                    f"${denom}",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=NAVY_DARK if is_selected else TEXT_DARK
                                ),
                                ft.Icon(
                                    ft.Icons.CHECK_CIRCLE if is_selected else ft.Icons.CIRCLE_OUTLINED,
                                    color=NAVY_DARK if is_selected else GREY_BORDER,
                                    size=22
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=12,
                        border_radius=12,
                        bgcolor=ft.Colors.WHITE,
                        border=ft.Border.all(
                            2 if is_selected else 1,
                            NAVY_DARK if is_selected else GREY_BORDER
                        ),
                        on_click=on_voucher_chip_click,
                        data=(denom, voucher_id)
                    )
                    grid.controls.append(chip)

                voucher_panel.controls.append(grid)

            update_summary_text(selected_summary)
            page.update()

        #  page header 
        header_bar = ft.Container(
        content=ft.Column(
        [
            ft.Row(
                [
                   
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                on_click=on_back,
                                icon_color=ft.Colors.WHITE,
                                tooltip="Back",
                                icon_size=20,
                            ),
                            _header_title_row(_cdc_badge(), "CDC Vouchers"),
                        ],
                        spacing=6,
                    ),

                    # RIGHT: actions
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.BAR_CHART,
                                on_click=go_analytics,
                                icon_color=ft.Colors.WHITE,
                                tooltip="Analytics",
                                icon_size=20,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.REFRESH,
                                on_click=on_refresh,
                                icon_color=ft.Colors.WHITE,
                                icon_size=20,
                            ),
                        ],
                        spacing=0,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Text("CDC Vouchers 2025", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Row(
                [
                    ft.Icon(ft.Icons.HOME, color=ft.Colors.WHITE70, size=16),
                    ft.Text(format_address(hid), size=12, color=ft.Colors.WHITE70),
                ],
                spacing=6,
            ),
        ],
        spacing=4,
    ),
    bgcolor=NAVY_DARK,
    padding=ft.Padding.symmetric(horizontal=16, vertical=14),
)


        message_bar = ft.Container(
            padding=ft.Padding.only(left=15, right=15, top=8),
            content=message_text,
        )

        #  Balance card 
        tranche_key = session.get("tranche_key") or "May2025"
        tranche_balance_data = voucher_balance.get(tranche_key) or {}
        is_claimed = bool(claimed_status.get(tranche_key, False))
        tranche_value = tranche_total(tranche_balance_data)
   
        claimed_badge = ft.Container(
            content=ft.Text(
                "Claimed" if is_claimed else "Not Claimed",
                size=10,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.W_500
            ),
            bgcolor=ft.Colors.GREEN if is_claimed else CDC_RED,
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=10, vertical=3)
        )

        denom_breakdown = ft.Row(
            [
                ft.Text(f"$2 x{tranche_balance_data.get('2', 0)}", size=12, color=GREY_TEXT),
                ft.Text("|", size=12, color=GREY_BORDER),
                ft.Text(f"$5 x{tranche_balance_data.get('5', 0)}", size=12, color=GREY_TEXT),
                ft.Text("|", size=12, color=GREY_BORDER),
                ft.Text(f"$10 x{tranche_balance_data.get('10', 0)}", size=12, color=GREY_TEXT),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8
        )

        balance_card_controls = [
            ft.Row(
                [
                    ft.Text("Total Balance", size=13, color=GREY_TEXT),
                    claimed_badge
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            ft.Text(f"${tranche_value}", size=36, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
            denom_breakdown
        ]

        # claim vouchers if not
        if not is_claimed:
            balance_card_controls.append(ft.Container(height=8))
            balance_card_controls.append(
                ft.ElevatedButton(
                    "Claim Vouchers",
                    data=tranche_key,
                    on_click=on_claim,
                    width=300,
                    style=ft.ButtonStyle(bgcolor=CDC_RED, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=8)),
                )
            )

        balance_card = ft.Container(
            content=ft.Column(
                balance_card_controls,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6
            ),
            padding=18,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, GREY_BORDER)
        )

        # tap to use header
        tap_to_use_header = ft.Row(
            [
                ft.Text("TAP TO USE", size=14, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
                ft.TextButton("Clear Selection", on_click=on_clear_selection)
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        # Selected summary bar
        summary_card = ft.Container(
            content=ft.Row(
                [
                    ft.Text("Selected Total", size=13, color=GREY_TEXT),
                    selected_summary
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=ft.Padding.symmetric(horizontal=18, vertical=12),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            border=ft.Border.all(1, GREY_BORDER)
        )

        # Info hint
        info_hint = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.INFO_OUTLINE, size=16, color="#E65100"),
                    ft.Text(
                        "Paste this into the Merchant app.\nPress Refresh after merchant confirms.",
                        size=11,
                        color="#E65100"
                    )
                ],
                spacing=8
            ),
            padding=12,
            border_radius=8,
            bgcolor="#FFF3E0"
        )

        # Redeem section
        redeem_section = ft.Column(
            [
                ft.Container(height=12),
                ft.Container(content=tranche_tabs_row, padding=ft.Padding.symmetric(horizontal=4)),
                ft.Container(height=12),
                balance_card,
                ft.Container(height=16),
                tap_to_use_header,
                voucher_panel,
                ft.Container(height=8),
                summary_card,
                ft.Container(height=12),
                ft.Button(
                    "Generate & Copy Request",
                    icon=ft.Icons.CONTENT_COPY,
                    on_click=on_generate_and_copy,
                    width=350,
                    height=48,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=CDC_RED,
                        shape=ft.RoundedRectangleBorder(radius=8)
                    )
                ),
                ft.Container(height=10),
                payment_request_container,
                ft.Container(height=10),
                info_hint,
                ft.Container(height=20)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        )

        dashboard_page = ft.Column(
            [
                header_bar,
                ft.Container(
                    content=ft.Column(
                        [
                            message_bar,
                            ft.Container(content=redeem_section, padding=ft.Padding.symmetric(horizontal=15), expand=True),
                        ],
                        scroll=ft.ScrollMode.AUTO,
                        spacing=0
                    ),
                    expand=True
                ),
            ],
            spacing=0,
            expand=True
        )

        render_vouchers()
        return ft.Container(content=dashboard_page, padding=0, expand=True)

    # View 3: Analytics

    def view_analytics():
        content_area = ft.Column(spacing=12, expand=True)

        def on_back(e):
            navigate("household_dashboard" if session.get("household_id") else "household_start")

        def summary_card(title, value, color=ft.Colors.BLUE):
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Text(title, size=11, color=ft.Colors.GREY_700),
                        ft.Text(str(value), size=20, weight=ft.FontWeight.BOLD, color=color),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                ),
                padding=12,
                border=ft.border.all(1, ft.Colors.GREY_300),
                border_radius=12,
                bgcolor=ft.Colors.WHITE,
                expand=True,
            )

        def section_title(text):
            return ft.Text(text, size=15, weight=ft.FontWeight.BOLD)

        def load_data():
            content_area.controls.clear()

            content_area.controls.append(
                ft.Column(
                    [
                        ft.ProgressRing(width=32, height=32),
                        ft.Text("Loading analytics...", size=12, color=ft.Colors.GREY_600),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10,
                )
            )
            page.update()

            status, data = _call_api("GET", "/api/dashboard_data")

            content_area.controls.clear()

            if status != 200 or not data.get("ok"):
                content_area.controls.append(
                    ft.Text(data.get("message", "Failed to load analytics."), color=ft.Colors.RED)
                )
                page.update()
                return

            total_hh = data.get("total_households", 0)
            claimed_may = data.get("claimed_may2025", 0)
            claimed_jan = data.get("claimed_jan2026", 0)
            total_merchants = data.get("total_merchants", 0)
            total_tx = data.get("total_transactions", 0)
            total_value = data.get("total_redeemed_value", 0)
            denom = data.get("denomination_breakdown", {})
            merchant_summary = data.get("merchant_summary", [])
            hourly = data.get("hourly_volume", [])

            content_area.controls.append(section_title("Overview"))
            content_area.controls.append(
                ft.Row(
                    [
                        summary_card("Households", total_hh, ft.Colors.BLUE),
                        summary_card("Merchants", total_merchants, ft.Colors.GREEN),
                        summary_card("Transactions", total_tx, ft.Colors.ORANGE),
                    ],
                    spacing=8,
                )
            )
            content_area.controls.append(
                ft.Row(
                    [summary_card("Total Redeemed", f"${total_value:,.2f}", ft.Colors.RED)],
                    spacing=8,
                )
            )

            content_area.controls.append(ft.Divider())
            content_area.controls.append(section_title("Voucher Claim Rate"))

            may_pct = (claimed_may / total_hh * 100) if total_hh > 0 else 0
            jan_pct = (claimed_jan / total_hh * 100) if total_hh > 0 else 0

            content_area.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text("May 2025:", size=12, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{claimed_may}/{total_hh} ({may_pct:.0f}%)", size=12),
                        ]),
                        ft.ProgressBar(value=may_pct / 100, color=ft.Colors.BLUE, bgcolor=ft.Colors.BLUE_100),
                        ft.Row([
                            ft.Text("Jan 2026:", size=12, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{claimed_jan}/{total_hh} ({jan_pct:.0f}%)", size=12),
                        ]),
                        ft.ProgressBar(value=jan_pct / 100, color=ft.Colors.GREEN, bgcolor=ft.Colors.GREEN_100),
                    ], spacing=6),
                    padding=12,
                    border=ft.Border.all(1, ft.Colors.GREY_300),
                    border_radius=12,
                    bgcolor=ft.Colors.WHITE,
                )
            )

            content_area.controls.append(ft.Divider())
            content_area.controls.append(section_title("Denomination Usage"))

            denom_total = sum(denom.values()) if denom else 1
            denom_colors = {"$2.00": ft.Colors.BLUE, "$5.00": ft.Colors.ORANGE, "$10.00": ft.Colors.RED}
            denom_items = []
            for d_label in ["$2.00", "$5.00", "$10.00"]:
                count = denom.get(d_label, 0)
                pct = (count / denom_total * 100) if denom_total > 0 else 0
                color = denom_colors.get(d_label, ft.Colors.GREY)
                denom_items.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(d_label, size=13, weight=ft.FontWeight.BOLD, color=color),
                            ft.Text(f"{count} vouchers", size=11),
                            ft.Text(f"{pct:.1f}%", size=10, color=ft.Colors.GREY_600),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                        padding=10,
                        border=ft.Border.all(1, ft.Colors.GREY_300),
                        border_radius=12,
                        bgcolor=ft.Colors.WHITE,
                        expand=True,
                    )
                )
            content_area.controls.append(ft.Row(denom_items, spacing=8))

            content_area.controls.append(ft.Divider())
            content_area.controls.append(section_title("Redemptions by Merchant"))

            if merchant_summary:
                merchant_rows = [
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(m["merchant_name"], size=11)),
                            ft.DataCell(ft.Text(str(m["voucher_count"]), size=11)),
                            ft.DataCell(ft.Text(f"${m['total_value']:,.2f}", size=11)),
                        ]
                    )
                    for m in merchant_summary[:10]
                ]
                content_area.controls.append(
                    ft.Container(
                        content=ft.DataTable(
                            columns=[
                                ft.DataColumn(ft.Text("Name", size=10, weight=ft.FontWeight.BOLD)),
                                ft.DataColumn(ft.Text("Qty", size=10, weight=ft.FontWeight.BOLD), numeric=True),
                                ft.DataColumn(ft.Text("Value", size=10, weight=ft.FontWeight.BOLD), numeric=True),
                            ],
                            rows=merchant_rows,
                            column_spacing=12,
                        ),
                        border=ft.Border.all(1, ft.Colors.GREY_300),
                        border_radius=12,
                        bgcolor=ft.Colors.WHITE,
                        padding=6,
                    )
                )
            else:
                content_area.controls.append(ft.Text("No redemption data yet.", size=12, color=ft.Colors.GREY_600))

            content_area.controls.append(ft.Divider())
            content_area.controls.append(section_title("Hourly Redemption Volume"))

            if hourly:
                max_count = max(h["count"] for h in hourly) or 1
                bar_groups = []
                bar_labels = []
                for i, h in enumerate(hourly):
                    bar_groups.append(
                        BarChartGroup(
                            x=i,
                            rods=[
                                BarChartRod(
                                    from_y=0,
                                    to_y=h["count"],
                                    width=8,
                                    color=NAVY_DARK,
                                    border_radius=3,
                                )
                            ],
                        )
                    )
                    short_label = h["hour"][-2:] + "h" if len(h["hour"]) >= 2 else h["hour"]
                    bar_labels.append(
                        ChartAxisLabel(value=i, label=ft.Text(short_label, size=8))
                    )

                chart = BarChart(
                    groups=bar_groups,
                    max_y=max_count * 1.2,
                    min_y=0,
                    bottom_axis=ChartAxis(labels=bar_labels, label_size=24),
                    left_axis=ChartAxis(label_size=28),
                    height=200,
                    expand=True,
                    interactive=True,
                )
                content_area.controls.append(
                    ft.Container(
                        content=chart,
                        border=ft.Border.all(1, ft.Colors.GREY_300),
                        border_radius=12,
                        bgcolor=ft.Colors.WHITE,
                        padding=10,
                    )
                )
            else:
                content_area.controls.append(ft.Text("No hourly data yet.", size=12, color=ft.Colors.GREY_600))

            page.update()

        def on_refresh(e):
            load_data()

        header_bar = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=on_back, icon_color=ft.Colors.WHITE),
                    ft.Text("Analytics", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    ft.IconButton(icon=ft.Icons.REFRESH, on_click=on_refresh, icon_color=ft.Colors.WHITE),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            bgcolor=NAVY_DARK,
            padding=12,
        )

        message_bar = ft.Container(
            padding=ft.padding.only(left=15, right=15, top=6),
            content=message_text,
        )

        analytics_page = ft.Column(
            [
                header_bar,
                ft.Container(
                    content=ft.Column(
                        [
                            message_bar,
                            ft.Container(
                                content=content_area,
                                padding=15,
                                expand=True,
                            ),
                        ],
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

        load_data()
        return ft.Container(content=analytics_page, padding=0, expand=True)

    def render():
        page.controls.clear()
        view_name = session.get("view")

        if view_name == "household_start":
            page.add(view_household_start())
        elif view_name == "household_dashboard":
            page.add(view_household_dashboard())
        elif view_name == "analytics":
            page.add(view_analytics())
        else:
            page.add(view_household_start())

        if session.get("flash_msg"):
            message_text.value = session["flash_msg"]
            message_text.color = ft.Colors.GREEN if session.get("flash_ok") else ft.Colors.RED
            session["flash_msg"] = ""

        page.update()

    render()


if __name__ == "__main__":
    ft.run(main)
