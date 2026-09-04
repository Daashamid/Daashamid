#!/usr/bin/env python3
"""Render the profile's stats and language cards as self-hosted SVGs.

Reads live data from the GitHub GraphQL API (via `gh api graphql`, or GITHUB_TOKEN)
and writes assets/stats.svg + assets/langs.svg in the profile's own theme, so the
README never depends on a third-party card service.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

USER = os.environ.get("PROFILE_USER", "Daashamid")
ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

BG_A, BG_B = "#0a0e14", "#050a10"
BAR_BG, CHROME, BORDER = "#161b22", "#0d1117", "#30363d"
FG, DIM, FAINT = "#f0f6fc", "#8b949e", "#6e7681"
GREEN, CYAN, GREY = "#00ff88", "#00c8ff", "#484f58"

MONO = ('ui-monospace, "SFMono-Regular", "JetBrains Mono", "Cascadia Code", '
        'Menlo, Consolas, "DejaVu Sans Mono", monospace')

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes {
        stargazerCount
        isPrivate
        pushedAt
        languages(first: 15, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar { totalContributions }
    }
  }
}
"""


def fetch() -> dict:
    p = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={QUERY}", "-F", f"login={USER}"],
        capture_output=True, text=True,
    )
    if p.returncode != 0:
        raise RuntimeError(f"gh api graphql failed ({p.returncode}): {p.stderr.strip()}")
    payload = json.loads(p.stdout)
    if payload.get("errors"):
        raise RuntimeError(f"graphql errors: {payload['errors']}")
    return payload["data"]["user"]


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


W, H = 500, 260


def shell(uid: str, path: str, label: str, body: str) -> str:
    """Wrap card content in the shared terminal-window chrome."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" \
viewBox="0 0 {W} {H}" role="img" aria-label="{esc(label)}">
  <title>{esc(label)}</title>
  <defs>
    <linearGradient id="bg{uid}" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{BG_A}"/><stop offset="100%" stop-color="{BG_B}"/>
    </linearGradient>
    <linearGradient id="rule{uid}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{GREEN}" stop-opacity="0"/>
      <stop offset="30%" stop-color="{GREEN}" stop-opacity="0.75"/>
      <stop offset="100%" stop-color="{CYAN}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="fill{uid}" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{GREEN}"/><stop offset="100%" stop-color="{CYAN}"/>
    </linearGradient>
    <linearGradient id="chrome{uid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.05"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0.25"/>
    </linearGradient>
    <pattern id="grid{uid}" width="26" height="26" patternUnits="userSpaceOnUse">
      <path d="M26 0H0v26" fill="none" stroke="{GREEN}" stroke-opacity="0.045"/>
    </pattern>
    <clipPath id="card{uid}"><rect width="{W}" height="{H}" rx="12"/></clipPath>
  </defs>
  <style>
    /* font-size lives on the wrapping group, not here: a CSS rule would override every
       per-element font-size="…" presentation attribute and silently overflow the card.
       Keep angle brackets out of this comment — SVG is parsed as XML, not HTML. */
    .m{uid} {{ font-family: {MONO}; }}
    .ed{uid} {{ animation: ed{uid} 9s linear infinite; }}
    @keyframes ed{uid} {{
      0%   {{ transform: translateX(0) }}
      100% {{ transform: translateX({W + 200}px) }}
    }}
  </style>
  <g clip-path="url(#card{uid})">
    <rect width="{W}" height="{H}" fill="url(#bg{uid})"/>
    <rect width="{W}" height="{H}" fill="url(#grid{uid})"/>
    <rect width="{W}" height="38" fill="{CHROME}"/>
    <rect width="{W}" height="38" fill="url(#chrome{uid})"/>
    <circle cx="24" cy="19" r="5" fill="#ff5f57"/>
    <circle cx="43" cy="19" r="5" fill="#febc2e"/>
    <circle cx="62" cy="19" r="5" fill="#28c840"/>
    <text class="m{uid}" x="{W // 2}" y="24" font-size="12.5" text-anchor="middle"
          letter-spacing="0.4"><tspan fill="{DIM}">hamid@arch</tspan\
><tspan fill="{GREY}">: {esc(path)}</tspan></text>
    <path d="M0 38h{W}" stroke="{BORDER}" stroke-opacity="0.8"/>
    <path d="M0 0.5h{W}" stroke="#ffffff" stroke-opacity="0.09"/>
    <rect class="ed{uid}" x="-200" y="0" width="200" height="2" fill="url(#rule{uid})"/>
    <g class="m{uid}" letter-spacing="0.2" font-size="12.5">
{body}
    </g>
    <rect x="0" y="{H - 3}" width="{W}" height="3" fill="url(#rule{uid})"/>
  </g>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="none"
        stroke="{BORDER}" stroke-opacity="0.85"/>
</svg>
"""


