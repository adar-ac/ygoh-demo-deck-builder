import random
from collections import Counter

import streamlit as st

from src import card_db, deck_manager, identity, theme, ui_cards

st.set_page_config(page_title="Test Hand — YGOh!", page_icon="🎴", layout="wide")
theme.theme_sidebar_control()
user = identity.require_user("Test Hand")
st.title("🎴 Test Hand")

df = card_db.load_cards()
CARD_BY_ID = {int(r["id"]): r for r in df.to_dict("records")}

decks = deck_manager.list_decks(user)
if not decks:
    st.info("No decks yet — build one in the Deck Editor first.")
    st.stop()

with st.sidebar:
    st.markdown("### Deck")
    active = st.session_state.get("active_deck_name")
    if active not in decks:
        active = decks[0]
    active = st.selectbox("Deck to test", decks, index=decks.index(active), key="th_deck_select")
    st.session_state.active_deck_name = active

deck = deck_manager.load_deck(user, active)
TH_KEY = "test_hand_state"
th = st.session_state.get(TH_KEY)


def card(cid):
    return CARD_BY_ID.get(cid)


def image_row(ids, cols_n=8, label_counts=False):
    if not ids:
        st.caption("(empty)")
        return
    cols = st.columns(cols_n)
    items = list(Counter(ids).items()) if label_counts else [(i, 1) for i in ids]
    idx = 0
    for cid, n in items:
        c = card(cid)
        if not c:
            continue
        with cols[idx % cols_n]:
            img = c.get("image_url_small") or c.get("image_url")
            st.markdown(ui_cards.thumbnail_html(img), unsafe_allow_html=True)
            st.caption(c["name"] + (f" ×{n}" if n > 1 else ""))
        idx += 1


def start_hand(main_pool, extra_pool, side_pool):
    library = list(main_pool)
    random.shuffle(library)
    hand = library[:5]
    library = library[5:]
    st.session_state[TH_KEY] = {
        "deck_name": active,
        "test_main": list(main_pool),
        "test_extra": list(extra_pool),
        "test_side": list(side_pool),
        "library": library,
        "hand": hand,
        "siding": False,
    }


if not th or th.get("deck_name") != active:
    st.write(f"Ready to test-hand **{deck['name']}** ({len(deck['main'])} main deck cards).")
    if len(deck["main"]) < 5:
        st.warning("This deck has fewer than 5 main deck cards — add more before testing.")
    elif st.button("🔀 Draw Opening Hand (5)", type="primary"):
        start_hand(deck["main"], deck["extra"], deck["side"])
        st.rerun()
    st.stop()

th = st.session_state[TH_KEY]

if th["siding"]:
    st.subheader("🔁 Side Deck")
    st.caption(
        "Set how many copies of each card to swap. The total moving OUT to Side must equal the "
        "total moving IN from Side before you can confirm — same as real sideboarding rules. "
        "(Streamlit doesn't support real drag-and-drop, so this is the click/stepper equivalent.)"
    )

    moves_out = st.session_state.setdefault("side_moves_out", {})
    moves_in = st.session_state.setdefault("side_moves_in", {})

    def zone_mover(ids, title, moves_dict, key_prefix, move_label):
        counter = Counter(ids)
        st.markdown(f"**{title}** ({len(ids)})")
        if not counter:
            st.caption("(empty)")
            return
        with st.container(height=420, border=True):
            for cid, n in sorted(counter.items(), key=lambda kv: (card(kv[0]) or {}).get("name", "")):
                c = card(cid)
                if not c:
                    continue
                row = st.columns([1, 3, 2])
                with row[0]:
                    img = c.get("image_url_small") or c.get("image_url")
                    st.markdown(ui_cards.thumbnail_html(img, width=44, height=64), unsafe_allow_html=True)
                with row[1]:
                    st.markdown(f"<div style='font-size:0.78rem'><b>{c['name']}</b><br>have {n}</div>",
                                unsafe_allow_html=True)
                with row[2]:
                    current = moves_dict.get(cid, 0)
                    moves_dict[cid] = st.number_input(
                        move_label, min_value=0, max_value=n, value=min(current, n),
                        key=f"{key_prefix}_{cid}", label_visibility="collapsed",
                    )

    col_main, col_extra, col_side = st.columns(3)
    with col_main:
        zone_mover(th["test_main"], "Main Deck", moves_out, "mv_out_main", "Move to Side")
    with col_extra:
        zone_mover(th["test_extra"], "Extra Deck", moves_out, "mv_out_extra", "Move to Side")
    with col_side:
        zone_mover(th["test_side"], "Side Deck", moves_in, "mv_in_side", "Move to Main/Extra")

    n_out, n_in = sum(moves_out.values()), sum(moves_in.values())
    st.write(f"Moving OUT to Side: **{n_out}** — Moving IN from Side: **{n_in}**")
    can_confirm = n_out == n_in and n_out > 0

    b1, b2 = st.columns(2)
    with b1:
        if st.button("✅ Confirm", disabled=not can_confirm, type="primary", use_container_width=True):
            for cid, n in moves_out.items():
                for _ in range(n):
                    if cid in th["test_main"]:
                        th["test_main"].remove(cid)
                    elif cid in th["test_extra"]:
                        th["test_extra"].remove(cid)
                    else:
                        continue
                    th["test_side"].append(cid)
            for cid, n in moves_in.items():
                for _ in range(n):
                    if cid not in th["test_side"]:
                        continue
                    th["test_side"].remove(cid)
                    c = card(cid)
                    if c is not None and deck_manager.is_extra_deck_type(c["type"]):
                        th["test_extra"].append(cid)
                    else:
                        th["test_main"].append(cid)
            th["siding"] = False
            st.session_state["side_moves_out"] = {}
            st.session_state["side_moves_in"] = {}
            library = list(th["test_main"])
            random.shuffle(library)
            th["hand"] = library[:5]
            th["library"] = library[5:]
            st.rerun()
    with b2:
        if st.button("✖️ Cancel", use_container_width=True):
            th["siding"] = False
            st.session_state["side_moves_out"] = {}
            st.session_state["side_moves_in"] = {}
            st.rerun()
    st.stop()

st.write(f"Testing: **{deck['name']}** — Library: **{len(th['library'])}** cards left "
         f"(Side pool: {len(th['test_side'])})")

st.markdown("### Hand")
image_row(th["hand"], cols_n=5)

st.divider()
c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("🃏 Draw", use_container_width=True):
        if th["library"]:
            th["hand"].append(th["library"].pop())
        else:
            st.warning("Library is empty!")
        st.rerun()
with c2:
    if st.button("🔁 Side", use_container_width=True):
        th["siding"] = True
        st.session_state["side_moves_out"] = {}
        st.session_state["side_moves_in"] = {}
        st.rerun()
with c3:
    if st.button("🔀 Reshuffle", use_container_width=True):
        start_hand(th["test_main"], th["test_extra"], th["test_side"])
        st.rerun()
with c4:
    if st.button("⬅️ Exit to Deck Editor", use_container_width=True):
        del st.session_state[TH_KEY]
        st.switch_page("pages/2_Deck_Editor.py")
