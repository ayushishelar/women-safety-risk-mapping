from flask import Flask, render_template, request, jsonify
from pathlib import Path
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import math
import pandas as pd
import joblib
import requests


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)
app.secret_key = "women_safety_secret_key_2026"


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

DB_PATH = PROJECT_ROOT / "data" / "mumbai_safety.db"

MODEL_PATH = PROJECT_ROOT / "models" / "risk_model.pkl"

CSV_PATH = PROJECT_ROOT / "mumbai_women_safety_dataset.csv"


# ============================================================
# SQLITE DATABASE CONNECTION
# ============================================================

def get_connection():

    connection = sqlite3.connect(DB_PATH)

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ============================================================
# CREATE INCIDENT TABLE IF NOT EXISTS
# ============================================================

def create_incident_table():

    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS incident_report
        (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,

            incident_type TEXT NOT NULL,

            area_id TEXT NOT NULL,

            incident_date TEXT NOT NULL,

            incident_time TEXT NOT NULL,

            description TEXT,

            is_anonymous INTEGER NOT NULL DEFAULT 1,

            report_status TEXT NOT NULL DEFAULT 'Submitted',

            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (area_id)
                REFERENCES admin_area(area_id)
        )
    """)

    connection.commit()

    connection.close()

# ============================================================
# CREATE SOS TABLES
# ============================================================

def create_sos_tables():

    connection = get_connection()

    # Emergency contacts
    connection.execute("""
        CREATE TABLE IF NOT EXISTS emergency_contact
        (
            contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            contact_name TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            relationship TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # SOS alerts
    connection.execute("""
        CREATE TABLE IF NOT EXISTS sos_alert
        (
            sos_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            alert_message TEXT,
            alert_status TEXT DEFAULT 'Triggered',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()

    print("SOS tables ready.")
# ============================================================
# LOAD MODEL
# ============================================================

model = joblib.load(MODEL_PATH)


# ============================================================
# LOAD DATASET
# ============================================================

df = pd.read_csv(CSV_PATH)

print()
print("Dataset loaded successfully")
print("Records:", len(df))
print("Model:", MODEL_PATH)
print()


# ============================================================
# HOME PAGE
# ============================================================


@app.route("/")
def home():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "index.html",
        user_name=session.get("full_name")
    )


# ============================================================
# GET ALL AREAS
# ============================================================

@app.route("/api/areas", methods=["GET"])
def get_areas():

    connection = None

    try:

        connection = get_connection()

        rows = connection.execute("""
            SELECT
                a.area_id,
                a.area_name,
                c.latitude,
                c.longitude

            FROM admin_area AS a

            LEFT JOIN area_coordinate AS c
                ON a.area_id = c.area_id

            ORDER BY a.area_name
        """).fetchall()

        areas = []

        for row in rows:

            areas.append({

                "area_id":
                    row["area_id"],

                "area_name":
                    row["area_name"],

                "latitude":
                    float(row["latitude"])
                    if row["latitude"] is not None
                    else None,

                "longitude":
                    float(row["longitude"])
                    if row["longitude"] is not None
                    else None

            })

        print(
            "Areas loaded from SQLite:",
            len(areas)
        )

        return jsonify(areas)

    except Exception as e:

        print(
            "ERROR loading areas:",
            e
        )

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if connection is not None:

            connection.close()


# ============================================================
# HELPER
# MOST COMMON CATEGORICAL VALUE
# ============================================================

def most_common(series):

    mode = series.mode()

    if len(mode) == 0:

        return series.iloc[0]

    return mode.iloc[0]


# ============================================================
# GET AREA FEATURES
# ============================================================

def get_area_features(
    area_name,
    time_period=None
):

    # --------------------------------------------------------
    # FILTER SELECTED AREA
    # --------------------------------------------------------

    area_data = df[
        df["Area"] == area_name
    ].copy()

    if area_data.empty:

        return None


    # --------------------------------------------------------
    # FILTER SELECTED TIME PERIOD
    # --------------------------------------------------------

    if time_period:

        filtered = area_data[
            area_data["TimePeriod"]
            == time_period
        ].copy()

        if not filtered.empty:

            area_data = filtered


    # --------------------------------------------------------
    # AGGREGATE NUMERIC VALUES
    # --------------------------------------------------------

    total_incidents = round(
        area_data[
            "TotalIncidents"
        ].mean()
    )

    harassment = round(
        area_data[
            "HarassmentCases"
        ].mean()
    )

    stalking = round(
        area_data[
            "StalkingCases"
        ].mean()
    )

    theft = round(
        area_data[
            "TheftCases"
        ].mean()
    )

    other = round(
        area_data[
            "OtherCases"
        ].mean()
    )

    police_distance = round(
        area_data[
            "PoliceStationDistanceKM"
        ].mean(),
        2
    )

    survey_unsafe = round(
        area_data[
            "SurveyUnsafePercent"
        ].mean(),
        2
    )

    risk_score = round(
        area_data[
            "RiskScore"
        ].mean(),
        1
    )


    # --------------------------------------------------------
    # CATEGORICAL VALUES
    # --------------------------------------------------------

    lighting = most_common(
        area_data[
            "StreetLighting"
        ]
    )

    crowd = most_common(
        area_data[
            "CrowdLevel"
        ]
    )

    transport = most_common(
        area_data[
            "PublicTransport"
        ]
    )


    # --------------------------------------------------------
    # TIME PERIOD
    # --------------------------------------------------------

    if time_period:

        selected_time = time_period

    else:

        selected_time = most_common(
            area_data[
                "TimePeriod"
            ]
        )


    # --------------------------------------------------------
    # RETURN FEATURES
    # --------------------------------------------------------

    return {

        "TotalIncidents":
            total_incidents,

        "HarassmentCases":
            harassment,

        "StalkingCases":
            stalking,

        "TheftCases":
            theft,

        "OtherCases":
            other,

        "StreetLighting":
            lighting,

        "CrowdLevel":
            crowd,

        "PublicTransport":
            transport,

        "PoliceStationDistanceKM":
            police_distance,

        "SurveyUnsafePercent":
            survey_unsafe,

        "TimePeriod":
            selected_time,

        "RiskScore":
            risk_score,

        "ObservationCount":
            len(area_data)

    }


# ============================================================
# RUN RANDOM FOREST PREDICTION
# ============================================================

def run_prediction(features):

    input_data = pd.DataFrame(
        [
            {

                "TotalIncidents":
                    features[
                        "TotalIncidents"
                    ],

                "HarassmentCases":
                    features[
                        "HarassmentCases"
                    ],

                "StalkingCases":
                    features[
                        "StalkingCases"
                    ],

                "TheftCases":
                    features[
                        "TheftCases"
                    ],

                "OtherCases":
                    features[
                        "OtherCases"
                    ],

                "StreetLighting":
                    features[
                        "StreetLighting"
                    ],

                "CrowdLevel":
                    features[
                        "CrowdLevel"
                    ],

                "PublicTransport":
                    features[
                        "PublicTransport"
                    ],

                "PoliceStationDistanceKM":
                    features[
                        "PoliceStationDistanceKM"
                    ],

                "SurveyUnsafePercent":
                    features[
                        "SurveyUnsafePercent"
                    ],

                "TimePeriod":
                    features[
                        "TimePeriod"
                    ]

            }
        ]
    )


    # --------------------------------------------------------
    # PREDICT CLASS
    # --------------------------------------------------------

    prediction = model.predict(
        input_data
    )[0]


    # --------------------------------------------------------
    # PREDICT PROBABILITIES
    # --------------------------------------------------------

    probabilities = (
        model.predict_proba(
            input_data
        )[0]
    )

    probability_dict = {}

    for class_name, probability in zip(
        model.classes_,
        probabilities
    ):

        probability_dict[
            str(class_name)
        ] = round(
            float(probability)
            * 100,
            2
        )

    confidence = round(
        max(
            probability_dict.values()
        ),
        2
    )

    return (
        str(prediction),
        confidence,
        probability_dict
    )


# ============================================================
# PREDICT SELECTED AREA
# ============================================================

@app.route(
    "/api/predict",
    methods=["POST"]
)
def predict():

    data = (
        request.get_json()
        or {}
    )

    area_name = data.get(
        "area"
    )

    time_period = data.get(
        "time_period"
    )


    # Empty means overall / historical
    if time_period == "":

        time_period = None


    if not area_name:

        return jsonify(
            {
                "error":
                    "Please select an area."
            }
        ), 400


    valid_periods = [
        "Day",
        "Evening",
        "Night"
    ]


    if (
        time_period
        and
        time_period
        not in valid_periods
    ):

        return jsonify(
            {
                "error":
                    "Invalid time period."
            }
        ), 400


    features = get_area_features(
        area_name,
        time_period
    )


    if features is None:

        return jsonify(
            {
                "error":
                    "Area data not found."
            }
        ), 404


    (
        prediction,
        confidence,
        probabilities
    ) = run_prediction(
        features
    )


    return jsonify(
        {

            "area":
                area_name,

            "risk_level":
                prediction,

            "risk_score":
                features[
                    "RiskScore"
                ],

            "confidence":
                confidence,

            "probabilities":
                probabilities,

            "time_period":
                features[
                    "TimePeriod"
                ],

            "observation_count":
                features[
                    "ObservationCount"
                ],

            "total_incidents":
                features[
                    "TotalIncidents"
                ],

            "harassment_cases":
                features[
                    "HarassmentCases"
                ],

            "stalking_cases":
                features[
                    "StalkingCases"
                ],

            "theft_cases":
                features[
                    "TheftCases"
                ],

            "other_cases":
                features[
                    "OtherCases"
                ],

            "street_lighting":
                features[
                    "StreetLighting"
                ],

            "crowd_level":
                features[
                    "CrowdLevel"
                ],

            "public_transport":
                features[
                    "PublicTransport"
                ],

            "police_distance":
                features[
                    "PoliceStationDistanceKM"
                ],

            "survey_unsafe":
                features[
                    "SurveyUnsafePercent"
                ]

        }
    )


# ============================================================
# GET PREDICTIONS FOR ALL AREAS
# ============================================================

@app.route(
    "/api/all-predictions"
)
def all_predictions():

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT
                a.area_name,
                c.latitude,
                c.longitude

            FROM admin_area a

            JOIN area_coordinate c
                ON a.area_id = c.area_id

            ORDER BY a.area_name
            """
        ).fetchall()

    finally:

        connection.close()


    results = []


    for row in rows:

        area_name = row[
            "area_name"
        ]

        features = get_area_features(
            area_name
        )

        if features is None:

            continue


        (
            prediction,
            confidence,
            probabilities
        ) = run_prediction(
            features
        )


        results.append(
            {

                "area":
                    area_name,

                "latitude":
                    row[
                        "latitude"
                    ],

                "longitude":
                    row[
                        "longitude"
                    ],

                "risk_level":
                    prediction,

                "risk_score":
                    features[
                        "RiskScore"
                    ],

                "confidence":
                    confidence,

                "time_period":
                    features[
                        "TimePeriod"
                    ],

                "total_incidents":
                    features[
                        "TotalIncidents"
                    ]

            }
        )


    return jsonify(
        results
    )


# ============================================================
# INCIDENT REPORTING
# GET = LOAD REPORTS
# POST = SAVE REPORT
# ============================================================

@app.route(
    "/api/incidents",
    methods=["GET", "POST"]
)
def incidents():

    connection = get_connection()


    # ========================================================
    # POST NEW INCIDENT
    # ========================================================

    if request.method == "POST":

        try:

            data = request.get_json() or {}


            incident_type = str(
                data.get(
                    "incident_type",
                    ""
                )
            ).strip()


            area_name = str(
                data.get(
                    "area",
                    ""
                )
            ).strip()


            incident_date = str(
                data.get(
                    "incident_date",
                    ""
                )
            ).strip()


            incident_time = str(
                data.get(
                    "incident_time",
                    ""
                )
            ).strip()


            description = str(
                data.get(
                    "description",
                    ""
                )
            ).strip()


            is_anonymous = bool(
                data.get(
                    "is_anonymous",
                    True
                )
            )


            # ------------------------------------------------
            # VALID INCIDENT TYPES
            # ------------------------------------------------

            allowed_types = [

                "Harassment",

                "Stalking",

                "Theft",

                "Unsafe Behaviour",

                "Poor Lighting",

                "Suspicious Activity",

                "Other"

            ]


            # ------------------------------------------------
            # VALIDATION
            # ------------------------------------------------

            if incident_type not in allowed_types:

                return jsonify({
                    "error":
                        "Please select a valid incident type."
                }), 400


            if not area_name:

                return jsonify({
                    "error":
                        "Please select an incident location."
                }), 400


            if not incident_date:

                return jsonify({
                    "error":
                        "Please select the incident date."
                }), 400


            if not incident_time:

                return jsonify({
                    "error":
                        "Please select the incident time."
                }), 400


            # ------------------------------------------------
            # FIND AREA ID
            # ------------------------------------------------

            area = connection.execute(
                """
                SELECT area_id

                FROM admin_area

                WHERE area_name = ?
                """,
                (
                    area_name,
                )
            ).fetchone()


            if area is None:

                return jsonify({
                    "error":
                        "Selected area was not found."
                }), 404


            area_id = area[
                "area_id"
            ]


            # ------------------------------------------------
            # INSERT INCIDENT INTO SQLITE
            # ------------------------------------------------

            cursor = connection.execute(
                """
                INSERT INTO incident_report
                (
                    incident_type,
                    area_id,
                    incident_date,
                    incident_time,
                    description,
                    is_anonymous,
                    report_status
                )

                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident_type,
                    area_id,
                    incident_date,
                    incident_time,
                    description,
                    1 if is_anonymous else 0,
                    "Submitted"
                )
            )


            report_id = (
                cursor.lastrowid
            )


            connection.commit()


            return jsonify({

                "success":
                    True,

                "message":
                    "Incident report submitted successfully.",

                "report_id":
                    report_id,

                "incident_type":
                    incident_type,

                "area":
                    area_name,

                "incident_date":
                    incident_date,

                "incident_time":
                    incident_time,

                "description":
                    description,

                "is_anonymous":
                    is_anonymous,

                "status":
                    "Submitted"

            }), 201


        except Exception as e:

            connection.rollback()

            print(
                "Incident submission error:",
                e
            )

            return jsonify({
                "error": str(e)
            }), 500


        finally:

            connection.close()


    # ========================================================
    # GET ALL INCIDENTS
    # ========================================================

    try:

        rows = connection.execute(
            """
            SELECT
                ir.report_id,
                ir.incident_type,
                a.area_name,
                ir.incident_date,
                ir.incident_time,
                ir.description,
                ir.is_anonymous,
                ir.report_status,
                ir.created_at

            FROM incident_report AS ir

            JOIN admin_area AS a
                ON ir.area_id = a.area_id

            ORDER BY ir.report_id DESC
            """
        ).fetchall()


        reports = []


        for row in rows:

            reports.append(
                {

                    "report_id":
                        row[
                            "report_id"
                        ],

                    "incident_type":
                        row[
                            "incident_type"
                        ],

                    "area":
                        row[
                            "area_name"
                        ],

                    "incident_date":
                        row[
                            "incident_date"
                        ],

                    "incident_time":
                        row[
                            "incident_time"
                        ],

                    "description":
                        row[
                            "description"
                        ],

                    "is_anonymous":
                        bool(
                            row[
                                "is_anonymous"
                            ]
                        ),

                    "status":
                        row[
                            "report_status"
                        ],

                    "created_at":
                        row[
                            "created_at"
                        ]

                }
            )


        return jsonify(
            reports
        )


    except Exception as e:

        print(
            "Incident loading error:",
            e
        )

        return jsonify({
            "error": str(e)
        }), 500


    finally:

        connection.close()


# ============================================================
# INCIDENT STATISTICS
# ============================================================

@app.route(
    "/api/incident-stats"
)
def incident_stats():

    connection = get_connection()

    try:

        total = connection.execute(
            """
            SELECT COUNT(*) AS total

            FROM incident_report
            """
        ).fetchone()[
            "total"
        ]


        rows = connection.execute(
            """
            SELECT
                incident_type,
                COUNT(*) AS count

            FROM incident_report

            GROUP BY incident_type
            """
        ).fetchall()


        type_counts = {

            row["incident_type"]:
                row["count"]

            for row in rows
        }


        return jsonify(
            {

                "total":
                    total,

                "harassment":
                    type_counts.get(
                        "Harassment",
                        0
                    ),

                "stalking":
                    type_counts.get(
                        "Stalking",
                        0
                    ),

                "theft":
                    type_counts.get(
                        "Theft",
                        0
                    ),

                "other":
                    sum(
                        count

                        for incident_type, count
                        in type_counts.items()

                        if incident_type not in [
                            "Harassment",
                            "Stalking",
                            "Theft"
                        ]
                    )

            }
        )

    except Exception as e:

        print(
            "Incident statistics error:",
            e
        )

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        connection.close()
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not full_name or not email or not password:
            flash("Please fill all fields.")
            return redirect(url_for("register"))

        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute(
            "SELECT user_id FROM users WHERE email = ?",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            connection.close()
            flash("Email is already registered.")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users
            (full_name, email, password, role)
            VALUES (?, ?, ?, ?)
        """, (
            full_name,
            email,
            hashed_password,
            "user"
        ))

        connection.commit()
        connection.close()

        flash("Registration successful. Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )

        user = cursor.fetchone()
        connection.close()

        if user and check_password_hash(user["password"], password):

            # Save user information in session
            session["user_id"] = user["user_id"]
            session["full_name"] = user["full_name"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            print("LOGIN SUCCESSFUL")
            print("Email:", user["email"])
            print("Role:", user["role"])

            # ADMIN
            if user["role"].strip().lower() == "admin":
                print("Redirecting to ADMIN dashboard")
                return redirect(url_for("admin_dashboard"))

            # NORMAL USER
            print("Redirecting to USER dashboard")
            return redirect(url_for("home"))

        flash("Invalid email or password.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/admin")
def admin_dashboard():

    # Check login
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Check admin role
    if session.get("role", "").strip().lower() != "admin":
        flash("Access denied. Admin only.")
        return redirect(url_for("home"))

    # Connect to SQLite
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    # ==========================================
    # REGISTERED USERS
    # ==========================================

    cursor.execute("""
        SELECT
            user_id,
            full_name,
            email,
            role,
            created_at
        FROM users
        ORDER BY user_id DESC
    """)

    users = cursor.fetchall()

    # Count normal registered users
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM users
        WHERE role = 'user'
    """)

    total_users = cursor.fetchone()["total"]

    # ==========================================
    # INCIDENT REPORTS
    # ==========================================

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM incident_report
    """)

    total_incidents = cursor.fetchone()["total"]

    # Get all incident reports
    cursor.execute("""
        SELECT
            report_id,
            incident_type,
            area_id,
            incident_date,
            incident_time,
            description,
            is_anonymous,
            report_status,
            created_at
        FROM incident_report
        ORDER BY report_id DESC
    """)

    incidents = cursor.fetchall()

    connection.close()

    # Debug output
    print("================================")
    print("ADMIN DASHBOARD")
    print("Users found:", len(users))
    print("Normal users:", total_users)
    print("Incidents:", total_incidents)
    print("================================")

    return render_template(
        "admin.html",
        admin_name=session.get("full_name"),
        users=users,
        incidents=incidents,
        total_users=total_users,
        total_incidents=total_incidents
    )

@app.route("/admin/update-status/<int:report_id>", methods=["POST"])
def update_incident_status(report_id):

    # Check login
    if "user_id" not in session:
        return redirect(url_for("login"))

    # Only admin can update incident status
    if session.get("role", "").strip().lower() != "admin":
        flash("Access denied. Admin only.")
        return redirect(url_for("home"))

    # Get selected status
    new_status = request.form.get("status", "").strip()

    # Allowed statuses
    allowed_statuses = [
        "Pending",
        "Under Review",
        "Resolved"
    ]

    if new_status not in allowed_statuses:
        flash("Invalid incident status.")
        return redirect(url_for("admin_dashboard"))

    # Connect to SQLite
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # Update status
    cursor.execute("""
        UPDATE incident_report
        SET report_status = ?
        WHERE report_id = ?
    """, (new_status, report_id))

    connection.commit()
    connection.close()

    flash("Incident status updated successfully.")

    return redirect(url_for("admin_dashboard"))

def calculate_distance(lat1, lon1, lat2, lon2):

    earth_radius = 6371.0

    lat1 = math.radians(float(lat1))
    lon1 = math.radians(float(lon1))
    lat2 = math.radians(float(lat2))
    lon2 = math.radians(float(lon2))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    distance = earth_radius * c

    return distance

@app.route("/api/safe-route", methods=["POST"])
def safe_route():

    connection = None

    try:
        data = request.get_json() or {}

        source = str(
            data.get("source", "")
        ).strip()

        destination = str(
            data.get("destination", "")
        ).strip()

        time_period = str(
            data.get("time_period", "Overall")
        ).strip()

        # -----------------------------------------
        # VALIDATION
        # -----------------------------------------

        if not source or not destination:

            return jsonify({
                "success": False,
                "message":
                    "Source and destination are required."
            }), 400

        if source == destination:

            return jsonify({
                "success": False,
                "message":
                    "Source and destination cannot be the same."
            }), 400

        # -----------------------------------------
        # GET SOURCE + DESTINATION COORDINATES
        # -----------------------------------------

        connection = get_connection()

        source_row = connection.execute(
            """
            SELECT
                a.area_name,
                c.latitude,
                c.longitude
            FROM admin_area AS a

            JOIN area_coordinate AS c
                ON a.area_id = c.area_id

            WHERE a.area_name = ?
            """,
            (source,)
        ).fetchone()

        destination_row = connection.execute(
            """
            SELECT
                a.area_name,
                c.latitude,
                c.longitude
            FROM admin_area AS a

            JOIN area_coordinate AS c
                ON a.area_id = c.area_id

            WHERE a.area_name = ?
            """,
            (destination,)
        ).fetchone()

        if source_row is None:

            return jsonify({
                "success": False,
                "message": "Source area not found."
            }), 404

        if destination_row is None:

            return jsonify({
                "success": False,
                "message": "Destination area not found."
            }), 404

        source_lat = float(
            source_row["latitude"]
        )

        source_lon = float(
            source_row["longitude"]
        )

        destination_lat = float(
            destination_row["latitude"]
        )

        destination_lon = float(
            destination_row["longitude"]
        )

        # -----------------------------------------
        # CALCULATE DISTANCE
        # -----------------------------------------

        straight_distance = calculate_distance(
            source_lat,
            source_lon,
            destination_lat,
            destination_lon
        )

        # Approximate road distance.
        # Roads are normally longer than straight line.
        estimated_road_distance = (
            straight_distance * 1.30
        )

        estimated_road_distance = round(
            estimated_road_distance,
            1
        )

        # -----------------------------------------
        # ESTIMATED TRAVEL TIME
        # -----------------------------------------

        # Prototype average urban speed = 25 km/h
        average_speed = 25

        estimated_minutes = round(
            (
                estimated_road_distance
                / average_speed
            ) * 60
        )

        # -----------------------------------------
        # GET ML RISK OF SOURCE
        # -----------------------------------------

        selected_time = None

        if time_period in [
            "Day",
            "Evening",
            "Night"
        ]:
            selected_time = time_period

        source_features = get_area_features(
            source,
            selected_time
        )

        destination_features = get_area_features(
            destination,
            selected_time
        )

        source_risk = "Unknown"
        destination_risk = "Unknown"

        if source_features:

            source_risk, _, _ = run_prediction(
                source_features
            )

        if destination_features:

            destination_risk, _, _ = run_prediction(
                destination_features
            )

        # -----------------------------------------
        # BASIC ROUTE SAFETY SCORE
        # -----------------------------------------

        risk_points = {
            "Low": 10,
            "Medium": 50,
            "High": 90
        }

        source_points = risk_points.get(
            source_risk,
            50
        )

        destination_points = risk_points.get(
            destination_risk,
            50
        )

        average_risk = (
            source_points
            + destination_points
        ) / 2

        safety_score = round(
            100 - average_risk
        )

        # -----------------------------------------
        # RETURN ROUTE
        # -----------------------------------------

        route = {

            "route_name":
                "Estimated Route",

            "areas": [
                source,
                destination
            ],

            "distance_km":
                estimated_road_distance,

            "estimated_minutes":
                estimated_minutes,

            "safety_score":
                safety_score,

            "source_risk":
                source_risk,

            "destination_risk":
                destination_risk,

            "coordinates": {

                "source": {
                    "latitude":
                        source_lat,

                    "longitude":
                        source_lon
                },

                "destination": {
                    "latitude":
                        destination_lat,

                    "longitude":
                        destination_lon
                }
            }
        }

        return jsonify({

            "success": True,

            "source":
                source,

            "destination":
                destination,

            "time_period":
                time_period,

            "routes": [
                route
            ]

        })

    except Exception as e:

        print(
            "SAFE ROUTE ERROR:",
            e
        )

        return jsonify({

            "success": False,

            "message":
                str(e)

        }), 500

    finally:

        if connection is not None:
            connection.close()
@app.route("/safe-route")
def safe_route_page():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("safe_route.html")

    # ============================================================
# SOS PAGE
# ============================================================

@app.route("/sos")
def sos_page():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "sos.html",
        user_name=session.get("full_name")
    )


# ============================================================
# GET EMERGENCY CONTACTS
# ============================================================

@app.route("/api/emergency-contacts", methods=["GET"])
def get_emergency_contacts():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login."
        }), 401

    connection = get_connection()

    try:

        rows = connection.execute("""
            SELECT
                contact_id,
                contact_name,
                phone_number,
                relationship

            FROM emergency_contact

            WHERE user_id = ?

            ORDER BY contact_id DESC
        """, (
            session["user_id"],
        )).fetchall()

        contacts = []

        for row in rows:

            contacts.append({
                "contact_id": row["contact_id"],
                "contact_name": row["contact_name"],
                "phone_number": row["phone_number"],
                "relationship": row["relationship"]
            })

        return jsonify({
            "success": True,
            "contacts": contacts
        })

    finally:

        connection.close()


