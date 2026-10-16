from pathlib import Path
import pandas as pd

from mysql_connection import get_connection


# =========================================================
# PATH
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = PROJECT_ROOT / "mumbai_women_safety_dataset.csv"

print("CSV Path:", CSV_PATH)


# =========================================================
# READ DATASET
# =========================================================

df = pd.read_csv(CSV_PATH)

print("CSV rows found:", len(df))


# =========================================================
# CONNECT MYSQL
# =========================================================

connection = get_connection()

cursor = connection.cursor(dictionary=True)


# =========================================================
# GET SYNTHETIC DATA SOURCE
# =========================================================

cursor.execute("""
    SELECT source_id
    FROM data_source
    WHERE source_name = %s
""", (
    "Synthetic Mumbai Women Safety Dataset",
))

source = cursor.fetchone()


if source is None:
    raise Exception(
        "Synthetic Mumbai Women Safety Dataset "
        "was not found in data_source table."
    )


source_id = source["source_id"]

print("Dataset Source ID:", source_id)


# =========================================================
# CLEAR OLD IMPORTED DATA
# =========================================================

cursor.execute("""
    DELETE FROM area_observation
    WHERE source_id = %s
""", (source_id,))

connection.commit()


# =========================================================
# GET UNIQUE AREAS
# =========================================================

areas = (
    df[
        [
            "Area",
            "Latitude",
            "Longitude"
        ]
    ]
    .drop_duplicates(subset=["Area"])
    .reset_index(drop=True)
)


print("Unique areas found:", len(areas))


# =========================================================
# INSERT AREAS
# =========================================================

area_mapping = {}


for index, row in areas.iterrows():

    area_id = f"MUM-{index + 1:03d}"

    area_name = str(
        row["Area"]
    ).strip()

    area_mapping[area_name] = area_id


    # -----------------------------------------------------
    # ADMIN AREA
    # -----------------------------------------------------

    cursor.execute("""
        INSERT INTO admin_area
        (
            area_id,
            city_id,
            area_name,
            area_type,
            boundary_source_id,
            boundary_version
        )
        VALUES
        (
            %s, %s, %s, %s, %s, %s
        )

        ON DUPLICATE KEY UPDATE

            area_name = VALUES(area_name),

            area_type = VALUES(area_type),

            boundary_source_id =
                VALUES(boundary_source_id),

            boundary_version =
                VALUES(boundary_version)
    """, (
        area_id,
        1,
        area_name,
        "locality",
        source_id,
        "synthetic-v1"
    ))


    # -----------------------------------------------------
    # COORDINATES
    # -----------------------------------------------------

    cursor.execute("""
        INSERT INTO area_coordinate
        (
            area_id,
            latitude,
            longitude
        )
        VALUES
        (
            %s, %s, %s
        )

        ON DUPLICATE KEY UPDATE

            latitude = VALUES(latitude),

            longitude = VALUES(longitude)
    """, (
        area_id,
        float(row["Latitude"]),
        float(row["Longitude"])
    ))


connection.commit()


# =========================================================
# MEASURES TO IMPORT
# =========================================================

measure_columns = {

    "TotalIncidents":
        ("total_incidents", "count"),

    "HarassmentCases":
        ("harassment_cases", "count"),

    "StalkingCases":
        ("stalking_cases", "count"),

    "TheftCases":
        ("theft_cases", "count"),

    "OtherCases":
        ("other_cases", "count"),

    "PoliceStationDistanceKM":
        ("police_station_distance", "km"),

    "SurveyUnsafePercent":
        ("survey_unsafe_percent", "percent"),

    "RiskScore":
        ("risk_score", "score")
}


# =========================================================
# IMPORT DATASET OBSERVATIONS
# =========================================================

inserted_observations = 0


for _, row in df.iterrows():

    area_name = str(
        row["Area"]
    ).strip()

    area_id = area_mapping[area_name]


    # -----------------------------------------------------
    # DATE + TIME
    # -----------------------------------------------------

    observed_at = (
        str(row["Date"])
        + " "
        + str(row["Time"])
    )


    # -----------------------------------------------------
    # EXTRA INFORMATION
    # -----------------------------------------------------

    notes = (
        f"TimePeriod={row['TimePeriod']}; "
        f"StreetLighting={row['StreetLighting']}; "
        f"CrowdLevel={row['CrowdLevel']}; "
        f"PublicTransport={row['PublicTransport']}; "
        f"RiskLevel={row['RiskLevel']}"
    )


    # -----------------------------------------------------
    # INSERT 8 MEASURES
    # -----------------------------------------------------

    for csv_column, (
        measure_name,
        unit
    ) in measure_columns.items():

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
            VALUES
            (
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """, (
            area_id,
            source_id,
            observed_at,
            measure_name,
            float(row[csv_column]),
            unit,
            "synthetic_prototype",
            notes
        ))

        inserted_observations += 1


connection.commit()


# =========================================================
# VERIFY IMPORT
# =========================================================

cursor.execute("""
    SELECT COUNT(*) AS total
    FROM admin_area
""")

area_count = cursor.fetchone()["total"]


cursor.execute("""
    SELECT COUNT(*) AS total
    FROM area_coordinate
""")

coordinate_count = cursor.fetchone()["total"]


cursor.execute("""
    SELECT COUNT(*) AS total
    FROM area_observation
    WHERE source_id = %s
""", (source_id,))

observation_count = cursor.fetchone()["total"]


print()
print("========================================")
print("MYSQL DATASET IMPORT SUCCESSFUL")
print("========================================")

print("Areas:", area_count)
print("Coordinates:", coordinate_count)
print("CSV rows:", len(df))
print("Area observations:", observation_count)

print("========================================")


cursor.close()
connection.close()