def prompt(uid: str, x: int, y: int, cmd: str) -> str:
    return (f'      <text class="m{uid}" x="{x}" y="{y}">'
            f'<tspan fill="{CYAN}">hamid@arch</tspan><tspan fill="{GREY}">:~</tspan>'
            f'<tspan fill="{GREEN}">$ </tspan>'
            f'<tspan fill="{FG}">{esc(cmd)}</tspan></text>')


MONTHS = ("jan feb mar apr may jun jul aug sep oct nov dec").split()


def ago(when: datetime) -> str:
    days = (datetime.now(timezone.utc) - when).days
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 30:
        return f"{days}d ago"
    if days < 365:
        return f"{days // 30}mo ago"
    return f"{days // 365}y ago"


def stats_card(u: dict) -> str:
    uid = "s"
    repos = u["repositories"]
    nodes = repos["nodes"]
    langs = {e["node"]["name"] for r in nodes for e in r["languages"]["edges"]}
    total_bytes = sum(e["size"] for r in nodes for e in r["languages"]["edges"])
    made = datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00"))
    pushes = [datetime.fromisoformat(r["pushedAt"].replace("Z", "+00:00"))
              for r in nodes if r["pushedAt"]]
    source = (f"{total_bytes / 1_048_576:.1f} MB" if total_bytes >= 1_048_576
              else f"{total_bytes / 1024:.0f} KB")

    # "private repos" rather than followers or a 1-year commit count: it is the number
    # that actually explains a quiet public profile, and it does not read as a vanity
    # metric that goes stale the moment someone unfollows.
    rows = [
        ("repositories", repos["totalCount"], "languages", len(langs)),
        ("source indexed", source, "stars earned",
         sum(r["stargazerCount"] for r in nodes)),
        ("still private", sum(1 for r in nodes if r["isPrivate"]),
         "last push", ago(max(pushes)) if pushes else "—"),
    ]

    body = [prompt(uid, 20, 60, "./stats.sh --summary")]
    y = 92
    for la, va, lb, vb in rows:
        for x, lab, val in ((20, la, va), (270, lb, vb)):
            body.append(
                f'      <text class="m{uid}" x="{x}" y="{y}" fill="{DIM}">{esc(lab)}</text>'
                f'<text class="m{uid}" x="{x + 190}" y="{y}" fill="{GREEN}" '
                f'text-anchor="end" font-weight="600">{esc(str(val))}</text>'
            )
        body.append(f'      <path d="M20 {y + 9}h460" stroke="{BORDER}" stroke-opacity="0.45"/>')
        y += 34

    since = f"{MONTHS[made.month - 1]} {made.year}"
    fresh = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    body += [
        f'      <text class="m{uid}" x="20" y="{y + 8}" fill="{FAINT}" font-size="11.5">'
        f'since {since}</text>',
        f'      <text class="m{uid}" x="480" y="{y + 8}" fill="{GREY}" font-size="11.5" '
        f'text-anchor="end">refreshed {fresh}</text>',
        f'      <text class="m{uid}" x="20" y="{y + 34}">'
        f'<tspan fill="{CYAN}">hamid@arch</tspan><tspan fill="{GREY}">:~</tspan>'
        f'<tspan fill="{GREEN}">$ </tspan><tspan fill="{GREEN}">▌</tspan></text>',
    ]
    return shell(uid, "~/stats", f"{USER} in numbers", "\n".join(body))


TOP_N = 7


