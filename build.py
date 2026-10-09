"""Rebuild the site from the course folders.

Scans the four course folders one level up for interactive .html files,
copies them into ./explorers/ under clean names and writes ./data.js,
which index.html reads to draw the catalogue.

    python build.py        # then: git add -A && git commit -m "Update" && git push
"""
import hashlib
import html
import json
import re
import shutil
from pathlib import Path

SITE = Path(__file__).resolve().parent
ROOT = SITE.parent
OUT = SITE / "explorers"

# Edit the status here as you move through the sequence.
COURSES = [
    {"n": 1, "status": "completed", "title": "Introduction to Differential Equations"},
    {"n": 2, "status": "ongoing", "title": "2×2 Systems"},
    {"n": 3, "status": "upcoming", "title": "Linear Algebra and N×N Systems"},
    {"n": 4, "status": "upcoming", "title": "Fourier Series and Partial Differential Equations"},
]

SKIP_DIRS = {"practice exam", "images_together", "app"}

# Blurbs for pages whose opening paragraph doesn't summarise them (keyed by file stem).
DESCRIPTIONS = {
    "critical_parabola_walkthrough": "Degenerate node and star node, built up from scratch, one step at a time.",
    "phase_direction_explorer": "Which way does the phase-plane ellipse turn, and why? Drag the dot, change the damping and watch the arrows.",
    "spiral_sink_walkthrough": "A step-by-step construction of the direction field and the trajectories spiralling into the origin.",
    "recitation5_walkthrough": "The system ẋ = sin(x + y), ẏ = sin(x − y), linearized from first principles.",
    "trig_identity_mathlet": "a cos(ωt) + b sin(ωt) = A cos(ωt − φ): see how two sinusoids combine into one.",
}


def natural(s):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", s)]


def unit_label(folder):
    """'1_Unit 1_Intro to 2x2 systems' -> (1, 'Intro to 2×2 systems')."""
    m = re.match(r"^(?:(\d+)_)?(?:Unit (\d+)_)?(.+)$", folder)
    num = m.group(2) or m.group(1)
    if num is None:
        return None
    name = m.group(3).replace("_", ", ")
    name = re.sub(r"(\d)x(\d)", r"\1×\2", name).replace("FUnctions", "Functions")
    return int(num), name


def slugify(stem):
    stem = re.sub(r"\s*\(\d+\)$", "", stem)
    return re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")


def strip_tags(s):
    s = re.sub(r"<(script|style)\b.*?</\1>", " ", s, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def describe(text):
    m = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', text, re.I)
    if m:
        return html.unescape(m.group(1)).strip()
    body = re.split(r"<body\b", text, maxsplit=1, flags=re.I)[-1]
    for p in re.findall(r"<p\b[^>]*>(.*?)</p>", body, flags=re.S | re.I)[:12]:
        t = strip_tags(p)
        if len(t) >= 60 and "\\" not in t and "$" not in t:
            if len(t) > 170:
                t = t[:170].rsplit(" ", 1)[0].rstrip(",;:") + "…"
            return t
    return ""


def with_shim(raw, shim):
    """Inline the phone-width safety net just before </body>."""
    tag = b"\n<script>\n" + shim + b"</script>\n"
    i = raw.lower().rfind(b"</body>")
    return raw + tag if i < 0 else raw[:i] + tag + raw[i:]


def main():
    shim = (SITE / "mobile-shim.js").read_bytes()
    # ignore_errors: Windows won't remove a folder some other program has open
    shutil.rmtree(OUT, ignore_errors=True)
    by_hash = {}
    used = set()
    data = []

    for course in COURSES:
        cdir = next((d for d in ROOT.iterdir() if d.is_dir() and d.name.startswith(f"{course['n']}_")), None)
        units = []
        for udir in sorted((d for d in cdir.iterdir() if d.is_dir()), key=lambda d: natural(d.name)) if cdir else []:
            if udir.name.startswith(".") or udir.name.lower() in SKIP_DIRS:
                continue
            label = unit_label(udir.name)
            if not label:
                continue
            unum, uname = label
            items = []
            files = sorted(udir.rglob("*.html"), key=lambda f: natural(str(f.relative_to(udir))))
            for f in files:
                rel = f.relative_to(udir)
                if any(p.startswith(".") or p.lower() in SKIP_DIRS for p in rel.parts[:-1]):
                    continue
                raw = f.read_bytes()
                if not raw.strip():
                    continue
                text = raw.decode("utf-8", errors="replace")
                digest = hashlib.md5(raw).hexdigest()
                if digest not in by_hash:
                    slug = base = f"c{course['n']}/u{unum}/{slugify(f.stem)}"
                    i = 2
                    while slug in used:
                        slug = f"{base}-{i}"
                        i += 1
                    used.add(slug)
                    dest = OUT / f"{slug}.html"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(with_shim(raw, shim))
                    by_hash[digest] = slug
                m = re.search(r"<title>(.*?)</title>", text, re.S | re.I)
                title = strip_tags(m.group(1)) if m else f.stem.replace("_", " ").title()
                lesson = ""
                if len(rel.parts) > 1:
                    lm = re.match(r"^(\d+)_(.+)$", rel.parts[0])
                    lesson = (f"Lesson {lm.group(1)} · {lm.group(2)}" if lm else rel.parts[0]).replace("FUnctions", "Functions")
                items.append({
                    "id": f"c{course['n']}-u{unum}-{slugify(f.stem)}",
                    "title": title,
                    "desc": DESCRIPTIONS.get(re.sub(r"\s*\(\d+\)$", "", f.stem)) or describe(text),
                    "_title": title,
                    "lesson": lesson,
                    "src": f"explorers/{by_hash[digest]}.html",
                    "kb": round(len(raw) / 1024),
                })
            for it in items:   # a blurb that just repeats the title adds nothing
                if it["desc"][:18].lower() == it.pop("_title")[:18].lower():
                    it["desc"] = ""
            # Several takes on one idea share a <title>; number them.
            seen = {}
            for it in items:
                seen.setdefault(it["title"], []).append(it)
            for group in seen.values():
                if len(group) > 1:
                    for i, it in enumerate(group, 1):
                        it["title"] += f" — version {i}"
            ids = set()
            for it in items:
                while it["id"] in ids:
                    it["id"] += "-b"
                ids.add(it["id"])
            units.append({"n": unum, "name": uname, "items": items})
        data.append({**course, "units": units})

    (SITE / "data.js").write_text(
        "window.COURSES = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")

    for c in data:
        print(f"Course {c['n']} [{c['status']}] {c['title']}")
        for u in c["units"]:
            print(f"  Unit {u['n']} · {u['name']}: {len(u['items'])}")
            for it in u["items"]:
                print(f"     - {it['title']}  ->  {it['src']}")
                print(f"         {it['desc']!r}")
    print(f"\n{len(by_hash)} files copied, {sum(len(u['items']) for c in data for u in c['units'])} entries listed.")


if __name__ == "__main__":
    main()
