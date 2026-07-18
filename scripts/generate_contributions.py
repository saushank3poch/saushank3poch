#!/usr/bin/env python3
"""Generate a GitHub-style contribution calendar SVG (includes private contribs via gh auth)."""

from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "contributions.svg"

QUERY = """
query {
  user(login: "saushank3poch") {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            color
          }
        }
      }
    }
  }
}
"""


def level_color(count: int, api_color: str | None) -> str:
    if api_color:
        return api_color
    if count == 0:
        return "#161b22"
    if count < 3:
        return "#0e4429"
    if count < 6:
        return "#006d32"
    if count < 10:
        return "#26a641"
    return "#39d353"


def main() -> None:
    raw = subprocess.check_output(
        ["gh", "api", "graphql", "-f", f"query={QUERY}"],
        text=True,
    )
    calendar = json.loads(raw)["data"]["user"]["contributionsCollection"][
        "contributionCalendar"
    ]
    weeks = calendar["weeks"]
    total = calendar["totalContributions"]

    cell = 12
    gap = 3
    left = 40
    top = 40
    width = left + len(weeks) * (cell + gap) + 24
    height = top + 7 * (cell + gap) + 56

    month_labels: list[tuple[int, str]] = []
    prev_month: int | None = None
    for i, week in enumerate(weeks):
        days = week["contributionDays"]
        if not days:
            continue
        day = dt.date.fromisoformat(days[0]["date"])
        if day.month != prev_month:
            month_labels.append((i, day.strftime("%b")))
            prev_month = day.month

    dow = ["", "Mon", "", "Wed", "", "Fri", ""]
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="#0d1117" rx="8"/>',
        (
            f'<text x="16" y="24" fill="#e6edf3" '
            f'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" '
            f'font-size="14" font-weight="600">{total:,} contributions in the last year</text>'
        ),
    ]

    for i, label in month_labels:
        x = left + i * (cell + gap)
        parts.append(
            f'<text x="{x}" y="36" fill="#8b949e" '
            f'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" '
            f'font-size="11">{label}</text>'
        )

    for row, label in enumerate(dow):
        if not label:
            continue
        y = top + row * (cell + gap) + cell - 1
        parts.append(
            f'<text x="8" y="{y}" fill="#8b949e" '
            f'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" '
            f'font-size="10">{label}</text>'
        )

    for wi, week in enumerate(weeks):
        for day in week["contributionDays"]:
            date = dt.date.fromisoformat(day["date"])
            row = (date.weekday() + 1) % 7  # Sunday = 0
            x = left + wi * (cell + gap)
            y = top + row * (cell + gap)
            fill = level_color(day["contributionCount"], day.get("color"))
            count = day["contributionCount"]
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{fill}">'
                f'<title>{day["date"]}: {count} contributions</title></rect>'
            )

    lx = left
    ly = top + 7 * (cell + gap) + 18
    parts.append(
        f'<text x="{lx}" y="{ly}" fill="#8b949e" '
        f'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" '
        f'font-size="11">Less</text>'
    )
    legend = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
    for i, color in enumerate(legend):
        parts.append(
            f'<rect x="{lx + 36 + i * (cell + gap)}" y="{ly - 10}" '
            f'width="{cell}" height="{cell}" rx="2" fill="{color}"/>'
        )
    parts.append(
        f'<text x="{lx + 36 + 5 * (cell + gap) + 4}" y="{ly}" fill="#8b949e" '
        f'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" '
        f'font-size="11">More</text>'
    )
    parts.append("</svg>")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({total} contributions)")


if __name__ == "__main__":
    main()
