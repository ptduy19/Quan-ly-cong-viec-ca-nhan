"""
Duypt2 Task Manager — Natural Language Parser.

Parses Vietnamese natural language input into structured task data.
Example: "Mail Báo cáo TU trạm mới sau phát sóng vào 15h thứ 3 hàng tuần"
       → {title: "Mail Báo cáo TU trạm mới sau phát sóng", deadline: "next Tuesday 15:00"}
"""
import re
from datetime import datetime, timedelta


# Vietnamese day name mapping (with and without diacritics)
_WEEKDAY_MAP = {
    "thứ 2": 0, "thứ hai": 0, "thu 2": 0, "thu hai": 0, "t2": 0,
    "thứ 3": 1, "thứ ba": 1, "thu 3": 1, "thu ba": 1, "t3": 1,
    "thứ 4": 2, "thứ tư": 2, "thu 4": 2, "thu tu": 2, "t4": 2,
    "thứ 5": 3, "thứ năm": 3, "thu 5": 3, "thu nam": 3, "t5": 3,
    "thứ 6": 4, "thứ sáu": 4, "thu 6": 4, "thu sau": 4, "t6": 4,
    "thứ 7": 5, "thứ bảy": 5, "thu 7": 5, "thu bay": 5, "t7": 5,
    "chủ nhật": 6, "chu nhat": 6, "cn": 6,
}


def parse_quick_input(text: str) -> dict:
    """
    Parse a Vietnamese natural language string into task fields.

    Returns:
        dict with keys: title, deadline_date (YYYY-MM-DD), deadline_time (HH:MM),
        and optionally: priority, category_hint
    """
    result = {
        "title": text.strip(),
        "deadline_date": None,
        "deadline_time": None,
        "priority": "medium",
    }

    lower = text.lower().strip()
    now = datetime.now()

    # ── Extract time (e.g., "15h", "15h30", "14:30", "lúc 9h") ──────────
    time_patterns = [
        r'(?:vào\s+|lúc\s+)?(\d{1,2})\s*[hg:]\s*(\d{1,2})',   # 15h30, 14:30
        r'(?:vào\s+|lúc\s+)?(\d{1,2})\s*[hg](?!\d)',           # 15h (no minutes)
    ]
    extracted_time = None
    time_match_span = None

    for pattern in time_patterns:
        match = re.search(pattern, lower)
        if match:
            groups = match.groups()
            hour = int(groups[0])
            minute = int(groups[1]) if len(groups) > 1 and groups[1] is not None else 0
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                extracted_time = f"{hour:02d}:{minute:02d}"
                time_match_span = match.span()
            break

    if extracted_time:
        result["deadline_time"] = extracted_time

    # ── Extract date ─────────────────────────────────────────────────────

    # Pattern: DD/MM/YYYY or DD-MM-YYYY
    date_match = re.search(r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})', lower)
    if date_match:
        day, month, year = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
        try:
            dt = datetime(year, month, day)
            result["deadline_date"] = dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Pattern: "hôm nay", "ngày mai", "ngày kia"
    if result["deadline_date"] is None:
        if "hôm nay" in lower or "hom nay" in lower:
            result["deadline_date"] = now.strftime("%Y-%m-%d")
        elif "ngày mai" in lower or "ngay mai" in lower:
            result["deadline_date"] = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        elif any(kw in lower for kw in ["ngày kia", "ngày mốt", "ngay kia", "ngay mot"]):
            result["deadline_date"] = (now + timedelta(days=2)).strftime("%Y-%m-%d")

    # Pattern: "thứ 3", "thứ ba", "chủ nhật", etc.
    if result["deadline_date"] is None:
        for day_name, weekday in _WEEKDAY_MAP.items():
            if day_name in lower:
                days_ahead = weekday - now.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                target_date = now + timedelta(days=days_ahead)
                result["deadline_date"] = target_date.strftime("%Y-%m-%d")
                break

    # Pattern: "tuần sau", "tuần tới"
    if result["deadline_date"] is None:
        if "tuần sau" in lower or "tuần tới" in lower:
            result["deadline_date"] = (now + timedelta(days=7)).strftime("%Y-%m-%d")

    # Default: if time found but no date, assume today (or tomorrow if time passed)
    if result["deadline_date"] is None and extracted_time:
        time_obj = datetime.strptime(extracted_time, "%H:%M")
        if time_obj.hour < now.hour or (time_obj.hour == now.hour and time_obj.minute <= now.minute):
            result["deadline_date"] = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            result["deadline_date"] = now.strftime("%Y-%m-%d")

    # Final default: tomorrow
    if result["deadline_date"] is None:
        result["deadline_date"] = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    if result["deadline_time"] is None:
        result["deadline_time"] = "23:59"

    # ── Extract priority hints ───────────────────────────────────────────
    if any(kw in lower for kw in ["gấp", "khẩn", "urgent", "quan trọng", "asap"]):
        result["priority"] = "high"
    elif any(kw in lower for kw in ["khi rảnh", "không gấp", "từ từ"]):
        result["priority"] = "low"

    # ── Clean title (remove time/date fragments) ─────────────────────────
    title = text.strip()
    # Remove matched patterns from title
    patterns_to_remove = [
        r'\s*(?:vào\s+|lúc\s+)?\d{1,2}\s*[hg:]\s*\d{0,2}',
        r'\s*(?:hôm nay|hom nay|ngày mai|ngay mai|ngày kia|ngày mốt|ngay kia|ngay mot)',
        r'\s*(?:tuần sau|tuần tới|tuan sau|tuan toi)',
        r'\s*(?:hàng tuần|hàng ngày|mỗi ngày|mỗi tuần|hang tuan|hang ngay)',
        r'\s*\d{1,2}[/\-]\d{1,2}[/\-]\d{4}',
    ]
    for pattern in _WEEKDAY_MAP:
        patterns_to_remove.append(rf'\s*{re.escape(pattern)}')

    for pattern in patterns_to_remove:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)

    # Remove dangling prepositions
    title = re.sub(r'\s+(vào|lúc|trước|sau)\s*$', '', title, flags=re.IGNORECASE)
    title = re.sub(r'\s+', ' ', title).strip()

    if title:
        result["title"] = title

    return result
