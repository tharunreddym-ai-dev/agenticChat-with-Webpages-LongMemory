# Agentic RAG System to Chat about Websites

Turn scattered web pages into isolated, chattable knowledge bases. Create a
"set," feed it URLs, and it scrapes, cleans, and indexes each page so you can
ask an agent questions grounded strictly in what you fed it — nothing else.

Conceptually similar to Claude Projects: each set has its own ingested
content and its own conversation memory, fully isolated from every other set.

Unlike a typical document-upload RAG tool, this one ingests **URLs**, not
file uploads.

## How it works

1. **Ingest**: give a set a URL. The backend validates it, scrapes it with
   Firecrawl, enriches it with a Tavily search pass, merges both into one
   clean Markdown document via an LLM consolidation pass, chunks it, embeds
   it with NVIDIA embeddings, and stores it in that set's own Qdrant
   collection. Each set has a hard cap of `MAX_CHUNKS` chunks (default 150,
   set in `.env`), enforced server-side. The page's real title (from
   Firecrawl's scrape metadata) is stored and shown on its source card,
   with the hostname as a fallback if a page has no title.
2. **Chat**: retrieval is *agentic*, not a fixed pipeline. A LangChain ReAct
   agent (Gemini) decides whether and how to use two tools — a
   document-search tool over that set's ingested pages, and a
   long-term-memory tool over that set's compacted older conversation — and
   is instructed to answer only from what those tools return, saying so
   explicitly when the answer isn't in there.
3. **Tiered memory**: the most recent N messages per set live in SQLite and
   go straight into the prompt. Once that buffer fills, the oldest 3/4 are
   summarized (Groq) and embedded into that set's own `_memory` collection,
   then dropped from SQLite — so old context isn't lost, it's just no longer
   free; the agent has to decide to go look for it. The frontend reloads
   whatever's still in that SQLite buffer via `GET /sets/{id}/messages`
   when you reopen a set, so recent chat survives a page reload.

## Architecture

```text
main.py                 FastAPI app entrypoint
config.py               env loading + validation (fails fast if a key is missing)

api/
  routes.py              HTTP endpoints (sets, ingestion, chat, messages, status)

agent/
  build_agent.py         builds the ReAct AgentExecutor (Gemini + 2 tools)
  tools.py                the document-search and long-term-memory tools
  prompts.py              ReAct prompt, summarization prompt, ingestion-consolidation prompt
  chat.py                 orchestrates one chat turn (history -> agent -> persist -> compact)
  compaction.py           tiered-memory summarization + Qdrant memory writes

db/
  database.py             SQLite schema (sets, messages, knowledge_bases)
  crud.py                 all SQLite queries

vectorstore/
  qdrant_client.py        local on-disk Qdrant client
  collections.py          per-set collection naming/lifecycle
  ingest.py               chunking, embedding, Firecrawl+Tavily consolidation

scarping/                 (yes, that's how it's spelled throughout — kept
  get_content.py          consistent rather than half-renamed)
  clean.py                 URL validation, Firecrawl fetch + title extraction, markdown cleanup

frontend/
  app.py                  Streamlit three-panel UI, light/dark theme toggle
  api_client.py            thin HTTP client — the frontend never imports backend code
  styles.py                 all CSS (not dependent on .streamlit/config.toml)
```

## Tech stack

- **API**: FastAPI + SQLite (message buffer) + Qdrant, local on-disk mode (two collections per set: `_knowledge`, `_memory`)
- **Agent**: LangChain (`langchain==1.2.13`) — `create_react_agent` / `AgentExecutor` from `langchain_classic.agents`, since that's where they live as of LangChain 1.x
- **Chat LLM**: Gemini via `langchain-google-genai`
- **Summarization LLM**: Groq (compaction only, not the main chat path)
- **Embeddings**: NVIDIA NIM (`nvidia/nemotron-3-embed-1b`)
- **Ingestion**: Firecrawl (scrape + title) + Tavily (supplementary search context) — via `firecrawl-py`'s `V1FirecrawlApp` (see "Fixed" below for why)
- **Frontend**: Streamlit, with a self-contained light/dark theme toggle (no dependency on `.streamlit/config.toml`)

## Example

Create a set for a documentation page:

```text
Set: LangChain Docs

URL:
https://python.langchain.com/docs/introduction/

The page is scraped, cleaned, enriched, consolidated, chunked,
embedded, and stored in the set's `_knowledge` collection.

You can then ask:

"What is LangChain used for?"

The agent retrieves relevant content from that set and answers
using the ingested knowledge. If the information is not available
in the set, it explicitly says that it cannot find the answer.
```


## Setup

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt

cp .env.example .env             # fill in your real API keys
mkdir -p data                    # holds the SQLite file + on-disk Qdrant store
```

## How to Run

```bash
# terminal 1 — backend
python -m uvicorn main:app

# terminal 2 — frontend
cd frontend
python -m streamlit run app.py
```

`BACKEND_URL` defaults to `http://localhost:8000` if you don't set it.

## Limitations

1. **Single-user** — No authentication or multi-user support yet.

2. **Page-level ingestion** — You chat with the ingested web page, not the entire website automatically. Other pages must be added separately.

3. **Local storage** — SQLite and Qdrant currently use local storage, so the system is mainly intended for local use and prototyping.
