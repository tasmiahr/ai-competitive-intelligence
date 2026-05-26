"""
load_to_db.py
=============
Loads all pipeline outputs into a local DuckDB database (market_intel.db).
Run this locally after each monthly pipeline run.

Usage: python load_to_db.py
       python load_to_db.py --data-dir /path/to/data
"""

import os
import re
import glob
import argparse
import duckdb
import pandas as pd
from datetime import datetime
from pathlib import Path

DB_PATH = "market_intel.db"


def get_db(db_path=DB_PATH):
    con = duckdb.connect(db_path)
    return con


def create_tables(con):
    con.execute("""
        CREATE TABLE IF NOT EXISTS news_themes (
            id          INTEGER PRIMARY KEY,
            year_month  VARCHAR,
            company     VARCHAR,
            category    VARCHAR,
            theme       VARCHAR,
            article_count INTEGER,
            date_range  VARCHAR,
            summary     VARCHAR,
            best_headline VARCHAR,
            best_source VARCHAR,
            best_url    VARCHAR,
            all_sources VARCHAR,
            all_urls    VARCHAR,
            loaded_at   TIMESTAMP DEFAULT NOW()
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS news_articles (
            id          INTEGER PRIMARY KEY,
            year_month  VARCHAR,
            company     VARCHAR,
            category    VARCHAR,
            date        DATE,
            title       VARCHAR,
            summary     VARCHAR,
            source      VARCHAR,
            url         VARCHAR,
            loaded_at   TIMESTAMP DEFAULT NOW()
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS card_offers (
            id                       INTEGER PRIMARY KEY,
            year_month               VARCHAR,
            site_name                VARCHAR,
            company                  VARCHAR,
            card_name                VARCHAR,
            card_tier                VARCHAR,
            annual_fee               DOUBLE,
            welcome_bonus_miles      INTEGER,
            spend_threshold          DOUBLE,
            spend_months             INTEGER,
            welcome_bonus_description VARCHAR,
            earn_rate                VARCHAR,
            has_limited_time_offer   BOOLEAN,
            limited_time_details     VARCHAR,
            source_url               VARCHAR,
            extraction_method        VARCHAR,
            loaded_at                TIMESTAMP DEFAULT NOW()
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS visual_changes (
            id              INTEGER PRIMARY KEY,
            year_month      VARCHAR,
            site_name       VARCHAR,
            card_name       VARCHAR,
            change_type     VARCHAR,
            previous_value  VARCHAR,
            current_value   VARCHAR,
            severity        VARCHAR,
            notes           VARCHAR,
            change_summary  VARCHAR,
            confidence      VARCHAR,
            loaded_at       TIMESTAMP DEFAULT NOW()
        )
    """)
    print("✅ Tables created/verified")


def extract_year_month(filepath):
    """Extract YYYY_MM from filename."""
    match = re.search(r"(\d{4})_(\d{2})", filepath)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    return datetime.now().strftime("%Y-%m")


def load_news_themes(con, data_dir):
    """Load from news_themes_YYYY_MM.xlsx Themes sheet."""
    files = glob.glob(os.path.join(data_dir, "news_themes_*.xlsx"))
    if not files:
        print("  ⚠️  No news_themes xlsx files found")
        return 0

    total = 0
    for filepath in sorted(files):
        year_month = extract_year_month(filepath)

        # Skip if already loaded
        existing = con.execute(
            "SELECT COUNT(*) FROM news_themes WHERE year_month = ?", [year_month]
        ).fetchone()[0]
        if existing > 0:
            print(f"  ⏭️  Themes {year_month} already loaded ({existing} rows)")
            continue

        try:
            df = pd.read_excel(filepath, sheet_name="Themes")
            df.columns = [c.lower().replace(" ", "_").replace("#", "num") for c in df.columns]
            df["year_month"] = year_month

            col_map = {
                "num_articles": "article_count",
                "best_headline": "best_headline",
                "best_source": "best_source",
                "best_url": "best_url",
                "all_sources": "all_sources",
                "all_urls": "all_urls",
            }
            df = df.rename(columns=col_map)

            # Get next ID
            max_id = con.execute("SELECT COALESCE(MAX(id), 0) FROM news_themes").fetchone()[0]

            for i, row in df.iterrows():
                max_id += 1
                con.execute("""
                    INSERT INTO news_themes
                    (id, year_month, company, category, theme, article_count, date_range,
                     summary, best_headline, best_source, best_url, all_sources, all_urls)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    max_id, year_month,
                    row.get("company", ""), row.get("category", ""),
                    row.get("theme", ""), row.get("article_count", 0),
                    row.get("date_range", ""), row.get("summary", ""),
                    row.get("best_headline", ""), row.get("best_source", ""),
                    row.get("best_url", ""), row.get("all_sources", ""),
                    row.get("all_urls", ""),
                ])

            print(f"  ✅ Themes {year_month}: {len(df)} rows loaded")
            total += len(df)
        except Exception as e:
            print(f"  ❌ Error loading {filepath}: {e}")

    return total


def load_news_articles(con, data_dir):
    """Load from news_articles_YYYY_MM.csv."""
    files = glob.glob(os.path.join(data_dir, "news_articles_*.csv"))
    # Also try old naming
    files += glob.glob(os.path.join(data_dir, "google_news_*.csv"))
    if not files:
        print("  ⚠️  No news_articles csv files found")
        return 0

    total = 0
    for filepath in sorted(set(files)):
        year_month = extract_year_month(filepath)
        existing = con.execute(
            "SELECT COUNT(*) FROM news_articles WHERE year_month = ?", [year_month]
        ).fetchone()[0]
        if existing > 0:
            print(f"  ⏭️  Articles {year_month} already loaded ({existing} rows)")
            continue

        try:
            df = pd.read_csv(filepath)
            df["year_month"] = year_month
            max_id = con.execute("SELECT COALESCE(MAX(id), 0) FROM news_articles").fetchone()[0]

            for i, row in df.iterrows():
                max_id += 1
                con.execute("""
                    INSERT INTO news_articles
                    (id, year_month, company, category, date, title, summary, source, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    max_id, year_month,
                    row.get("company", ""), row.get("category", ""),
                    row.get("date", None), row.get("title", ""),
                    row.get("summary", ""), row.get("source", ""),
                    row.get("url", ""),
                ])

            print(f"  ✅ Articles {year_month}: {len(df)} rows loaded")
            total += len(df)
        except Exception as e:
            print(f"  ❌ Error loading {filepath}: {e}")

    return total


