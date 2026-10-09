# AISEO.ai – Content Audit Dashboard

Full-stack SEO Content Audit tool.  
**Audit any website** – discovers pages, calculates real SEO scores, detects issues.

## Stack
- **Frontend**: HTML + CSS + Vanilla JS + Chart.js
- **Backend**: Python Flask
- **Database**: MySQL 8
- **Audit engine**: Live page fetcher + internal link discovery

## Features
- Add **any website URL** and run a live content audit
- Automatic discovery of internal pages from homepage
- SEO score, readability, meta, H1, word-count, load-time analysis
- Issues summary + traffic chart
- Pre-seeded Uncodemy & Aeonac examples

## Quick Start (Windows / Linux / Mac)

### 1. MySQL Setup

Create user + database:

```sql
CREATE USER 'aiseo'@'localhost' IDENTIFIED BY 'aiseo123';
CREATE DATABASE aiseo_audit;
GRANT ALL PRIVILEGES ON aiseo_audit.* TO 'aiseo'@'localhost';
FLUSH PRIVILEGES;
```

Load schema + seed data:

```bash
mysql -u aiseo -paiseo123 aiseo_audit < sql/schema.sql
```

### 2. Install Dependencies

```bash
cd aiseo_audit
pip install -r requirements.txt
```

### 3. Run

```bash
python run.py
```

Open → **http://127.0.0.1:5001**

> Default port is **5001** (to avoid conflict with other apps on 5000).  
> Change port: `set PORT=5002` (Windows) or `PORT=5002 python run.py` (Linux/Mac)

## How to Audit Any Website

1. Click **+ Add Website**
2. Enter URL (e.g. `https://example.com`)
3. Click **Add & Audit**
4. Wait 10–30 seconds while pages are fetched live
5. View scores, issues, and content list

You can also select an existing website and click **Run Audit** to re-analyze.

## API Endpoints

| Method | Path                    | Description                          |
|--------|-------------------------|--------------------------------------|
| GET    | `/`                     | Dashboard UI                         |
| GET    | `/api/websites`         | List websites                        |
| GET    | `/api/audit/<id>`       | Full audit data for a website        |
| POST   | `/api/run-audit`        | Run live audit (`website_id` or `url`) |
| POST   | `/api/add-website`      | Add a new website                    |

## Project Structure

```
aiseo_audit/
├── app/
│   ├── main.py            # Flask routes + API
│   ├── config.py          # DB credentials
│   ├── db.py              # PyMySQL helper (Windows + Linux compatible)
│   ├── audit_engine.py    # Live page analysis + link discovery
│   ├── templates/
│   │   └── dashboard.html
│   └── static/
│       ├── css/style.css
│       └── js/app.js
├── sql/
│   └── schema.sql
├── requirements.txt
├── run.py
└── README.md
```

## Notes
- Works on **Windows** (no Unix socket) and Linux/Mac.
- Audit fetches live HTML – internet required.
- Organic traffic is estimated (real traffic needs external SEO API).
- Max ~8 pages analyzed per audit for speed.
