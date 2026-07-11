#!/usr/bin/env python3
"""
fetch_contributions.py — scrape the public GitHub contribution calendar (no auth).

  GH_PROFILE_USER=Vinayak682 python scripts/fetch_contributions.py

Writes contributions.json: {"user", "days": [{"date","level","count"}, ...]}
"""
import json
import os
import re

import requests
from bs4 import BeautifulSoup

# ──────────────────────────── CONFIG ────────────────────────────
GH_PROFILE_USER = os.environ.get("GH_PROFILE_USER", "Vinayak682")
# ────────────────────────────────────────────────────────────────


def main() -> None:
    url = f"https://github.com/users/{GH_PROFILE_USER}/contributions"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (profile-art)"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    tooltips = {tt.get("for"): tt.get_text(" ", strip=True) for tt in soup.find_all("tool-tip")}

    days = []
    for td in soup.find_all("td", class_="ContributionCalendar-day"):
        date = td.get("data-date")
        if not date:
            continue
        level = int(td.get("data-level", 0))
        label = tooltips.get(td.get("id"), "") or td.get_text(" ", strip=True)
        m = re.search(r"(\d+)\s+contribution", label)
        count = int(m.group(1)) if m else 0
        days.append({"date": date, "level": level, "count": count})

    if not days:
        raise SystemExit("no calendar cells found — GitHub markup may have changed")

    days.sort(key=lambda d: d["date"])
    with open("contributions.json", "w") as f:
        json.dump({"user": GH_PROFILE_USER, "days": days}, f, separators=(",", ":"))

    total = sum(d["count"] for d in days)
    print(f"saved contributions.json — {len(days)} days, {total} contributions "
          f"({days[0]['date']} → {days[-1]['date']})")


if __name__ == "__main__":
    main()
