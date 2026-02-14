import requests
import datetime
import math
import flet as ft
from flet_charts import BarChart, BarChartGroup, BarChartRod, ChartAxis, ChartAxisLabel

base_url = "http://127.0.0.1:5000"

#  Color tweaks
BAR_COLOR = ft.Colors.BLUE
TOOLTIP_BG = ft.Colors.WHITE
TOOLTIP_TEXT = ft.Colors.BLACK


def _call_api(path: str):
    try:
        r = requests.get(base_url + path)
        return r.status_code, r.json()
    except Exception as e:
        return 0, {"ok": False, "message": str(e)}


def main(page: ft.Page):
    page.title = "CDC Analytics Dashboard"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.window.width = 520
    page.window.height = 900
    page.scroll = ft.ScrollMode.AUTO

    message_text = ft.Text("", size=12, color=ft.Colors.RED)

    def set_message(msg: str, ok: bool = False):
        message_text.value = msg
        message_text.color = ft.Colors.GREEN if ok else ft.Colors.RED
        page.update()

    # last 7 days
    def last_7_days_iso():
        today = datetime.date.today()
        days = []
        i = 0
        while i < 7:
            days.append((today - datetime.timedelta(days=i)).strftime("%Y-%m-%d"))
            i += 1
        return days

    iso_days = last_7_days_iso()
    default_iso = iso_days[0]

    # Filter 1: End date
    date_filter = ft.Dropdown(
        width=190,
        label="End Date (YYYY-MM-DD)",
        value=default_iso,
        options=[ft.dropdown.Option(key=d, text=d) for d in iso_days],
        dense=True,
    )

    # Filter 2: Periods ( allow 1, 3, or 7 days)
    period_filter = ft.Dropdown(
        width=140,
        label="Period",
        value="1",
        options=[
            ft.dropdown.Option(key="1", text="1 days"),
            ft.dropdown.Option(key="3", text="3 days"),
            ft.dropdown.Option(key="7", text="7 days"),
        ],
        dense=True
    )

    header = ft.Container(
        content=ft.Column(
            [
                ft.Text("CDC Voucher System", size=12, color=ft.Colors.WHITE70),
                ft.Text("Analytics Dashboard", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text("Stakeholder: Government / CDC", size=11, color=ft.Colors.WHITE70),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=2,
        ),
        bgcolor=ft.Colors.INDIGO,
        padding=18,
        alignment=ft.Alignment.CENTER
    )

    content_area = ft.Column(spacing=12, expand=True)

    def summary_card(title, value, color=ft.Colors.BLUE):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(title, size=11, color=ft.Colors.GREY_700),
                    ft.Text(str(value), size=22, weight=ft.FontWeight.BOLD, color=color),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            padding=14,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
            expand=True
        )

    def section_title(text):
        return ft.Text(text, size=16, weight=ft.FontWeight.BOLD)

    
   
    def build_hourly_chart(bar_groups, bar_labels, max_y, left_labels):
        base_kwargs = dict(
            groups=bar_groups,
            max_y=max_y,
            min_y=0,
            bottom_axis=ChartAxis(labels=bar_labels, label_size=44),
            left_axis=ChartAxis(labels=left_labels, label_size=44),
            height=300,
            expand=True,
            interactive=True,
        )

        return BarChart(**base_kwargs)
        
    # dashboard note
    how_filters_work = ft.Container(
        bgcolor=ft.Colors.INDIGO_50,
        border=ft.Border.all(1, ft.Colors.INDIGO_100),
        border_radius=10,
        padding=12,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.INFO_OUTLINE, size=18, color=ft.Colors.INDIGO),
                        ft.Text("How filters work", weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO),
                    ],
                    spacing=8,
                ),
                ft.Text("• Period affects Totals + Merchant Rank only.", size=12, color=ft.Colors.INDIGO_900),
                ft.Text(
                    "• Selected End Date is treated as the END date (inclusive) of the rolling window.",
                    size=12,
                    color=ft.Colors.INDIGO_900,
                ),
                ft.Text("• Hourly Redemption chart is ALWAYS single-day for the selected End Date.", size=12, color=ft.Colors.INDIGO_900),
            ],
            spacing=6
        ),
    )

    window_summary_text = ft.Text("", size=12, color=ft.Colors.GREY_700)

    def load_dashboard(e=None):
        content_area.controls.clear()
        set_message("Loading...", ok=True)

        selected_date = (date_filter.value or "").strip()
        if not selected_date:
            selected_date = default_iso
            date_filter.value = selected_date

        window_days_str = (period_filter.value or "7").strip()
        try:
            window_days = int(window_days_str)
        except ValueError:
            window_days = 7

        if window_days not in (1, 3, 7):
            window_days = 7
            period_filter.value = "7"

        # call dashboard api with 2 query parameters
        path = f"/api/dashboard_data?date={selected_date}&window={window_days}"
        status, data = _call_api(path)

        if status != 200 or not data.get("ok"):
            set_message(data.get("message", "Failed to load dashboard data"))
            return

        # all-time metrics
        total_hh = data.get("total_households", 0)
        total_merchants = data.get("total_merchants", 0)
        claimed_may = data.get("claimed_may2025", 0)
        claimed_jan = data.get("claimed_jan2026", 0)

        # window metrics
        total_tx = data.get("total_transactions", 0)
        total_value = float(data.get("total_redeemed_value", 0.0) or 0.0)
        merchant_summary = data.get("merchant_summary", []) or []

        # single day metrics
        hourly = data.get("hourly_volume", []) or []

        end_date_from_api = str(data.get("end_date", selected_date))
        window_days_from_api = int(data.get("window_days", window_days))

        window_summary_text.value = (
            f"Window metrics: last {window_days_from_api} days, ending on {end_date_from_api} (inclusive). "
            f"Hourly chart: {end_date_from_api} only."
        )

        # All-time Metrics card
        all_time_header = section_title("All-time Metrics")
        all_time_cards = ft.Row(
            [
                summary_card("Households", total_hh, ft.Colors.BLUE),
                summary_card("Merchants", total_merchants, ft.Colors.GREEN),
            ],
            spacing=8,
        )

        may_pct = (claimed_may / total_hh * 100) if total_hh > 0 else 0
        jan_pct = (claimed_jan / total_hh * 100) if total_hh > 0 else 0

        all_time_claim = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Voucher Claim Rate (All-time)", size=14, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        [
                            ft.Text("May 2025:", size=13, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{claimed_may} / {total_hh} households ({may_pct:.0f}%)", size=13),
                        ]
                    ),
                    ft.ProgressBar(value=may_pct / 100, color=ft.Colors.BLUE, bgcolor=ft.Colors.BLUE_100),
                    ft.Row(
                        [
                            ft.Text("Jan 2026:", size=13, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{claimed_jan} / {total_hh} households ({jan_pct:.0f}%)", size=13),
                        ]
                    ),
                    ft.ProgressBar(value=jan_pct / 100, color=ft.Colors.GREEN, bgcolor=ft.Colors.GREEN_100),
                ],
                spacing=8,
            ),
            padding=12,
            border=ft.Border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            bgcolor=ft.Colors.WHITE
        )

        all_time_block = ft.Container(
            content=ft.Column([all_time_header, all_time_cards, all_time_claim], spacing=10),
            padding=12,
            border=ft.Border.all(1, ft.Colors.GREY_200),
            border_radius=12,
            bgcolor=ft.Colors.WHITE
        )

        # Window Metrics card
        window_header = section_title("Window Metrics")
        window_cards = ft.Row(
            [
                summary_card("Transactions", total_tx, ft.Colors.ORANGE),
                summary_card("Total Redeemed", f"${total_value:,.2f}", ft.Colors.RED),
            ],
            spacing=8
        )

        merchant_table_title = ft.Text("Merchant Rank", size=14, weight=ft.FontWeight.BOLD)

        if merchant_summary:
            rows = []
            i = 0
            while i < len(merchant_summary) and i < 10:
                m = merchant_summary[i]
                rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(m.get("merchant_id", ""), size=12)),
                            ft.DataCell(ft.Text(m.get("merchant_name", ""), size=12)),
                            ft.DataCell(ft.Text(str(m.get("voucher_count", 0)), size=12)),
                            ft.DataCell(ft.Text(f"${float(m.get('total_value', 0.0)):,.2f}", size=12))
                        ]
                    )
                )
                i += 1

            table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("ID", size=11, weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Name", size=11, weight=ft.FontWeight.BOLD)),
                    ft.DataColumn(ft.Text("Vouchers", size=11, weight=ft.FontWeight.BOLD), numeric=True),
                    ft.DataColumn(ft.Text("Value", size=11, weight=ft.FontWeight.BOLD), numeric=True),
                ],
                rows=rows,
                column_spacing=16
            )

            merchant_table_container = ft.Container(
                content=table,
                border=ft.Border.all(1, ft.Colors.GREY_300),
                border_radius=10,
                bgcolor=ft.Colors.WHITE,
                padding=8
            )
        else:
            merchant_table_container = ft.Text("No redemption data in this window.", size=12, color=ft.Colors.GREY_600)

        window_block = ft.Container(
            content=ft.Column([window_header, window_cards, merchant_table_title, merchant_table_container], spacing=10),
            padding=12,
            border=ft.Border.all(1, ft.Colors.GREY_200),
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
        )

        # =========================
        # Single-day chart (Y-axis = Amount)
        # =========================
        hour_count_map = {h: 0 for h in range(24)}
        hour_value_map = {h: 0.0 for h in range(24)}

        for item in hourly:
            hour_key = str(item.get("hour") or "").strip()

            # count
            try:
                cnt = int(item.get("count", 0) or 0)
            except Exception:
                cnt = 0

            # value
            try:
                val = float(item.get("value", 0.0) or 0.0)
            except Exception:
                val = 0.0

            hh = None
            if hour_key.isdecimal():
                hh = int(hour_key)
            else:
                tail = hour_key[-2:] if len(hour_key) >= 2 else ""
                if tail.isdecimal():
                    hh = int(tail)

            if hh is not None and 0 <= hh <= 23:
                hour_count_map[hh] += cnt
                hour_value_map[hh] += val

        # single-day total value
        single_day_total_value = 0.0
        h = 0
        while h < 24:
            single_day_total_value += float(hour_value_map[h])
            h += 1

        
        max_value = 0.0
        for v in hour_value_map.values():
            if float(v) > max_value:
                max_value = float(v)

        if max_value <= 0:
            step = 5.0
            nice_max = 10.0
        elif max_value <= 20:
            step = 5.0
            nice_max = math.ceil(max_value / step) * step
        elif max_value <= 100:
            step = 10.0
            nice_max = math.ceil(max_value / step) * step
        else:
            step = 50.0
            nice_max = math.ceil(max_value / step) * step

        y_labels = []
        vv = 0.0
        while vv <= nice_max + 1e-9:
            y_labels.append(ChartAxisLabel(value=vv, label=ft.Text(f"${vv:,.0f}", size=10)))
            vv += step

        # IMPORTANT: bar height uses AMOUNT (val_local), NOT count
        def make_hourly_rod(hour_idx: int):
            cnt_local = int(hour_count_map[hour_idx])
            val_local = float(hour_value_map[hour_idx])

            tip = f"{hour_idx:02d}h\nCount: {cnt_local}\nValue: ${val_local:,.2f}"

            try:
                return BarChartRod(
                    from_y=0,
                    to_y=float(val_local),  # <-- AMOUNT on Y-axis
                    width=12,
                    color=BAR_COLOR,
                    border_radius=3,
                    tooltip=tip,
                )
            except TypeError:
                pass

            try:
                return BarChartRod(
                    from_y=0,
                    to_y=float(val_local),  # <-- AMOUNT on Y-axis
                    width=12,
                    color=BAR_COLOR,
                    border_radius=3,
                    tooltip_text=tip,
                )
            except TypeError:
                pass

            return BarChartRod(
                from_y=0,
                to_y=float(val_local),  # <-- AMOUNT on Y-axis
                width=12,
                color=BAR_COLOR,
                border_radius=3,
            )

        bar_groups = []
        i = 0
        while i < 24:
            bar_groups.append(BarChartGroup(x=i, rods=[make_hourly_rod(i)]))
            i += 1

        LABEL_STEP = 2
        bar_labels = []
        i = 0
        while i < 24:
            label_txt = f"{i}h" if i % LABEL_STEP == 0 else ""
            bar_labels.append(ChartAxisLabel(value=i, label=ft.Text(label_txt, size=10)))
            i += 1

        hourly_chart = build_hourly_chart(
            bar_groups=bar_groups,
            bar_labels=bar_labels,
            max_y=float(nice_max),
            left_labels=y_labels,
        )

        hourly_block = ft.Container(
            content=ft.Column(
                [
                    section_title("Hourly Redemption Amount"),
                    ft.Text(f"End Date: {end_date_from_api}", size=12, color=ft.Colors.GREY_700),
                    ft.Text(f"Total Redeemed (Single-day): ${single_day_total_value:,.2f}", size=12, color=ft.Colors.GREY_700),
                    ft.Container(
                        content=hourly_chart,
                        border=ft.Border.all(1, ft.Colors.GREY_300),
                        border_radius=10,
                        bgcolor=ft.Colors.WHITE,
                        padding=ft.Padding.only(left=18, right=12, top=100, bottom=20),
                    ),
                ],
                spacing=8,
            ),
            padding=12,
            border=ft.Border.all(1, ft.Colors.GREY_200),
            border_radius=12,
            bgcolor=ft.Colors.WHITE
        )

        # Compose page
        content_area.controls.extend(
            [
                how_filters_work,
                window_summary_text,
                all_time_block,
                window_block,
                hourly_block,
            ]
        )

        page.update()
        set_message("Dashboard loaded.", ok=True)

    apply_btn = ft.Button(
        "Apply",
        icon=ft.Icons.FILTER_ALT,
        on_click=load_dashboard,
        style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE),
    )

    refresh_btn = ft.Button(
        "Refresh",
        icon=ft.Icons.REFRESH,
        on_click=load_dashboard,
        style=ft.ButtonStyle(bgcolor=ft.Colors.INDIGO, color=ft.Colors.WHITE),
    )

    message_bar = ft.Container(
        padding=ft.Padding.only(left=15, right=15, top=6),
        content=message_text,
    )

    page.add(
        ft.Column(
            [
                header,
                message_bar,
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [date_filter, period_filter, apply_btn, refresh_btn],
                                alignment=ft.MainAxisAlignment.END,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            content_area,
                        ],
                        spacing=10,
                    ),
                    padding=15,
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )
    )

    load_dashboard()


if __name__ == "__main__":
    ft.run(main)
