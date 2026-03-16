# Plan

1. **Restructure existing files and update GitHub Actions**
   - Create a `public/` directory.
   - Move `index.html` into `public/index.html`. Add semantic tags (`<header>`, `<main>`, `<footer>`) and basic GSAP scripts as required.
   - Run Prettier to format `public/index.html`.
   - Update `.github/workflows/static.yml` to deploy only the `public/` folder to prevent Overly Broad Artifact Upload.
   - Create `.gitignore` to ignore python artifacts, sqlite databases, log files, etc.

2. **Implement Database Backend (`database.py`)**
   - Create SQLite schema for the `leads` table: `id`, `business_name`, `type`, `city`, `phone`, `contacted`, `created_at`.
   - Write helper functions to initialize and interact with the database (`get_db`, `init_db`, `add_lead`, `get_uncontacted_leads`, `mark_contacted`, `get_stats`).
   - Use dynamic db pathing to support tests (e.g., `test_leads.db`).

3. **Implement Lead Scraper (`collector.py`)**
   - Create `collector.py` using Playwright to scrape DuckDuckGo HTML for local businesses in Bahawalpur without websites.
   - Implement `generate_mock_leads()` fallback mechanism for testing or when the scraper fails.

4. **Implement Flask Application (`run.py`)**
   - Create the Flask app that serves the dashboard.
   - Endpoints: `GET /api/leads`, `GET /api/stats`, `POST /api/contact`.
   - Integrate `APScheduler` to run `collect_leads` periodically (using `is_collecting` flag to prevent concurrency).

5. **Implement Dashboard Frontend**
   - Create `templates/index.html` with a professional, responsive UI and analytics section.
   - Create `static/css/style.css` using the requested WhatsApp color palette.
   - Create `static/js/script.js` to poll APIs every 30 seconds, handle UI interactions (event delegation for "Send WhatsApp"), and construct the dynamic WhatsApp outreach URL.

6. **Write and Execute Tests**
   - `test_db.py` for DB queries.
   - `test_backend.py` for Flask endpoints.
   - `verify_dashboard.py` using Playwright and `unittest` for the frontend.
   - Start the background Flask server and execute all tests.

7. **Pre Commit Checks & Submit**
   - Run `pre_commit_instructions` to ensure all reflections and verification steps are complete.
   - Stop the background server and clean up.
   - Call submit.
