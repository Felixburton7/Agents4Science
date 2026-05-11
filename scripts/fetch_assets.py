"""One-shot asset fetcher for the frontend demo.

Reads frontend/src/data/institutions.json, downloads each university crest to
frontend/public/badges/{id}.png. Falls back to a Clearbit logo URL, then to a
generated text-monogram PNG so the demo never breaks.

Usage:
    python scripts/fetch_assets.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.stderr.write("Pillow is required. Install with `pip install pillow`.\n")
    raise

if shutil.which("curl") is None:
    sys.stderr.write("curl is required (used for HTTPS fetches; requests gets 403'd by Wikipedia from this host).\n")
    raise SystemExit(1)


ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "frontend" / "src" / "data" / "institutions.json"
BADGES_DIR = ROOT / "frontend" / "public" / "badges"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
TIMEOUT = 15

# Canonical Wikimedia Commons filenames for university crests.
# Wikipedia's Special:FilePath endpoint follows redirects to the current file,
# so we don't have to track filename revisions (e.g. MIT_logo -> MIT_logo_2003-2023).
# Each entry may list multiple candidate filenames; we try them in order.
WIKI_FILE: dict[str, list[str]] = {
    "cambridge_uk": ["Coat_of_Arms_of_the_University_of_Cambridge.svg"],
    "mit": ["MIT_logo.svg"],
    "stanford": ["Seal_of_Leland_Stanford_Junior_University.svg"],
    "oxford": ["Oxford-University-Circlet.svg"],
    "toronto": [
        "University_of_Toronto_coat_of_arms.svg",
        "Utoronto_coa.svg",
        "University_of_Toronto_Logo.svg",
    ],
    "berkeley": ["Seal_of_University_of_California,_Berkeley.svg"],
    "eth": ["ETH_Zürich_Logo_black.svg", "ETH_Zürich-Logo.svg"],
    "tum": [
        "Logo_of_the_Technical_University_of_Munich.svg",
        "TU_München_Logo.svg",
        "Technische_Universität_München_logo.svg",
    ],
    "tsinghua": [
        "Tsinghua_University_Logo.svg",
        "Tsinghua_University_seal.svg",
    ],
    "tokyo": [
        "University_of_Tokyo_logo.svg",
        "UTokyo_Logo.svg",
        "Logo_university_of_tokyo.svg",
    ],
    "ucl": [
        "UCL_logo.svg",
        "University_College_London_logo.svg",
        "UCL_Indigo.svg",
    ],
}


def fetch(url: str) -> tuple[bytes, str] | None:
    try:
        result = subprocess.run(
            [
                "curl",
                "-sSL",
                "--max-time",
                str(TIMEOUT),
                "-A",
                USER_AGENT,
                "-H",
                "Accept: image/svg+xml,image/png,image/*",
                "-D",
                "-",  # dump headers to stdout
                "-o",
                "-",  # body to stdout too (after headers, blank-line separated)
                url,
            ],
            capture_output=True,
            timeout=TIMEOUT + 5,
        )
    except subprocess.TimeoutExpired:
        print(f"  ! curl timed out")
        return None

    if result.returncode != 0:
        print(f"  ! curl failed (rc={result.returncode}): {result.stderr.decode(errors='replace')[:200]}")
        return None

    # Split header blocks (curl -D - emits all redirect headers separated by blank lines).
    body = result.stdout
    headers_end = body.rfind(b"\r\n\r\n")
    if headers_end == -1:
        headers_end = body.rfind(b"\n\n")
    if headers_end == -1:
        return None
    header_block = body[:headers_end].decode(errors="replace")
    body_bytes = body[headers_end:].lstrip(b"\r\n")

    # Find the final HTTP status line.
    status_lines = [l for l in header_block.splitlines() if l.startswith("HTTP/")]
    if not status_lines:
        return None
    status = status_lines[-1].split()[1]
    if status != "200":
        print(f"  ! status {status}")
        return None

    ctype = ""
    for line in header_block.splitlines():
        low = line.lower()
        if low.startswith("content-type:"):
            ctype = line.split(":", 1)[1].split(";")[0].strip()
    return body_bytes, ctype


def generate_monogram(label: str, dest: Path) -> None:
    size = 240
    img = Image.new("RGBA", (size, size), (244, 244, 242, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse((6, 6, size - 6, size - 6), outline=(26, 26, 26, 255), width=2)
    monogram = "".join(part[:1] for part in label.split())[:3].upper()
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), monogram, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1]), monogram, fill=(26, 26, 26, 255), font=font)
    img.save(dest, "PNG")


def save_or_monogram(item: dict[str, Any], dest_stem: Path) -> Path:
    name = item["name"]
    iid = item["id"]
    candidates = WIKI_FILE.get(iid, [])
    for filename in candidates:
        url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{filename}"
        print(f"  -> {url}")
        result = fetch(url)
        # Polite delay to dodge upload.wikimedia.org rate limits.
        time.sleep(1.5)
        if result:
            content, ctype = result
            ext = "svg" if "svg" in ctype else "png" if "png" in ctype else "img"
            dest = dest_stem.with_suffix(f".{ext}")
            dest.write_bytes(content)
            print(f"  saved {dest.name} ({ctype}, {len(content)} bytes)")
            return dest
    print("  -> falling back to monogram")
    dest = dest_stem.with_suffix(".png")
    generate_monogram(name, dest)
    return dest


BASEMAP_DIR = ROOT / "frontend" / "public" / "basemap"
BASEMAP_FILES = {
    # Equirectangular Blue Marble — wraps onto deck.gl GlobeView.
    "blue-marble.jpg": "BlueMarble-2001-2002.jpg",
}


def fetch_basemaps() -> None:
    BASEMAP_DIR.mkdir(parents=True, exist_ok=True)
    for dest_name, wikifile in BASEMAP_FILES.items():
        dest = BASEMAP_DIR / dest_name
        if dest.exists() and dest.stat().st_size > 0 and "--force" not in sys.argv:
            print(f"= basemap/{dest_name} already present, skipping")
            continue
        url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{wikifile}"
        print(f"fetching basemap/{dest_name} <- {url}")
        result = fetch(url)
        time.sleep(1.5)
        if result is None:
            print(f"  ! failed to fetch {dest_name}")
            continue
        content, ctype = result
        dest.write_bytes(content)
        print(f"  saved {dest.name} ({ctype}, {len(content)} bytes)")


def main() -> int:
    if not DATA_FILE.exists():
        print(f"missing {DATA_FILE}", file=sys.stderr)
        return 1
    BADGES_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.loads(DATA_FILE.read_text())

    items: list[dict[str, Any]] = [payload["origin"], *payload["institutions"]]
    for item in items:
        stem = BADGES_DIR / item["id"]
        existing = [p for p in BADGES_DIR.glob(f"{item['id']}.*") if p.suffix in {".svg", ".png"}]
        if existing and existing[0].stat().st_size > 0 and "--force" not in sys.argv:
            print(f"= {item['id']} already present, skipping ({existing[0].name})")
            continue
        # Clear any stale monogram for this id before re-fetching.
        for p in existing:
            p.unlink()
        print(f"fetching {item['id']} ({item['name']})")
        save_or_monogram(item, stem)

    fetch_basemaps()

    print(f"\ndone. badges in {BADGES_DIR}, basemap in {BASEMAP_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
