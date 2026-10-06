"""
Streamlit frontend for the multi-set web-knowledge RAG chatbot.

Three panels:
  - LEFT (sidebar):    theme toggle, set switcher, new-set form
  - CENTER:            chat log (chat input docked below it), for the active set
  - RIGHT:             chunk-usage gauge, add-URL form, ingested-source cards

All backend access goes through ApiClient (frontend/api_client.py) over HTTP —
this file never imports a backend module directly.

Ordering notes (both learned the hard way, via headless testing, not guesswork):

1. The set switcher's row buttons (select/delete) are rendered exactly ONCE,
   early. Selecting a set is just a session_state write inside that same
   render — nothing here calls st.stop() until *after* that write has had a
   chance to happen, so clicking a set's name takes effect on the very click
   that did it, not the click after.

2. The right column (which can change this set's chunk count via the ingest
   form) is processed before the center column, even though the center
   column appears first on screen — a layout container keeps its screen
   position regardless of when in the script it's written to, so "chat
   unlocks after the first source is added" reflects the same click that
   added it, with no extra st.rerun() (which would cause a visible
   double-render flicker).

3. Chat history is rendered into an st.empty() placeholder created *before*
   st.chat_input() is called. The placeholder keeps its screen position
   (above the input) regardless of when it's last written to, so a new
   message can be appended and the placeholder refilled *after* chat_input
   returns it, and the log still updates immediately, above the input.

Row/button styling: an active row's left accent border and the delete
button's danger-red hover are applied via st.container(key=...), which
Streamlit renders as a real DOM wrapper carrying an `st-key-<key>` class
(see styles.py) — not via raw <div> tags split across separate st.markdown
calls, which don't actually wrap anything since each call renders as its
own sibling element.

Known limitation (backend, not this file's doing): GET /messages only
returns whatever is still buffered in SQLite (the most recent messages for
that set). Once older turns get compacted into that set's Qdrant memory
collection, they're still recallable by the agent's memory tool, but this
history view won't replay them verbatim.
"""

import os
from urllib.parse import urlparse

import streamlit as st

from api_client import ApiClient, ApiError
from styles import inject

APP_TITLE = "Web RAG Agentic Chat"
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title=APP_TITLE, page_icon="🧠", layout="wide")

# ---------------------------------------------------------------- state ---

if "active_set_id" not in st.session_state:
    st.session_state.active_set_id = None
if "chat_histories" not in st.session_state:
    st.session_state.chat_histories = {}  # set_id -> list[{"role","content"}]
if "knowledge_cache" not in st.session_state:
    st.session_state.knowledge_cache = {}  # set_id -> list[dict] | None
if "status_cache" not in st.session_state:
    st.session_state.status_cache = {}  # set_id -> dict | None
if "confirm_delete_id" not in st.session_state:
    st.session_state.confirm_delete_id = None
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

inject(st.session_state.theme)

api = ApiClient(BACKEND_URL)

# --------------------------------------------------------------- helpers ---


def is_well_formed_url(candidate: str) -> bool:
    try:
        parsed = urlparse(candidate.strip())
    except Exception:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def load_set_data(set_id: int, force: bool = False):
    """Fetch (and cache) knowledge list + status for a set. Safe to call every run."""
    if not force and set_id in st.session_state.knowledge_cache:
        return
    try:
        st.session_state.knowledge_cache[set_id] = api.list_knowledges(set_id)
        st.session_state.status_cache[set_id] = api.get_status(set_id)
    except ApiError as e:
        st.session_state.knowledge_cache[set_id] = None
        st.session_state.status_cache[set_id] = None
        st.session_state[f"_load_error_{set_id}"] = str(e)


def ensure_chat_history_loaded(set_id: int):
    """Hydrate a set's chat history from the backend the first time it's
    opened this session. After that, local session_state is the source of
    truth (it already includes everything the server has, plus whatever was
    just sent this run)."""
    if set_id in st.session_state.chat_histories:
        return
    try:
        messages = api.get_messages(set_id) or []
        st.session_state.chat_histories[set_id] = [
            {"role": m["role"], "content": m["content"]} for m in messages
        ]
    except ApiError:
        st.session_state.chat_histories[set_id] = []


