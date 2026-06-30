# Intelligent Support Framework for Stress Management

A working implementation of the project report: a Decision Support System
that combines a stress assessment questionnaire, a Random Forest stress
classifier, a collaborative-filtering recommendation engine, progress
tracking, a knowledge base, and an admin panel.

## Architecture

- **Frontend**: static HTML/CSS/vanilla JS (`frontend/`). No build step,
  no framework. All pages call the backend REST API directly via `fetch`.
  Auth is a JWT stored in `localStorage`.
- **Backend**: Python (Flask) REST API (`backend/`). Owns all business
  logic, auth, ML, and database access.
- **Database**: PostgreSQL (`backend/schema.sql`).
- **ML**: scikit-learn `RandomForestClassifier`, trained on a synthetic
  dataset (`backend/ml/train_model.py`) since no real labeled stress
  dataset was available (see Limitations in the report). Already trained
  and committed at `backend/ml/model.joblib`.

## One-time setup

1. **Database** (PostgreSQL must be running; `pg_hba.conf` here uses
   `trust` auth for localhost, so no password is needed):
   ```bash
   psql -U postgres -h 127.0.0.1 -c "CREATE DATABASE stress_support;"
   psql -U postgres -h 127.0.0.1 -d stress_support -f backend/schema.sql
   ```
   This also seeds 26 interventions and 6 knowledge-base articles.

2. **Backend deps + admin account**:
   ```bash
   cd backend
   python -m venv venv
   venv/Scripts/pip install -r requirements.txt   # venv/bin/pip on Linux/Mac
   venv/Scripts/python seed_admin.py               # creates admin / Admin@1234
   ```
   `backend/.env` has the DB connection settings — edit if your Postgres
   user/password differ from the local default.

3. **(Already done, re-run only if you want to retrain)**:
   ```bash
   venv/Scripts/python ml/train_model.py
   ```

## Running

Two processes, both must be running:

```bash
# Terminal 1 - backend API on :5000
cd backend
venv/Scripts/python app.py

# Terminal 2 - frontend static files on :8000
cd frontend
python -m http.server 8000
```

Open **http://127.0.0.1:8000/index.html**.

Admin login: `admin` / `Admin@1234` (change the password by registering
through the UI's profile flow is not yet supported for password change —
update it directly in the DB or via `seed_admin.py` if needed).

If you serve the frontend from a different host/port, update
`frontend/assets/js/config.js` (`API_BASE_URL`) and `backend/.env`
(`CORS_ORIGIN`) — CORS is currently wide open (`*`) for local dev.

## Project structure

```
backend/
  app.py                 Flask entry point, blueprint registration
  config.py, db.py        config + Postgres connection helper
  auth_utils.py            JWT issue/verify, bcrypt, @token_required/@admin_required
  questions.py             the 10-item assessment + theme mapping
  recommend_engine.py      collaborative filtering + content-based fallback
  schema.sql               Postgres schema + seed data (interventions, articles)
  seed_admin.py            creates the default admin account
  ml/
    train_model.py         synthetic dataset generator + RF training
    classifier.py           loads the trained model, classifies responses
    model.joblib            trained model (committed, ~76% test accuracy
                             by design — labels include intentional noise)
  routes/
    auth.py                 register / login / me
    assessment.py            questions / submit / history
    recommend.py             recommendations for an assessment / rate intervention
    progress.py              check-ins + trend summary
    knowledge.py             knowledge base browse/search
    feedback.py              user feedback
    admin.py                 users, knowledge CRUD, reports

frontend/
  index.html, login.html, register.html
  dashboard.html, assessment.html, results.html, history.html
  progress.html, knowledge.html, knowledge_detail.html
  feedback.html, profile.html
  admin/index.html, admin/users.html, admin/knowledge.html
  assets/css/style.css
  assets/js/config.js      API_BASE_URL
  assets/js/api.js          fetch wrapper, Auth helper, shared navbar
  assets/js/chart.js        dependency-free SVG line chart for progress trends
```

## Notes on the ML / recommendation design

- **Classifier**: trained on a synthetic dataset where 10 correlated
  item responses are generated from a latent "true stress" value, and
  the label is that latent value's severity bucket *plus noise* — so
  the forest has to learn from response patterns rather than just
  re-deriving `sum(responses)`. Real labeled data should replace this
  before any clinical use.
- **Recommendations**: item-based collaborative filtering over the
  `user_interventions` rating matrix (cosine similarity), falling back
  to content-based filtering (match on `severity_level` /
  `stress_category`, sorted by `effectiveness_rating`) until there's
  enough rating history (`MIN_RATINGS_FOR_CF = 5` in
  `recommend_engine.py`) — standard cold-start handling for
  recommender systems.
