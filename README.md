## Odyssey

Odyssey is a lightweight movie recommendation web app. You upload your watch history (CSV), then swipe through recommendations in a **3-card carousel** with satisfying click/flip animations, a **persistent watchlist**, and two recommendation modes:

- **Regular mode**: fast, mostly local recommendations (with a Gemini fallback when the local pool is exhausted).
- **Super mode**: Gemini-powered recommendations with an explainable **mapping panel** (radar chart + matched genres/directors/actors).

The project is intentionally “no build step”: it’s plain HTML/CSS/JS served by a small Flask app.

---

## Features

### Recommendations UX
- **Batch queue**: the client requests a batch, stores it in a queue, and displays **3 movies at a time**.
- **Flip + star** interactions: clicking “like” triggers the star animation and flips the card before the next movie appears.
- **Counters**: “liked / seen / left” and a small cursor-near `+1` feedback.
- **State persistence**: navigating away and back to `recommend.html` keeps your current queue (within the same tab) using `sessionStorage`.

### Watchlist
- Liking a movie adds it to a **collapsible watchlist** panel.
- You can **download your watchlist as CSV**.
- Watchlist removal is supported.

### Modes
- **Regular**: local recommender over a curated pool + optional Gemini fallback.
- **Super**: Gemini-only picks + **mapping metrics** and an on-demand radar chart.

### Posters
- Posters are resolved via **TMDb** when needed.
- UI uses `default_poster.svg` as a fallback so images are never blank.

---

## Tech stack

- **Backend**: Python + Flask (`src/app.py`)
- **Frontend**: static HTML/CSS/JS (`src/index.html`, `src/recommend.html`, etc.)
- **AI**: Gemini via `google-genai` (`src/gemini_client.py`)
- **Posters**: TMDb search API (`TMDB_API_KEY`)
- **Local cache**: SQLite (`src/movie_cache.sqlite3`) for lightweight movie metadata caching

---

## Project structure

```text
.
├─ src/
│  ├─ app.py                  # Flask server + API routes
│  ├─ gemini_client.py         # Gemini calls + robust JSON extraction
│  ├─ recommender.py           # Local recommender (Regular mode)
│  ├─ index.html               # Landing + upload + Super toggle
│  ├─ recommend.html           # 3-card recommendation UI + watchlist + mapping
│  ├─ script.js                # Landing page logic (upload + mode toggle)
│  ├─ recommend.js             # Recommend page logic (queue, UI, mapping)
│  ├─ style.css                # Landing styles
│  ├─ recommend.css            # Recommend styles
│  ├─ shared.css               # Shared animations/styles
│  ├─ default_poster.svg       # Poster fallback
│  ├─ logo.png                 # Current PNG favicon/logo
│  ├─ movie_database_top250.json
│  └─ ...
├─ requirements.txt
├─ Dockerfile
└─ .env.docker                 # Example env (do NOT commit real keys)
```

---

## Running locally (Python)

### Prerequisites
- Python **3.12+** recommended (Docker image uses 3.12)
- A Gemini API key (for **Super mode**, and Regular fallback if enabled)
- A TMDb API key (for posters)

### Install

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure environment

Create a `.env` file in the repo root:

```bash
GEMINI_API_KEY=your_key_here
TMDB_API_KEY=your_tmdb_key_here
```

Important:
- **Do not commit** real keys. (`gitignore.txt` ignores `.env*`.)
- If you already committed secrets anywhere, rotate them immediately.

### Start the server

```bash
python3 src/app.py
```

Then open:
- `http://localhost:5000/` (home)
- `http://localhost:5000/recommend.html` (recommendations)

---

## Running with Docker

### Build

```bash
docker build -t odyssey .
```

### Run

If you want to use a local env file:

```bash
docker run --rm -p 5000:5000 --env-file .env odyssey
```

Then open `http://localhost:5000/`.

---

## How to use Odyssey

### 1) Choose mode
On the home page, use the **Super** toggle:
- **OFF** → Regular
- **ON** → Super

Mode is stored in `localStorage` under:
- `odyssey.mode`

### 2) Upload your CSV
Click “Upload CSV File” and select your watch-history export.

The backend parses the CSV and stores a normalized list of watched titles (and ratings when present).

### 3) View recommendations
Click “View Recommendations”.

