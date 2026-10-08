"""MITRE ATT&CK coverage: which attacker techniques my projects detect or defend against.

Sources (kept honest, update when a project gains or loses a capability):
  AEGISX      backend/app/detection/rules.py, 12 rules with MITRE IDs
  ARGUS       threat-model scenarios: Mirai-style recruitment, beaconing, MQTT abuse,
              ARP spoofing, DNS tunnelling
  StegoShield steganalysis classifier for hidden payloads in images
  CI/CD gate  Semgrep / Gitleaks / Trivy / Checkov / SCA gates that block deploys

usage: python attack.py <out.svg>
"""
import sys

from common import C, W, appear, esc, svg, write

PROJECTS = {
    "A": ("AEGISX", "https://github.com/raghavanand-prog/aegis-ai"),
    "R": ("ARGUS", "https://github.com/raghavanand-prog/Argus_IOT"),
    "S": ("StegoShield", "https://github.com/raghavanand-prog/StegoShield"),
    "P": ("CI/CD gate", "https://github.com/raghavanand-prog/PARA_CI-CD"),
}

# tactic -> [(technique id, short name, projects)]
MATRIX = [
    ("TA0007", "Discovery", [("T1046", "Network Svc Scan", "AR")]),
    ("TA0001", "Initial Access", [("T1078", "Valid Accounts", "A"), ("T1195.002", "Supply Chain", "P")]),
    ("TA0002", "Execution", [("T1059.001", "PowerShell", "A"), ("T1204.002", "Malicious File", "A")]),
    ("TA0004", "Privilege Esc", [("T1548", "Elevation Abuse", "A")]),
    ("TA0005", "Defense Evasion", [("T1027", "Obfuscation", "A"), ("T1027.003", "Steganography", "S"),
                                   ("T1218", "LOLBins", "A")]),
    ("TA0006", "Credential Access", [("T1110", "Brute Force", "AR"), ("T1003.001", "LSASS Dump", "A"),
                                     ("T1552.001", "Creds in Files", "P"), ("T1557.002", "ARP Poisoning", "R")]),
    ("TA0011", "Command & Control", [("T1071.004", "DNS C2", "AR"), ("T1572", "DNS Tunnel", "R"),
                                     ("T1105", "Tool Transfer", "A"), ("T1001.002", "Stego C2", "S")]),
    ("TA0010", "Exfiltration", [("T1041", "Exfil over C2", "A")]),
    ("TA0040", "Impact", [("T1486", "Ransomware", "A")]),
]

ROW_H = 38
TOP = 74
LABEL_W = 168
CHAR = 6.7


def chip_w(tid, name, projects):
    return (len(tid) + len(name) + 2) * CHAR + len(projects) * 15 + 18


LINE_H = 30


def place(techs):
    """Flow chips left to right, wrapping inside the row. Returns [(tech, x, line)], lines."""
    out, x, line = [], LABEL_W, 0
    for t in techs:
        w = chip_w(*t)
        if x + w > W - 18 and x > LABEL_W:
            x, line = LABEL_W, line + 1
        out.append((t, x, line, w))
        x += w + 8
    return out, line + 1


def render():
    techniques = sum(len(t) for _, _, t in MATRIX)
    layouts = [place(techs) for _, _, techs in MATRIX]
    rows_h = [max(ROW_H, lines * LINE_H + 8) for _, lines in layouts]
    h = TOP + sum(rows_h) + 52
    p = [f'<rect width="{W}" height="{h}" rx="10" fill="{C["bg"]}" stroke="{C["line"]}"/>']
    p.append(
        f'<text x="22" y="30" font-size="12" fill="{C["dim"]}">$ attack-coverage --framework mitre-enterprise '
        f'<tspan fill="{C["green"]}">→ {techniques} techniques · {len(MATRIX)} tactics · {len(PROJECTS)} projects</tspan></text>'
    )
    # project legend
    lx = 22
    for key, (name, url) in PROJECTS.items():
        p.append(
            f'<a href="{url}"><rect x="{lx}" y="44" width="15" height="15" rx="2" fill="{C["panel"]}" stroke="{C["dim"]}"/>'
            f'<text x="{lx + 7.5}" y="55.5" text-anchor="middle" font-size="10" font-weight="700" fill="{C["cyan"]}">{key}</text>'
            f'<text x="{lx + 21}" y="56" font-size="11" fill="{C["text"]}">{esc(name)}</text></a>'
        )
        lx += 21 + len(name) * CHAR + 22

    n = 0
    row_y = TOP
    for i, (ta, tactic, _techs) in enumerate(MATRIX):
        placed, _ = layouts[i]
        rh = rows_h[i]
        if i % 2 == 0:
            p.append(f'<rect x="10" y="{row_y}" width="{W - 20}" height="{rh}" fill="{C["panel"]}" opacity=".55"/>')
        p.append(f'<text x="22" y="{row_y + 17}" font-size="12" fill="{C["text"]}">{esc(tactic)}</text>')
        p.append(f'<text x="22" y="{row_y + 30}" font-size="9.5" fill="{C["dim"]}" letter-spacing=".6">{ta}</text>')
        for (tid, name, projects), x, line, w in placed:
            y = row_y + line * LINE_H
            strong = len(projects) > 1
            stroke = C["green"] if strong else C["line"]
            delay = 0.12 * n
            n += 1
            p.append(
                f'<g>{appear(delay, .3)}'
                f'<a href="https://attack.mitre.org/techniques/{tid.replace(".", "/")}/">'
                f'<rect x="{x}" y="{y + 7}" width="{w:.0f}" height="24" rx="3" fill="{C["bg"]}" stroke="{stroke}" '
                f'stroke-opacity="{1 if strong else .9}"/>'
                f'<text x="{x + 9}" y="{y + 23}" font-size="11"><tspan fill="{C["green"]}">{tid}</tspan>'
                f'<tspan dx="7" fill="{C["text"]}">{esc(name)}</tspan></text></a>'
            )
            tx = x + w - len(projects) * 15 - 4
            for k in projects:
                p.append(
                    f'<rect x="{tx:.0f}" y="{y + 12}" width="13" height="14" rx="2" fill="{C["panel"]}" stroke="{C["dim"]}" stroke-opacity=".7"/>'
                    f'<text x="{tx + 6.5:.0f}" y="{y + 22.5}" text-anchor="middle" font-size="9" font-weight="700" fill="{C["cyan"]}">{k}</text>'
                )
                tx += 15
            p.append("</g>")
        row_y += rh

    p.append(
        f'<text x="22" y="{h - 16}" font-size="10" fill="{C["dim"]}">'
        f'<tspan fill="{C["green"]}">▢</tspan> green border = covered by 2+ projects · '
        "IDs link to attack.mitre.org · mapping lives in scripts/attack.py</text>"
    )
    return svg(W, h, "\n".join(p), "MITRE ATT&CK coverage",
               "Attacker techniques my projects detect or defend against, grouped by MITRE ATT&CK tactic")


if __name__ == "__main__":
    write(sys.argv[1], render())
