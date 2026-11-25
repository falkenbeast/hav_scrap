"""
Workbook Formatter Subsystem.
Implements OpenPyXL styles, formula injection sanitization, responsive column widths,
and typography matching the placement intelligence design system.
"""
from datetime import datetime, date
from typing import Any, List, Optional, Dict
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet


# ==============================================================================
# 1. Formula Injection Protection (CWE-1236)
# ==============================================================================

def escape_formula_value(val: Any) -> Any:
    """
    Sanitizes string values to prevent Excel Formula Injection (CSV/Formula Injection).
    If a string begins with dangerous prefix characters ('=', '+', '-', '@'),
    it is prepended with a single apostrophe (') to guarantee safe plain-text rendering.
    """
    if val is None:
        return ""
    if isinstance(val, (int, float, bool, datetime, date)):
        return val
    
    val_str = str(val)
    # Check leading non-whitespace character
    stripped = val_str.lstrip()
    if stripped and stripped[0] in ("=", "+", "-", "@"):
        return "'" + val_str
    return val_str


# ==============================================================================
# 2. Design System Colors & Fonts
# ==============================================================================

# Stark Industries / Placement Intelligence Theme
COLOR_PRIMARY_NAVY = "1B2635"
COLOR_SECONDARY_DARK = "101620"
COLOR_ACCENT_ORANGE = "FF6A00"
COLOR_ACCENT_CYAN = "00D4FF"
COLOR_ZEBRA_EVEN = "F8FAFC"
COLOR_ZEBRA_ODD = "FFFFFF"
COLOR_BORDER = "CBD5E1"
COLOR_LIGHT_BORDER = "E2E8F0"

HEADER_FILL_PRIMARY = PatternFill(
    start_color=COLOR_PRIMARY_NAVY,
    end_color=COLOR_PRIMARY_NAVY,
    fill_type="solid"
)

HEADER_FILL_SECONDARY = PatternFill(
    start_color=COLOR_SECONDARY_DARK,
    end_color=COLOR_SECONDARY_DARK,
    fill_type="solid"
)

ZEBRA_FILL_EVEN = PatternFill(
    start_color=COLOR_ZEBRA_EVEN,
    end_color=COLOR_ZEBRA_EVEN,
    fill_type="solid"
)

ZEBRA_FILL_ODD = PatternFill(
    start_color=COLOR_ZEBRA_ODD,
    end_color=COLOR_ZEBRA_ODD,
    fill_type="solid"
)

HEADER_FONT = Font(
    name="Segoe UI",
    size=10.5,
    bold=True,
    color="FFFFFF"
)

DATA_FONT = Font(
    name="Segoe UI",
    size=9.5,
    bold=False,
    color="1E293B"
)

DATA_FONT_MUTED = Font(
    name="Segoe UI",
    size=9.0,
    italic=True,
    color="64748B"
)

REPORT_TITLE_FONT = Font(
    name="Segoe UI",
    size=14,
    bold=True,
    color=COLOR_PRIMARY_NAVY
)

REPORT_SUBTITLE_FONT = Font(
    name="Segoe UI",
    size=9.5,
    italic=True,
    color="64748B"
)

SECTION_HEADER_FONT = Font(
    name="Segoe UI",
    size=11,
    bold=True,
    color="FFFFFF"
)

SECTION_FILL = PatternFill(
    start_color="334155",
    end_color="334155",
    fill_type="solid"
)

# Borders
BORDER_THIN = Border(
    left=Side(style="thin", color=COLOR_LIGHT_BORDER),
    right=Side(style="thin", color=COLOR_LIGHT_BORDER),
    top=Side(style="thin", color=COLOR_LIGHT_BORDER),
    bottom=Side(style="thin", color=COLOR_LIGHT_BORDER)
)

HEADER_BORDER = Border(
    left=Side(style="thin", color="334155"),
    right=Side(style="thin", color="334155"),
    top=Side(style="medium", color=COLOR_PRIMARY_NAVY),
    bottom=Side(style="medium", color=COLOR_ACCENT_ORANGE)
)

