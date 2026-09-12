"""Loading and querying the format banlists (data/banlists/*.json)."""
import json
import os

import streamlit as st

BANLIST_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "banlists")
ARCHIVE_PATH = os.path.join(BANLIST_DIR, "tcg_archive.json")

# Named, curated retro/community formats, in chronological order.
FORMATS = {
    "GOAT Format (2005)": "goat2005.json",
    "Reaper Format (2005)": "reaper2005.json",
    "TeleDAD Format (2008)": "teledad2008.json",
    "Edison Format (2010)": "edison2010.json",
    "Tengu Plant Format (2011)": "tenguplant2011.json",
    "Wind-Up Format (2012)": "windup2012.json",
    "HAT Format (2014)": "hat2014.json",
    "Advanced Format": "advanced.json",
}

STATUS_LIMIT = {"Forbidden": 0, "Limited": 1, "Semi-Limited": 2, "Unlimited": 3}


def normalize_name(name: str) -> str:
    """Fold away the case/punctuation drift between banlist sources (often ALL
    CAPS, en-dashes, curly quotes) and the card database's display names."""
    if not name:
        return ""
    n = name.strip().casefold()
    n = n.replace("–", "-").replace("—", "-")
    n = n.replace("’", "'").replace("‘", "'")
    n = n.replace("“", '"').replace("”", '"')
    n = " ".join(n.split())
    return n


@st.cache_data(show_spinner=False)
def load_archive_entries() -> dict:
    """Every other official TCG banlist date (data/banlists/tcg_archive.json),
    keyed by its display format_name -- everything not curated into FORMATS."""
    if not os.path.exists(ARCHIVE_PATH):
        return {}
    with open(ARCHIVE_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return {e["format_name"]: e for e in data.get("entries", [])}


@st.cache_data(show_spinner=False)
def load_banlist(format_name: str) -> dict:
    fname = FORMATS.get(format_name)
    if fname:
        path = os.path.join(BANLIST_DIR, fname)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    archive_entry = load_archive_entries().get(format_name)
    if archive_entry:
        return archive_entry
    return {"format_name": format_name, "forbidden": [], "limited": [], "semi_limited": []}


@st.cache_data(show_spinner=False)
def status_map(format_name: str) -> dict:
    """normalized card name -> status string, for every non-Unlimited card."""
    data = load_banlist(format_name)
    m = {}
    for name in data.get("forbidden", []):
        m[normalize_name(name)] = "Forbidden"
    for name in data.get("limited", []):
        m[normalize_name(name)] = "Limited"
    for name in data.get("semi_limited", []):
        m[normalize_name(name)] = "Semi-Limited"
    return m


def card_status(card_name: str, format_name: str) -> str:
    return status_map(format_name).get(normalize_name(card_name), "Unlimited")


def max_copies(card_name: str, format_name: str) -> int:
    return STATUS_LIMIT[card_status(card_name, format_name)]


def format_list() -> list:
    """Named/curated formats first, then every other official TCG banlist date."""
    archive_names = list(load_archive_entries().keys())
    return list(FORMATS.keys()) + archive_names
