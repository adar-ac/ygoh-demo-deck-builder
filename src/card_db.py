"""Loading and filtering the local YGOPRODeck card snapshot."""
import json
import os

import pandas as pd
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CARDS_PATH = os.path.join(DATA_DIR, "cards.json")

MONSTER_CARD_TYPES = [
    "Normal Monster", "Effect Monster", "Ritual Monster", "Ritual Effect Monster",
    "Fusion Monster", "Synchro Monster", "Synchro Tuner Monster",
    "Synchro Pendulum Effect Monster", "Xyz Monster", "Xyz Pendulum Effect Monster",
    "Link Monster", "Pendulum Normal Monster", "Pendulum Effect Monster",
    "Pendulum Effect Ritual Monster", "Pendulum Flip Effect Monster",
    "Pendulum Tuner Effect Monster", "Normal Tuner Monster", "Tuner Monster",
    "Flip Effect Monster", "Spirit Monster", "Toon Monster", "Union Effect Monster",
]
SPELL_TYPE = "Spell Card"
TRAP_TYPE = "Trap Card"
SKILL_TYPE = "Skill Card"

ATTRIBUTES = ["DARK", "LIGHT", "EARTH", "WATER", "FIRE", "WIND", "DIVINE"]
SPELL_RACES = ["Normal", "Field", "Equip", "Continuous", "Quick-Play", "Ritual"]
TRAP_RACES = ["Normal", "Continuous", "Counter"]

# High-level ability tags derived from the free-text `type` field.
ABILITY_TAGS = [
    "Normal", "Effect", "Ritual", "Fusion", "Synchro", "Xyz", "Pendulum",
    "Link", "Tuner", "Flip", "Spirit", "Toon", "Union",
]


def card_main_category(card_type: str) -> str:
    if card_type == SPELL_TYPE:
        return "Spell"
    if card_type == TRAP_TYPE:
        return "Trap"
    if card_type == SKILL_TYPE:
        return "Skill"
    return "Monster"


def card_ability_tags(card_type: str) -> set:
    return {tag for tag in ABILITY_TAGS if tag in card_type}


@st.cache_data(show_spinner=False)
def load_cards() -> pd.DataFrame:
    with open(CARDS_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    df = pd.DataFrame(raw)
    df["category"] = df["type"].apply(card_main_category)
    df["ability_tags"] = df["type"].apply(card_ability_tags)
    df["archetype"] = df["archetype"].fillna("")
    df["race"] = df["race"].fillna("")
    df["attribute"] = df["attribute"].fillna("")
    for col in ["atk", "def", "level", "scale", "linkval"]:
        if col not in df.columns:
            df[col] = None
    if "linkmarkers" not in df.columns:
        df["linkmarkers"] = [[] for _ in range(len(df))]
    df["linkmarkers"] = df["linkmarkers"].apply(lambda v: v if isinstance(v, list) else [])
    df["formats"] = df["formats"].apply(lambda v: v if isinstance(v, list) else [])
    df["regions"] = df["regions"].apply(lambda v: v if isinstance(v, list) else [])
    return df


@st.cache_data(show_spinner=False)
def all_archetypes() -> list:
    df = load_cards()
    vals = sorted({a for a in df["archetype"].tolist() if a})
    return vals


@st.cache_data(show_spinner=False)
def all_races(category: str) -> list:
    df = load_cards()
    vals = sorted({r for r in df[df["category"] == category]["race"].tolist() if r})
    return vals


def get_card_by_name(name: str):
    df = load_cards()
    match = df[df["name"] == name]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def get_card_by_id(card_id: int):
    df = load_cards()
    match = df[df["id"] == card_id]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def search_cards(
    df: pd.DataFrame,
    name_query: str = "",
    text_query: str = "",
    categories: list = None,
    ability_tags: list = None,
    races: list = None,
    attributes: list = None,
    archetypes: list = None,
    level_range: tuple = None,
    atk_range: tuple = None,
    def_range: tuple = None,
    scale_range: tuple = None,
    linkval_range: tuple = None,
    linkmarkers: list = None,
    regions: list = None,
    formats: list = None,
) -> pd.DataFrame:
    out = df

    if name_query:
        out = out[out["name"].str.contains(name_query, case=False, na=False, regex=False)]
    if text_query:
        out = out[out["desc"].str.contains(text_query, case=False, na=False, regex=False)]
    if categories:
        out = out[out["category"].isin(categories)]
    if ability_tags:
        wanted = set(ability_tags)
        out = out[out["ability_tags"].apply(lambda tags: wanted.issubset(tags))]
    if races:
        out = out[out["race"].isin(races)]
    if attributes:
        out = out[out["attribute"].isin(attributes)]
    if archetypes:
        out = out[out["archetype"].isin(archetypes)]
    if level_range:
        lo, hi = level_range
        out = out[out["level"].apply(lambda v: v is not None and not pd.isna(v) and lo <= v <= hi)]
    if atk_range:
        lo, hi = atk_range
        out = out[out["atk"].apply(lambda v: v is not None and not pd.isna(v) and lo <= v <= hi)]
    if def_range:
        lo, hi = def_range
        out = out[out["def"].apply(lambda v: v is not None and not pd.isna(v) and lo <= v <= hi)]
    if scale_range:
        lo, hi = scale_range
        out = out[out["scale"].apply(lambda v: v is not None and not pd.isna(v) and lo <= v <= hi)]
    if linkval_range:
        lo, hi = linkval_range
        out = out[out["linkval"].apply(lambda v: v is not None and not pd.isna(v) and lo <= v <= hi)]
    if linkmarkers:
        wanted = set(linkmarkers)
        out = out[out["linkmarkers"].apply(lambda m: wanted.issubset(set(m)))]
    if regions:
        out = out[out["regions"].apply(lambda r: any(x in r for x in regions))]
    if formats:
        out = out[out["formats"].apply(lambda f: any(x in f for x in formats))]

    return out
