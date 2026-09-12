"""Lightweight per-visitor identity: no passwords, just a name that scopes
which decks you see. The name round-trips through the URL's ?user= query
param so bookmarking the page brings you back as yourself."""
import streamlit as st

QUERY_KEY = "user"


def _clean(name: str) -> str:
    return name.strip()[:40]


def get_current_user() -> str:
    if st.session_state.get("user_name"):
        return st.session_state.user_name
    q = st.query_params.get(QUERY_KEY)
    if q:
        st.session_state.user_name = _clean(q)
        return st.session_state.user_name
    return ""


def set_current_user(name: str) -> None:
    name = _clean(name)
    st.session_state.user_name = name
    st.query_params[QUERY_KEY] = name


def sign_out() -> None:
    st.session_state.pop("user_name", None)
    if QUERY_KEY in st.query_params:
        del st.query_params[QUERY_KEY]


def identity_sidebar() -> str:
    """Render the name gate / switcher in the sidebar on every page.
    Returns the current user's name, or "" if none has been set yet."""
    user = get_current_user()
    with st.sidebar:
        st.markdown("#### 👤 Who's playing?")
        if user:
            st.caption(f"Signed in as **{user}**. Bookmark this URL to come back as {user}.")
            with st.expander("Switch name"):
                new_name = st.text_input("Type a different name", key="switch_name_input")
                if st.button("Switch", key="switch_name_btn") and new_name.strip():
                    set_current_user(new_name)
                    st.rerun()
        else:
            st.text_input("Enter your name to see your own decks", key="name_gate_input")
            if st.button("Continue", key="name_gate_btn"):
                typed = st.session_state.get("name_gate_input", "")
                if typed.strip():
                    set_current_user(typed)
                    st.rerun()
    return user


def require_user(page_label: str = "this page") -> str:
    """Call at the top of a personal page (Deck Editor, Test Hand). Renders
    the gate and halts the page with st.stop() until a name is set."""
    user = identity_sidebar()
    if not user:
        st.info(f"Enter your name in the sidebar to use {page_label}.")
        st.stop()
    return user
