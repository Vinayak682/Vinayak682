#!/usr/bin/env python3
"""
fetch_commits.py: count every commit I authored across my public repos in the
last 12 months, whatever email it was made with. GitHub's own calendar skips
commits from emails not linked to the account, so this file fills the gap.

  GH_TOKEN=... GH_PROFILE_USER=Vinayak682 python scripts/fetch_commits.py

Writes commits.json: {"user", "repos", "days": {"YYYY-MM-DD": n}, "by_repo": {...}}
"""
import datetime as dt
import json
import os
import time

import requests

USER = os.environ.get("GH_PROFILE_USER", "Vinayak682")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
H = {"Accept": "application/vnd.github+json", "User-Agent": "profile-art"}
if TOKEN:
    H["Authorization"] = f"Bearer {TOKEN}"
# Names/emails that are me; bots and other people are excluded.
ME_LOGINS = {USER.lower(), "bhadanivinayak"}
ME_NAMES = {"vinayak bhadani", "vinayak682", "vinayak"}
SINCE = (dt.datetime.utcnow() - dt.timedelta(days=371)).strftime("%Y-%m-%dT00:00:00Z")


def get(url, **params):
    out, page = [], 1
    while True:
        for attempt in range(4):
            try:
                r = requests.get(url, headers=H, params={**params, "per_page": 100, "page": page}, timeout=30)
                break
            except requests.ConnectionError:
                if attempt == 3:
                    raise
                time.sleep(3 * (attempt + 1))
        if r.status_code == 409:  # empty repo
            return out
        r.raise_for_status()
        batch = r.json()
        out += batch
        if len(batch) < 100:
            return out
        page += 1


def is_me(c):
    login = ((c.get("author") or {}).get("login") or "").lower()
    if login.endswith("[bot]"):
        return False
    if login in ME_LOGINS:
        return True
    a = c["commit"]["author"]
    if "bot" in (a.get("email") or "") or "noreply@anthropic.com" == a.get("email"):
        return False
    return (a.get("name") or "").strip().lower() in ME_NAMES


def main():
    repos = [r for r in get(f"https://api.github.com/users/{USER}/repos", type="owner")
             if not r["fork"] and not r["private"]]
    days, by_repo, seen = {}, {}, set()
    for r in repos:
        n = 0
        for c in get(f"https://api.github.com/repos/{USER}/{r['name']}/commits", since=SINCE):
            if c["sha"] in seen or not is_me(c):
                continue
            seen.add(c["sha"])
            d = c["commit"]["author"]["date"][:10]
            days[d] = days.get(d, 0) + 1
            n += 1
        by_repo[r["name"]] = n
    json.dump({"user": USER, "repos": len(repos), "days": dict(sorted(days.items())),
               "by_repo": dict(sorted(by_repo.items(), key=lambda x: -x[1]))},
              open("commits.json", "w"), separators=(",", ":"))
    print(f"commits.json: {sum(days.values())} commits, {len(days)} active days, {len(repos)} repos")


if __name__ == "__main__":
    main()
