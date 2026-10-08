"""Replace the RECENT block in README.md with the owner's most recently pushed repos."""
import json
import os
import re
import urllib.request

OWNER = os.environ["OWNER"]
TOKEN = os.environ["GH_TOKEN"]
LIMIT = 5

req = urllib.request.Request(
    f"https://api.github.com/users/{OWNER}/repos?sort=pushed&per_page=30",
    headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"},
)
with urllib.request.urlopen(req) as resp:
    repos = json.load(resp)

repos = [r for r in repos if not r["fork"] and not r["archived"] and r["name"] != OWNER][:LIMIT]

lines = []
for r in repos:
    desc = (r["description"] or "").strip()
    lang = r["language"] or ""
    date = r["pushed_at"][:10]
    line = f"- [**{r['name']}**]({r['html_url']})"
    if desc:
        line += f": {desc}"
    meta = " · ".join(x for x in (lang, f"updated {date}") if x)
    lines.append(f"{line} <sub>({meta})</sub>")

block = "<!--RECENT:START-->\n" + "\n".join(lines) + "\n<!--RECENT:END-->"

with open("README.md", encoding="utf-8") as f:
    readme = f.read()

updated = re.sub(r"<!--RECENT:START-->.*?<!--RECENT:END-->", block, readme, flags=re.S)

with open("README.md", "w", encoding="utf-8") as f:
    f.write(updated)
