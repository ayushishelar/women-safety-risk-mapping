from pathlib import Path
import sqlite3
import csv

# import_mumbai_data.py is inside /ml
# So parents[1] gives the main project folder
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DB_PATH = PROJECT_ROOT / "data" / "mumbai_safety.db"

CSV_PATH = PROJECT_ROOT / "mumbai_women_safety_dataset.csv"

print("Project root:", PROJECT_ROOT)
print("Database path:", DB_PATH)
print("CSV path:", CSV_PATH)


# ---------------------------------------
# CONNECT DATABASE
# ---------------------------------------

connection = sqlite3.connect(DB_PATH)

connection.execute("PRAGMA foreign_keys = ON")

cursor = connection.cursor()


# ---------------------------------------
# ADD SYNTHETIC DATA SOURCE
# ---------------------------------------

cursor.execute("""
INSERT OR IGNORE INTO data_source
(
    source_name,
    source_type,
    geographic_level,
    import_status,
    notes
)
VALUES (?, ?, ?, ?, ?)
""", (
    "Synthetic Mumbai Women Safety Dataset",
    "synthetic_prototype",
    "Mumbai locality",
    "imported",
    "Synthetic academic dataset created for ML and dashboard prototype. "
    "Not official crime statistics."
))

connection.commit()


# Get source ID

source_id = cursor.execute("""
SELECT source_id
FROM data_source
WHERE source_name = ?
""", (
    "Synthetic Mumbai Women Safety Dataset",
)).fetchone()[0]


# ---------------------------------------
# READ CSV
# ---------------------------------------

with open(CSV_PATH, "r", encoding="utf-8-sig") as file:

    reader = csv.DictReader(file)

    rows = list(reader)


print("CSV records found:", len(rows))


# ---------------------------------------
# INSERT AREAS
# ---------------------------------------

unique_areas = {}

for row in rows:

    area = row["Area"]

    if area not in unique_areas:

        unique_areas[area] = (
            float(row["Latitude"]),
            float(row["Longitude"])
        )


for index, (area, coordinates) in enumerate(
        unique_areas.items(), start=1):

    area_id = f"MUM-{index:03d}"

    cursor.execute("""
    INSERT OR IGNORE INTO admin_area
    (
        area_id,
        city_id,
        area_name,
        area_type,
        boundary_source_id,
        boundary_version
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        area_id,
        1,
        area,
        "locality",
        source_id,
        "synthetic-prototype-v1"
    ))


connection.commit()


# ---------------------------------------
# CREATE COORDINATE TABLE
# ---------------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS area_coordinate
(
    area_id TEXT PRIMARY KEY,

    latitude REAL NOT NULL,

    longitude REAL NOT NULL,

    FOREIGN KEY(area_id)
        REFERENCES admin_area(area_id)
)
""")


# Save coordinates

for area, coordinates in unique_areas.items():

    latitude, longitude = coordinates

    area_id = cursor.execute("""
        SELECT area_id
        FROM admin_area
        WHERE area_name = ?
        AND city_id = 1
    """, (area,)).fetchone()[0]

    cursor.execute("""
        INSERT OR REPLACE INTO area_coordinate
        (
            area_id,
            latitude,
            longitude
        )
        VALUES (?, ?, ?)
    """, (
        area_id,
        latitude,
        longitude
    ))


connection.commit()


# ---------------------------------------
# CLEAR OLD SYNTHETIC OBSERVATIONS
# ---------------------------------------

cursor.execute("""
DELETE FROM area_observation
WHERE source_id = ?
""", (source_id,))

connection.commit()


# ---------------------------------------
# INSERT OBSERVATIONS
# ---------------------------------------

observation_count = 0


for row in rows:

    area = row["Area"]

    area_id = cursor.execute("""
        SELECT area_id
        FROM admin_area
        WHERE area_name = ?
        AND city_id = 1
    """, (area,)).fetchone()[0]


    observed_at = (
        row["Date"]
        + " "
        + row["Time"]
    )


    # --------------------------------
    # Numerical measurements
    # --------------------------------

    measurements = [

        (
            "total_incidents",
            float(row["TotalIncidents"]),
            "count"
        ),

        (
            "harassment_cases",
            float(row["HarassmentCases"]),
            "count"
        ),

        (
            "stalking_cases",
            float(row["StalkingCases"]),
            "count"
        ),

        (
            "theft_cases",
            float(row["TheftCases"]),
            "count"
        ),

        (
            "other_cases",
            float(row["OtherCases"]),
            "count"
        ),

        (
            "police_station_distance",
            float(row["PoliceStationDistanceKM"]),
            "km"
        ),

        (
            "survey_unsafe_percent",
            float(row["SurveyUnsafePercent"]),
            "percent"
        ),

        (
            "risk_score",
            float(row["RiskScore"]),
            "score"
        )
    ]


    for measure_name, value, unit in measurements:

        cursor.execute("""
        INSERT INTO area_observation
        (
            area_id,
            source_id,
            observed_at,
            measure_name,
            measure_value,
            unit,
            record_type,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            area_id,
            source_id,
            observed_at,
            measure_name,
            value,
            unit,
            "synthetic",
            f"""
            TimePeriod={row['TimePeriod']};
            Lighting={row['StreetLighting']};
            Crowd={row['CrowdLevel']};
            Transport={row['PublicTransport']};
            RiskLevel={row['RiskLevel']}
            """
        ))

        observation_count += 1


connection.commit()


# ---------------------------------------
# VERIFY DATABASE
# ---------------------------------------

area_count = cursor.execute("""
SELECT COUNT(*)
FROM admin_area
WHERE city_id = 1
""").fetchone()[0]


coordinate_count = cursor.execute("""
SELECT COUNT(*)
FROM area_coordinate
""").fetchone()[0]


database_observations = cursor.execute("""
SELECT COUNT(*)
FROM area_observation
WHERE source_id = ?
""", (source_id,)).fetchone()[0]


connection.close()


# ---------------------------------------
# RESULT
# ---------------------------------------

print()
print("IMPORT SUCCESSFUL")
print("-----------------------------")

print("Mumbai areas:", area_count)

print("Coordinates:", coordinate_count)

print("CSV rows:", len(rows))

print("Area observations:",
      database_observations)

print("-----------------------------")

print("Database:", DB_PATH)