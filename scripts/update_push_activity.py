#!/usr/bin/env python3
"""Render a compact chart from the latest public GitHub push events."""

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
import json


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "push-activity.svg"
API = "https://api.github.com/users/Sharon-ctl/events/public?per_page=100"


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
    fill = "#67d9c4" if value else "#223247"
    opacity = 0.38 + 0.62 * value / maximum if value and maximum else 1
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="4" fill="{fill}" opacity="{opacity:.2f}"/>'


def main():
    pushes = fetch_pushes()
    weekdays = Counter(event.weekday() for event in pushes)
    hours = Counter(event.hour for event in pushes)
    max_day = max(weekdays.values(), default=1)
    max_hour = max(hours.values(), default=1)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 310" role="img" aria-labelledby="title desc">',
        '<title id="title">Recent public push activity</title>',
        f'<desc id="desc">{len(pushes)} public push events, grouped by weekday and UTC hour.</desc>',
        '<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#14243a"/><stop offset="1" stop-color="#101a2a"/></linearGradient></defs>',
        '<rect width="900" height="310" rx="22" fill="url(#bg)" stroke="#34475c"/>',
        '<g font-family="Inter,Segoe UI,Arial,sans-serif" fill="#edf5f7">',
        '<text x="30" y="42" font-size="19" font-weight="700">When public pushes happened</text>',
        f'<text x="30" y="65" font-size="12" fill="#a8bac8">Latest public event sample · {len(pushes)} pushes · UTC</text>',
        '<text x="30" y="101" font-size="12" fill="#b5c5d2">By weekday</text>',
    ]
    for i, day in enumerate(days):
        x, y = 30 + i * 62, 116
        value = weekdays[i]
        parts.append(bar(x, y + 49 - round(49 * value / max_day), 42, max(3, round(49 * value / max_day)), value, max_day))
        parts.append(f'<text x="{x+21}" y="183" text-anchor="middle" font-size="10" fill="#b5c5d2">{day}</text>')
        parts.append(f'<text x="{x+21}" y="201" text-anchor="middle" font-size="10" fill="#edf5f7">{value}</text>')
    parts.append('<text x="500" y="101" font-size="12" fill="#b5c5d2">By hour of day</text>')
    for hour in range(24):
        x = 500 + hour * 15.3
        value = hours[hour]
        height = max(3, round(53 * value / max_hour)) if value else 3
        parts.append(bar(round(x), 167 - height, 10, height, value, max_hour))
        if hour % 3 == 0:
            parts.append(f'<text x="{round(x+5)}" y="184" text-anchor="middle" font-size="9" fill="#b5c5d2">{hour:02d}</text>')
    parts.extend([
        '<line x1="30" y1="226" x2="870" y2="226" stroke="#34475c"/>',
        '<text x="30" y="253" font-size="12" fill="#d7e4e9">Activity snapshot, refreshed weekly from GitHub public events.</text>',
        '<text x="30" y="275" font-size="11" fill="#91a6b6">Event API is capped; this is not a complete history or an availability schedule.</text>',
        '</g></svg>',
    ])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(parts) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
