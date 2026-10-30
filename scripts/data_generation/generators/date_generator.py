"""
Northstar Retail Group — Enterprise Retail Analytics Platform
Stage 5.3.2: Date Dimension Generator (gold.dim_date)

Generates 2,556 deterministic calendar records spanning 2021-01-01 through 2027-12-31.
Includes calendar hierarchies, Indian fiscal calendar (April-March), Indian national holidays,
and major retail festival seasons with days relative to peak.
"""

from datetime import date, timedelta
from typing import List, Dict, Any, Optional

# Indian Fiscal Year mapping:
# In India, Fiscal Year starts April 1.
# Q1: Apr-Jun, Q2: Jul-Sep, Q3: Oct-Dec, Q4: Jan-Mar.
# If month >= 4, FY = year + 1 (e.g. Oct 2026 is FY 2027).

# Indian National Gazetted Holidays (Fixed dates)
FIXED_NATIONAL_HOLIDAYS = {
    (1, 26): "Republic Day",
    (8, 15): "Independence Day",
    (10, 2): "Gandhi Jayanti",
}

# Other major recognized public holidays (Fixed dates)
FIXED_PUBLIC_HOLIDAYS = {
    (1, 1): "New Year's Day",
    (5, 1): "May Day / International Labour Day",
    (12, 25): "Christmas Day",
}

# Major Movable Indian Festivals Peak Dates (2021 - 2027)
# Source: Standard Indian Retail Calendar benchmarks
FESTIVAL_PEAKS = {
    # Diwali (Deepavali Lakshmi Puja) - Prime Retail Spike
    2021: [
        (date(2021, 1, 14), "SANKRANTI_PONGAL"),
        (date(2021, 4, 13), "UGADI"),
        (date(2021, 5, 14), "EID_UL_FITR"),
        (date(2021, 8, 21), "ONAM"),
        (date(2021, 10, 15), "DUSSEHRA"),
        (date(2021, 11, 4), "DIWALI"),
        (date(2021, 12, 25), "CHRISTMAS_NEW_YEAR"),
    ],
    2022: [
        (date(2022, 1, 14), "SANKRANTI_PONGAL"),
        (date(2022, 4, 2), "UGADI"),
        (date(2022, 5, 3), "EID_UL_FITR"),
        (date(2022, 9, 8), "ONAM"),
        (date(2022, 10, 5), "DUSSEHRA"),
        (date(2022, 10, 24), "DIWALI"),
        (date(2022, 12, 25), "CHRISTMAS_NEW_YEAR"),
    ],
    2023: [
        (date(2023, 1, 15), "SANKRANTI_PONGAL"),
        (date(2023, 3, 22), "UGADI"),
        (date(2023, 4, 22), "EID_UL_FITR"),
        (date(2023, 8, 29), "ONAM"),
        (date(2023, 10, 24), "DUSSEHRA"),
        (date(2023, 11, 12), "DIWALI"),
        (date(2023, 12, 25), "CHRISTMAS_NEW_YEAR"),
    ],
    2024: [
        (date(2024, 1, 15), "SANKRANTI_PONGAL"),
        (date(2024, 4, 9), "UGADI"),
        (date(2024, 4, 11), "EID_UL_FITR"),
        (date(2024, 9, 15), "ONAM"),
        (date(2024, 10, 12), "DUSSEHRA"),
        (date(2024, 11, 1), "DIWALI"),
        (date(2024, 12, 25), "CHRISTMAS_NEW_YEAR"),
    ],
    2025: [
        (date(2025, 1, 14), "SANKRANTI_PONGAL"),
        (date(2025, 3, 30), "UGADI"),
        (date(2025, 3, 31), "EID_UL_FITR"),
        (date(2025, 9, 5), "ONAM"),
        (date(2025, 10, 2), "DUSSEHRA"),
        (date(2025, 10, 20), "DIWALI"),
        (date(2025, 12, 25), "CHRISTMAS_NEW_YEAR"),
    ],
    2026: [
        (date(2026, 1, 14), "SANKRANTI_PONGAL"),
        (date(2026, 3, 19), "UGADI"),
        (date(2026, 3, 20), "EID_UL_FITR"),
        (date(2026, 8, 26), "ONAM"),
        (date(2026, 10, 20), "DUSSEHRA"),
        (date(2026, 11, 8), "DIWALI"),
        (date(2026, 12, 25), "CHRISTMAS_NEW_YEAR"),
    ],
    2027: [
        (date(2027, 1, 15), "SANKRANTI_PONGAL"),
        (date(2027, 4, 7), "UGADI"),
        (date(2027, 3, 10), "EID_UL_FITR"),
        (date(2027, 9, 13), "ONAM"),
        (date(2027, 10, 10), "DUSSEHRA"),
        (date(2027, 10, 29), "DIWALI"),
        (date(2027, 12, 25), "CHRISTMAS_NEW_YEAR"),
    ],
}


