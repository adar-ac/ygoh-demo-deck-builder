import streamlit as st

from src import banlist, card_db, deck_manager, identity, theme

st.set_page_config(
    page_title="YGO Demo Deck Builder",
    page_icon="🃏",
    layout="wide",
    initial_sidebar_state="expanded",
)

theme.theme_sidebar_control()
user = identity.identity_sidebar()

st.title("🃏 Yu-Gi-Oh! Demo Deck Builder")
st.caption(
    "A deck-building sandbox: search every TCG/OCG card, build decks under dozens of "
    "banlists (from the very first list in 1999 through today), and playtest opening hands."
)

with st.spinner("Loading card database..."):
    df = card_db.load_cards()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Cards in database", f"{len(df):,}")
col2.metric("Your saved decks", len(deck_manager.list_decks(user)) if user else "—")
col3.metric("Banlist formats", len(banlist.format_list()))
col4.metric("Archetypes indexed", len(card_db.all_archetypes()))

st.markdown("---")
st.markdown(
    """
### Get started
- **🔍 Card Search** — browse and filter the full card pool (type, attribute, level/rank, link
  arrows, Pendulum scale, archetype, banlist status, and more), and see what decks a card is
  typically used in.
- **🛠️ Deck Editor** — build, save, rename, and switch between as many decks as you like, with
  full undo, YDK / YDKE import-export, and shareable deck links.
- **🎴 Test Hand** — shuffle a 5-card opening hand from any saved deck, draw, side-deck between
  games, and reshuffle whenever you like.

Use the sidebar to navigate between pages. Enter your name in the sidebar first — that's what
keeps your decks separate from anyone else using this same site.
"""
)

if not user:
    st.info("Enter your name in the sidebar to start building your own decks.")
elif st.session_state.get("active_deck_name"):
    st.info(f"Active deck: **{st.session_state.active_deck_name}**")
