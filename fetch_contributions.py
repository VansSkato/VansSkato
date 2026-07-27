#!/usr/bin/env python3
"""
Step 5a — Get real contribution data, no token required.

GitHub serves the contribution calendar as public HTML at:
    https://github.com/users/<username>/contributions
(the same fragment the profile page itself uses). We fetch it with
requests, parse the day cells with BeautifulSoup, and write
data/contributions.json with raw days plus derived stats (current
streak, longest streak, best day, monthly totals).

Usage:
    python scripts/fetch_contributions.py [username]
Writes:
    data/contributions.json
"""
import sys
import json
import datetime
import os
from collections import defaultdict

import requests
from bs4 import BeautifulSoup

USERNAME = sys.argv[1] if len(sys.argv) > 1 else "VansSkato"
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT = "data/contributions.json"


def fetch(username: str):
    headers = {"User-Agent": "Mozilla/5.0 (profile-readme-bot)"}
    resp = requests.get(URL, headers=headers, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    days = []
    # GitHub renders each day as a <td> or <rect> tool-tipped cell
    # depending on markup version; handle both.
    cells = soup.select("td.ContributionCalendar-day") or soup.select("rect.ContributionCalendar-day")

    for cell in cells:
        date_str = cell.get("data-date")
        count_attr = cell.get("data-count")
        level_attr = cell.get("data-level")
        if date_str is None:
            continue
        try:
            count = int(count_attr) if count_attr is not None else 0
        except ValueError:
            count = 0
        try:
            level = int(level_attr) if level_attr is not None else min(count, 4)
        except ValueError:
            level = min(count, 4)
        days.append({"date": date_str, "count": count, "level": level})

    days.sort(key=lambda d: d["date"])
    return days


def derive_stats(days):
    if not days:
        return {
            "total": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "best_day": None,
            "monthly": {},
        }

    total = sum(d["count"] for d in days)

    # streaks
    longest = cur = 0
    for d in days:
        if d["count"] > 0:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0

    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    best_day = max(days, key=lambda d: d["count"])

    monthly = defaultdict(int)
    for d in days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly[month_key] += d["count"]

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest,
        "best_day": best_day,
        "monthly": dict(monthly),
    }


def main():
    days = fetch(USERNAME)
    stats = derive_stats(days)
    payload = {
        "username": USERNAME,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "days": days,
        "stats": stats,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"wrote {OUT}: {len(days)} days, {stats['total']} total contributions")


if __name__ == "__main__":
    main()
