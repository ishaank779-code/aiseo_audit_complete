import os
import sys
import random
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from app.config import Config
from app.db import db_cursor, get_connection
from app.audit_engine import run_site_audit

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.from_object(Config)
CORS(app)

FEATURED_URLS = [
    "https://uncodemy.com/course/digital-marketing-training-course-in-noida",
    "https://uncodemy.com/course/digital-marketing-training-course-in-delhi",
]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fetch_all(sql, args=None):
    with db_cursor() as cur:
        cur.execute(sql, args or ())
        return cur.fetchall()


def fetch_one(sql, args=None):
    with db_cursor() as cur:
        cur.execute(sql, args or ())
        return cur.fetchone()


def execute(sql, args=None):
    with db_cursor() as cur:
        cur.execute(sql, args or ())
        return cur.lastrowid


def seed_traffic_history(cur, website_id, base_traffic=None):
    """Insert 7 months of mock traffic so chart always has data."""
    if base_traffic is None:
        base_traffic = random.randint(8000, 25000)
    now = datetime.now()
    for i in range(6, -1, -1):
        m = (now.month - 1 - i) % 12
        label = MONTHS[m]
        # slight growth trend
        traffic = int(base_traffic * (0.75 + (6 - i) * 0.04) + random.randint(-800, 800))
        traffic = max(1000, traffic)
        cur.execute(
            "INSERT INTO traffic_history (website_id, month_label, traffic) VALUES (%s, %s, %s)",
            (website_id, label, traffic),
        )
    return base_traffic


@app.route("/")
def index():
    websites = fetch_all("SELECT id, url, name, country FROM websites ORDER BY id")
    default_id = websites[0]["id"] if websites else 1
    return render_template(
        "dashboard.html",
        websites=websites,
        default_website_id=default_id,
    )


@app.route("/api/websites")
def api_websites():
    sites = fetch_all("SELECT id, url, name, country FROM websites ORDER BY id")
    return jsonify(sites)


@app.route("/api/audit/<int:website_id>")
def api_audit(website_id):
    website = fetch_one(
        "SELECT id, url, name, country FROM websites WHERE id=%s", (website_id,)
    )
    if not website:
        return jsonify({"error": "Website not found"}), 404

    audit = fetch_one(
        "SELECT * FROM audits WHERE website_id=%s AND status='completed' "
        "ORDER BY created_at DESC LIMIT 1",
        (website_id,),
    )
    if not audit:
        return jsonify({"error": "No completed audit. Click Run Audit first."}), 404

    pages = fetch_all(
        "SELECT * FROM pages WHERE audit_id=%s ORDER BY seo_score DESC",
        (audit["id"],),
    )
    issues = fetch_all(
        "SELECT * FROM issues WHERE audit_id=%s ORDER BY count DESC",
        (audit["id"],),
    )
    traffic = fetch_all(
        "SELECT month_label AS month, traffic FROM traffic_history "
        "WHERE website_id=%s ORDER BY id",
        (website_id,),
    )

    # Checklist signals
    checks = []
    if pages:
        n = len(pages)
        kw_ok = sum(1 for p in pages if p.get("has_main_keyword_in_title"))
        checks.append({
            "label": "Main Keyword in Titles",
            "status": "ok" if kw_ok >= n * 0.5 else "need",
            "detail": "Present" if kw_ok >= n * 0.5 else "Not present",
        })
        h1_ok = sum(1 for p in pages if p.get("h1_present"))
        checks.append({
            "label": "Title, H1 and H2 tag used",
            "status": "ok" if h1_ok >= n * 0.6 else "need",
            "detail": "All right" if h1_ok >= n * 0.6 else "Not satisfactory",
        })
        meta_ok = sum(1 for p in pages if p.get("has_meta_description"))
        checks.append({
            "label": "Meta descriptions present",
            "status": "ok" if meta_ok >= n * 0.6 else "need",
            "detail": "All right" if meta_ok >= n * 0.6 else "Need improvement",
        })
        avg_words = sum(p.get("word_count") or 0 for p in pages) / n
        checks.append({
            "label": "Topic depth in data",
            "status": "ok" if avg_words >= 400 else "need",
            "detail": "All right" if avg_words >= 400 else "Thin content",
        })
    else:
        checks = [
            {"label": "Main Keyword in Titles", "status": "need", "detail": "No pages"},
            {"label": "Title, H1 and H2 tag used", "status": "need", "detail": "No pages"},
            {"label": "Meta descriptions present", "status": "need", "detail": "No pages"},
            {"label": "Topic depth in data", "status": "need", "detail": "No pages"},
        ]

    return jsonify({
        "website": website,
        "audit": {
            "id": audit["id"],
            "content_score": audit["content_score"],
            "readability_score": audit["readability_score"],
            "freshness_score": audit["freshness_score"],
            "organic_traffic": audit["organic_traffic"],
            "status": audit["status"],
            "created_at": str(audit["created_at"]) if audit.get("created_at") else None,
        },
        "checks": checks,
        "pages": [{
            "id": p["id"],
            "title": p["title"],
            "url": p["url"],
            "seo_score": p["seo_score"],
            "readability": p["readability"],
            "page_size_kb": float(p["page_size_kb"] or 0),
            "load_time_ms": p["load_time_ms"],
            "word_count": p["word_count"],
            "has_meta_description": bool(p["has_meta_description"]),
            "has_main_keyword_in_title": bool(p["has_main_keyword_in_title"]),
            "h1_present": bool(p["h1_present"]),
        } for p in pages],
        "issues": [{
            "id": i["id"],
            "type": i["issue_type"],
            "description": i["description"],
            "impact": i["impact"],
            "count": i["count"],
        } for i in issues],
        "traffic_history": traffic,
    })


