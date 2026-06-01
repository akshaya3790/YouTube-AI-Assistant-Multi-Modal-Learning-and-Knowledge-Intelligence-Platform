# How to add real screenshots to the README

The README currently uses **SVG UI previews** in this folder. For a more polished GitHub page, replace them with PNG captures from your running app.

## Steps

1. Start the app:
   ```bash
   streamlit run yt_summary.py
   ```

2. Open each view and capture the window:
   - **Home** — summary after processing a video
   - **RAG Chatbot** — a question with an answer and confidence score
   - **My Dashboard** — KPI cards and charts visible
   - **Mind Map Generator** — graph rendered

3. Save PNG files in this folder (same names, `.png` extension):
   - `home.png`
   - `rag-chat.png`
   - `dashboard.png`
   - `mind-map.png`

4. Update `README.md` image paths from `.svg` to `.png`:
   ```markdown
   ![Home](docs/screenshots/home.png)
   ```

## Windows shortcut

Press **Win + Shift + S** to snip a region, or use **Win + PrtScn** for full screen.

## Optional

Use [Streamlit's built-in screenshot](https://docs.streamlit.io/) or browser DevTools (F12 → device toolbar) for consistent width (~1200px).
