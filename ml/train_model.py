from pathlib import Path
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report


# -----------------------------------------
# PATHS
# -----------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = (
    PROJECT_ROOT
    / "mumbai_women_safety_dataset.csv"
)

MODEL_DIR = PROJECT_ROOT / "models"

MODEL_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODEL_DIR / "risk_model.pkl"


# -----------------------------------------
# LOAD DATA
# -----------------------------------------

df = pd.read_csv(CSV_PATH)

print("\nDataset loaded successfully")
print("Rows:", len(df))
print("Columns:", len(df.columns))


# -----------------------------------------
# INPUT FEATURES
# -----------------------------------------

features = [

    "TotalIncidents",

    "HarassmentCases",

    "StalkingCases",

    "TheftCases",

    "OtherCases",

    "StreetLighting",

    "CrowdLevel",

    "PublicTransport",

    "PoliceStationDistanceKM",

    "SurveyUnsafePercent",

    "TimePeriod"
]


X = df[features]

y = df["RiskLevel"]


# -----------------------------------------
# COLUMN TYPES
# -----------------------------------------

numeric_features = [

    "TotalIncidents",

    "HarassmentCases",

    "StalkingCases",

    "TheftCases",

    "OtherCases",

    "PoliceStationDistanceKM",

    "SurveyUnsafePercent"
]


categorical_features = [

    "StreetLighting",

    "CrowdLevel",

    "PublicTransport",

    "TimePeriod"
]


# -----------------------------------------
# PREPROCESSING
# -----------------------------------------

preprocessor = ColumnTransformer(

    transformers=[

        (
            "num",
            "passthrough",
            numeric_features
        ),

        (
            "cat",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
            categorical_features
        )
    ]
)


# -----------------------------------------
# RANDOM FOREST MODEL
# -----------------------------------------

model = RandomForestClassifier(

    n_estimators=200,

    random_state=42,

    class_weight="balanced"
)


# -----------------------------------------
# PIPELINE
# -----------------------------------------

pipeline = Pipeline([

    ("preprocessor", preprocessor),

    ("classifier", model)

])


# -----------------------------------------
# TRAIN / TEST SPLIT
# -----------------------------------------
print("\nRisk Level Distribution:")
print(y.value_counts())

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining records:", len(X_train))
print("Testing records:", len(X_test))


# -----------------------------------------
# TRAIN MODEL
# -----------------------------------------

pipeline.fit(
    X_train,
    y_train
)


# -----------------------------------------
# PREDICTION
# -----------------------------------------

predictions = pipeline.predict(X_test)


# -----------------------------------------
# ACCURACY
# -----------------------------------------

accuracy = accuracy_score(
    y_test,
    predictions
)


print("\n-----------------------------")
print("MODEL RESULTS")
print("-----------------------------")

print(
    f"Accuracy: {accuracy * 100:.2f}%"
)


print("\nClassification Report:")

print(
    classification_report(
        y_test,
        predictions,
        zero_division=0
    )
)


# -----------------------------------------
# SAVE MODEL
# -----------------------------------------

joblib.dump(
    pipeline,
    MODEL_PATH
)


print("-----------------------------")

print(
    "Model saved successfully:"
)

print(MODEL_PATH)

print("-----------------------------")