# ============================================================
# ADD EMERGENCY CONTACT
# ============================================================

@app.route("/api/emergency-contacts", methods=["POST"])
def add_emergency_contact():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login."
        }), 401

    data = request.get_json() or {}

    contact_name = str(
        data.get("contact_name", "")
    ).strip()

    phone_number = str(
        data.get("phone_number", "")
    ).strip()

    relationship = str(
        data.get("relationship", "")
    ).strip()

    if not contact_name or not phone_number:

        return jsonify({
            "success": False,
            "message":
                "Contact name and phone number are required."
        }), 400

    connection = get_connection()

    try:

        cursor = connection.execute("""
            INSERT INTO emergency_contact
            (
                user_id,
                contact_name,
                phone_number,
                relationship
            )

            VALUES (?, ?, ?, ?)
        """, (
            session["user_id"],
            contact_name,
            phone_number,
            relationship
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message":
                "Emergency contact saved successfully.",
            "contact_id":
                cursor.lastrowid
        })

    except Exception as e:

        connection.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        connection.close()


# ============================================================
# DELETE EMERGENCY CONTACT
# ============================================================

@app.route(
    "/api/emergency-contacts/<int:contact_id>",
    methods=["DELETE"]
)
def delete_emergency_contact(contact_id):

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login."
        }), 401

    connection = get_connection()

    try:

        connection.execute("""
            DELETE FROM emergency_contact

            WHERE contact_id = ?
            AND user_id = ?
        """, (
            contact_id,
            session["user_id"]
        ))

        connection.commit()

        return jsonify({
            "success": True,
            "message": "Contact deleted."
        })

    finally:

        connection.close()


