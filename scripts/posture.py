"""Security posture scorecard: audits each of my repos against basic hygiene checks.

usage: python posture.py <login> <out.svg>
"""
import sys
import urllib.error

from common import C, W, esc, own_repos, rest, svg, write

CHECKS = ["README", "LICENSE", "SECURITY", "DEPENDABOT", "CI", "ABOUT"]
GRADES = [(6, "A", C["green"]), (5, "B", C["green"]), (4, "C", C["amber"]), (3, "D", C["amber"]), (0, "F", C["red"])]


def exists(path):
    try:
        rest(path)
        return True
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        raise


def audit(login, repo):
    base = f"/repos/{login}/{repo['name']}"
    return {
        "README": exists(f"{base}/readme"),
        "LICENSE": repo.get("license") is not None,
        "SECURITY": any(exists(f"{base}/contents/{p}") for p in ("SECURITY.md", ".github/SECURITY.md")),
        "DEPENDABOT": any(exists(f"{base}/contents/.github/{p}") for p in ("dependabot.yml", "dependabot.yaml")),
        "CI": exists(f"{base}/contents/.github/workflows"),
        "ABOUT": bool(repo.get("description")) and bool(repo.get("topics")),
    }


def grade(score):
    for floor, letter, col in GRADES:
        if score >= floor:
            return letter, col


def render(rows):
    row_h = 26
    h = 96 + len(rows) * row_h + 40
    name_x, check_x0, check_dx = 22, 270, 82
    grade_x = W - 40
    p = [f'<rect width="{W}" height="{h}" rx="12" fill="{C["bg"]}" stroke="{C["line"]}"/>']

    total = sum(sum(r["checks"].values()) for r in rows)
    possible = len(rows) * len(CHECKS) or 1
    pct = 100 * total / possible
    p.append(
        f'<text x="22" y="30" font-size="12" fill="{C["dim"]}">$ ./audit --all-repos '
        f'<tspan fill="{C["green"] if pct >= 70 else C["amber"] if pct >= 40 else C["red"]}">→ overall hygiene {pct:.0f}%</tspan>'
        f'<tspan dx="10">({total}/{possible} controls passing)</tspan></text>'
    )
    # overall progress bar
    p.append(f'<rect x="22" y="42" width="{W - 44}" height="6" rx="3" fill="{C["panel"]}"/>')
    p.append(
        f'<rect x="22" y="42" width="{(W - 44) * pct / 100:.1f}" height="6" rx="3" fill="{C["green"]}">'
        f'<animate attributeName="width" from="0" to="{(W - 44) * pct / 100:.1f}" dur="1.2s" fill="freeze"/></rect>'
    )

    hy = 78
    p.append(f'<text x="{name_x}" y="{hy}" font-size="10" fill="{C["dim"]}" letter-spacing=".8">REPOSITORY</text>')
    for j, c in enumerate(CHECKS):
        p.append(f'<text x="{check_x0 + j * check_dx}" y="{hy}" text-anchor="middle" font-size="10" fill="{C["dim"]}" letter-spacing=".8">{c}</text>')
    p.append(f'<text x="{grade_x}" y="{hy}" text-anchor="middle" font-size="10" fill="{C["dim"]}" letter-spacing=".8">GRADE</text>')

    for i, r in enumerate(rows):
        y = 104 + i * row_h
        if i % 2 == 0:
            p.append(f'<rect x="14" y="{y - 17}" width="{W - 28}" height="{row_h - 2}" rx="4" fill="{C["panel"]}"/>')
        p.append(
            f'<a href="{esc(r["url"])}"><text x="{name_x}" y="{y}" font-size="12" fill="{C["text"]}">{esc(r["name"][:28])}</text></a>'
        )
        for j, c in enumerate(CHECKS):
            ok = r["checks"][c]
            cx = check_x0 + j * check_dx
            if ok:
                p.append(f'<text x="{cx}" y="{y}" text-anchor="middle" font-size="13" fill="{C["green"]}">✔</text>')
            else:
                p.append(f'<text x="{cx}" y="{y}" text-anchor="middle" font-size="13" fill="{C["red"]}" opacity=".75">✘</text>')
        letter, col = grade(sum(r["checks"].values()))
        p.append(
            f'<rect x="{grade_x - 13}" y="{y - 14}" width="26" height="19" rx="4" fill="{col}" fill-opacity=".15" stroke="{col}" stroke-opacity=".6"/>'
            f'<text x="{grade_x}" y="{y}" text-anchor="middle" font-size="12" font-weight="700" fill="{col}">{letter}</text>'
        )

    p.append(
        f'<text x="22" y="{h - 14}" font-size="10" fill="{C["dim"]}">'
        "SECURITY = SECURITY.md policy · DEPENDABOT = automated dependency updates · CI = GitHub Actions · ABOUT = description + topics</text>"
    )
    return svg(W, h, "\n".join(p), "Security posture",
               "Hygiene audit of each repo: README, license, security policy, Dependabot, CI and description, graded A to F")


if __name__ == "__main__":
    login, out = sys.argv[1], sys.argv[2]
    repos = own_repos(login)
    rows = [{"name": r["name"], "url": r["html_url"], "checks": audit(login, r)} for r in repos]
    rows.sort(key=lambda r: (-sum(r["checks"].values()), r["name"].lower()))
    write(out, render(rows))
