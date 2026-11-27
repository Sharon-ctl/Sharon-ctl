#!/usr/bin/env python3
"""Render a compact chart from the latest public GitHub push events.

Colors and type follow the portfolio site (sharon-ctl.github.io): obsidian
surface, white bars, muted grey labels, mono for numbers.
"""

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
import json


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "push-activity.svg"
API = "https://api.github.com/users/Sharon-ctl/events/public?per_page=100"

SANS = "Geist, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def fetch_pushes():
    request = Request(API, headers={"Accept": "application/vnd.github+json", "User-Agent": "Sharon-profile-activity-chart"})
    with urlopen(request, timeout=20) as response:
        events = json.load(response)
    return [
        datetime.fromisoformat(event["created_at"].replace("Z", "+00:00")).astimezone(timezone.utc)
        for event in events
        if event.get("type") == "PushEvent" and event.get("created_at")
    ]


def bar(x, y, width, height, value, maximum):
    if not value:
        return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="3" fill="#ffffff" fill-opacity="0.07"/>'
    opacity = 0.35 + 0.65 * value / maximum
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="3" fill="#ffffff" fill-opacity="{opacity:.2f}"/>'


def render(weekdays: Counter, hours: Counter, total: int) -> str:
    max_day = max(weekdays.values(), default=1)
    max_hour = max(hours.values(), default=1)
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="216" viewBox="0 0 900 216" role="img" aria-labelledby="title desc">',
        '<title id="title">Recent public push activity</title>',
        f'<desc id="desc">{total} recent public push events, grouped by weekday and by UTC hour.</desc>',
        '<rect width="900" height="216" rx="18" fill="#111115"/>',
        '<rect x="0.5" y="0.5" width="899" height="215" rx="17.5" fill="none" stroke="#ffffff" stroke-opacity="0.12"/>',
        f'<text x="32" y="42" font-family="{SANS}" font-size="16" font-weight="600" fill="#ffffff">Push activity</text>',
        f'<text x="32" y="62" font-family="{MONO}" font-size="12" fill="#71717a">last {total} public pushes · UTC</text>',
        f'<text x="32" y="92" font-family="{MONO}" font-size="11" letter-spacing="1" fill="#71717a">BY WEEKDAY</text>',
    ]
    for i, day in enumerate(DAYS):
        x, base = 32 + i * 60, 160
        value = weekdays[i]
        height = max(3, round(48 * value / max_day)) if value else 3
        parts.append(bar(x, base - height, 34, height, value, max_day))
        parts.append(f'<text x="{x + 17}" y="178" text-anchor="middle" font-family="{MONO}" font-size="11" fill="#a1a1aa">{day}</text>')
        parts.append(f'<text x="{x + 17}" y="196" text-anchor="middle" font-family="{MONO}" font-size="11" fill="#f4f4f6">{value}</text>')
    parts.append(f'<text x="500" y="92" font-family="{MONO}" font-size="11" letter-spacing="1" fill="#71717a">BY HOUR</text>')
    for hour in range(24):
        x = 500 + hour * 15.4
        value = hours[hour]
        height = max(3, round(48 * value / max_hour)) if value else 3
        parts.append(bar(round(x), 160 - height, 10, height, value, max_hour))
        if hour % 3 == 0:
            parts.append(f'<text x="{round(x + 5)}" y="178" text-anchor="middle" font-family="{MONO}" font-size="10" fill="#a1a1aa">{hour:02d}</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main():
    pushes = fetch_pushes()
    weekdays = Counter(event.weekday() for event in pushes)
    hours = Counter(event.hour for event in pushes)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(weekdays, hours, len(pushes)), encoding="utf-8")


if __name__ == "__main__":
    main()
