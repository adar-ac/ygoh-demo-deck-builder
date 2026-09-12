"""Site-wide visual theme: a real color-wheel picker (native browser color
input -- drag anywhere, updates live) drives every accent color on the site."""
import colorsys
import json
import os
import textwrap

import streamlit as st

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", ".streamlit", "user_theme.json")
DEFAULT_COLOR = "#B026FF"  # neon purple


def hex_to_hls(hex_color: str):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, l * 100, s * 100


def hls_to_hex(h: float, l: float, s: float) -> str:
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, max(0, min(l, 100)) / 100, max(0, min(s, 100)) / 100)
    return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def load_saved_color() -> str:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
            return data.get("color", DEFAULT_COLOR)
    except (OSError, json.JSONDecodeError, ValueError):
        return DEFAULT_COLOR


def save_color(color: str) -> None:
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"color": color}, f)


def palette(accent: str) -> dict:
    h, l, s = hex_to_hls(accent)
    return {
        "accent": accent,
        "accent_bright": hls_to_hex(h, min(l + 20, 88), min(s + 5, 100)),
        "accent_dim": hls_to_hex(h, max(l - 26, 10), s),
        "accent_bg": hls_to_hex(h, 9, min(s, 65)),
        "accent_soft": hls_to_hex(h, max(l - 10, 12), max(s - 20, 15)),
    }


