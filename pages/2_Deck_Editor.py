import math
from collections import Counter

import streamlit as st
from streamlit_searchbox import st_searchbox

from src import banlist, card_db, deck_manager, identity, theme, ui_cards, ydk

st.set_page_config(page_title="Deck Editor — YGOh!", page_icon="🛠️", layout="wide")
theme.theme_sidebar_control()
user = identity.require_user("the Deck Editor")
st.title("🛠️ Deck Editor")

df = card_db.load_cards()
CARD_BY_ID = {int(r["id"]): r for r in df.to_dict("records")}


def unique_name(base: str) -> str:
    existing = set(deck_manager.list_decks(user))
    if base not in existing:
        return base
    i = 2
    while f"{base} ({i})" in existing:
        i += 1
    return f"{base} ({i})"


# ---- Sidebar: deck selection / creation / import ----
with st.sidebar:
    st.markdown("### Your decks")
    decks = deck_manager.list_decks(user)
    active = st.session_state.get("active_deck_name")
    if active not in decks:
        active = decks[0] if decks else None
    active = st.selectbox("Active deck", decks, index=(decks.index(active) if active in decks else 0)
                           if decks else None, key="deck_select") if decks else None
    st.session_state.active_deck_name = active

    with st.expander("➕ New deck"):
        new_name = st.text_input("Deck name", key="new_deck_name")
        new_format = ui_cards.format_picker("new_deck", label="Format")
        if st.button("Create", key="create_deck_btn") and new_name.strip():
            nm = unique_name(new_name.strip())
            d = deck_manager.new_deck(nm, new_format)
            deck_manager.save_deck(user, d)
            st.session_state.active_deck_name = nm
            st.rerun()

    if active:
        with st.expander("📋 Duplicate / rename / delete"):
            dup_name = st.text_input("Duplicate as", value=f"{active} copy", key="dup_name")
            if st.button("Duplicate", key="dup_btn"):
                src = deck_manager.load_deck(user, active)
                nm = unique_name(dup_name.strip() or f"{active} copy")
                new = deck_manager.new_deck(nm, src["format"])
                new["main"], new["extra"], new["side"] = list(src["main"]), list(src["extra"]), list(src["side"])
                deck_manager.save_deck(user, new)
                st.session_state.active_deck_name = nm
                st.rerun()

            rename_to = st.text_input("Rename to", value=active, key="rename_to")
            if st.button("Rename", key="rename_btn") and rename_to.strip() and rename_to != active:
                d = deck_manager.load_deck(user, active)
                d["name"] = unique_name(rename_to.strip())
                deck_manager.save_deck(user, d, old_name=active)
                st.session_state.active_deck_name = d["name"]
                st.rerun()

            if st.button("🗑️ Delete this deck", key="delete_btn"):
                deck_manager.delete_deck(user, active)
                deck_manager.clear_undo(active)
                st.session_state.active_deck_name = None
                st.rerun()

    with st.expander("📥 Import deck"):
        import_name = st.text_input("New deck name", key="import_name", value="Imported Deck")
        import_format = ui_cards.format_picker("import_deck", label="Format")
        pasted = st.text_area("Paste .ydk text or a ydke:// link", key="import_text", height=120)
        uploaded = st.file_uploader("...or upload a .ydk file", type=["ydk"], key="import_file")
        if st.button("Import", key="import_btn"):
            content = uploaded.read().decode("utf-8") if uploaded else pasted
            if content.strip():
                try:
                    d = ydk.parse_import(content, name=unique_name(import_name.strip() or "Imported Deck"),
                                          deck_format=import_format)
                    deck_manager.save_deck(user, d)
                    st.session_state.active_deck_name = d["name"]
                    st.success(f"Imported '{d['name']}'.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Couldn't parse that: {e}")
            else:
                st.warning("Paste some YDK/YDKE content or upload a file first.")

if not active:
    st.info("Create a deck in the sidebar to get started.")
    st.stop()

