import math

import streamlit as st
from streamlit_searchbox import st_searchbox

from src import banlist, card_db, deck_manager, identity, theme, ui_cards

st.set_page_config(page_title="Card Search — YGOh!", page_icon="🔍", layout="wide")
theme.theme_sidebar_control()
user = identity.identity_sidebar()
st.title("🔍 Card Search")

df = card_db.load_cards()

with st.sidebar:
    st.markdown("### Format context")
    format_name = ui_cards.format_picker("search_fmt", label="Banlist format")
    st.markdown("### Add results to deck")
    if user:
        deck_names = deck_manager.list_decks(user)
        target_deck_name = st.selectbox("Target deck", ["(none)"] + deck_names, key="search_target_deck")
    else:
        st.caption("Enter your name above to add cards to a deck.")
        target_deck_name = "(none)"

def _search_names(searchterm: str):
    st.session_state["name_query_live"] = searchterm
    if not searchterm:
        return []
    hits = df[df["name"].str.contains(searchterm, case=False, na=False, regex=False)]["name"]
    return hits.head(20).tolist()


with st.expander("🔧 Filters", expanded=True):
    row1 = st.columns([2, 2])
    with row1[0]:
        picked_name = st_searchbox(
            _search_names,
            label="Card name",
            placeholder="Start typing a card name...",
            key="name_searchbox",
            clear_on_submit=False,
        )
    name_query = picked_name or st.session_state.get("name_query_live", "")
    text_query = row1[1].text_input("Card text contains")

    row2 = st.columns(4)
    categories = row2[0].multiselect("Card category", ["Monster", "Spell", "Trap", "Skill"])
    ability_tags = row2[1].multiselect(
        "Monster ability / summon type",
        card_db.ABILITY_TAGS,
        help="Normal, Effect, Ritual, Fusion, Synchro, Xyz, Pendulum, Link, Tuner, Flip, Spirit, Toon, Union",
    )
    attributes = row2[2].multiselect("Attribute", card_db.ATTRIBUTES)
    archetypes = row2[3].multiselect("Archetype", card_db.all_archetypes())

    row3 = st.columns(4)
    monster_races = card_db.all_races("Monster")
    spelltrap_races = sorted(set(card_db.SPELL_RACES) | set(card_db.TRAP_RACES))
    races = row3[0].multiselect(
        "Type / Race",
        sorted(set(monster_races) | set(spelltrap_races)),
        help="Monster Type (Dragon, Spellcaster...) or Spell/Trap subtype (Field, Equip, Quick-Play, Counter...)",
    )
    regions = row3[1].multiselect("Region availability", ["TCG", "OCG"])
    formats = row3[2].multiselect(
        "Game format legality",
        ["TCG", "OCG", "Master Duel", "Duel Links", "Speed Duel", "Common Charity"],
    )
    ban_statuses = row3[3].multiselect(
        "Banlist status (in format above)", ["Forbidden", "Limited", "Semi-Limited", "Unlimited"],
    )

    row4 = st.columns(4)
    level_range = row4[0].slider("Level / Rank", 0, 12, (0, 12))
    atk_range = row4[1].slider("ATK", 0, 5000, (0, 5000), step=50)
    def_range = row4[2].slider("DEF", 0, 5000, (0, 5000), step=50)
    scale_range = row4[3].slider("Pendulum Scale", 0, 13, (0, 13))

    row5 = st.columns(2)
    linkval_range = row5[0].slider("Link Rating", 1, 8, (1, 8))
    linkmarkers = row5[1].multiselect(
        "Link Markers (must include all selected)",
        ["Top", "Top-Left", "Top-Right", "Bottom", "Bottom-Left", "Bottom-Right", "Left", "Right"],
    )

results = card_db.search_cards(
    df,
    name_query=name_query,
    text_query=text_query,
    categories=categories or None,
    ability_tags=ability_tags or None,
    races=races or None,
    attributes=attributes or None,
    archetypes=archetypes or None,
    level_range=level_range if level_range != (0, 12) else None,
    atk_range=atk_range if atk_range != (0, 5000) else None,
    def_range=def_range if def_range != (0, 5000) else None,
    scale_range=scale_range if scale_range != (0, 13) else None,
    linkval_range=linkval_range if linkval_range != (1, 8) else None,
    linkmarkers=linkmarkers or None,
    regions=regions or None,
    formats=formats or None,
)

if ban_statuses:
    wanted = set(ban_statuses)
    results = results[results["name"].apply(lambda n: banlist.card_status(n, format_name) in wanted)]

results = results.sort_values("name")
st.write(f"**{len(results):,}** cards match.")

PAGE_SIZE = 42
total_pages = max(1, math.ceil(len(results) / PAGE_SIZE))
page = st.number_input("Page", 1, total_pages, 1) if total_pages > 1 else 1
page_slice = results.iloc[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]


def add_to_deck(card: dict, zone: str):
    if target_deck_name == "(none)":
        st.warning("Pick a target deck in the sidebar first.")
        return
    deck = deck_manager.load_deck(user, target_deck_name)
    deck_manager.push_undo(deck["name"], deck)
    deck[zone].append(int(card["id"]))
    deck_manager.save_deck(user, deck)
    st.toast(f"Added {card['name']} to {zone} of '{deck['name']}'")


N_COLS = 7
cols = st.columns(N_COLS)
for i, (_, row) in enumerate(page_slice.iterrows()):
    card = row.to_dict()
    with cols[i % N_COLS]:
        with st.container(border=True):
            img = card.get("image_url_small") or card.get("image_url")
            status = banlist.card_status(card["name"], format_name)
            st.markdown(ui_cards.thumbnail_html(img, status), unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:0.85rem;font-weight:600'>{card['name']}</div>",
                        unsafe_allow_html=True)
            st.caption(ui_cards.monster_stat_line(card) or card["type"])

            is_extra = deck_manager.is_extra_deck_type(card["type"])
            b1, b2 = st.columns(2)
            with b1:
                main_label = "➕ Extra" if is_extra else "➕ Main"
                main_zone = "extra" if is_extra else "main"
                if st.button(main_label, key=f"add_main_{card['id']}", use_container_width=True,
                             disabled=(status == "Forbidden")):
                    add_to_deck(card, main_zone)
            with b2:
                if st.button("➕ Side", key=f"add_side_{card['id']}", use_container_width=True,
                             disabled=(status == "Forbidden")):
                    add_to_deck(card, "side")

            with st.expander("Details / Used In"):
                ui_cards.render_card_detail(card, format_name)