def inject_css(accent: str) -> None:
    p = palette(accent)

    st.markdown(
        textwrap.dedent(f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
        :root {{
            --accent: {p['accent']};
            --accent-bright: {p['accent_bright']};
            --accent-dim: {p['accent_dim']};
            --accent-bg: {p['accent_bg']};
            --accent-soft: {p['accent_soft']};
            --bg-0: #060509;
            --bg-1: #0c0a13;
            --bg-2: #14111d;
        }}

        html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

        .stApp {{
            background:
                radial-gradient(ellipse 900px 500px at 15% -10%, var(--accent-bg) 0%, transparent 60%),
                radial-gradient(ellipse 700px 500px at 100% 10%, {p['accent_soft']}33 0%, transparent 55%),
                var(--bg-0);
            color: #ece8f7;
        }}

        /* Hide default Streamlit chrome for a more custom app feel */
        footer {{ visibility: hidden; height: 0; }}
        #MainMenu {{ visibility: hidden; }}
        [data-testid="stToolbar"] {{ right: 8px; }}
        [data-testid="stHeader"] {{ background: transparent; }}
        [data-testid="stDecoration"] {{ background: linear-gradient(90deg, var(--accent-dim), var(--accent-bright)); }}

        h1, h2, h3 {{
            font-family: 'Space Grotesk', sans-serif;
            letter-spacing: 0.2px;
        }}
        h1 {{
            color: var(--accent-bright) !important;
            text-shadow: 0 0 24px {p['accent']}55;
            font-weight: 700;
        }}
        h2, h3 {{ color: var(--accent-bright) !important; }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, var(--bg-1), var(--bg-0));
            border-right: 1px solid var(--accent-dim);
        }}
        section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] h4 {{
            color: var(--accent-bright) !important;
            -webkit-text-fill-color: var(--accent-bright) !important;
            background: none !important;
        }}

        /* Buttons */
        .stButton>button, .stDownloadButton>button {{
            background: linear-gradient(135deg, var(--accent-soft), var(--accent-dim));
            color: #fff;
            border: 1px solid var(--accent);
            border-radius: 10px;
            font-weight: 500;
            box-shadow: 0 2px 10px rgba(0,0,0,.35);
            transition: all 0.15s ease-out;
        }}
        .stButton>button:hover, .stDownloadButton>button:hover {{
            border-color: var(--accent-bright);
            box-shadow: 0 0 18px {p['accent']}88, 0 2px 14px rgba(0,0,0,.4);
            transform: translateY(-1px);
            color: #fff;
        }}
        .stButton>button:active {{ transform: translateY(0); }}
        .stButton>button[kind="primary"] {{
            background: linear-gradient(135deg, var(--accent), var(--accent-bright));
            border-color: var(--accent-bright);
        }}

        /* Bordered card containers (search grid tiles, deck zones) */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background: linear-gradient(165deg, var(--bg-2), var(--bg-1));
            border: 1px solid #2a2436 !important;
            border-radius: 14px !important;
            transition: transform 0.15s ease-out, border-color 0.15s ease-out, box-shadow 0.15s ease-out;
        }}
        [data-testid="stVerticalBlockBorderWrapper"]:hover {{
            border-color: var(--accent) !important;
            box-shadow: 0 6px 22px {p['accent']}33;
            transform: translateY(-2px);
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid #2a2436; }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 10px 10px 0 0;
            padding: 8px 16px;
            color: #b7b0c9;
        }}
        .stTabs [aria-selected="true"] {{
            color: var(--accent-bright) !important;
            background: var(--accent-bg);
            border-bottom: 2px solid var(--accent-bright) !important;
        }}

        /* Expanders */
        [data-testid="stExpander"] {{
            border: 1px solid #2a2436 !important;
            border-radius: 12px !important;
            background: var(--bg-1);
        }}

        /* Metrics */
        [data-testid="stMetric"] {{
            background: linear-gradient(165deg, var(--bg-2), var(--bg-1));
            border: 1px solid var(--accent-dim);
            border-radius: 12px;
            padding: 10px 14px;
        }}
        [data-testid="stMetricValue"] {{ color: var(--accent-bright); }}

        /* Inputs */
        [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
        div[data-baseweb="select"] > div {{
            background-color: var(--bg-2) !important;
            border-color: #34304a !important;
            border-radius: 8px !important;
        }}
        div[data-baseweb="tag"] {{
            background-color: var(--accent-dim) !important;
            border-radius: 6px !important;
        }}
        [data-testid="stSlider"] [role="slider"] {{ background-color: var(--accent-bright) !important; }}
        .stProgress > div > div {{
            background-image: linear-gradient(90deg, var(--accent-dim), var(--accent-bright));
        }}

        /* Scrollbar */
        ::-webkit-scrollbar {{ width: 10px; height: 10px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg-0); }}
        ::-webkit-scrollbar-thumb {{ background: var(--accent-dim); border-radius: 6px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: var(--accent); }}

        hr {{ border-color: #2a2436 !important; }}

        /* Card badges (used by ui_cards.status_badge_html) */
        .ygo-badge {{
            display: inline-block; padding: 2px 8px; border-radius: 999px;
            font-size: 0.72rem; font-weight: 700; margin-right: 4px; letter-spacing: .2px;
        }}
        .ygo-badge-forbidden {{ background:#3a0a0a; color:#ff6b6b; border:1px solid #ff6b6b; }}
        .ygo-badge-limited {{ background:#3a2a0a; color:#ffc266; border:1px solid #ffc266; }}
        .ygo-badge-semi {{ background:#2a2a0a; color:#e6e64d; border:1px solid #e6e64d; }}
        .ygo-badge-unlimited {{ background:#0a2a12; color:#66ff99; border:1px solid #66ff99; }}

        .ygo-card-name {{ color: var(--accent-bright); font-weight: 700; }}
        </style>
        """),
        unsafe_allow_html=True,
    )


def theme_sidebar_control() -> str:
    if "theme_color" not in st.session_state:
        st.session_state.theme_color = load_saved_color()

    with st.sidebar:
        st.markdown("#### 🎨 Site Color")
        color = st.color_picker(
            "Site color",
            value=st.session_state.theme_color,
            key="theme_color_picker",
            label_visibility="collapsed",
        )
        if color != st.session_state.theme_color:
            st.session_state.theme_color = color
            save_color(color)

    inject_css(st.session_state.theme_color)
    return st.session_state.theme_color
