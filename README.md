# post-it

Turn web content into ready-to-publish social media posts. **LinkedIn first**, with a
clean, pluggable core so other platforms and LLM providers drop in easily.

You give it content **one of two ways**, it generates **3 distinct post variants** with an
LLM, you **pick and approve one**, and it **publishes** — either as a local draft or
straight to LinkedIn via the official API.

## How it works

```
                 ┌── Option A: .txt file of URL(s) ──► scrape each page ──┐
 choose source ──┤                                                        ├─► content
                 └── Option B: AI-direct (a topic OR a single URL) ───────┘
                                          │
                          LLM generates 3 variants (insightful / punchy / story-driven)
                                          │
                          review the 3 → select & approve one
                                          │
                 publish ──► draft (file + clipboard)  OR  LinkedIn (official API)
```

## Install

```bash
pip install -e .            # core (Anthropic/Claude default)
pip install -e ".[openai]"  # add the OpenAI provider
pip install -e ".[dev]"     # add the test/lint toolchain
```

## Configure

Copy `.env.example` to `.env` and fill in what you need (everything is optional until you
use the feature that needs it):

```bash
cp .env.example .env
```

At minimum, set the API key for your LLM provider — `POSTIT_ANTHROPIC_API_KEY`
(default provider) or `POSTIT_OPENAI_API_KEY`. `.env` is gitignored; never commit secrets.

## Usage

**Option A — a file of URLs:**

```bash
printf 'https://example.com/post-1\nhttps://example.com/post-2\n' > urls.txt
post-it run --source url-file --input urls.txt
```

**Option B — AI-direct (a topic, or a single URL):**

```bash
post-it run --source ai --input "the future of retrieval-augmented generation"
post-it run --source ai --input "https://example.com/some-article"
```

Then follow the prompts: review the 3 variants, select one (`1`/`2`/`3`), approve, and
choose a publish mode (`draft` or `linkedin`). Omit any flag and you'll be prompted for it.

Useful flags: `--provider anthropic|openai`, `--platform linkedin`, `--mode draft|linkedin`.

### Publish modes

- **`draft`** (zero setup): writes the approved post to `drafts/post-<timestamp>.txt` and
  copies it to your clipboard. The always-works path.
- **`linkedin`**: publishes via LinkedIn's official Posts API (one-time setup below).

## LinkedIn API setup (one time)

Publishing to LinkedIn requires a LinkedIn developer app and a member access token.

1. Create an app at <https://www.linkedin.com/developers/apps>, associated with a Company Page.
2. Under **Products**, request **"Share on LinkedIn"** and **"Sign In with LinkedIn using
   OpenID Connect"**.
3. Add `http://localhost:8000/callback` as an authorized redirect URL.
4. Put your app credentials in `.env`:
   ```
   POSTIT_LINKEDIN_CLIENT_ID=...
   POSTIT_LINKEDIN_CLIENT_SECRET=...
   ```
5. Run the one-time OAuth flow (opens your browser, scopes `openid profile w_member_social`):
   ```bash
   post-it auth linkedin
   ```
   The access token and your author URN are saved to `~/.post-it/credentials.json` (mode 0600).
6. Publish: `post-it run --source ai --input "..." --mode linkedin`.

**Notes & limits**
- Member access tokens last ~60 days; re-run `post-it auth linkedin` when one expires.
- `POSTIT_LINKEDIN_API_VERSION` (the `LinkedIn-Version` header, `YYYYMM`) must track a
  supported version — bump it if LinkedIn rejects the version.
- Automated posting is subject to LinkedIn's Terms and rate limits; use responsibly. Draft
  mode needs no LinkedIn account at all.

## Extending it

The core is three small abstractions wired through `src/post_it/registry.py` — add an entry
and you're done, no CLI changes:

- **Content source** (`sources/base.py`) — a new way to supply input.
- **LLM provider** (`llm/base.py`) — e.g. a Gemini backend; return the same `PostVariant`s.
- **Social publisher** (`publishers/base.py`) — e.g. a `TwitterPublisher`; add a
  `PLATFORM_GUIDELINES` entry in `llm/prompts.py` and a `PLATFORM_MAX_LENGTH` entry in
  `publishers/base.py`.

The orchestrator (`orchestrator.py`) exposes `generate()` / `publish()` — a UI-agnostic
core that a future web app can reuse directly.

## Development

```bash
pytest         # all tests; network/LLM/LinkedIn calls are fully mocked
ruff check src tests
```

## Security notes

- Scraped page text is treated as **untrusted** and kept in the user turn with a guard
  instruction (prompt-injection mitigation in `llm/prompts.py`).
- Secrets live only in `.env` / `~/.post-it/credentials.json`, never in the repo.
