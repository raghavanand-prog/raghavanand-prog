"""Terminal boot header and the section dividers.

usage: python banners.py <login> <out_dir>
"""
import sys

from common import C, W, appear, esc, svg, write

LINES = [
    ("$ ", "whoami", "cmd"),
    ("", "raghav anand :: cloud security // AI-driven detection // DevSecOps", "out"),
    ("$ ", "cat ./mission", "cmd"),
    ("", "build systems that see the attack, explain it, and act on it.", "out"),
    ("$ ", "./sensors --status", "cmd"),
    ("", "[ OK ] telemetry   [ OK ] detection   [ OK ] response   [ .. ] learning", "ok"),
]

CHAR_W = 8.4  # advance width of a 14px monospace glyph


def header():
    h = 236
    top = 46
    step = 27
    t = 0.4
    parts = [
        f'<rect width="{W}" height="{h}" rx="12" fill="{C["bg"]}" stroke="{C["line"]}"/>',
        f'<rect width="{W}" height="32" rx="12" fill="{C["panel"]}"/>',
        f'<rect y="20" width="{W}" height="12" fill="{C["panel"]}"/>',
        f'<line x1="0" y1="32" x2="{W}" y2="32" stroke="{C["line"]}"/>',
    ]
    for i, col in enumerate((C["red"], C["amber"], C["green"])):
        parts.append(f'<circle cx="{20 + i * 18}" cy="16" r="5.5" fill="{col}" opacity=".85"/>')
    parts.append(
        f'<text x="{W / 2}" y="20.5" text-anchor="middle" font-size="12" fill="{C["dim"]}">'
        f"raghav@soc-01: ~ — zsh — {W}x{h}</text>"
    )

    for i, (prompt, text, kind) in enumerate(LINES):
        y = top + 12 + i * step
        full = prompt + text
        width = len(full) * CHAR_W + 4
        typing = kind == "cmd"
        dur = max(0.35, len(text) * 0.045) if typing else 0.15
        cid = f"l{i}"
        # rest state = fully typed; the animation (from t=0) hides it, then types it out
        total = t + dur
        if typing:
            steps = len(text)
            widths = [len(prompt) * CHAR_W + 4] + [float(v) for v in _values(prompt, text).split(";")]
            times = [0.0] + [(t + dur * k / steps) / total for k in range(steps + 1)]
        else:
            widths, times = [0, width], [0.0, t / total]
        parts.append(
            f'<clipPath id="{cid}"><rect x="24" y="{y - 15}" height="21" width="{width}">'
            f'<animate attributeName="width" calcMode="discrete" dur="{total:.2f}s" fill="freeze" '
            f'values="{";".join(f"{v:.1f}" for v in widths)}" keyTimes="{";".join(f"{v:.4f}" for v in times)}"/>'
            "</rect></clipPath>"
        )
        colour = {"cmd": C["text"], "out": C["cyan"], "ok": C["green"]}[kind]
        spans = ""
        if prompt:
            spans += f'<tspan fill="{C["amber"]}">{esc(prompt)}</tspan>'
        spans += f'<tspan fill="{colour}">{esc(text)}</tspan>'
        parts.append(f'<text x="26" y="{y}" font-size="14" clip-path="url(#{cid})">{spans}</text>')
        t += dur + (0.25 if typing else 0.35)

    y = top + 12 + len(LINES) * step
    parts.append(f'<text x="26" y="{y}" font-size="14" fill="{C["amber"]}">$ {appear(t, 0.01)}</text>')
    parts.append(
        f'<rect x="{26 + 2 * CHAR_W}" y="{y - 12}" width="8" height="15" fill="{C["green"]}">'
        f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1s" repeatCount="indefinite"/></rect>'
    )
    # a faint scanline sweep for the CRT feel
    parts.append(
        f'<rect x="0" y="32" width="{W}" height="40" fill="url(#scan)" opacity=".5">'
        f'<animate attributeName="y" from="32" to="{h}" dur="6s" repeatCount="indefinite"/></rect>'
    )
    defs = (
        '<defs><linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{C["cyan"]}" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="{C["cyan"]}" stop-opacity=".06"/>'
        f'<stop offset="1" stop-color="{C["cyan"]}" stop-opacity="0"/></linearGradient></defs>'
    )
    return svg(W, h, defs + "\n".join(parts), "raghav@soc-01 terminal",
               "Animated terminal: whoami, mission and sensor status for Raghav Anand")


def _key_times(n):
    return ";".join(f"{i / n:.4f}" for i in range(n + 1))


def _values(prompt, text):
    return ";".join(f"{(len(prompt) + i) * CHAR_W + 4:.1f}" for i in range(len(text) + 1))


DIVIDERS = {
    "telemetry": ("0x01", "SOC.TELEMETRY"),
    "topology": ("0x02", "NETWORK.TOPOLOGY"),
    "heartbeat": ("0x03", "SIGNAL.HEARTBEAT"),
    "attack": ("0x04", "ATTACK.COVERAGE"),
    "intel": ("0x05", "THREAT.INTEL"),
    "posture": ("0x06", "SECURITY.POSTURE"),
    "cases": ("0x07", "CASE.FILES"),
    "arsenal": ("0x08", "TOOLCHAIN"),
}


def divider(addr, label):
    h = 34
    lw = len(label) * 8.4 + 28
    x0 = (W - lw) / 2
    body = (
        f'<line x1="0" y1="{h / 2}" x2="{x0 - 10}" y2="{h / 2}" stroke="{C["line"]}" stroke-dasharray="2 4"/>'
        f'<line x1="{x0 + lw + 10}" y1="{h / 2}" x2="{W}" y2="{h / 2}" stroke="{C["line"]}" stroke-dasharray="2 4"/>'
        f'<text x="{x0 - 18}" y="{h / 2 + 4}" text-anchor="end" font-size="11" fill="{C["dim"]}">{addr}</text>'
        f'<rect x="{x0}" y="4" width="{lw}" height="{h - 8}" rx="4" fill="{C["panel"]}" stroke="{C["cyan"]}" stroke-opacity=".5"/>'
        f'<text x="{W / 2}" y="{h / 2 + 5}" text-anchor="middle" font-size="14" fill="{C["cyan"]}" '
        f'letter-spacing="1">{esc(label)}</text>'
        f'<circle cx="{x0 + lw + 22}" cy="{h / 2}" r="3" fill="{C["green"]}">'
        f'<animate attributeName="opacity" values="1;.2;1" dur="2s" repeatCount="indefinite"/></circle>'
    )
    return svg(W, h, body, label)


if __name__ == "__main__":
    _login, out = sys.argv[1], sys.argv[2]
    write(f"{out}/header.svg", header())
    for key, (addr, label) in DIVIDERS.items():
        write(f"{out}/div-{key}.svg", divider(addr, label))
