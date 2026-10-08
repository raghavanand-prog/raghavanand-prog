"""Threat intel feed: the newest entries in CISA's Known Exploited Vulnerabilities catalog.

usage: python threatintel.py <out.svg>
"""
import json
import sys
import urllib.request

from common import C, W, appear, esc, now_utc, svg, write

SOURCES = [
    "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
    "https://raw.githubusercontent.com/cisagov/kev-data/develop/known_exploited_vulnerabilities.json",
]
ROWS = 7


def fetch():
    last = None
    for url in SOURCES:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "profile-threat-intel"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:  # try the mirror
            last = e
    raise RuntimeError(f"KEV feed unavailable: {last}")


def clip(s, n):
    return s if len(s) <= n else s[: n - 1] + "…"


def render(kev):
    vulns = sorted(kev["vulnerabilities"], key=lambda v: (v["dateAdded"], v["cveID"]), reverse=True)[:ROWS]
    h = 92 + ROWS * 34 + 30
    p = [
        f'<rect width="{W}" height="{h}" rx="12" fill="{C["bg"]}" stroke="{C["line"]}"/>',
        f'<text x="22" y="30" font-size="12" fill="{C["dim"]}"><tspan fill="{C["red"]}">●</tspan> '
        f'CISA KEV · {kev["count"]:,} known exploited CVEs tracked · synced {now_utc()}</text>',
    ]
    cols = [(22, "ADDED"), (122, "CVE"), (268, "VENDOR / PRODUCT"), (508, "VULNERABILITY"), (W - 22, "RANSOMWARE")]
    for x, label in cols:
        anchor = "end" if label == "RANSOMWARE" else "start"
        p.append(f'<text x="{x}" y="62" text-anchor="{anchor}" font-size="10" fill="{C["dim"]}" letter-spacing=".8">{label}</text>')
    p.append(f'<line x1="22" y1="72" x2="{W - 22}" y2="72" stroke="{C["line"]}"/>')

    for i, v in enumerate(vulns):
        y = 98 + i * 34
        ransom = v.get("knownRansomwareCampaignUse", "").lower() == "known"
        sev = C["red"] if ransom else C["amber"]
        p.append(f'<g>{appear(0.2 + i * 0.18)}')
        if i % 2 == 0:
            p.append(f'<rect x="14" y="{y - 21}" width="{W - 28}" height="32" rx="5" fill="{C["panel"]}"/>')
        p.append(f'<rect x="14" y="{y - 21}" width="3" height="32" rx="1.5" fill="{sev}"/>')
        p.append(f'<text x="22" y="{y}" font-size="12" fill="{C["dim"]}">{esc(v["dateAdded"])}</text>')
        p.append(
            f'<a href="https://nvd.nist.gov/vuln/detail/{esc(v["cveID"])}"><text x="122" y="{y}" font-size="12" '
            f'font-weight="700" fill="{C["cyan"]}">{esc(v["cveID"])}</text></a>'
        )
        p.append(f'<text x="268" y="{y}" font-size="12" fill="{C["text"]}">{esc(clip(v["vendorProject"] + " " + v["product"], 30))}</text>')
        p.append(f'<text x="508" y="{y}" font-size="12" fill="{C["text"]}">{esc(clip(v["vulnerabilityName"], 36))}</text>')
        p.append(
            f'<text x="{W - 22}" y="{y}" text-anchor="end" font-size="11" fill="{sev}">'
            f'{"⚠ KNOWN" if ransom else "unknown"}</text></g>'
        )

    p.append(
        f'<text x="{W - 22}" y="{h - 14}" text-anchor="end" font-size="10" fill="{C["dim"]}">'
        "source: cisa.gov/known-exploited-vulnerabilities-catalog · rendered by scripts/threatintel.py</text>"
    )
    return svg(W, h, "\n".join(p), "Threat intel feed",
               "The newest vulnerabilities added to CISA's Known Exploited Vulnerabilities catalog")


if __name__ == "__main__":
    write(sys.argv[1], render(fetch()))