def load_card_offers(con, data_dir):
    """Load from card_data_*.xlsx or card_data_*.json."""
    files = glob.glob(os.path.join(data_dir, "card_data_*.xlsx"))
    if not files:
        print("  ⚠️  No card_data xlsx files found")
        return 0

    total = 0
    for filepath in sorted(files):
        year_month = extract_year_month(filepath)
        existing = con.execute(
            "SELECT COUNT(*) FROM card_offers WHERE year_month = ?", [year_month]
        ).fetchone()[0]
        if existing > 0:
            print(f"  ⏭️  Card offers {year_month} already loaded ({existing} rows)")
            continue

        try:
            df = pd.read_excel(filepath)
            df.columns = [c.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("$", "") for c in df.columns]
            df["year_month"] = year_month
            max_id = con.execute("SELECT COALESCE(MAX(id), 0) FROM card_offers").fetchone()[0]

            for i, row in df.iterrows():
                if "⚠️" in str(row.get("card_name", "")):
                    continue
                max_id += 1
                con.execute("""
                    INSERT INTO card_offers
                    (id, year_month, site_name, company, card_name, card_tier,
                     annual_fee, welcome_bonus_miles, spend_threshold, spend_months,
                     welcome_bonus_description, earn_rate, has_limited_time_offer,
                     limited_time_details, source_url, extraction_method)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    max_id, year_month,
                    row.get("site", ""), row.get("company", ""),
                    row.get("card_name", ""), row.get("tier", ""),
                    row.get("annual_fee"), row.get("welcome_bonus_miles"),
                    row.get("spend_threshold"), row.get("spend_months"),
                    row.get("bonus_description", ""), row.get("earn_rate", ""),
                    bool(row.get("limited_time", False)),
                    row.get("limited_time_details", ""),
                    row.get("source_url", ""), row.get("method", ""),
                ])

            print(f"  ✅ Card offers {year_month}: loaded")
            total += len(df)
        except Exception as e:
            print(f"  ❌ Error loading {filepath}: {e}")

    return total


def load_visual_changes(con, data_dir):
    """Load from change_report.xlsx Changes Detail sheet."""
    files = glob.glob(os.path.join(data_dir, "change_report*.xlsx"))
    if not files:
        print("  ⚠️  No change_report xlsx files found")
        return 0

    total = 0
    for filepath in sorted(files):
        year_month = extract_year_month(filepath)
        if year_month == datetime.now().strftime("%Y-%m"):
            year_month = datetime.now().strftime("%Y-%m")

        existing = con.execute(
            "SELECT COUNT(*) FROM visual_changes WHERE year_month = ?", [year_month]
        ).fetchone()[0]
        if existing > 0:
            print(f"  ⏭️  Visual changes {year_month} already loaded ({existing} rows)")
            continue

        try:
            df = pd.read_excel(filepath, sheet_name="Changes Detail")
            df["year_month"] = year_month
            max_id = con.execute("SELECT COALESCE(MAX(id), 0) FROM visual_changes").fetchone()[0]

            for i, row in df.iterrows():
                max_id += 1
                con.execute("""
                    INSERT INTO visual_changes
                    (id, year_month, site_name, card_name, change_type,
                     previous_value, current_value, severity, notes,
                     change_summary, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    max_id, year_month,
                    row.get("Site", ""), row.get("Card Name", ""),
                    row.get("Change Type", ""), row.get("Previous Value", ""),
                    row.get("Current Value", ""), row.get("Severity", ""),
                    row.get("Notes", ""), "", row.get("Confidence", ""),
                ])

            print(f"  ✅ Visual changes {year_month}: {len(df)} rows loaded")
            total += len(df)
        except Exception as e:
            print(f"  ❌ Error loading {filepath}: {e}")

    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data", help="Path to data directory")
    parser.add_argument("--db", default=DB_PATH, help="DuckDB file path")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Loading pipeline outputs into DuckDB")
    print(f"  Data dir: {args.data_dir}")
    print(f"  DB: {args.db}")
    print(f"{'='*60}\n")

    con = get_db(args.db)
    create_tables(con)

    print("\n📰 Loading news themes...")
    load_news_themes(con, args.data_dir)

    print("\n📄 Loading news articles...")
    load_news_articles(con, args.data_dir)

    print("\n💳 Loading card offers...")
    load_card_offers(con, args.data_dir)

    print("\n🖼️  Loading visual changes...")
    load_visual_changes(con, args.data_dir)

    # Summary
    print(f"\n{'='*60}")
    print("  Database summary:")
    for table in ["news_themes", "news_articles", "card_offers", "visual_changes"]:
        count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {count} rows")
    print(f"  DB saved to: {args.db}")
    print(f"{'='*60}\n")

    con.close()


if __name__ == "__main__":
    main()