# Alignments
ALIGN_LEFT = Alignment(horizontal="left", vertical="center", wrap_text=False)
ALIGN_CENTER = Alignment(horizontal="center", vertical="center")
ALIGN_RIGHT = Alignment(horizontal="right", vertical="center")
ALIGN_WRAP = Alignment(horizontal="left", vertical="center", wrap_text=True)

# Standard Number Formats
FMT_LPA = '0.00 "LPA"'
FMT_CURRENCY_INR = '₹#,##0'
FMT_CGPA = '0.00'
FMT_DATE = 'YYYY-MM-DD'
FMT_DATETIME = 'YYYY-MM-DD HH:MM'
FMT_INTEGER = '#,##0'
FMT_PERCENT = '0.0%'


# ==============================================================================
# 3. Sheet Layout & Styling Utilities
# ==============================================================================

def apply_table_header(
    ws: Worksheet,
    row_idx: int,
    headers: List[str],
    fill: Optional[PatternFill] = None,
    row_height: float = 26.0
) -> None:
    """
    Renders styled table header cells with custom background, bold white font,
    and bottom accent border.
    """
    ws.row_dimensions[row_idx].height = row_height
    header_fill = fill or HEADER_FILL_PRIMARY

    for col_idx, header_text in enumerate(headers, start=1):
        cell = ws.cell(row=row_idx, column=col_idx, value=header_text)
        cell.font = HEADER_FONT
        cell.fill = header_fill
        cell.border = HEADER_BORDER
        cell.alignment = ALIGN_CENTER if "ID" in header_text or "Date" in header_text or "Status" in header_text else ALIGN_LEFT


def format_data_row(
    ws: Worksheet,
    row_idx: int,
    values: List[Any],
    is_even: bool = False,
    alignments: Optional[List[Alignment]] = None,
    number_formats: Optional[List[Optional[str]]] = None,
    row_height: float = 20.0
) -> None:
    """
    Writes data row with alternating zebra striping, thin borders,
    and tailored column alignments / number formatting.
    """
    ws.row_dimensions[row_idx].height = row_height
    row_fill = ZEBRA_FILL_EVEN if is_even else ZEBRA_FILL_ODD

    for col_idx, val in enumerate(values, start=1):
        safe_val = escape_formula_value(val)
        cell = ws.cell(row=row_idx, column=col_idx, value=safe_val)
        cell.font = DATA_FONT
        cell.fill = row_fill
        cell.border = BORDER_THIN

        # Alignment
        if alignments and col_idx - 1 < len(alignments) and alignments[col_idx - 1] is not None:
            cell.alignment = alignments[col_idx - 1]
        else:
            if isinstance(val, (int, float)):
                cell.alignment = ALIGN_RIGHT
            elif isinstance(val, (datetime, date)):
                cell.alignment = ALIGN_CENTER
            else:
                cell.alignment = ALIGN_LEFT

        # Number formatting
        if number_formats and col_idx - 1 < len(number_formats) and number_formats[col_idx - 1]:
            cell.number_format = number_formats[col_idx - 1]
        elif isinstance(val, (datetime, date)):
            cell.number_format = FMT_DATE


def auto_fit_column_widths(
    ws: Worksheet,
    min_width: int = 12,
    max_width: int = 55,
    padding: int = 3
) -> None:
    """
    Calculates auto-fit column widths based on maximum cell content length.
    Constrained within min_width and max_width bounds to ensure clean readability.
    """
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            if cell.value is not None:
                # Handle multi-line strings
                lines = str(cell.value).split("\n")
                line_max = max(len(l) for l in lines) if lines else 0
                if line_max > max_len:
                    max_len = line_max

        calculated_width = max(min_width, min(max_len + padding, max_width))
        ws.column_dimensions[col_letter].width = calculated_width


def setup_sheet_view(
    ws: Worksheet,
    freeze_pane: str = "A2",
    enable_filter: bool = True
) -> None:
    """
    Configures sheet views: freezes header row, enables auto-filtering,
    and turns on visible grid lines.
    """
    ws.freeze_panes = freeze_pane
    if enable_filter and ws.max_row > 1 and ws.max_column > 0:
        ws.auto_filter.ref = ws.dimensions

    if ws.views.sheetView:
        ws.views.sheetView[0].showGridLines = True

