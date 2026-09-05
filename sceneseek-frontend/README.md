# SceneSeek Frontend (scaffold)

React + Vite scaffold for SceneSeek, built to replace the old Jinja2 templates.
Currently wired to **mock data** — see `src/api/client.js`.

## Structure

```
src/
├── config/queryTypes.js        # the 3 query types — single source of truth
├── api/client.js                # ALL network calls go through here (mock for now)
├── context/
│   ├── SearchContext.jsx        # search state/actions for the Home page
│   └── ModalContext.jsx         # shared image-lightbox state
├── components/
│   ├── layout/                  # Navbar, Layout
│   ├── search/                  # TypeSelector, SearchForm, KeywordChips, SearchOptions
│   ├── results/                 # ResultsGrid, GalleryItem, FeedbackButtons, Pagination
│   └── modal/                   # ImageModal (one shared lightbox, not three copies)
├── pages/
│   ├── HomePage.jsx              # search + results
│   └── DataPage.jsx              # browse keyframes by video_ID/timestamp
├── styles/theme.css              # all CSS variables + classes, one file
└── App.jsx                       # state-based Home/Data routing
```

## "I need to change X — which file?"

| Change | File(s) to touch |
|---|---|
| Add/edit a query type (e.g. a 4th type) | `config/queryTypes.js` only |
| Swap mock data for the real backend | `api/client.js` only — flip `USE_MOCK = false`, fill in real endpoints |
| Change colors / spacing / fonts | `styles/theme.css` — variables at the top |
| Change what a results tile looks like | `components/results/GalleryItem.jsx` (used by both Home and Data pages) |
| Change modal/lightbox behavior | `components/modal/ImageModal.jsx` + `context/ModalContext.jsx` (one place, used everywhere) |
| Add a new page | add to `pages/`, register in `PAGES` map in `App.jsx`, add a link in `Navbar.jsx` |
| Add a backend route | add the route, then point to it from `endpoint` in `config/queryTypes.js` (Type 1/2/3) or directly in `api/client.js` (Data page, feedback) |

## Notes on intentional design choices

- **Type 2 (start/end event)** doesn't need special-case code in `SearchForm.jsx` — it's just a type whose config has two fields instead of one. The form renders whatever fields the active type declares.
- **The modal was duplicated 3 times** in the old templates (`data.html`, `show_results.html`, `v0_search_results.html`), each with its own copy-pasted JS. Here it's one `ImageModal` + one `ModalContext`, used by both Home results and the Data browser.
- **`database_name` (CLIP_v0 / CLIP_v2) was removed** — SceneSeek uses a single jina-clip-v2 model, so there's no model-version picker anymore. If a model A/B picker is ever needed again, it would be a new option in `SearchOptions.jsx`, not a query-type concern.
- **Hashtags → keyword chips**: same interaction pattern as before (chip list + free-text add), renamed component (`KeywordChips.jsx`) and renamed concept (keyword graph instead of hashtag graph) to match the Vietnamese-language design discussed earlier (no diacritics-stripping, proper word segmentation expected server-side).

## Running

```bash
npm install
npm run dev
```

Mock data renders immediately, no backend needed. The Vite dev server proxies
`/api/*` to `http://localhost:8000` (see `vite.config.js`) for when the real
FastAPI backend is ready and `USE_MOCK` is flipped off.
