import os
import sys
import json
import urllib.request

GH_TOKEN = os.environ["GH_TOKEN"]
GH_USERNAME = os.environ.get("GH_USERNAME", "anshkaushik26")

QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    login
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def fetch_contributions():
    body = json.dumps({"query": QUERY, "variables": {"login": GH_USERNAME}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"Bearer {GH_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": GH_USERNAME,
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        payload = json.loads(resp.read().decode())
    if "errors" in payload:
        raise SystemExit(f"GraphQL errors: {payload['errors']}")
    user = payload["data"]["user"]
    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = []
    for w in weeks:
        for d in w["contributionDays"]:
            days.append({"date": d["date"], "count": d["contributionCount"]})
    days.sort(key=lambda d: d["date"])
    display_name = (user.get("name") or user["login"]).upper()
    return display_name, days[-31:]


def build_svg(display_name, data):
    W, H = 800, 420
    padL, padR, padT, padB = 70, 40, 70, 70
    plotW = W - padL - padR
    plotH = H - padT - padB

    counts = [d["count"] for d in data]
    max_c = max(counts) if counts else 0
    y_max = max(4, ((max_c // 2) + 1) * 2)
    n = len(data)

    def x_for(i):
        return padL + (plotW * i / (n - 1)) if n > 1 else padL

    def y_for(c):
        return padT + plotH - (plotH * c / y_max)

    points = [(x_for(i), y_for(d["count"])) for i, d in enumerate(data)]

    path_d = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    area_d = path_d + f" L {points[-1][0]:.2f},{padT+plotH:.2f} L {points[0][0]:.2f},{padT+plotH:.2f} Z"

    y_ticks = []
    vals = list(range(0, y_max + 1, max(1, y_max // 6)))
    for v in vals:
        y = y_for(v)
        y_ticks.append(f'<line x1="{padL}" y1="{y:.2f}" x2="{W-padR}" y2="{y:.2f}" stroke="#233047" stroke-width="1" stroke-dasharray="2,3"/>')
        y_ticks.append(f'<text x="{padL-12}" y="{y+4:.2f}" text-anchor="end" font-size="12" fill="#5b7899" font-family="Segoe UI, Helvetica, sans-serif">{v}</text>')

    x_labels = []
    for i, d in enumerate(data):
        day = int(d["date"].split("-")[2])
        x = x_for(i)
        x_labels.append(f'<text x="{x:.2f}" y="{H-padB+20}" text-anchor="middle" font-size="11" fill="#5b7899" font-family="Segoe UI, Helvetica, sans-serif">{day}</text>')

    dots = []
    for (x, y), d in zip(points, data):
        r = 3.2 if d["count"] > 0 else 2.2
        dots.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{r}" fill="#0d1117" stroke="#38bdf8" stroke-width="1.6"/>')

    title = f"{display_name}'s Contribution Graph".replace("&", "&amp;")

    svg = f'''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#38bdf8" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="{W}" height="{H}" rx="10" fill="#0d1117"/>
  <text x="{W/2}" y="34" text-anchor="middle" font-size="20" font-weight="700" fill="#38bdf8" font-family="Segoe UI, Helvetica, sans-serif">{title}</text>
  <line x1="{padL}" y1="{padT-15}" x2="{W-padR}" y2="{padT-15}" stroke="#233047" stroke-width="1"/>
  {''.join(y_ticks)}
  <line x1="{padL}" y1="{padT}" x2="{padL}" y2="{padT+plotH}" stroke="#5b7899" stroke-width="1.2"/>
  <line x1="{padL}" y1="{padT+plotH}" x2="{W-padR}" y2="{padT+plotH}" stroke="#5b7899" stroke-width="1.2"/>
  <path d="{area_d}" fill="url(#areaFill)"/>
  <path d="{path_d}" fill="none" stroke="#38bdf8" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round"/>
  {''.join(dots)}
  {''.join(x_labels)}
  <text x="18" y="{padT+plotH/2}" text-anchor="middle" font-size="12" fill="#5b7899" font-family="Segoe UI, Helvetica, sans-serif" transform="rotate(-90 18 {padT+plotH/2})">Contributions</text>
  <text x="{W/2}" y="{H-12}" text-anchor="middle" font-size="12" fill="#5b7899" font-family="Segoe UI, Helvetica, sans-serif">Days</text>
</svg>'''
    return svg


def main():
    display_name, data = fetch_contributions()
    svg = build_svg(display_name, data)
    with open("contribution-graph.svg", "w") as f:
        f.write(svg)
    print(f"Wrote contribution-graph.svg with {len(data)} days of data for {display_name}")


if __name__ == "__main__":
    main()