def langs_card(u: dict) -> str:
    uid = "l"
    nodes = u["repositories"]["nodes"]
    size: dict[str, int] = {}
    color: dict[str, str] = {}
    for r in nodes:
        for e in r["languages"]["edges"]:
            name = e["node"]["name"]
            size[name] = size.get(name, 0) + e["size"]
            color[name] = e["node"]["color"] or GREY
    total = sum(size.values()) or 1

    ranked = sorted(size.items(), key=lambda kv: -kv[1])
    top = ranked[:TOP_N]
    rest = sum(v for _, v in ranked[TOP_N:])
    if rest:
        top.append(("other", rest))
        color["other"] = GREY

    body = [
        prompt(uid, 20, 60, "cloc ~/repos --all"),
        f'      <text class="m{uid}" x="20" y="80" fill="{FAINT}" font-size="11">'
        f'# {len(nodes)} repos · {len(size)} languages · '
        f'{total / 1_048_576:.1f} MB indexed</text>',
    ]

    # stacked bar
    bar_x, bar_w, bar_y, bar_h = 20, 460, 96, 16
    body.append(f'      <clipPath id="bar{uid}"><rect x="{bar_x}" y="{bar_y}" '
                f'width="{bar_w}" height="{bar_h}" rx="{bar_h / 2}"/></clipPath>')
    body.append(f'      <g clip-path="url(#bar{uid})">')
    body.append(f'        <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" '
                f'height="{bar_h}" fill="{BAR_BG}"/>')
    cx = float(bar_x)
    for name, val in top:
        w = bar_w * val / total
        body.append(f'        <rect x="{cx:.2f}" y="{bar_y}" width="{w:.2f}" '
                    f'height="{bar_h}" fill="{color[name]}"/>')
        cx += w
    body.append("      </g>")
    body.append(f'      <rect x="{bar_x}.5" y="{bar_y}.5" width="{bar_w - 1}" '
                f'height="{bar_h - 1}" rx="{bar_h / 2}" fill="none" stroke="#ffffff" '
                f'stroke-opacity="0.08"/>')

    # legend, two columns
    for i, (name, val) in enumerate(top):
        col, row = divmod(i, 4)
        x = 20 + col * 238
        y = 146 + row * 24
        pct = 100 * val / total
        body += [
            f'      <circle cx="{x + 4}" cy="{y - 4}" r="4.5" fill="{color[name]}"/>',
            f'      <text class="m{uid}" x="{x + 16}" y="{y}" fill="{DIM}">{esc(name)}</text>',
            f'      <text class="m{uid}" x="{x + 212}" y="{y}" fill="{FG}" '
            f'text-anchor="end">{pct:.1f}%</text>',
        ]
    # Rust/Kotlin/Dart rank high here because AI wrote those repos. Say so on the card.
    body.append(
        f'      <text class="m{uid}" x="20" y="243" font-size="11" fill="{GREY}">'
        f'# bytes on disk, not skill — see ./progress.sh</text>')
    return shell(uid, "~/repos", "Language distribution across all repos",
                 "\n".join(body))


# Hamid's own assessment — not derived from the API, edit here to change the card.
# Deliberately not rounded up: Python is the only one he'd call solid.
SKILLS = [
    ("Python",       80, "OOP · files · bots · automation"),
    ("Linux",        45, "daily driver · bash · systemd basics"),
    ("Git / GitHub", 40, "branch · remote · actions basics"),
    ("Network+",     35, "TCP/IP · subnetting · DNS — studying"),
    ("HTML / CSS",   30, "layout · responsive basics"),
    ("C / C++",      25, "pointers · memory — university level"),
]

# Languages that show up in the language card but are not skills: those repos were
# AI-written. Saying so on the card is cheaper than being asked about it later.
NOT_MINE = "rust · kotlin · dart"
NEXT_UP = "networking depth · security basics · a little IoT"

SW, SH = 1000, 356
BAR_X, BAR_W, BAR_H = 168, 400, 12


