"""Shared card-grid / card-detail rendering helpers for the Streamlit pages."""
import streamlit as st

from src import banlist, card_db, used_in

BADGE_CLASS = {
    "Forbidden": "ygo-badge-forbidden",
    "Limited": "ygo-badge-limited",
    "Semi-Limited": "ygo-badge-semi",
    "Unlimited": "ygo-badge-unlimited",
}


def status_badge_html(status: str) -> str:
    cls = BADGE_CLASS.get(status, "ygo-badge-unlimited")
    return f'<span class="ygo-badge {cls}">{status}</span>'


# Fixed thumbnail box (matches the ~0.685 aspect ratio of a real card scan).
THUMB_W, THUMB_H = 120, 175


def banlist_icon_html(status: str, size: int = 22) -> str:
    """A small Master-Duel/YGOPRODeck-style corner icon: red circle with '1'
    (Limited), '2' (Semi-Limited), or a prohibition slash (Forbidden). Empty
    for Unlimited -- unrestricted cards don't get a badge."""
    if status == "Limited":
        inner = f'<span style="color:#fff;font-weight:800;font-size:{size*0.6:.0f}px;line-height:1;">1</span>'
    elif status == "Semi-Limited":
        inner = f'<span style="color:#fff;font-weight:800;font-size:{size*0.6:.0f}px;line-height:1;">2</span>'
    elif status == "Forbidden":
        inner = (
            f'<svg width="{size*0.62:.0f}" height="{size*0.62:.0f}" viewBox="0 0 22 22">'
            f'<line x1="4" y1="18" x2="18" y2="4" stroke="#fff" stroke-width="3" stroke-linecap="round"/></svg>'
        )
    else:
        return ""
    return (
        f'<div style="position:absolute;top:3px;left:3px;width:{size}px;height:{size}px;border-radius:50%;'
        f'background:#d81e2c;border:2px solid #fff;display:flex;align-items:center;justify-content:center;'
        f'box-shadow:0 1px 4px rgba(0,0,0,.7);z-index:2;">{inner}</div>'
    )


def thumbnail_html(image_url: str, status: str = None, width: int = THUMB_W, height: int = THUMB_H) -> str:
    """A fixed-size card thumbnail (every card renders at the same box size,
    regardless of the source scan's native resolution/aspect ratio), with an
    optional banlist-status corner icon overlaid on top."""
    badge = banlist_icon_html(status) if status else ""
    img = f'<img src="{image_url}" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block;"/>' \
        if image_url else ""
    return (
        f'<div style="position:relative;width:{width}px;max-width:100%;margin:0 auto;">'
        f'<div style="width:100%;aspect-ratio:{width}/{height};overflow:hidden;border-radius:8px;'
        f'background:#141018;border:1px solid #333;">{img}</div>{badge}</div>'
    )


def format_picker(key_prefix: str, label: str = "Banlist format", default: str = None) -> str:
    """Two-tier format selector: a handful of curated named formats front and
    center, with the full 65-entry chronological TCG archive tucked behind a
    toggle so the common case stays a short, sane dropdown."""
    named = list(banlist.FORMATS.keys())
    archive = list(banlist.load_archive_entries().keys())
    default = default if default in named or default in archive else named[-1]
    is_archive_default = default in archive and default not in named

    tab_key = f"{key_prefix}_fmt_tab"
    if tab_key not in st.session_state:
        st.session_state[tab_key] = "Full Archive by Date" if is_archive_default else "Popular Formats"

    st.caption(label)
    tab = st.radio(
        label, ["Popular Formats", "Full Archive by Date"], key=tab_key,
        horizontal=True, label_visibility="collapsed",
    )
    if tab == "Popular Formats":
        idx = named.index(default) if default in named else len(named) - 1
        return st.selectbox("Format", named, index=idx, key=f"{key_prefix}_named_select",
                             label_visibility="collapsed")
    idx = archive.index(default) if default in archive else 0
    return st.selectbox("Archive date", archive, index=idx, key=f"{key_prefix}_archive_select",
                         label_visibility="collapsed")


