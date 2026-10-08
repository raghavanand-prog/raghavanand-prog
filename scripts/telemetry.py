"""SOC-style telemetry dashboard: KPI tiles, an event log and the language mix.

usage: python telemetry.py <login> <out.svg>
"""
import sys
from collections import Counter

from common import C, W, appear, calendar, days_ago, esc, lang_color, now_utc, own_repos, rest, svg, write


def gather(login):
    user = rest(f"/users/{login}")
    repos = own_repos(login)
    _, total = calendar(login)

    langs = Counter()
    for r in repos:
        for name, size in rest(f"/repos/{login}/{r['name']}/languages").items():
            langs[name] += size

    events = []
    for e in rest(f"/users/{login}/events/public?per_page=60"):
        if e["type"] != "PushEvent":
            continue
        repo = e["repo"]["name"].split("/", 1)[1]
        if repo.lower() == login.lower():
            continue
        commits = e["payload"].get("commits") or []
        branch = (e["payload"].get("ref") or "").rsplit("/", 1)[-1] or "main"
        msg = commits[-1]["message"].splitlines()[0] if commits else f"pushed to {branch}"
        events.append((e["created_at"][:16].replace("T", " "), repo, msg))
        if len(events) == 6:
            break

    return {
        "kpis": [
            ("REPOSITORIES", user["public_repos"], C["cyan"]),
            ("STARS EARNED", sum(r["stargazers_count"] for r in repos), C["amber"]),
            ("FOLLOWERS", user["followers"], C["violet"]),
            ("CONTRIBUTIONS / 1Y", total, C["green"]),
            ("ACTIVE REPOS / 30D", sum(days_ago(r["pushed_at"]) <= 30 for r in repos), C["cyan"]),
            ("TOP LANGUAGE", langs.most_common(1)[0][0] if langs else "-", C["red"]),
        ],
        "langs": langs,
        "events": events,
    }


def render(data):
    h = 372
    p = [
        f'<rect width="{W}" height="{h}" rx="12" fill="{C["bg"]}" stroke="{C["line"]}"/>',
        f'<text x="22" y="30" font-size="12" fill="{C["dim"]}">'
        f'<tspan fill="{C["green"]}">●</tspan> LIVE · source: api.github.com · last sync {now_utc()}</text>',
    ]

    # KPI tiles, 3 x 2
    tw, th, gx, gy, x0, y0 = 150, 74, 10, 10, 22, 46
    for i, (label, value, col) in enumerate(data["kpis"]):
        x = x0 + (i % 3) * (tw + gx)
        y = y0 + (i // 3) * (th + gy)
        p.append(f'<rect x="{x}" y="{y}" width="{tw}" height="{th}" rx="6" fill="{C["panel"]}" stroke="{C["grid"]}"/>')
        p.append(f'<rect x="{x}" y="{y}" width="3" height="{th}" rx="1.5" fill="{col}"/>')
        p.append(f'<text x="{x + 14}" y="{y + 22}" font-size="10" fill="{C["dim"]}" letter-spacing=".8">{esc(label)}</text>')
        p.append(
            f'<text x="{x + 14}" y="{y + 56}" font-size="{28 if len(str(value)) <= 7 else 19}" font-weight="700" fill="{col}">{esc(value)}{appear(0.15 * i, .4)}</text>'
        )

    # event log
    lx, ly, lw, lh = 512, 46, 326, 158
    p.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" rx="6" fill="{C["panel"]}" stroke="{C["grid"]}"/>')
    p.append(f'<text x="{lx + 14}" y="{ly + 20}" font-size="10" fill="{C["dim"]}" letter-spacing=".8">EVENT LOG · git push</text>')
    events = data["events"] or [("—", "—", "no recent public pushes")]
    for i, (ts, repo, msg) in enumerate(events):
        y = ly + 42 + i * 19
        line = f"{repo}: {msg}"
        if len(line) > 30:
            line = line[:29] + "…"
        p.append(
            f'<g>{appear(0.9 + 0.25 * i, .3)}'
            f'<text x="{lx + 14}" y="{y}" font-size="11"><tspan fill="{C["dim"]}">{esc(ts[5:])}</tspan>'
            f'<tspan dx="8" fill="{C["green"]}">INFO</tspan><tspan dx="8" fill="{C["text"]}">{esc(line)}</tspan></text></g>'
        )

    # language mix
    by = 232
    p.append(f'<text x="22" y="{by}" font-size="10" fill="{C["dim"]}" letter-spacing=".8">PAYLOAD COMPOSITION · bytes of code across my repos</text>')
    total = sum(data["langs"].values()) or 1
    top = data["langs"].most_common(7)
    other = total - sum(v for _, v in top)
    if other > 0:
        top.append(("Other", other))
    x, bw = 22.0, W - 44
    p.append(f'<clipPath id="bar"><rect x="22" y="{by + 12}" width="{bw}" height="14" rx="7"/></clipPath><g clip-path="url(#bar)">')
    for name, v in top:
        w = bw * v / total
        p.append(f'<rect x="{x:.1f}" y="{by + 12}" width="{w:.1f}" height="14" fill="{lang_color(name if name != "Other" else "")}"/>')
        x += w
    p.append("</g>")
    for i, (name, v) in enumerate(top):
        cx = 22 + (i % 4) * 205
        cy = by + 52 + (i // 4) * 24
        p.append(f'<circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{lang_color(name if name != "Other" else "")}"/>')
        p.append(
            f'<text x="{cx + 16}" y="{cy}" font-size="12" fill="{C["text"]}">{esc(name)} '
            f'<tspan fill="{C["dim"]}">{100 * v / total:.1f}%</tspan></text>'
        )

    p.append(
        f'<text x="{W - 22}" y="{h - 14}" text-anchor="end" font-size="10" fill="{C["dim"]}">'
        "rendered by scripts/telemetry.py · no third-party widgets</text>"
    )
    return svg(W, h, "\n".join(p), "SOC telemetry",
               "Live GitHub stats for raghavanand-prog: repos, stars, followers, contributions, streaks, recent pushes and language mix")


if __name__ == "__main__":
    login, out = sys.argv[1], sys.argv[2]
    write(out, render(gather(login)))
