"""Shared helpers: GitHub API access, palette and SVG utilities."""
import datetime as dt
import json
import os
import urllib.request
from xml.sax.saxutils import escape

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

W = 860  # every panel shares one width so the README lines up

# black + graphite, one terminal green for "ok", red/amber only for real alerts
C = {
    "bg": "#0a0a0a",
    "panel": "#121212",
    "grid": "#1a1a1a",
    "line": "#2a2a2a",
    "text": "#d4d4d4",
    "dim": "#6e6e6e",
    "cyan": "#e8e8e8",    # primary highlight: near-white, not blue
    "amber": "#c9a24a",
    "red": "#d64545",
    "green": "#4ade80",
    "violet": "#a3a3a3",
}

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

LANG = {  # graphite ramp, terminal green for the main language
    "Python": "#4ade80",
    "TypeScript": "#e5e5e5",
    "JavaScript": "#a3a3a3",
    "Java": "#c9a24a",
    "HTML": "#737373",
    "CSS": "#525252",
    "HCL": "#8a8a8a",
    "Shell": "#bdbdbd",
}


def lang_color(name):
    return LANG.get(name or "", C["dim"])


def _call(url, payload=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-telemetry"}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def rest(path):
    return _call("https://api.github.com" + path)


def gql(query, **variables):
    out = _call("https://api.github.com/graphql", {"query": query, "variables": variables})
    if out.get("errors"):
        raise RuntimeError(out["errors"])
    return out["data"]


def own_repos(login):
    """Public, non-fork repos, excluding the profile repo itself."""
    repos = rest(f"/users/{login}/repos?per_page=100&type=owner&sort=pushed")
    return [r for r in repos if not r["fork"] and r["name"].lower() != login.lower()]


def calendar(login):
    """[(date, count)] for the last year of contributions, oldest first."""
    q = """query($login:String!){user(login:$login){contributionsCollection{
           contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"""
    cal = gql(q, login=login)["user"]["contributionsCollection"]["contributionCalendar"]
    days = [
        (dt.date.fromisoformat(d["date"]), d["contributionCount"])
        for w in cal["weeks"]
        for d in w["contributionDays"]
    ]
    return days, cal["totalContributions"]


def days_ago(iso):
    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (dt.datetime.now(dt.timezone.utc) - t).days


def now_utc():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def esc(s):
    return escape(str(s), {'"': "&quot;"})


def appear(delay, dur=0.35):
    """Fade-in that starts at t=0, so the element's resting state stays visible
    wherever SVG animation doesn't run (previews, thumbnails, reduced motion)."""
    total = delay + dur
    return (
        f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{delay / total:.4f};1" '
        f'dur="{total:.2f}s" fill="freeze"/>'
    )


def chrome(width, height):
    """Shared panel finish: faint CRT scanlines and targeting-bracket corners."""
    s, i = 14, 5  # bracket arm length, inset
    corners = [
        (i, i, 1, 1), (width - i, i, -1, 1), (i, height - i, 1, -1), (width - i, height - i, -1, -1),
    ]
    paths = " ".join(f"M{x},{y + dy * s} L{x},{y} L{x + dx * s},{y}" for x, y, dx, dy in corners)
    return (
        '<defs><pattern id="scanlines" width="4" height="3" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="1" fill="#ffffff" opacity=".028"/></pattern></defs>'
        f'<rect width="{width}" height="{height}" rx="10" fill="url(#scanlines)" pointer-events="none"/>'
        f'<path d="{paths}" fill="none" stroke="{C["dim"]}" stroke-width="1.5"/>'
    )


def svg(width, height, body, title, desc=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" font-family="{FONT}">\n'
        f"<title>{esc(title)}</title>\n"
        + (f"<desc>{esc(desc)}</desc>\n" if desc else "")
        + body
        + ("\n" + chrome(width, height) if height > 60 else "")
        + "\n</svg>\n"
    )


def write(path, content):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"wrote {path} ({len(content):,} bytes)")