def render_set_rows(sets):
    """Sidebar: the switcher/delete rows. Rendered exactly once per run —
    see module docstring for why."""
    if not sets:
        st.markdown(
            '<div class="empty-state">No sets yet. Create one above to start ingesting pages.</div>',
            unsafe_allow_html=True,
        )
        return

    for s in sets:
        set_id = s["id"]
        row_slot = st.empty()

        # draw_normal and draw_confirm both open with a single st.columns(...)
        # call as their very first element inside `with row_slot.container():`.
        # That match matters: when this placeholder gets refilled a second
        # time in the same run (e.g. draw_confirm cancelling back to
        # draw_normal), Streamlit reconciles the new content against the old
        # by position — if the first element's *type* differs between the
        # two fills (a keyed container vs. a bare columns block, or a
        # markdown line vs. a columns block), the old content doesn't get
        # cleanly replaced, it lingers alongside the new content. Keeping
        # both functions' top-level shape identical avoids that; it's also
        # why the active-row/delete/confirm styling below uses the built-in
        # `type="primary"` button parameter rather than a wrapping
        # st.container(key=...) — a wrapper would itself be a shape
        # mismatch between the two functions.

        def draw_normal(row_slot=row_slot, s=s, set_id=set_id):
            # `is_active` reflects active_set_id as of the *start* of this
            # run, so on the exact click that changes it, this row's own
            # highlight is one interaction behind (button `type` has to be
            # fixed at creation time, before we know this click's outcome).
            # It self-corrects on the very next interaction — cosmetic only,
            # doesn't affect which set is actually active.
            is_active = set_id == st.session_state.active_set_id
            with row_slot.container():
                c1, c2 = st.columns([4, 1])
                with c1:
                    if st.button(
                        s["name"],
                        key=f"select_{set_id}",
                        type="primary" if is_active else "secondary",
                        use_container_width=True,
                    ):
                        st.session_state.active_set_id = set_id
                        st.session_state.confirm_delete_id = None
                with c2:
                    if st.button(
                        "🗑️", key=f"del_{set_id}", help="Delete this set", use_container_width=True
                    ):
                        st.session_state.confirm_delete_id = set_id
            # Redraw AFTER the `with row_slot.container():` above has fully
            # exited, not from inside its own click handler.
            if st.session_state.confirm_delete_id == set_id:
                draw_confirm()

        def draw_confirm(row_slot=row_slot, s=s, set_id=set_id):
            delete_error = None
            with row_slot.container():
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(
                        "Confirm delete", key=f"delconfirm_{set_id}", type="primary", use_container_width=True
                    ):
                        try:
                            api.delete_set(set_id)
                            st.session_state.chat_histories.pop(set_id, None)
                            st.session_state.knowledge_cache.pop(set_id, None)
                            st.session_state.status_cache.pop(set_id, None)
                            if st.session_state.active_set_id == set_id:
                                st.session_state.active_set_id = None
                            st.session_state.confirm_delete_id = None
                            # Row will correctly drop off on the next rerun,
                            # once `sets` is refetched at the top of the script.
                        except ApiError as e:
                            st.session_state.confirm_delete_id = None
                            delete_error = str(e)
                with c2:
                    if st.button("Cancel", key=f"delcancel_{set_id}", use_container_width=True):
                        st.session_state.confirm_delete_id = None
            if st.session_state.confirm_delete_id != set_id:
                draw_normal()
            if delete_error:
                st.error(f"Couldn't delete set: {delete_error}")

        if st.session_state.confirm_delete_id == set_id:
            draw_confirm()
        else:
            draw_normal()


# ------------------------------------------------------------ top-level ---

try:
    sets = api.list_sets()
except ApiError as e:
    st.error(f"⚠️ {e}")
    st.stop()

with st.sidebar:
    st.subheader("Orchestrated by Tharun")
    title_col, toggle_col = st.columns([3.2, 1])
    with title_col:
        st.markdown(f'<div class="app-title">{APP_TITLE}</div>', unsafe_allow_html=True)
    with toggle_col:
        with st.container(key="theme-toggle"):
            icon = "☀️" if st.session_state.theme == "dark" else "🌙"
            if st.button(icon, key="theme_toggle_btn", help="Switch light/dark theme"):
                st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"

    
    st.markdown(
        '<div class="app-tagline">Turn Web pages into an Agent-Powered Knowledge System you can Chat with.</div>',
        unsafe_allow_html=True,
    )

    with st.form("new_set_form", clear_on_submit=True, border=True):
        new_name = st.text_input(
            "New set", placeholder="e.g. Competitor research", label_visibility="collapsed"
        )
        created = st.form_submit_button("+ New set", use_container_width=True)
        if created:
            if not new_name.strip():
                st.error("Give the set a name first.")
            else:
                try:
                    result = api.create_set(new_name.strip())
                    sets = api.list_sets()  # refresh: `sets` was fetched before this set existed
                    st.session_state.active_set_id = result["id"]
                except ApiError as e:
                    st.error(f"Couldn't create set: {e}")

    st.divider()
    render_set_rows(sets)

# `active_set_id` now reflects: any set just created above, any row just
# clicked in render_set_rows, or a delete that just cleared it.
if st.session_state.active_set_id is not None and not any(
    s["id"] == st.session_state.active_set_id for s in sets
):
    st.session_state.active_set_id = None

