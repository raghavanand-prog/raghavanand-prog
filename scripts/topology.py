"""Network topology map: every repo is a host on my network.

Inner ring = pushed in the last 30 days, outer ring = older.
Node colour = primary language, node size = repo size.
Live hosts (pushed in the last 14 days) get packets flowing to them.

usage: python topology.py <login> <out.svg>
"""
import math
import sys

from common import C, W, days_ago, esc, lang_color, own_repos, svg, write

H = 452
CX, CY = W / 2, 214
RINGS = {"inner": (178, 98), "outer": (360, 178)}


def layout(repos):
    nodes = []
    for ring in ("inner", "outer"):
        members = [r for r in repos if (days_ago(r["pushed_at"]) <= 30) == (ring == "inner")]
        members.sort(key=lambda r: (r["language"] or "~", r["name"].lower()))
        rx, ry = RINGS[ring]
        n = len(members)
        offset = -math.pi / 2 + (0.0 if ring == "inner" else math.pi / max(n, 1))
        for i, r in enumerate(members):
            a = offset + 2 * math.pi * i / max(n, 1)
            size = max(r["size"], 1)
            nodes.append({
                "repo": r,
                "x": CX + rx * math.cos(a),
                "y": CY + ry * math.sin(a),
                "r": 5 + min(9, math.log10(size) * 2.4),
                "age": days_ago(r["pushed_at"]),
                "ring": ring,
            })
    return nodes


def render(nodes):
    p = [f'<rect width="{W}" height="{H}" rx="12" fill="{C["bg"]}" stroke="{C["line"]}"/>']

    # background grid + ring guides
    for gx in range(0, W, 30):
        p.append(f'<line x1="{gx}" y1="0" x2="{gx}" y2="{H}" stroke="{C["grid"]}" stroke-opacity=".35"/>')
    for gy in range(0, H, 30):
        p.append(f'<line x1="0" y1="{gy}" x2="{W}" y2="{gy}" stroke="{C["grid"]}" stroke-opacity=".35"/>')
    for rx, ry in RINGS.values():
        p.append(f'<ellipse cx="{CX}" cy="{CY}" rx="{rx}" ry="{ry}" fill="none" stroke="{C["line"]}" stroke-dasharray="3 6"/>')

    # links between neighbouring hosts that share a language
    for ring in ("inner", "outer"):
        ring_nodes = [n for n in nodes if n["ring"] == ring]
        for a, b in zip(ring_nodes, ring_nodes[1:] + ring_nodes[:1]):
            if a is not b and a["repo"]["language"] and a["repo"]["language"] == b["repo"]["language"]:
                p.append(
                    f'<line x1="{a["x"]:.1f}" y1="{a["y"]:.1f}" x2="{b["x"]:.1f}" y2="{b["y"]:.1f}" '
                    f'stroke="{lang_color(a["repo"]["language"])}" stroke-opacity=".35"/>'
                )

    # uplinks from the core to every host, with packets to live ones
    for i, n in enumerate(nodes):
        live = n["age"] <= 14
        dash = "" if live else ' stroke-dasharray="2 5"'
        p.append(
            f'<line x1="{CX}" y1="{CY}" x2="{n["x"]:.1f}" y2="{n["y"]:.1f}" stroke="{C["cyan"] if live else C["line"]}" '
            f'stroke-opacity="{".55" if live else ".7"}"{dash}/>'
        )
        if live:
            dur = 1.6 + (i % 4) * 0.35
            path = f"M{CX},{CY} L{n['x']:.1f},{n['y']:.1f}"
            p.append(
                f'<circle r="2.6" fill="{C["cyan"]}"><animateMotion dur="{dur:.2f}s" repeatCount="indefinite" path="{path}"/></circle>'
            )

    # hosts
    for i, n in enumerate(nodes):
        r = n["repo"]
        col = lang_color(r["language"])
        live = n["age"] <= 14
        if live:
            p.append(
                f'<circle cx="{n["x"]:.1f}" cy="{n["y"]:.1f}" r="{n["r"]:.1f}" fill="none" stroke="{col}">'
                f'<animate attributeName="r" from="{n["r"]:.1f}" to="{n["r"] + 12:.1f}" dur="2.2s" begin="{(i % 5) * 0.4:.1f}s" repeatCount="indefinite"/>'
                f'<animate attributeName="stroke-opacity" from=".8" to="0" dur="2.2s" begin="{(i % 5) * 0.4:.1f}s" repeatCount="indefinite"/></circle>'
            )
        p.append(
            f'<a href="{esc(r["html_url"])}"><circle cx="{n["x"]:.1f}" cy="{n["y"]:.1f}" r="{n["r"]:.1f}" fill="{C["panel"]}" '
            f'stroke="{col}" stroke-width="2"/><circle cx="{n["x"]:.1f}" cy="{n["y"]:.1f}" r="{n["r"] * 0.45:.1f}" fill="{col}"/></a>'
        )
        name = r["name"] if len(r["name"]) <= 20 else r["name"][:19] + "…"
        below = n["y"] >= CY - 4
        ty = n["y"] + (n["r"] + 13 if below else -n["r"] - 6)
        anchor = "middle"
        if n["x"] < CX - 250:
            anchor = "start"
        elif n["x"] > CX + 250:
            anchor = "end"
        tx = n["x"] - 8 if anchor == "start" else n["x"] + 8 if anchor == "end" else n["x"]
        p.append(
            f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="{anchor}" font-size="11" fill="{C["text"] if live else C["dim"]}">'
            f"{esc(name)}</text>"
        )

    # core node
    hexagon = " ".join(f"{CX + 30 * math.cos(math.pi / 6 + k * math.pi / 3):.1f},{CY + 30 * math.sin(math.pi / 6 + k * math.pi / 3):.1f}" for k in range(6))
    p.append(f'<polygon points="{hexagon}" fill="{C["panel"]}" stroke="{C["cyan"]}" stroke-width="2"/>')
    p.append(f'<text x="{CX}" y="{CY - 2}" text-anchor="middle" font-size="10" fill="{C["cyan"]}">SOC-01</text>')
    p.append(f'<text x="{CX}" y="{CY + 11}" text-anchor="middle" font-size="9" fill="{C["dim"]}">raghav</text>')

    # legend
    langs = []
    for n in nodes:
        lang = n["repo"]["language"]
        if lang and lang not in langs:
            langs.append(lang)
    lx = 22
    for lang in langs:
        p.append(f'<circle cx="{lx + 4}" cy="{H - 22}" r="4" fill="{lang_color(lang)}"/>')
        p.append(f'<text x="{lx + 13}" y="{H - 18}" font-size="11" fill="{C["dim"]}">{esc(lang)}</text>')
        lx += 22 + len(lang) * 7
    live_count = sum(n["age"] <= 14 for n in nodes)
    p.append(
        f'<text x="{W - 22}" y="{H - 18}" text-anchor="end" font-size="11" fill="{C["dim"]}">'
        f'<tspan fill="{C["cyan"]}">{live_count}</tspan> live hosts · inner ring = pushed ≤30d · {len(nodes)} total</text>'
    )
    p.append(
        f'<text x="22" y="26" font-size="12" fill="{C["dim"]}">'
        f'$ nmap -sn ./repos <tspan fill="{C["green"]}">→ {len(nodes)} hosts up</tspan></text>'
    )
    return svg(W, H, "\n".join(p), "Network topology",
               "Every repo drawn as a host on a network map; inner ring is recently active, packets flow to repos pushed in the last two weeks")


if __name__ == "__main__":
    login, out = sys.argv[1], sys.argv[2]
    write(out, render(layout(own_repos(login))))
