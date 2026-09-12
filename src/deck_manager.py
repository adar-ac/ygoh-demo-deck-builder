"""Deck persistence (JSON on disk, namespaced per user) + deck/zone helpers +
undo stacks. There's no password -- a visitor's typed name is just a folder
key, enough to keep friends sharing one deployed link from stepping on each
other's decks."""
import json
import os
import re

import streamlit as st

DECKS_DIR = os.path.join(os.path.dirname(__file__), "..", "decks")
os.makedirs(DECKS_DIR, exist_ok=True)

EXTRA_TAGS = ("Fusion", "Synchro", "Xyz", "Link")

MAIN_MIN, MAIN_MAX = 40, 60
EXTRA_MAX = 15
SIDE_MAX = 15


def is_extra_deck_type(card_type: str) -> bool:
    return any(tag in card_type for tag in EXTRA_TAGS)


def zone_for_type(card_type: str) -> str:
    return "extra" if is_extra_deck_type(card_type) else "main"


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", name.strip()).strip("_")
    return slug or "deck"


def _user_dir(user: str) -> str:
    path = os.path.join(DECKS_DIR, _slugify(user) or "_anonymous")
    os.makedirs(path, exist_ok=True)
    return path


def _path_for(user: str, name: str) -> str:
    return os.path.join(_user_dir(user), f"{_slugify(name)}.json")


def list_decks(user: str) -> list:
    names = []
    user_dir = _user_dir(user)
    for fname in sorted(os.listdir(user_dir)):
        if fname.endswith(".json"):
            try:
                with open(os.path.join(user_dir, fname), encoding="utf-8") as f:
                    d = json.load(f)
                names.append(d.get("name", fname[:-5]))
            except (json.JSONDecodeError, OSError):
                continue
    return names


def new_deck(name: str, deck_format: str = "Advanced Format") -> dict:
    return {"name": name, "format": deck_format, "main": [], "extra": [], "side": []}


def load_deck(user: str, name: str) -> dict | None:
    path = _path_for(user, name)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_deck(user: str, deck: dict, old_name: str | None = None) -> None:
    if old_name and _slugify(old_name) != _slugify(deck["name"]):
        old_path = _path_for(user, old_name)
        if os.path.exists(old_path):
            os.remove(old_path)
    with open(_path_for(user, deck["name"]), "w", encoding="utf-8") as f:
        json.dump(deck, f, ensure_ascii=False, indent=2)


def delete_deck(user: str, name: str) -> None:
    path = _path_for(user, name)
    if os.path.exists(path):
        os.remove(path)


def deck_counts(deck: dict) -> dict:
    return {zone: len(deck.get(zone, [])) for zone in ("main", "extra", "side")}


def copies_in_deck(deck: dict, card_id: int) -> int:
    total = 0
    for zone in ("main", "extra", "side"):
        total += deck.get(zone, []).count(card_id)
    return total


# ---- Undo stack, kept in session_state (already isolated per browser
# session/visitor by Streamlit itself), keyed by the deck's on-disk name ----

def _undo_key(deck_name: str) -> str:
    return f"undo_stack::{deck_name}"


def push_undo(deck_name: str, deck_snapshot: dict) -> None:
    key = _undo_key(deck_name)
    stack = st.session_state.setdefault(key, [])
    stack.append(json.loads(json.dumps(deck_snapshot)))
    if len(stack) > 50:
        stack.pop(0)


def pop_undo(deck_name: str) -> dict | None:
    key = _undo_key(deck_name)
    stack = st.session_state.get(key, [])
    if not stack:
        return None
    return stack.pop()


def has_undo(deck_name: str) -> bool:
    return bool(st.session_state.get(_undo_key(deck_name)))


def clear_undo(deck_name: str) -> None:
    st.session_state.pop(_undo_key(deck_name), None)
