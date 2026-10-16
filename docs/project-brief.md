# AI-Enabled Women Safety Risk Mapping — Project Brief

**Purpose:** Consolidate the decisions and proposed scope from the shared conversation “Safety Navigation App” into the project context.

**Project level:** BSc IT final-year prototype, scoped for roughly 4–6 months.

## Project summary

Build a mobile safety-navigation prototype that estimates how risk may vary by location and time, displays the estimates on a map, and helps a user compare route options. The system also supports incident reporting, an opt-in SOS flow, and an administrative analytics view.

**One-sentence description:** An AI-assisted mobile safety system that uses historical and contextual location data to estimate area risk at a particular time, show risk on a map, compare routes, and support incident reporting and emergency contact alerts.

## User scenario

A user plans a journey home late in the evening. The app displays route choices with their estimated risk and travel time. It may explain that a faster route crosses a higher-estimated-risk area and show a lower-estimated-risk alternative. The user can view nearby reports, submit an incident report, or use an SOS control to share their location with configured contacts.

Risk scores are estimates from available data. They must not be presented as guarantees of safety or danger, and the prototype is not a replacement for emergency services.

## Core capabilities

1. **Risk map:** Display low, moderate, and high estimated-risk zones, incident markers, and optionally a heatmap.
2. **Time-and-location risk estimate:** Estimate a score from 0–100 and a corresponding category for a place and time.
3. **Route comparison:** Compare candidate routes by travel time and estimated risk; explain the trade-off and let the user choose.
4. **Incident reporting:** Submit a type, location, date/time, optional description/photo, and anonymity preference.
5. **SOS prototype:** Request current location and share it with user-configured contacts; continuous sharing can be an optional extension.
6. **Analytics dashboard:** Show report counts, trends by location/time/type, risk-zone summaries, and model evaluation results.

## Proposed technical architecture

| Layer | Proposed choice | Responsibility |
|---|---|---|
| Mobile client | Flutter (Dart) | Map, route comparison, reports, alerts, SOS UI |
| API/backend | Python + FastAPI | Authentication checks, app APIs, risk-prediction endpoint, data access |
| ML/data | Python, pandas, NumPy, scikit-learn | Feature preparation, baseline model training and evaluation |
| Geospatial database | PostgreSQL + PostGIS | Incident coordinates, spatial queries, risk zones, route-related data |
| Maps/routing | Google Maps APIs, or OpenStreetMap-based alternatives | Map display, geocoding, route options |
| Authentication | Firebase Authentication (proposed) | Email/Google/phone sign-in for prototype |
| Image storage | Firebase Storage (optional) | Optional incident evidence images |
| Push notifications | Firebase Cloud Messaging (optional) | SOS and relevant safety notifications |
| Deployment | Render/Railway + Supabase/Neon (proposed) | Prototype hosting and managed PostgreSQL |
| Version control | Git and GitHub | Source history and collaboration |

The stack is a proposal from the linked chat, not a final implementation decision. Keep the first release small; add external services only when they support a demonstrable requirement.

## Risk-model concept

**Potential input features:** location/grid or area, time, day of week, prior incident count and type/severity, lighting, crowd/population proxy, weather, nearby support services, and public event context where data is available.

**Output:** a calibrated or otherwise clearly explained 0–100 estimated risk score plus a low/moderate/high category. Candidate baseline models mentioned in the chat were logistic regression, random forest, and gradient boosting. Start with an interpretable baseline and compare it with a stronger model only if the dataset supports a meaningful evaluation.

**Workflow:** collect permitted data → clean and document it → engineer time/location features → split data without leakage → train and evaluate baseline → save the model → load it in FastAPI → return a risk estimate to the app.

Do not assume that synthetic or user-submitted data represents real-world prevalence. Clearly label demonstration data. Avoid claiming predictive accuracy until evaluated on a suitable, documented dataset. Review bias, under-reporting, location privacy, and the risk of stigmatizing areas before using or displaying categories.

## Data and privacy approach

Possible sources discussed include public/open crime datasets, user-submitted reports, and synthetic data for demonstration. Police records should only be used if legitimately available and approved. Store only the location precision and personal information needed for the prototype. Make optional photo and anonymity choices clear; protect access to reports and avoid exposing reporter identity or exact sensitive locations on a public map. Define retention and moderation rules before accepting real user submissions.

## MVP boundary

**Build first:** map with demo risk zones; route comparison using a routing source; risk API with a simple evaluated baseline or transparent demonstration scoring; incident submission and persistence; basic sign-in; a controlled SOS flow using test contacts; small analytics dashboard.

**Defer unless time/data allow:** voice-triggered SOS, continuous live sharing, automated model retraining from submissions, broad push campaigns, deep learning, live crowd-density inference, and production emergency-service integrations.

## Suggested modules

- **User mobile app:** map, risk detail, route comparison, reports, SOS, settings.
- **Backend API:** users, incidents, risk estimates, route-support endpoints, admin endpoints.
- **Prediction service:** feature transformation, model loading, prediction, model version metadata.
- **Geospatial data layer:** incidents, grid/zone aggregation, spatial lookups.
- **Admin dashboard:** reports, time/location trends, model metrics, moderation view.

## Success criteria to define

- A user can request a journey and compare at least two route options with risk and time shown.
- A report is validated, stored, and visible according to the chosen privacy/moderation policy.
- SOS can share a test user's location with configured test contacts, with clear consent and status feedback.
- Risk output is reproducible and traceable to a model/data version.
- Model evaluation uses a documented holdout strategy and appropriate metrics; the UI describes limitations.
- The prototype can be demonstrated end-to-end on a documented sample dataset.

## Open decisions

1. Select one initial geography and an available, permitted dataset.
2. Decide whether risk is predicted per grid cell, named area, or route segment.
3. Choose the routing/map provider after checking cost, terms, and student access; retain an OpenStreetMap option.
4. Define risk categories, score interpretation, minimum data thresholds, and how stale data is handled.
5. Decide moderation, anonymity, retention, access control, and precise-location handling for reports.
6. Decide the project’s actual deployment target and whether Firebase services are necessary alongside FastAPI/PostgreSQL.
7. Set evaluation metrics and document dataset limitations before making accuracy claims.

## Source and status

This brief maps the shared chat titled **“Safety Navigation App”** (share link provided by the project owner). The conversation proposed the architecture and features above; it did not establish that data sources, provider terms, deployment choices, model performance, or emergency integrations have been validated. Treat these as project proposals pending implementation and review.