def _get_festival_info(current_date: date) -> tuple[Optional[str], Optional[int]]:
    """
    Checks if current_date falls within a festival season window (-7 to +2 days from peak).
    Returns (festival_name, days_relative_to_peak).
    """
    year_peaks = FESTIVAL_PEAKS.get(current_date.year, [])
    # Also check adjacent years for boundaries near year-end/start
    if current_date.month == 1:
        year_peaks = FESTIVAL_PEAKS.get(current_date.year - 1, []) + year_peaks
    elif current_date.month == 12:
        year_peaks = year_peaks + FESTIVAL_PEAKS.get(current_date.year + 1, [])

    for peak_date, fest_name in year_peaks:
        delta_days = (current_date - peak_date).days
        # Festival season window: 7 days before peak to 2 days after peak
        if -7 <= delta_days <= 2:
            return fest_name, delta_days

    return None, None


def generate_dim_date_records(
    start_date: date = date(2021, 1, 1),
    end_date: date = date(2027, 12, 31),
) -> List[Dict[str, Any]]:
    """
    Generates all calendar dimension records between start_date and end_date (inclusive).
    Total for 2021-01-01 to 2027-12-31: exactly 2,556 rows.
    """
    records = []
    current = start_date

    while current <= end_date:
        date_key = int(current.strftime("%Y%m%d"))
        year = current.year
        month = current.month
        day = current.day

        # Calendar Quarter: 1-4
        cal_quarter = (month - 1) // 3 + 1
        month_name = current.strftime("%B")
        week_of_year = current.isocalendar()[1]
        day_name = current.strftime("%A")

        # Weekend flag: Saturday (5) or Sunday (6) in weekday()
        is_weekend = current.weekday() in (5, 6)

        # Indian Fiscal Calendar (Apr 1 - Mar 31)
        if month >= 4:
            fiscal_year = year + 1
            fiscal_quarter = (month - 4) // 3 + 1
        else:
            fiscal_year = year
            fiscal_quarter = 4

        # National Holiday Flag (Jan 26, Aug 15, Oct 2)
        is_nat_holiday = (month, day) in FIXED_NATIONAL_HOLIDAYS

        # Festival Season & Peak Delta
        fest_name, delta_fest = _get_festival_info(current)

        records.append({
            "date_key": date_key,
            "calendar_date": current,
            "calendar_year": year,
            "calendar_quarter": cal_quarter,
            "calendar_month_number": month,
            "calendar_month_name": month_name,
            "calendar_week_of_year": week_of_year,
            "day_of_month": day,
            "day_name": day_name,
            "is_weekend_flag": is_weekend,
            "fiscal_year": fiscal_year,
            "fiscal_quarter": fiscal_quarter,
            "is_indian_national_holiday_flag": is_nat_holiday,
            "festival_season_name": fest_name,
            "days_relative_to_festival_peak": delta_fest,
        })

        current += timedelta(days=1)

    return records