@app.route("/api/run-audit", methods=["POST"])
def api_run_audit():
    data = request.get_json() or {}
    target_url = (data.get("url") or "").strip()
    website_id = data.get("website_id")

    if not target_url and not website_id:
        return jsonify({"error": "url or website_id required"}), 400

    extra = []
    if website_id:
        website = fetch_one("SELECT * FROM websites WHERE id=%s", (website_id,))
        if not website:
            return jsonify({"error": "Website not found"}), 404
        target_url = website["url"]
        if "uncodemy.com" in (website["url"] or "").lower():
            extra = FEATURED_URLS[:]
    else:
        if "uncodemy.com" in target_url.lower():
            extra = FEATURED_URLS[:]

    # Normalize URL
    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url

    try:
        summary = run_site_audit(target_url, extra_urls=extra, max_pages=8)
    except Exception as e:
        return jsonify({"error": f"Audit engine failed: {str(e)}"}), 500

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if not website_id:
                name = (
                    target_url.replace("https://", "")
                    .replace("http://", "")
                    .split("/")[0]
                )
                cur.execute(
                    "INSERT INTO websites (url, name, country) VALUES (%s, %s, %s)",
                    (target_url, name, "India"),
                )
                website_id = cur.lastrowid
                # Seed traffic for new site
                traffic_base = seed_traffic_history(cur, website_id)
            else:
                website_id = int(website_id)
                # Ensure traffic history exists
                cur.execute(
                    "SELECT COUNT(*) AS c FROM traffic_history WHERE website_id=%s",
                    (website_id,),
                )
                row = cur.fetchone()
                if not row or row["c"] == 0:
                    seed_traffic_history(cur, website_id)

            # Estimate organic traffic from score (mock)
            estimated_traffic = summary.get("organic_traffic") or 0
            if estimated_traffic == 0:
                estimated_traffic = int(
                    5000 + summary["content_score"] * 180 + random.randint(0, 3000)
                )

            cur.execute(
                """INSERT INTO audits
                   (website_id, content_score, readability_score, freshness_score,
                    organic_traffic, status)
                   VALUES (%s, %s, %s, %s, %s, 'completed')""",
                (
                    website_id,
                    summary["content_score"],
                    summary["readability_score"],
                    summary["freshness_score"],
                    estimated_traffic,
                ),
            )
            audit_id = cur.lastrowid

            for p in summary["pages"]:
                cur.execute(
                    """INSERT INTO pages
                       (website_id, audit_id, title, url, seo_score, readability,
                        page_size_kb, load_time_ms, word_count,
                        has_meta_description, has_main_keyword_in_title, h1_present)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (
                        website_id,
                        audit_id,
                        p["title"],
                        p["url"],
                        p["seo_score"],
                        p["readability"],
                        p["page_size_kb"],
                        p["load_time_ms"],
                        p["word_count"],
                        1 if p["has_meta_description"] else 0,
                        1 if p["has_main_keyword_in_title"] else 0,
                        1 if p["h1_present"] else 0,
                    ),
                )

            for iss in summary["issues"]:
                cur.execute(
                    """INSERT INTO issues
                       (audit_id, issue_type, description, impact, count)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (
                        audit_id,
                        iss.get("type", "other"),
                        iss.get("desc", ""),
                        iss.get("impact", "medium"),
                        iss.get("count", 1),
                    ),
                )

        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({
        "success": True,
        "website_id": website_id,
        "audit_id": audit_id,
        "content_score": summary["content_score"],
        "pages_analyzed": len(summary["pages"]),
        "message": "Audit completed",
    })


@app.route("/api/add-website", methods=["POST"])
def api_add_website():
    data = request.get_json() or {}
    url = (data.get("url") or "").strip()
    name = (data.get("name") or "").strip()
    country = data.get("country", "India")

    if not url:
        return jsonify({"error": "url required"}), 400

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    if not name:
        name = url.replace("https://", "").replace("http://", "").split("/")[0]

    # Avoid duplicates
    existing = fetch_one("SELECT id, url, name FROM websites WHERE url=%s", (url,))
    if existing:
        return jsonify({
            "id": existing["id"],
            "url": existing["url"],
            "name": existing["name"],
            "already_exists": True,
        })

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO websites (url, name, country) VALUES (%s, %s, %s)",
                (url, name, country),
            )
            wid = cur.lastrowid
            seed_traffic_history(cur, wid)
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"id": wid, "url": url, "name": name, "already_exists": False})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
