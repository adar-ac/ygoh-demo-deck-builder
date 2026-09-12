"""Import/export decks as .ydk files, YDKE links, and shareable base64 links."""
import base64
import struct


def deck_to_ydk(deck: dict) -> str:
    lines = [f"#created by YGO Demo Deck Builder - {deck.get('name', 'deck')}", "#main"]
    lines += [str(cid) for cid in deck.get("main", [])]
    lines.append("#extra")
    lines += [str(cid) for cid in deck.get("extra", [])]
    lines.append("!side")
    lines += [str(cid) for cid in deck.get("side", [])]
    return "\n".join(lines) + "\n"


def ydk_to_deck(text: str, name: str = "Imported Deck", deck_format: str = "Advanced Format") -> dict:
    main, extra, side = [], [], []
    target = main
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#main"):
            target = main
            continue
        if line.startswith("#extra"):
            target = extra
            continue
        if line.startswith("!side"):
            target = side
            continue
        if line.startswith("#"):
            continue
        if line.isdigit():
            target.append(int(line))
    return {"name": name, "format": deck_format, "main": main, "extra": extra, "side": side}


def _ids_to_b64(ids: list) -> str:
    packed = b"".join(struct.pack("<I", cid) for cid in ids)
    return base64.b64encode(packed).decode("ascii")


def _b64_to_ids(b64: str) -> list:
    if not b64:
        return []
    padded = b64 + "=" * (-len(b64) % 4)
    raw = base64.b64decode(padded)
    count = len(raw) // 4
    return list(struct.unpack(f"<{count}I", raw[: count * 4]))


def deck_to_ydke(deck: dict) -> str:
    main_b64 = _ids_to_b64(deck.get("main", []))
    extra_b64 = _ids_to_b64(deck.get("extra", []))
    side_b64 = _ids_to_b64(deck.get("side", []))
    return f"ydke://{main_b64}!{extra_b64}!{side_b64}!"


def ydke_to_deck(link: str, name: str = "Imported Deck", deck_format: str = "Advanced Format") -> dict:
    link = link.strip()
    if link.startswith("ydke://"):
        link = link[len("ydke://"):]
    parts = link.split("!")
    parts += [""] * (3 - len(parts))
    main = _b64_to_ids(parts[0])
    extra = _b64_to_ids(parts[1])
    side = _b64_to_ids(parts[2])
    return {"name": name, "format": deck_format, "main": main, "extra": extra, "side": side}


def parse_import(text: str, name: str = "Imported Deck", deck_format: str = "Advanced Format") -> dict:
    """Auto-detect YDK vs YDKE-link content and parse accordingly."""
    stripped = text.strip()
    if stripped.startswith("ydke://"):
        return ydke_to_deck(stripped, name, deck_format)
    return ydk_to_deck(stripped, name, deck_format)
