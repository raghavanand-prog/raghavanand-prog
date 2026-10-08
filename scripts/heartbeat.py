"""Contribution heartbeat: the last year of commits drawn as an ECG trace.

Every day is one beat; spike height = commits that day.

usage: python heartbeat.py <login> <out.svg>
"""
import math
import sys

from common import C, W, calendar, esc, svg, write

H = 236
X0, X1 = 22, W - 22
BASE = 140
AMP = 82


def trace(days):
    peak = max((c for _, c in days), default=0) or 1
    step = (X1 - X0) / len(days)
    pts = [f"M{X0},{BASE}"]
    for i, (_, c) in enumerate(days):
        x = X0 + i * step
        if c:
            a = AMP * math.sqrt(c / peak)
            pts.append(
                f"L{x + step * .25:.1f},{BASE} L{x + step * .45:.1f},{BASE - a:.1f} "
                f"L{x + step * .65:.1f},{BASE + a * .28:.1f} L{x + step * .85:.1f},{BASE}"
            )
        else:
            pts.append(f"L{x + step:.1f},{BASE}")
    return " ".join(pts), step


def render(days, total):
    path, step = trace(days)
    last30 = sum(c for _, c in days[-30:])
    peak_day, peak = max(days, key=lambda d: d[1])
    active = sum(1 for _, c in days if c)

    p = [
        '<defs><linearGradient id="sweep" x1="0" x2="1">'
        f'<stop offset="0" stop-color="{C["bg"]}" stop-opacity="0"/>'
        f'<stop offset="1" stop-color="{C["bg"]}" stop-opacity="1"/></linearGradient>'
        f'<filter id="glow"><feGaussianBlur stdDeviation="2.2" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
        f'<rect width="{W}" height="{H}" rx="12" fill="{C["bg"]}" stroke="{C["line"]}"/>',
    ]
    for gx in range(X0, X1 + 1, 20):
        p.append(f'<line x1="{gx}" y1="44" x2="{gx}" y2="{H - 34}" stroke="{C["grid"]}" stroke-opacity="{".9" if (gx - X0) % 100 == 0 else ".35"}"/>')
    for gy in range(44, H - 33, 20):
        p.append(f'<line x1="{X0}" y1="{gy}" x2="{X1}" y2="{gy}" stroke="{C["grid"]}" stroke-opacity=".35"/>')

    # month ticks
    seen = set()
    for i, (d, _) in enumerate(days):
        key = (d.year, d.month)
        if d.day <= 7 and key not in seen:
            seen.add(key)
            p.append(f'<text x="{X0 + i * step:.1f}" y="{H - 16}" font-size="10" fill="{C["dim"]}">{d.strftime("%b").upper()}</text>')

    p.append(
        f'<path d="{path}" fill="none" stroke="{C["green"]}" stroke-width="1.6" stroke-linejoin="round" filter="url(#glow)" '
        f'pathLength="1000" stroke-dasharray="1000" stroke-dashoffset="0">'
        '<animate attributeName="stroke-dashoffset" from="1000" to="0" dur="5s" fill="freeze"/></path>'
    )
    # monitor sweep: a dark band that keeps travelling over the trace
    p.append(
        f'<rect x="{X0 - 60}" y="44" width="60" height="{H - 78}" fill="url(#sweep)">'
        f'<animate attributeName="x" from="{X0 - 60}" to="{X1}" begin="5s" dur="4s" repeatCount="indefinite"/></rect>'
    )
    p.append(
        f'<circle r="3.5" fill="{C["green"]}" filter="url(#glow)"><animateMotion dur="4s" begin="5s" '
        f'repeatCount="indefinite" path="{path}"/></circle>'
    )

    stats = [
        ("BPM", last30, "commits / last 30d", C["green"]),
        ("TOTAL", total, "contributions / 1y", C["cyan"]),
        ("ACTIVE", active, "days with a beat", C["amber"]),
        ("PEAK", peak, peak_day.strftime("%d %b %Y"), C["red"]),
    ]
    for i, (k, v, sub, col) in enumerate(stats):
        x = X0 + i * 210
        p.append(
            f'<text x="{x}" y="30" font-size="11" fill="{C["dim"]}">{k} '
            f'<tspan font-size="17" font-weight="700" fill="{col}">{esc(v)}</tspan>'
            f'<tspan dx="6">{esc(sub)}</tspan></text>'
        )
    return svg(W, H, "\n".join(p), "Signal heartbeat",
               "My last year of GitHub contributions as an ECG trace: one beat per day, taller spikes mean more commits")


if __name__ == "__main__":
    login, out = sys.argv[1], sys.argv[2]
    days, total = calendar(login)
    write(out, render(days, total))