if st.session_state.active_set_id is None:
    st.markdown(
        '<div class="empty-state">Select a set from the sidebar, or create a new one, to start '
        "adding pages and chatting.</div>",
        unsafe_allow_html=True,
    )
    st.stop()

active_id = st.session_state.active_set_id
active_set = next(s for s in sets if s["id"] == active_id)
load_set_data(active_id)
ensure_chat_history_loaded(active_id)

knowledges = st.session_state.knowledge_cache.get(active_id)
status = st.session_state.status_cache.get(active_id)
load_error = st.session_state.pop(f"_load_error_{active_id}", None)

center_col, right_col = st.columns([2.1, 1])

# ---- RIGHT: usage gauge + sources (processed first so a fresh ingest is
#      reflected below, in the same run) ---------------------------------

with right_col:
    st.markdown("### Sources")

    if load_error:
        st.warning(f"Couldn't load this set's data: {load_error}")

    # Reserve the gauge's position now, but fill it last (after the ingest
    # form and refresh button below have had a chance to update `status` in
    # this same run) — otherwise a same-run ingest shows the new source card
    # immediately but leaves the gauge one run behind.
    gauge_slot = st.empty()

    is_full = bool(status) and status["chunk_count"] >= status["chunk_limit"]

    if is_full:
        st.warning(
            f"This set is at capacity ({status['chunk_count']}/{status['chunk_limit']} chunks). "
            "Start a new set for more material."
        )
    else:
        with st.form(f"ingest_form_{active_id}", clear_on_submit=True, border=True):
            url_input = st.text_input("Add a URL", placeholder="https://example.com/article")
            submit_url = st.form_submit_button("Ingest", use_container_width=True)
            if submit_url:
                if not url_input.strip():
                    st.error("Enter a URL first.")
                elif not is_well_formed_url(url_input):
                    st.error("That doesn't look like a valid http(s) URL.")
                else:
                    with st.spinner("Scraping and indexing page..."):
                        try:
                            api.ingest_url(active_id, url_input.strip())
                            load_set_data(active_id, force=True)
                            knowledges = st.session_state.knowledge_cache.get(active_id)
                            status = st.session_state.status_cache.get(active_id)
                            st.success("Page added.")
                        except ApiError as e:
                            st.error(f"Couldn't add that page: {e}")

    if st.button("↻ Refresh", key=f"refresh_{active_id}"):
        load_set_data(active_id, force=True)
        knowledges = st.session_state.knowledge_cache.get(active_id)
        status = st.session_state.status_cache.get(active_id)

    with gauge_slot.container():
        if status:
            limit = max(status["chunk_limit"], 1)
            used = status["chunk_count"]
            st.progress(min(used / limit, 1.0))
            st.markdown(
                f'<div class="chunk-caption">{used}/{status["chunk_limit"]} chunks used</div>',
                unsafe_allow_html=True,
            )

    st.markdown("")

    if not knowledges:
        st.markdown('<div class="empty-state">No pages ingested yet.</div>', unsafe_allow_html=True)
    else:
        for k in knowledges:
            title = k["url_name"]
            source_url = k.get("source_url") or "#"
            st.markdown(
                f"""<div class="source-card">
                        <a class="title-link" href="{source_url}" target="_blank" rel="noopener noreferrer">{title}</a>
                        <div class="meta">{k['chunk_count']} chunks &middot; added {k['uploaded_at']}</div>
                    </div>""",
                unsafe_allow_html=True,
            )

# ---- CENTER: chat (uses `knowledges`/`status` as refreshed by the right
#      column above; input is docked below the log) -----------------------

with center_col:
    st.markdown(f"### {active_set['name']}")

    has_docs = bool(knowledges)
    history = st.session_state.chat_histories.setdefault(active_id, [])

    chat_slot = st.empty()

    def render_chat_log(chat_slot=chat_slot, history=history):
        with chat_slot.container(height=460, border=True, autoscroll=True):
            if not history:
                st.markdown(
                    '<div class="empty-state">No messages yet. Ask a question once a page is added.</div>',
                    unsafe_allow_html=True,
                )
            for turn in history:
                avatar = "🧑" if turn["role"] == "user" else "🧠"
                with st.chat_message(turn["role"], avatar=avatar):
                    st.write(turn["content"])

    render_chat_log()

    if has_docs:
        prompt = st.chat_input("Ask something about this set's sources...")
        if prompt:
            history.append({"role": "user", "content": prompt})
            try:
                response = api.send_chat(active_id, prompt)
                history.append({"role": "assistant", "content": response["answer"]})
            except ApiError as e:
                history.append({"role": "assistant", "content": f"⚠️ {e}"})
            render_chat_log()
    else:
        st.info("Add at least one URL on the right before you can chat with this set.")

    st.caption(
        "Recent messages are saved and reload with this set; much older ones move into "
        "long-term memory and aren't replayed here, but the agent can still recall them."
    )
