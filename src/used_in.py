"""Curated 'Used In' lookup (data/meta_usage.json) -- see that file's _readme.

Schema: {"Card Name": [{"deck": "...", "share_pct": 0-100}, ...], ...}
"""
import json
import os

import streamlit as st

PATH = os.path.join(os.path.dirname(__file__), "..", "data", "meta_usage.json")


@st.cache_data(show_spinner=False)
def load_meta_usage() -> dict:
    with open(PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.pop("_readme", None)
    return data


def get_usage(card_name: str):
    return load_meta_usage().get(card_name)
