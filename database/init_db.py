"""Create the local SQLite starter database for the Mumbai safety project.

Run from the project root with: python database/init_db.py

This creates data/mumbai_safety.db. It does not import raw survey answers or
invent Mumbai incident records. The database can be deleted and recreated.
"""

from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "mumbai_safety.db"


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS city (
    city_id INTEGER PRIMARY KEY,
    city_name TEXT NOT NULL UNIQUE,
    state_name TEXT NOT NULL,
    country_name TEXT NOT NULL,
    boundary_status TEXT NOT NULL,
    notes TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS data_source (
    source_id INTEGER PRIMARY KEY,
    source_name TEXT NOT NULL UNIQUE,
    source_type TEXT NOT NULL,
    geographic_level TEXT NOT NULL,
    import_status TEXT NOT NULL,
    notes TEXT NOT NULL
);

-- Populate only after selecting a current, documented boundary dataset.
CREATE TABLE IF NOT EXISTS admin_area (
    area_id TEXT PRIMARY KEY,
    city_id INTEGER NOT NULL REFERENCES city(city_id),
    area_name TEXT NOT NULL,
    area_type TEXT NOT NULL,
    boundary_source_id INTEGER REFERENCES data_source(source_id),
    boundary_version TEXT,
    UNIQUE(city_id, area_name)
);

-- These are aggregate survey counts, not individual responses. The survey
-- did not record geography, so city_id intentionally remains NULL.
CREATE TABLE IF NOT EXISTS survey_summary (
    summary_id INTEGER PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES data_source(source_id),
    question_label TEXT NOT NULL,
    answer_label TEXT NOT NULL,
    response_count INTEGER NOT NULL CHECK(response_count >= 0),
    geography_scope TEXT NOT NULL,
    city_id INTEGER REFERENCES city(city_id),
    notes TEXT NOT NULL,
    CHECK (geography_scope != 'not_recorded' OR city_id IS NULL)
);

-- Use for future verified, area-level data. Do not mix reports, official
-- counts, and perceptions without preserving the source and measure type.
CREATE TABLE IF NOT EXISTS area_observation (
    observation_id INTEGER PRIMARY KEY,
    area_id TEXT NOT NULL REFERENCES admin_area(area_id),
    source_id INTEGER NOT NULL REFERENCES data_source(source_id),
    observed_at TEXT,
    measure_name TEXT NOT NULL,
    measure_value REAL NOT NULL,
    unit TEXT NOT NULL,
    record_type TEXT NOT NULL,
    notes TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_observation_area_time
    ON area_observation(area_id, observed_at);
CREATE INDEX IF NOT EXISTS idx_observation_measure
    ON area_observation(measure_name, record_type);
"""


def seed_database(connection: sqlite3.Connection) -> None:
    connection.execute(
        """INSERT OR IGNORE INTO city
           (city_id, city_name, state_name, country_name, boundary_status, notes)
           VALUES (1, 'Mumbai', 'Maharashtra', 'India', 'pending',
                   'City selected for the project. No ward boundaries imported yet.')"""
    )

    sources = [
        (
            "Microsoft Forms safety survey (48 responses)",
            "user_survey",
            "geography not recorded",
            "aggregate reference only",
            "Used to understand possible factors and question themes. The form has no city, ward, locality, or coordinates; do not assign its results to Mumbai.",
        ),
        (
            "Open Government Data India: Crime against Women",
            "official_statistics",
            "state/UT",
            "candidate; not imported",
            "Reference for national/state context only. Its geographic level is not sufficient for Mumbai ward-level mapping.",
        ),
        (
            "MyBMC City Map / ward reference",
            "administrative_boundary",
            "ward reference",
            "candidate; verify before use",
            "A ward map reference was found, but the page indicates an old update date. Obtain and verify a current boundary source before loading areas.",
        ),
    ]
    connection.executemany(
        """INSERT OR IGNORE INTO data_source
           (source_name, source_type, geographic_level, import_status, notes)
           VALUES (?, ?, ?, ?, ?)""",
        sources,
    )

    survey_source_id = connection.execute(
        "SELECT source_id FROM data_source WHERE source_name = ?",
        ("Microsoft Forms safety survey (48 responses)",),
    ).fetchone()[0]
    question = "Have you ever faced a threatening situation?"
    summaries = [
        ("Yes", 20),
        ("No", 28),
    ]
    connection.executemany(
        """INSERT INTO survey_summary
           (source_id, question_label, answer_label, response_count,
            geography_scope, city_id, notes)
           SELECT ?, ?, ?, ?, 'not_recorded', NULL, ?
           WHERE NOT EXISTS (
               SELECT 1 FROM survey_summary
               WHERE source_id = ? AND question_label = ? AND answer_label = ?
           )""",
        [
            (
                survey_source_id,
                question,
                answer,
                count,
                "Aggregate count from the provided workbook; not geographically attributable.",
                survey_source_id,
                question,
                answer,
            )
            for answer, count in summaries
        ],
    )


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.executescript(SCHEMA)
        seed_database(connection)

        city_count = connection.execute("SELECT COUNT(*) FROM city").fetchone()[0]
        source_count = connection.execute("SELECT COUNT(*) FROM data_source").fetchone()[0]
        area_count = connection.execute("SELECT COUNT(*) FROM admin_area").fetchone()[0]
        summary_count = connection.execute("SELECT COUNT(*) FROM survey_summary").fetchone()[0]
        observation_count = connection.execute("SELECT COUNT(*) FROM area_observation").fetchone()[0]

    print(f"Created or updated: {DB_PATH}")
    print(f"Cities: {city_count} | Sources: {source_count} | Survey summaries: {summary_count}")
    print(f"Mumbai areas: {area_count} | Area observations: {observation_count}")
    print("No individual survey responses or Mumbai incident data were imported.")


if __name__ == "__main__":
    main()
