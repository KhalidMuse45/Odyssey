## Odyssey

Odyssey is a lightweight movie recommendation web app. You upload your watch history (CSV), then swipe through recommendations in a **3-card carousel** with satisfying click/flip animations, a **persistent watchlist**, and two recommendation modes:

- **Regular mode**: local-first recommendations (optionally topped up by Gemini to fill a full batch).
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
- **Regular**: local recommender over a curated pool + optional Gemini top-up.
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
│  ├─ logo.svg                 # App icon (used as favicon on index.html)
│  ├─ logo.png                 # PNG logo (served by /favicon.png)
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
- A Gemini API key (required for **Super mode**, optional for Regular top-up)
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

These are the exact commands you can use to rebuild and run the container cleanly.

### 1) Stop/remove any existing container

```bash
docker rm -f messagebox 2>/dev/null || true
```

### 2) Build the image (no cache)

```bash
docker build --no-cache -t messagebox .
```

### 3) Run the container

```bash
docker run --rm --name messagebox -p 5001:5000 --env-file .env.docker messagebox
```

Notes:
- **Port mapping**: `-p 5001:5000` means the app is available at `http://localhost:5001/`.
- Your last command snippet ended with `messagebo` — the final argument should be the image name **`messagebox`**.

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
- Uses a **local curated pool** from `movie_database_top250.json`.
- The loader applies filters (see `src/recommender.py`):
  - keeps only “English-ish” (ASCII) titles
  - keeps only movies with `poster_url` starting with `http`
  - sorts by `imdb_rating` and keeps the **Top 100** as the working pool
- The backend builds a `watched_keys` set from your uploaded CSV and excludes:
  - anything you’ve watched
  - anything already shown this session (`exclude_keys`)
  - anything you already liked (taste context)
- Local scoring uses your history (and ratings when present) + optional preferences.

**Batch size target**: 80

Note: the local recommender currently caps its own output at **60** items; if Gemini is configured, the backend can fill the remainder to reach 80. If Gemini isn’t configured, Regular may return fewer than 80.

**Gemini top-up (fill-only)**:
If the backend can’t provide a full 80 fresh picks locally, it can **fill the remainder** via Gemini (if Gemini is configured) using:
- watched CSV context
- liked context (recent likes + persistent watchlist)
- exclude list (seen titles)

### Super mode (Gemini-only + explainability)

Super mode aims for deeper personalization and transparency:
- Uses the uploaded watched CSV (plus likes/watchlist) as the “taste source”.
- Makes **one Gemini call per batch** and returns:
  - `movies` (target 50, filtered server-side against watched + excluded)
  - `profiles` (used by the mapping panel)

**Batch size target delivered to UI**: 50

Note: the server filters Gemini results against watched titles + `exclude_keys`, so the response may contain fewer than 50 if many picks are duplicates/seen.

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
    - `preferredActors`: `string[]` (optional; regular only)
    - `preferredDirectors`: `string[]` (optional; regular only)
- **POST** `/api/refresh`: legacy “refresh all”
- **GET** `/api/recommendations`: legacy “current list”

### Watchlist
- **POST** `/api/like`: track a like (adds to watchlist)
- **POST** `/api/click`: legacy click tracker (kept for compatibility)
- **GET** `/api/watchlist`: get watchlist
- **POST** `/api/watchlist/remove`: remove a watchlist item

### Favicons
- `index.html` sets its own favicon links (with a cache-buster).
- `recommend.html` does not set a page-specific favicon (browser falls back to `/favicon.ico`).
- **GET** `/favicon.png`: served from `src/logo.png`
- **GET** `/favicon.svg`: SVG route (fallback/legacy)

---

## Frontend state & persistence

`recommend.html` state is persisted per-tab using `sessionStorage`:
- `odyssey.recommend.state.v2` includes the queue, displayed movies, counters, round number, and Super mapping history.

Mode is stored in `localStorage`:
- `odyssey.mode`

---

## Environment variables

- **`GEMINI_API_KEY`**: required for Super mode; optional for Regular top-up
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

If it still fails, the server returns a **502** and you can retry.
