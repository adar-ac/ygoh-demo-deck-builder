"""
One-time (re-runnable) data fetch: downloads the full YGOPRODeck card database
and trims it down to the fields the app actually needs, saved to data/cards.json.

Run with:  python scripts/fetch_cards.py
"""
import json
import os
import sys
import time
import urllib.request

API_URL = "https://db.ygoprodeck.com/api/v7/cardinfo.php?misc=yes"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cards.json")

KEEP_FIELDS = [
    "id", "name", "type", "frameType", "desc", "race", "archetype",
    "atk", "def", "level", "attribute", "scale", "linkval", "linkmarkers",
    "ygoprodeck_url",
]


def trim_card(card):
    out = {k: card[k] for k in KEEP_FIELDS if k in card}

    images = card.get("card_images") or []
    if images:
        out["image_url"] = images[0].get("image_url")
        out["image_url_small"] = images[0].get("image_url_small")
        out["image_url_cropped"] = images[0].get("image_url_cropped")

    misc = (card.get("misc_info") or [{}])[0]
    out["formats"] = misc.get("formats", [])
    out["tcg_date"] = misc.get("tcg_date")
    out["ocg_date"] = misc.get("ocg_date")
    out["konami_id"] = misc.get("konami_id")

    sets = card.get("card_sets") or []
    regions = set()
    for s in sets:
        code = s.get("set_code", "")
        if "-JP" in code:
            regions.add("OCG")
        elif any(tag in code for tag in ("-EN", "-NA", "-FR", "-DE", "-IT", "-SP", "-PT")):
            regions.add("TCG")
    if not regions:
        # fall back on format list: if it ever had a TCG/OCG release date, tag it
        if out.get("tcg_date"):
            regions.add("TCG")
        if out.get("ocg_date"):
            regions.add("OCG")
    out["regions"] = sorted(regions) if regions else ["TCG", "OCG"]

    return out


def main():
    print(f"Fetching {API_URL} ...")
    req = urllib.request.Request(API_URL, headers={"User-Agent": "ygoh-demo-site/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    cards = payload.get("data", [])
    print(f"Fetched {len(cards)} cards. Trimming...")

    trimmed = [trim_card(c) for c in cards]

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(trimmed, f, ensure_ascii=False)

    size_mb = os.path.getsize(OUT_PATH) / (1024 * 1024)
    print(f"Wrote {len(trimmed)} cards to {OUT_PATH} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    sys.exit(main())