def monster_stat_line(card: dict) -> str:
    bits = []
    if card.get("attribute"):
        bits.append(str(card["attribute"]))
    if card.get("race"):
        bits.append(str(card["race"]))
    if card.get("linkval") not in (None, "") and not (isinstance(card.get("linkval"), float) and card["linkval"] != card["linkval"]):
        bits.append(f"LINK-{int(card['linkval'])}")
    elif card.get("level") not in (None, "") and not (isinstance(card.get("level"), float) and card["level"] != card["level"]):
        tag = "Rank" if "Xyz" in card.get("type", "") else "Level"
        bits.append(f"{tag} {int(card['level'])}")
    if card.get("atk") is not None and card["atk"] == card["atk"]:
        atk = int(card["atk"])
        defn = card.get("def")
        def_str = "?" if defn is None or defn != defn else int(defn)
        bits.append(f"ATK {atk} / DEF {def_str}")
    return " | ".join(bits)


def render_grid(cards: list, format_name: str, key_prefix: str, columns: int = 5,
                 select_key: str = "selected_card_id", add_callback=None, add_label: str = "➕ Add"):
    """Render a responsive grid of card thumbnails. `cards` is a list of dict-like rows."""
    if not cards:
        st.info("No cards match the current filters.")
        return

    cols = st.columns(columns)
    for i, card in enumerate(cards):
        col = cols[i % columns]
        with col:
            img = card.get("image_url_small") or card.get("image_url")
            status = banlist.card_status(card["name"], format_name)
            st.markdown(thumbnail_html(img, status), unsafe_allow_html=True)
            st.markdown(f"**{card['name']}**")

            b1, b2 = st.columns(2)
            with b1:
                if st.button("Details", key=f"{key_prefix}_detail_{card['id']}_{i}", use_container_width=True):
                    st.session_state[select_key] = int(card["id"])
                    st.rerun()
            with b2:
                if add_callback and status != "Forbidden":
                    if st.button(add_label, key=f"{key_prefix}_add_{card['id']}_{i}", use_container_width=True):
                        add_callback(card)
                elif add_callback and status == "Forbidden":
                    st.button("🚫 Banned", key=f"{key_prefix}_banned_{card['id']}_{i}", use_container_width=True, disabled=True)


def render_card_detail(card: dict, format_name: str):
    c1, c2 = st.columns([1, 2])
    with c1:
        img = card.get("image_url")
        if img:
            st.image(img, use_container_width=True)
    with c2:
        st.markdown(f"## {card['name']}")
        st.caption(card.get("type", ""))
        st.write(monster_stat_line(card))
        if card.get("archetype"):
            st.write(f"**Archetype:** {card['archetype']}")
        st.write(f"**Regions:** {', '.join(card.get('regions', []) or [])}")
        st.write(f"**Formats:** {', '.join(card.get('formats', []) or [])}")

        st.markdown("#### Banlist status by format")
        named_formats = list(banlist.FORMATS.keys())
        status_cols = st.columns(len(named_formats))
        for sc, fmt in zip(status_cols, named_formats):
            with sc:
                st.markdown(f"**{fmt}**")
                st.markdown(status_badge_html(banlist.card_status(card["name"], fmt)), unsafe_allow_html=True)

        with st.expander("Status in the full historical archive (65 more dates)"):
            archive_fmt = st.selectbox(
                "Archive date", list(banlist.load_archive_entries().keys()),
                key=f"detail_archive_fmt_{card['id']}",
            )
            st.markdown(status_badge_html(banlist.card_status(card["name"], archive_fmt)),
                        unsafe_allow_html=True)

        st.markdown("#### Card text")
        st.write(card.get("desc", ""))

        usage = used_in.get_usage(card["name"])
        with st.expander("📊 Used In — common decks for this card", expanded=False):
            if usage:
                for entry in usage:
                    st.progress(min(entry["share_pct"], 100) / 100, text=f"{entry['deck']} — ~{entry['share_pct']}% of sampled decks")
                st.caption("Illustrative usage estimates compiled from general TCG meta trends — not live tournament data.")
            elif card.get("archetype"):
                st.write(f"No detailed usage stats yet, but this card belongs to the **{card['archetype']}** archetype.")
            else:
                st.write("No usage data available for this card yet.")