def skills_card() -> str:
    uid = "k"
    rows = []
    y = 96
    for i, (name, pct, note) in enumerate(SKILLS):
        w = BAR_W * pct / 100
        mid = y - BAR_H / 2 - 1
        r = BAR_H / 2
        # The fill rect is static so the bar can never misrepresent the number:
        # only the shine moves, and it is clipped to the fill. The gloss overlay is
        # what makes a flat rect read as a rounded, lit tube.
        rows += [
            f'      <text class="mk" x="28" y="{y}" fill="{DIM}">{esc(name)}</text>',
            f'      <clipPath id="c{i}"><rect x="{BAR_X}" y="{mid:.1f}" '
            f'width="{w:.1f}" height="{BAR_H}" rx="{r}"/></clipPath>',
            f'      <rect x="{BAR_X}" y="{mid + 2:.1f}" width="{BAR_W}" height="{BAR_H}" '
            f'rx="{r}" fill="#000000" fill-opacity="0.45"/>',
            f'      <rect x="{BAR_X}" y="{mid:.1f}" width="{BAR_W}" height="{BAR_H}" '
            f'rx="{r}" fill="{BAR_BG}"/>',
            f'      <rect x="{BAR_X}" y="{mid:.1f}" width="{BAR_W}" height="{BAR_H}" '
            f'rx="{r}" fill="url(#trackk)"/>',
            *(f'      <path d="M{BAR_X + BAR_W * t / 100} {mid:.1f}v{BAR_H}" '
              f'stroke="#ffffff" stroke-opacity="0.05"/>' for t in (25, 50, 75)),
            f'      <rect x="{BAR_X}" y="{mid:.1f}" width="{w:.1f}" height="{BAR_H}" '
            f'rx="{r}" fill="url(#fillk)"/>',
            f'      <rect x="{BAR_X}" y="{mid:.1f}" width="{w:.1f}" height="{BAR_H}" '
            f'rx="{r}" fill="url(#glossk)"/>',
            f'      <g clip-path="url(#c{i})"><rect class="sh" x="{BAR_X - 110}" '
            f'y="{mid:.1f}" width="110" height="{BAR_H}" fill="url(#shinek)" '
            f'style="animation-delay:{0.42 * i:.2f}s"/></g>',
            f'      <text class="mk" x="{BAR_X + BAR_W + 44}" y="{y}" fill="{FG}" '
            f'text-anchor="end" font-weight="600">{pct}%</text>',
            f'      <text class="mk" x="{BAR_X + BAR_W + 76}" y="{y}" fill="{FAINT}">'
            f'{esc(note)}</text>',
        ]
        y += 34

    body = "\n".join([
        f'      <text class="mk" x="28" y="62">'
        f'<tspan fill="{CYAN}">hamid@arch</tspan><tspan fill="{GREY}">:~</tspan>'
        f'<tspan fill="{GREEN}">$ </tspan><tspan fill="{FG}">./progress.sh</tspan>'
        f'<tspan fill="{GREY}" dx="16">#</tspan>'
        f'<tspan fill="{FAINT}" dx="8">self-assessed, not rounded up</tspan></text>',
        *rows,
        f'      <path d="M28 {y - 6}h944" stroke="{BORDER}" stroke-opacity="0.5"/>',
        f'      <text class="mk" x="28" y="{y + 18}" font-size="12" fill="{GREY}">'
        f'# not on this list: <tspan fill="{FAINT}">{esc(NOT_MINE)}</tspan>'
        f' — those repos were AI-written, I can read them, not write them</text>',
        f'      <text class="mk" x="28" y="{y + 40}" font-size="12" fill="{GREY}">'
        f'# next up: <tspan fill="{FAINT}">{esc(NEXT_UP)}</tspan></text>',
    ])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{SW}" height="{SH}" \
viewBox="0 0 {SW} {SH}" role="img" aria-label="Skill levels: \
{esc(', '.join(f'{n} {p}%' for n, p, _ in SKILLS))}">
  <title>$ ./progress.sh</title>
  <defs>
    <linearGradient id="bgk" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{BG_A}"/><stop offset="100%" stop-color="{BG_B}"/>
    </linearGradient>
    <linearGradient id="fillk" gradientUnits="userSpaceOnUse"
                    x1="{BAR_X}" y1="0" x2="{BAR_X + BAR_W}" y2="0">
      <stop offset="0%" stop-color="{GREEN}"/>
      <stop offset="55%" stop-color="#00e5a0"/>
      <stop offset="100%" stop-color="{CYAN}"/>
    </linearGradient>
    <linearGradient id="rulek" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{GREEN}" stop-opacity="0"/>
      <stop offset="26%" stop-color="{GREEN}" stop-opacity="0.85"/>
      <stop offset="100%" stop-color="{CYAN}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="shinek" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="50%" stop-color="#ffffff" stop-opacity="0.42"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="trackk" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#000000" stop-opacity="0.5"/>
      <stop offset="60%" stop-color="#000000" stop-opacity="0"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0.05"/>
    </linearGradient>
    <linearGradient id="glossk" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.34"/>
      <stop offset="44%" stop-color="#ffffff" stop-opacity="0.05"/>
      <stop offset="56%" stop-color="#000000" stop-opacity="0.04"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0.3"/>
    </linearGradient>
    <pattern id="gridk" width="26" height="26" patternUnits="userSpaceOnUse">
      <path d="M26 0H0v26" fill="none" stroke="{GREEN}" stroke-opacity="0.04"/>
    </pattern>
    <linearGradient id="chromek" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.05"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0.25"/>
    </linearGradient>
    <clipPath id="cardk"><rect width="{SW}" height="{SH}" rx="14"/></clipPath>
  </defs>
  <style>
    /* see the note in shell(): font-size stays off the class so the per-element
       font-size="…" attributes on the footnote lines are not overridden */
    .mk {{ font-family: {MONO}; letter-spacing: 0.2px; }}
    .sh {{ animation: sh 5.2s ease-in-out infinite; }}
    @keyframes sh {{
      0%      {{ transform: translateX(0) }}
      55%,
      100%    {{ transform: translateX({BAR_W + 220}px) }}
    }}
    .edge {{ animation: edge 9s linear infinite; }}
    @keyframes edge {{
      0%   {{ transform: translateX(0) }}
      100% {{ transform: translateX({SW + 260}px) }}
    }}
  </style>
  <g clip-path="url(#cardk)">
    <rect width="{SW}" height="{SH}" fill="url(#bgk)"/>
    <rect width="{SW}" height="{SH}" fill="url(#gridk)"/>
    <rect width="{SW}" height="40" fill="{CHROME}"/>
    <rect width="{SW}" height="40" fill="url(#chromek)"/>
    <circle cx="28" cy="20" r="5.5" fill="#ff5f57"/>
    <circle cx="49" cy="20" r="5.5" fill="#febc2e"/>
    <circle cx="70" cy="20" r="5.5" fill="#28c840"/>
    <text class="mk" x="{SW // 2}" y="25" font-size="12.5"
          text-anchor="middle" letter-spacing="0.4"><tspan fill="{DIM}">hamid@arch</tspan\