The recommend page:
- requests a batch from the backend (`/api/batch`)
- stores it in a queue
- renders 3 cards at a time

### 4) Like movies (watchlist + feedback)
When you like a movie:
- it’s added to the watchlist (`/api/like`)
- the client advances the carousel
- the next batch uses your **previous batch likes** as context

---

## Recommendation modes (implementation details)

### Regular mode (local-first)

Regular mode is designed to be fast and consistent:
- Uses a **local curated pool** derived from `movie_database_top250.json`
- The loader applies filters:
  - keeps only movies with `poster_url` starting with `http`
  - keeps only “English-ish” (ASCII) titles
  - sorts by `imdb_rating` and keeps the **Top 100** from that pool
- The local recommender scores candidates based on your history and preferences.

**Batch size**: 80

**Gemini fallback**:
If the local pool can’t provide the full 80 fresh picks (because you’ve watched/seen most of them), the backend fills the remainder via Gemini using:
- watched CSV context
- liked watchlist context
- exclude list (seen titles)

### Super mode (Gemini-only + explainability)

Super mode aims for deeper personalization and transparency:
- Calls Gemini to produce **profiles**:
  - `genreProfile`
  - `actorProfile`
  - `directorProfile`
- Calls Gemini again to produce **recommendations** using those profiles.

**Gemini request size**: 200 (server returns 50 after filtering / posters)

**Batch size delivered to UI**: 50

**Mapping panel (right side)**:
- Collapsible “Mapping” tab appears in Super mode.
- Rendering is on-demand (chart draws only when opened).
- Radar chart has 6 axes:
  - Genres / Directors / Actors (strength)
  - Diversity (genre entropy)
  - Coverage (how many mapped items exist)
  - Stability (similarity vs the previous round)
- A dashed overlay shows the previous round when available.

---

## API endpoints

Backend routes are in `src/app.py`.

### Upload & status
- **POST** `/upload`: upload and parse the CSV
- **GET** `/api/status`: basic server status
- **GET** `/api/csv-status`: whether a CSV has been uploaded

### Recommendations
- **POST** `/api/batch`: get a recommendation batch
  - body:
    - `mode`: `"regular"` | `"super"`
    - `liked_titles`: `string[]`
    - `exclude_keys`: `string[]` (`"normalizedTitle::year"`)
- **POST** `/api/refresh`: legacy “refresh all”
- **GET** `/api/recommendations`: legacy “current list”

### Watchlist
- **POST** `/api/like`: track a like (adds to watchlist)
- **POST** `/api/click`: legacy click tracker (kept for compatibility)
- **GET** `/api/watchlist`: get watchlist
- **POST** `/api/watchlist/remove`: remove a watchlist item

### Favicons
- **GET** `/favicon.png`: served from `src/logo.png`
- **GET** `/favicon.svg`: older SVG support / fallback

---

## Frontend state & persistence

`recommend.html` state is persisted per-tab using `sessionStorage`:
- `odyssey.recommend.state.v2` includes the queue, displayed movies, counters, round number, and Super mapping history.

Mode is stored in `localStorage`:
- `odyssey.mode`

---

## Environment variables

- **`GEMINI_API_KEY`**: required for Super mode and Regular fallback
- **`TMDB_API_KEY`**: required for poster lookup

Security note:
- This repo includes `.env.docker` as a convenience file, but you should treat it as an **example only** and never commit real keys.

---

## Troubleshooting

### “No CSV uploaded yet.”
- Upload a CSV from the home page first.
- Confirm `/api/csv-status` returns `csv_uploaded: true`.

### Posters are missing / blank
- Ensure `TMDB_API_KEY` is set.
- The UI should still show `default_poster.svg` if a poster can’t be found.

### Gemini returns invalid JSON / `/api/batch` fails
Gemini can sometimes return JSON-like output with small syntax errors. Odyssey’s `_extract_json()` now:
- extracts the JSON substring
- repairs common issues (trailing commas, unquoted keys, single quotes)
- retries parsing

If it still fails, the server returns a **502** and you can retry.

### Favicon not updating
- Hard refresh (`Cmd+Shift+R`) or clear site data.
- During dev, the server sets `Cache-Control: no-store` for HTML/JS/CSS and favicon assets.

---

## Development notes

- Static assets are served directly from `src/`.
- There is no frontend bundler; edit files and refresh.

---

## License

Add your preferred license here.