deck = deck_manager.load_deck(user, active)
fmt = deck.get("format", "Advanced Format")

top = st.columns([2, 2, 1, 1])
with top[0]:
    st.subheader(deck["name"])
with top[1]:
    new_fmt = ui_cards.format_picker(f"active_deck_{active}", label="Banlist format for this deck", default=fmt)
    if new_fmt != fmt:
        deck["format"] = new_fmt
        deck_manager.save_deck(user, deck)
        fmt = new_fmt
with top[2]:
    if st.button("↩️ Undo", disabled=not deck_manager.has_undo(active), use_container_width=True):
        prev = deck_manager.pop_undo(active)
        if prev is not None:
            deck.update(prev)
            deck_manager.save_deck(user, deck)
            st.rerun()
with top[3]:
    if st.button("🎴 Test Hand →", use_container_width=True):
        st.switch_page("pages/3_Test_Hand.py")

counts = deck_manager.deck_counts(deck)
c1, c2, c3 = st.columns(3)
c1.metric("Main", f"{counts['main']} / {deck_manager.MAIN_MIN}-{deck_manager.MAIN_MAX}")
c2.metric("Extra", f"{counts['extra']} / {deck_manager.EXTRA_MAX}")
c3.metric("Side", f"{counts['side']} / {deck_manager.SIDE_MAX}")

warnings = []
if not (deck_manager.MAIN_MIN <= counts["main"] <= deck_manager.MAIN_MAX):
    warnings.append(f"Main deck must be {deck_manager.MAIN_MIN}-{deck_manager.MAIN_MAX} cards.")
if counts["extra"] > deck_manager.EXTRA_MAX:
    warnings.append(f"Extra deck exceeds {deck_manager.EXTRA_MAX} cards.")
if counts["side"] > deck_manager.SIDE_MAX:
    warnings.append(f"Side deck exceeds {deck_manager.SIDE_MAX} cards.")
for card_id in set(deck["main"] + deck["extra"] + deck["side"]):
    card = CARD_BY_ID.get(card_id)
    if not card:
        continue
    n = deck_manager.copies_in_deck(deck, card_id)
    limit = banlist.max_copies(card["name"], fmt)
    if n > limit:
        warnings.append(f"'{card['name']}' has {n} copies but is {banlist.card_status(card['name'], fmt)} "
                         f"(max {limit}) in {fmt}.")
if warnings:
    st.error("  \n".join(f"⚠️ {w}" for w in warnings))
else:
    st.success("✅ Deck is legal for " + fmt)

st.divider()

# ---- Zone rendering ----


def remove_one(zone, card_id):
    deck_manager.push_undo(active, deck)
    deck[zone].remove(card_id)
    deck_manager.save_deck(user, deck)
    st.rerun()


def add_card(card, zone):
    deck_manager.push_undo(active, deck)
    deck[zone].append(int(card["id"]))
    deck_manager.save_deck(user, deck)
    st.toast(f"Added {card['name']} to {zone}")
    st.rerun()


def _search_names_for_add(searchterm: str):
    st.session_state["deck_add_name_live"] = searchterm
    if not searchterm:
        return []
    hits = df[df["name"].str.contains(searchterm, case=False, na=False, regex=False)]["name"]
    return hits.head(20).tolist()


def render_add_cards_tab():
    row1 = st.columns([2, 1, 1])
    with row1[0]:
        picked = st_searchbox(
            _search_names_for_add, label="Card name", placeholder="Start typing a card name...",
            key="deck_add_searchbox", clear_on_submit=False,
        )
    name_query = picked or st.session_state.get("deck_add_name_live", "")
    categories = row1[1].multiselect("Category", ["Monster", "Spell", "Trap", "Skill"], key="deck_add_cat")
    archetypes = row1[2].multiselect("Archetype", card_db.all_archetypes(), key="deck_add_arch")

    with st.expander("More filters"):
        f1 = st.columns(3)
        attributes = f1[0].multiselect("Attribute", card_db.ATTRIBUTES, key="deck_add_attr")
        ability_tags = f1[1].multiselect("Ability / summon type", card_db.ABILITY_TAGS, key="deck_add_ability")
        text_query = f1[2].text_input("Card text contains", key="deck_add_text")

    if not (name_query or categories or archetypes or attributes or ability_tags or text_query):
        st.caption("Start typing a name or pick a filter above to find cards to add.")
        return

    results = card_db.search_cards(
        df, name_query=name_query, text_query=text_query,
        categories=categories or None, archetypes=archetypes or None,
        attributes=attributes or None, ability_tags=ability_tags or None,
    ).sort_values("name")

    st.write(f"**{len(results):,}** cards match.")
    PAGE_SIZE = 28
    total_pages = max(1, math.ceil(len(results) / PAGE_SIZE))
    page = st.number_input("Page", 1, total_pages, 1, key="deck_add_page") if total_pages > 1 else 1
    page_slice = results.iloc[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]

    n_cols = 7
    cols = st.columns(n_cols)
    for i, (_, row) in enumerate(page_slice.iterrows()):
        card = row.to_dict()
        with cols[i % n_cols]:
            with st.container(border=True):
                img = card.get("image_url_small") or card.get("image_url")
                status = banlist.card_status(card["name"], fmt)
                st.markdown(ui_cards.thumbnail_html(img, status), unsafe_allow_html=True)
                st.markdown(f"<div style='font-size:0.8rem;font-weight:600'>{card['name']}</div>",
                            unsafe_allow_html=True)
                st.caption(ui_cards.monster_stat_line(card) or card["type"])
                is_extra = deck_manager.is_extra_deck_type(card["type"])
                b1, b2 = st.columns(2)
                with b1:
                    label = "➕ Extra" if is_extra else "➕ Main"
                    zone = "extra" if is_extra else "main"
                    if st.button(label, key=f"deck_add_main_{card['id']}", use_container_width=True,
                                 disabled=(status == "Forbidden")):
                        add_card(card, zone)
                with b2:
                    if st.button("➕ Side", key=f"deck_add_side_{card['id']}", use_container_width=True,
                                 disabled=(status == "Forbidden")):
                        add_card(card, "side")


def render_zone(zone_key: str, label: str):
    ids = deck[zone_key]
    if not ids:
        st.caption(f"No cards in {label} deck yet — use the '🔍 Add Cards' tab to find some.")
        return
    counter = Counter(ids)
    n_cols = 8
    cols = st.columns(n_cols)
    for i, (card_id, n) in enumerate(sorted(counter.items(), key=lambda kv: CARD_BY_ID.get(kv[0], {}).get("name", ""))):
        card = CARD_BY_ID.get(card_id)
        if not card:
            continue
        with cols[i % n_cols]:
            img = card.get("image_url_small") or card.get("image_url")
            status = banlist.card_status(card["name"], fmt)
            st.markdown(ui_cards.thumbnail_html(img, status), unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:0.8rem'><b>{card['name']}</b> ×{n}</div>",
                        unsafe_allow_html=True)
            if st.button("－ Remove one", key=f"rm_{zone_key}_{card_id}", use_container_width=True):
                remove_one(zone_key, card_id)


tabs = st.tabs(["🔍 Add Cards", "Main Deck", "Extra Deck", "Side Deck", "Export"])
with tabs[0]:
    render_add_cards_tab()
with tabs[1]:
    render_zone("main", "Main")
with tabs[2]:
    render_zone("extra", "Extra")
with tabs[3]:
    render_zone("side", "Side")
with tabs[4]:
    st.markdown("##### YDK file")
    ydk_text = ydk.deck_to_ydk(deck)
    st.download_button("⬇️ Download .ydk", ydk_text, file_name=f"{deck['name']}.ydk", mime="text/plain")
    st.code(ydk_text, language=None)

    st.markdown("##### YDKE link (pasteable, like Dueling Book)")
    link = ydk.deck_to_ydke(deck)
    st.text_input("Copy this link", value=link, key="ydke_out")
