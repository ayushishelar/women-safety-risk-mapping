from pathlib import Path
import pandas as pd
import joblib


# -----------------------------------------
# PATH
# -----------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = PROJECT_ROOT / "models" / "risk_model.pkl"


# -----------------------------------------
# LOAD MODEL
# -----------------------------------------

model = joblib.load(MODEL_PATH)

print("\nWomen Safety Risk Prediction System")
print("------------------------------------")


# -----------------------------------------
# USER INPUT
# -----------------------------------------

total_incidents = int(
    input("Total incidents: ")
)

harassment_cases = int(
    input("Harassment cases: ")
)

stalking_cases = int(
    input("Stalking cases: ")
)

theft_cases = int(
    input("Theft cases: ")
)

other_cases = int(
    input("Other cases: ")
)

street_lighting = input(
    "Street lighting (Poor/Average/Good): "
).title()

crowd_level = input(
    "Crowd level (Low/Medium/High): "
).title()

public_transport = input(
    "Public transport (Poor/Average/Good): "
).title()

police_distance = float(
    input("Police station distance (KM): ")
)

survey_unsafe = float(
    input("Survey unsafe percentage: ")
)

time_period = input(
    "Time period (Day/Evening/Night): "
).title()


# -----------------------------------------
# CREATE DATAFRAME
# -----------------------------------------

input_data = pd.DataFrame([{

    "TotalIncidents":
        total_incidents,

    "HarassmentCases":
        harassment_cases,

    "StalkingCases":
        stalking_cases,

    "TheftCases":
        theft_cases,

    "OtherCases":
        other_cases,

    "StreetLighting":
        street_lighting,

    "CrowdLevel":
        crowd_level,

    "PublicTransport":
        public_transport,

    "PoliceStationDistanceKM":
        police_distance,

    "SurveyUnsafePercent":
        survey_unsafe,

    "TimePeriod":
        time_period
}])


# -----------------------------------------
# PREDICT
# -----------------------------------------

prediction = model.predict(
    input_data
)[0]


# -----------------------------------------
# PROBABILITY
# -----------------------------------------

probabilities = model.predict_proba(
    input_data
)[0]

classes = model.classes_


# -----------------------------------------
# RESULT
# -----------------------------------------

print("\n================================")
print("SAFETY RISK RESULT")
print("================================")

print(
    "Predicted Risk Level:",
    prediction
)

print("\nPrediction Confidence:")

for risk_class, probability in zip(
        classes,
        probabilities):

    print(
        f"{risk_class}: "
        f"{probability * 100:.2f}%"
    )


# -----------------------------------------
# SAFETY MESSAGE
# -----------------------------------------

if prediction == "High":

    print(
        "\n⚠ HIGH RISK AREA"
    )

    print(
        "Extra safety precautions are recommended."
    )


elif prediction == "Medium":

    print(
        "\n⚠ MEDIUM RISK AREA"
    )

    print(
        "Remain alert while travelling in this area."
    )


else:

    print(
        "\n✓ LOW RISK AREA"
    )

    print(
        "The area currently has comparatively lower risk."
    )