><tspan fill="{GREY}">: ~/progress</tspan></text>
    <path d="M0 40h{SW}" stroke="{BORDER}" stroke-opacity="0.8"/>
    <path d="M0 0.5h{SW}" stroke="#ffffff" stroke-opacity="0.09"/>
    <rect class="edge" x="-260" y="0" width="260" height="2" fill="url(#rulek)"/>
    <g font-size="13">
{body}
    </g>
    <rect x="0" y="{SH - 4}" width="{SW}" height="4" fill="url(#rulek)"/>
  </g>
  <rect x="0.5" y="0.5" width="{SW - 1}" height="{SH - 1}" rx="14" fill="none"
        stroke="{BORDER}" stroke-opacity="0.85"/>
</svg>
"""


def write(name: str, svg: str) -> None:
    (ASSETS / name).write_text(svg, encoding="utf-8")
    print(f"wrote assets/{name}  ({len(svg)} bytes)")


def main() -> int:
    ASSETS.mkdir(exist_ok=True)
    write("skills.svg", skills_card())  # static data, never blocked by the API

    try:
        user = fetch()
    except Exception as exc:  # a transient API blip must not blank the cards
        print(f"warning: keeping existing stats/langs cards — {exc}", file=sys.stderr)
        missing = [n for n in ("stats.svg", "langs.svg") if not (ASSETS / n).exists()]
        return 1 if missing else 0

    write("stats.svg", stats_card(user))
    write("langs.svg", langs_card(user))
    return 0


if __name__ == "__main__":
    sys.exit(main())