# ============================================================
# TRIGGER SOS
# ============================================================

@app.route("/api/sos", methods=["POST"])
def trigger_sos():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "Please login."
        }), 401

    data = request.get_json() or {}

    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is None or longitude is None:

        return jsonify({
            "success": False,
            "message":
                "Current location is required."
        }), 400

    try:

        latitude = float(latitude)
        longitude = float(longitude)

    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "message":
                "Invalid location coordinates."
        }), 400

    if not (-90 <= latitude <= 90):
        return jsonify({
            "success": False,
            "message": "Invalid latitude."
        }), 400

    if not (-180 <= longitude <= 180):
        return jsonify({
            "success": False,
            "message": "Invalid longitude."
        }), 400

    user_name = session.get(
        "full_name",
        "User"
    )

    map_link = (
        "https://www.google.com/maps/search/"
        "?api=1&query="
        f"{latitude},{longitude}"
    )

    alert_message = (
        f"SOS! {user_name} may need emergency assistance. "
        f"Current location: {map_link}"
    )

    connection = get_connection()

    try:

        cursor = connection.execute("""
            INSERT INTO sos_alert
            (
                user_id,
                latitude,
                longitude,
                alert_message,
                alert_status
            )

            VALUES (?, ?, ?, ?, ?)
        """, (
            session["user_id"],
            latitude,
            longitude,
            alert_message,
            "Triggered"
        ))

        connection.commit()

        rows = connection.execute("""
            SELECT
                contact_id,
                contact_name,
                phone_number

            FROM emergency_contact

            WHERE user_id = ?

            ORDER BY contact_id
        """, (
            session["user_id"],
        )).fetchall()

        contacts = []

        for row in rows:

            contacts.append({
                "contact_id":
                    row["contact_id"],

                "contact_name":
                    row["contact_name"],

                "phone_number":
                    row["phone_number"]
            })

        return jsonify({
            "success": True,
            "message":
                "SOS alert created successfully.",
            "sos_id":
                cursor.lastrowid,
            "latitude":
                latitude,
            "longitude":
                longitude,
            "map_link":
                map_link,
            "alert_message":
                alert_message,
            "contacts":
                contacts
        })

    except Exception as e:

        connection.rollback()

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

    finally:

        connection.close()
# ============================================================
# RUN FLASK
# ============================================================

if __name__ == "__main__":

    # Make sure incident table exists
    create_incident_table()
    create_sos_tables()

    print()

    print(
        "========================================="
    )

    print(
        "Women Safety Risk Mapping Dashboard"
    )

    print(
        "========================================="
    )

    print(
        "Dataset:",
        CSV_PATH
    )

    print(
        "Model:",
        MODEL_PATH
    )

    print(
        "Database:",
        DB_PATH
    )

    print(
        "Database Type: SQLite3"
    )

    print(
        "Incident Reporting: Enabled"
    )

    print(
        "========================================="
    )


    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )