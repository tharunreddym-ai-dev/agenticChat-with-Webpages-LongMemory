"""
Central CSS for the app — the only source of visual styling (not dependent
on .streamlit/config.toml, which only loads from the current working
directory and silently fails to apply if the app is launched from anywhere
else).

Palette: an ink-and-brass "reading room" theme in dark mode, flipped to a
warm-paper-and-brass theme in light mode — a brass/lamplight accent rather
than the generic cream+terracotta or near-black+neon-accent combinations
most AI-generated UIs default to. Fits the subject matter (turning
scattered web pages into an archive you sit down and read/chat with).

Row/button targeting note: earlier drafts of this app tried to style a
sidebar row by opening and closing a raw <div class="..."> across two
separate st.markdown() calls with widgets in between. That never actually
wrapped anything — each st.markdown/st.button call renders as its own
sibling element, not nested inside the markdown's div. The buttons that
need distinct styling here (the active-row accent, the delete button) are
instead wrapped in a real st.container(key=...), which Streamlit renders
as an actual DOM wrapper carrying an `st-key-<key>` class — that's what
the selectors below target.
"""

PALETTES = {
    "dark": {
        "bg": "#1B1D22",
        "bg-panel": "#21242B",
        "bg-card": "#282B33",
        "bg-card-hi": "#30333D",
        "border": "#383C46",
        "text": "#E7E4DC",
        "text-dim": "#9B9CA3",
        "accent": "#C9A24B",
        "accent-hi": "#DCB562",
        "accent-text": "#241D0D",
        "danger": "#C1595A",
        "danger-hi": "#D97374",
        "danger-text": "#2A1414",
        "success": "#7FA37A",
        "shadow": "0 2px 10px rgba(0,0,0,0.35)",
    },
    "light": {
        "bg": "#F3F0E7",
        "bg-panel": "#ECE7DA",
        "bg-card": "#FFFFFF",
        "bg-card-hi": "#F7F4EC",
        "border": "#DDD5C2",
        "text": "#2A2620",
        "text-dim": "#756F60",
        "accent": "#A9782F",
        "accent-hi": "#8F6527",
        "accent-text": "#FFFFFF",
        "danger": "#A23B3C",
        "danger-hi": "#8A2F30",
        "danger-text": "#FFFFFF",
        "success": "#3F6B3A",
        "shadow": "0 2px 10px rgba(60,50,30,0.12)",
    },
}

CSS_TEMPLATE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {{
    --bg:          {bg};
    --bg-panel:    {bg-panel};
    --bg-card:     {bg-card};
    --bg-card-hi:  {bg-card-hi};
    --border:      {border};
    --text:        {text};
    --text-dim:    {text-dim};
    --accent:      {accent};
    --accent-hi:   {accent-hi};
    --accent-text: {accent-text};
    --danger:      {danger};
    --danger-hi:   {danger-hi};
    --danger-text: {danger-text};
    --success:     {success};
    --shadow:      {shadow};
}}

/* ---- base ---- */
[data-testid="stAppViewContainer"], [data-testid="stHeader"], .main {{
    background-color: var(--bg) !important;
}}
[data-testid="stSidebar"] {{
    background-color: var(--bg-panel) !important;
    border-right: 1px solid var(--border) !important;
}}
html, body, [class*="css"] {{
    color: var(--text) !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}}
h1, h2, h3, h4 {{
    font-family: 'Source Serif 4', serif !important;
    font-weight: 600 !important;
    color: var(--text) !important;
    letter-spacing: 0.01em;
}}
p, span, label, div {{ color: var(--text); }}
a {{ color: var(--accent) !important; }}

/* ---- app title block ---- */
.app-title {{
    font-family: 'Source Serif 4', serif;
    font-size: 1.35rem;
    font-weight: 600;
    line-height: 1.25;
    color: var(--text);
    margin-bottom: 0.2rem;
}}
.app-tagline {{
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.82rem;
    color: var(--text-dim);
    margin-bottom: 1rem;
}}

/* ---- theme toggle ---- */
div[class*="st-key-theme-toggle"] button {{
    background-color: transparent !important;
    border: 1px solid var(--border) !important;
    border-radius: 999px !important;
    padding: 0.15rem 0.7rem !important;
    font-size: 0.85rem !important;
}}
div[class*="st-key-theme-toggle"] button:hover {{
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}}

/* ---- generic buttons: quiet by default, brass when primary ---- */
.stButton > button, .stFormSubmitButton > button {{
    background-color: var(--bg-card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 500 !important;
}}
.stButton > button:hover, .stFormSubmitButton > button:hover {{
    background-color: var(--bg-card-hi) !important;
    border-color: var(--accent) !important;
    color: var(--accent-hi) !important;
}}
.stButton > button:focus-visible, .stFormSubmitButton > button:focus-visible {{
    outline: 2px solid var(--accent) !important;
    outline-offset: 1px;
}}
button[kind="primary"] {{
    background-color: var(--accent) !important;
    color: var(--accent-text) !important;
    border: 1px solid var(--accent) !important;
}}
button[kind="primary"]:hover {{
    background-color: var(--accent-hi) !important;
    color: var(--accent-text) !important;
}}

/* ---- sidebar set rows ---- */
/* Active/inactive and delete/confirm styling is done via the button's
   built-in `type="primary"` parameter (see app.py's render_set_rows) rather
   than a wrapping st.container(key=...) — see the comment there for why. */

/* ---- inputs ---- */
.stTextInput input, .stTextArea textarea {{
    background-color: var(--bg-card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.9rem !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
    border-color: var(--accent) !important;
    box-shadow: none !important;
}}

/* ---- progress / chunk gauge ---- */
[data-testid="stProgress"] div div {{
    background-color: var(--accent) !important;
}}
[data-testid="stProgress"] {{
    background-color: var(--bg-card) !important;
    border-radius: 4px;
}}
.chunk-caption {{
    color: var(--text-dim);
    font-size: 0.78rem;
    font-family: 'IBM Plex Mono', monospace;
    margin-top: -0.3rem;
    margin-bottom: 0.5rem;
}}

/* ---- source cards (right panel) ---- */
.source-card {{
    background-color: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.7rem 0.85rem;
    margin-bottom: 0.6rem;
    box-shadow: var(--shadow);
    transition: border-color 150ms ease, transform 150ms ease;
}}
.source-card:hover {{
    border-color: var(--accent);
    transform: translateY(-1px);
}}
.source-card a.title-link {{
    font-family: 'IBM Plex Sans', sans-serif;
    font-weight: 600;
    font-size: 0.92rem;
    color: var(--text) !important;
    text-decoration: none;
}}
.source-card a.title-link:hover {{
    color: var(--accent) !important;
    text-decoration: underline;
}}
.source-card .meta {{
    font-size: 0.75rem;
    color: var(--text-dim);
    margin-top: 0.3rem;
    font-family: 'IBM Plex Mono', monospace;
}}

/* ---- empty states ---- */
.empty-state {{
    color: var(--text-dim);
    font-size: 0.9rem;
    border: 1px dashed var(--border);
    border-radius: 8px;
    padding: 1rem;
    text-align: left;
}}

/* ---- chat bubbles ---- */
[data-testid="stChatMessage"] {{
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    box-shadow: var(--shadow);
}}
[data-testid="stChatInput"] textarea {{
    background-color: var(--bg-card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
}}

/* ---- misc ---- */
hr {{ border-color: var(--border) !important; }}
[data-testid="stAlert"] {{ border-radius: 8px !important; }}
</style>
"""


def inject(theme: str = "dark"):
    import streamlit as st
    palette = PALETTES.get(theme, PALETTES["dark"])
    st.markdown(CSS_TEMPLATE.format(**palette), unsafe_allow_html=True)
