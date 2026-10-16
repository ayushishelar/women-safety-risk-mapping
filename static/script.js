// =========================================================
// WOMEN SAFETY RISK MAPPING
// FRONTEND JAVASCRIPT
// =========================================================


// =========================================================
// MAP INITIALIZATION
// =========================================================

const map = L.map(
    "map"
).setView(
    [
        19.0760,
        72.8777
    ],
    11
);


// =========================================================
// OPENSTREETMAP
// =========================================================

L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {

        attribution:
            "&copy; OpenStreetMap contributors"

    }
).addTo(map);


// =========================================================
// GLOBAL VARIABLES
// =========================================================

let areas = [];

let markers = {};


// =========================================================
// RISK COLOR
// =========================================================

function getRiskColor(risk) {

    if (risk === "High") {

        return "#ef4444";

    }


    if (risk === "Medium") {

        return "#f59e0b";

    }


    return "#22c55e";

}
// =========================================================
// STEP 7 - INCIDENT REPORTING
// =========================================================

let incidentMarkers = [];


// =========================================================
// SUBMIT INCIDENT
// =========================================================

async function submitIncident() {

    const incidentType =
        document.getElementById(
            "incidentType"
        ).value;


    const area =
        document.getElementById(
            "incidentArea"
        ).value;


    const incidentDate =
        document.getElementById(
            "incidentDate"
        ).value;


    const incidentTime =
        document.getElementById(
            "incidentTime"
        ).value;


    const description =
        document.getElementById(
            "incidentDescription"
        ).value.trim();


    const isAnonymous =
        document.getElementById(
            "anonymousReport"
        ).checked;


    // -----------------------------------------------------
    // VALIDATION
    // -----------------------------------------------------

    if (!incidentType) {

        showIncidentMessage(
            "Please select an incident type.",
            false
        );

        return;
    }


    if (!area) {

        showIncidentMessage(
            "Please select the incident location.",
            false
        );

        return;
    }


    if (!incidentDate) {

        showIncidentMessage(
            "Please select the incident date.",
            false
        );

        return;
    }


    if (!incidentTime) {

        showIncidentMessage(
            "Please select the incident time.",
            false
        );

        return;
    }


    const button =
        document.getElementById(
            "submitIncidentButton"
        );


    button.disabled =
        true;


    button.textContent =
        "Submitting...";


    try {

        const response =
            await fetch(
                "/api/incidents",
                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            incident_type:
                                incidentType,

                            area:
                                area,

                            incident_date:
                                incidentDate,

                            incident_time:
                                incidentTime,

                            description:
                                description,

                            is_anonymous:
                                isAnonymous

                        })

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error
                ||
                "Unable to submit incident."
            );

        }


        showIncidentMessage(
            "Incident report submitted successfully. Report ID: "
            + data.report_id,
            true
        );


        // ---------------------------------------------
        // CLEAR FORM
        // ---------------------------------------------

        document.getElementById(
            "incidentType"
        ).value = "";


        document.getElementById(
            "incidentDescription"
        ).value = "";


        // Keep area/date/time available if desired.
        // Anonymous remains checked.


        // ---------------------------------------------
        // RELOAD REPORTS
        // ---------------------------------------------

        await loadIncidents();

        await loadIncidentStats();

    }

    catch (error) {

        console.error(
            "Incident submission error:",
            error
        );


        showIncidentMessage(
            error.message,
            false
        );

    }

    finally {

        button.disabled =
            false;


        button.textContent =
            "Submit Incident Report";

    }

}


// =========================================================
// INCIDENT MESSAGE
// =========================================================

function showIncidentMessage(
    message,
    success
) {

    const box =
        document.getElementById(
            "incidentMessage"
        );


    box.classList.remove(
        "hidden",
        "incident-success",
        "incident-error"
    );


    if (success) {

        box.classList.add(
            "incident-success"
        );

    }

    else {

        box.classList.add(
            "incident-error"
        );

    }


    box.textContent =
        message;

}


// =========================================================
// LOAD INCIDENT REPORTS
// =========================================================

async function loadIncidents() {

    try {

        const response =
            await fetch(
                "/api/incidents"
            );


        if (!response.ok) {

            throw new Error(
                "Unable to load incident reports."
            );

        }


        const reports =
            await response.json();


        // -------------------------------------------------
        // REMOVE OLD INCIDENT MARKERS
        // -------------------------------------------------

        incidentMarkers.forEach(
            marker => {

                map.removeLayer(
                    marker
                );

            }
        );


        incidentMarkers = [];


        // -------------------------------------------------
        // ADD REPORT MARKERS
        // -------------------------------------------------

        reports.forEach(
            report => {


                if (
                    report.latitude == null
                    ||
                    report.longitude == null
                ) {

                    return;

                }


                // Slight visual offset prevents every
                // incident marker from sitting exactly
                // under the area's risk circle.

                const offset =
                    (
                        report.report_id
                        % 5
                    )
                    * 0.00025;


                const marker =
                    L.marker(
                        [
                            Number(
                                report.latitude
                            )
                            + offset,

                            Number(
                                report.longitude
                            )
                            + offset
                        ]
                    );


                marker.addTo(
                    map
                );


                let descriptionText =
                    report.description
                    ?
                    escapeHtml(
                        report.description
                    )
                    :
                    "No description provided";


                marker.bindPopup(
                    `
                    <strong>
                        Submitted Incident
                    </strong>

                    <br><br>

                    Type:
                    <strong>
                        ${escapeHtml(
                            report.incident_type
                        )}
                    </strong>

                    <br>

                    Area:
                    ${escapeHtml(
                        report.area
                    )}

                    <br>

                    Date:
                    ${escapeHtml(
                        report.incident_date
                    )}

                    <br>

                    Time:
                    ${escapeHtml(
                        report.incident_time
                    )}

                    <br>

                    Status:
                    ${escapeHtml(
                        report.status
                    )}

                    <br><br>

                    ${descriptionText}
                    `
                );


                incidentMarkers.push(
                    marker
                );

            }
        );


        showRecentReports(
            reports
        );

    }

    catch (error) {

        console.error(
            "Incident loading error:",
            error
        );

    }

}


// =========================================================
// RECENT INCIDENT REPORTS
// =========================================================

function showRecentReports(
    reports
) {

    const container =
        document.getElementById(
            "recentReportsList"
        );


    container.innerHTML = "";


    if (reports.length === 0) {

        container.innerHTML =
            `
            <p class="empty-message">
                No incident reports submitted yet.
            </p>
            `;

        return;

    }


    // Show latest 6 reports.

    reports
        .slice(0, 6)
        .forEach(
            report => {


                const card =
                    document.createElement(
                        "div"
                    );


                card.className =
                    "report-card";


                card.innerHTML =
                    `
                    <div class="report-card-top">

                        <strong>
                            ${escapeHtml(
                                report.incident_type
                            )}
                        </strong>

                        <span>
                            Report #${report.report_id}
                        </span>

                    </div>


                    <p>

                        <strong>
                            Area:
                        </strong>

                        ${escapeHtml(
                            report.area
                        )}

                    </p>


                    <p>

                        <strong>
                            Date:
                        </strong>

                        ${escapeHtml(
                            report.incident_date
                        )}

                        &nbsp;

                        <strong>
                            Time:
                        </strong>

                        ${escapeHtml(
                            report.incident_time
                        )}

                    </p>


                    <p>

                        <strong>
                            Status:
                        </strong>

                        ${escapeHtml(
                            report.status
                        )}

                    </p>


                    <p class="report-description">

                        ${
                            report.description
                            ?
                            escapeHtml(
                                report.description
                            )
                            :
                            "No description provided."
                        }

                    </p>
                    `;


                container.appendChild(
                    card
                );

            }
        );

}


// =========================================================
// INCIDENT STATISTICS
// =========================================================

async function loadIncidentStats() {

    try {

        const response =
            await fetch(
                "/api/incident-stats"
            );


        if (!response.ok) {

            throw new Error(
                "Unable to load incident statistics."
            );

        }


        const data =
            await response.json();


        document.getElementById(
            "totalReports"
        ).textContent =
            data.total;


        document.getElementById(
            "harassmentReports"
        ).textContent =
            data.harassment;


        document.getElementById(
            "stalkingReports"
        ).textContent =
            data.stalking;


        document.getElementById(
            "theftReports"
        ).textContent =
            data.theft;


        document.getElementById(
            "otherReports"
        ).textContent =
            data.other;

    }

    catch (error) {

        console.error(
            "Incident statistics error:",
            error
        );

    }

}


// =========================================================
// ESCAPE USER TEXT
// =========================================================

function escapeHtml(value) {

    const div =
        document.createElement(
            "div"
        );


    div.textContent =
        String(value ?? "");


    return div.innerHTML;

}


// =========================================================
// INCIDENT SUBMIT BUTTON
// =========================================================

document.getElementById(
    "submitIncidentButton"
).addEventListener(
    "click",
    submitIncident
);

// =========================================================
// LOAD AREAS
// =========================================================

async function loadAreas() {

    try {

        const response =
            await fetch(
                "/api/areas"
            );


        if (!response.ok) {

            throw new Error(
                "Unable to load areas."
            );

        }


        areas =
            await response.json();


        // -------------------------------------------------
        // TOTAL AREA CARD
        // -------------------------------------------------

        document.getElementById(
            "totalAreas"
        ).textContent =
            areas.length;


        // -------------------------------------------------
        // AREA DROPDOWN
        // -------------------------------------------------

        const areaSelect =
            document.getElementById(
                "areaSelect"
            );
const incidentArea =
    document.getElementById(
        "incidentArea"
    );

        areas.forEach(
            area => {

// -----------------------------------------
// INCIDENT LOCATION OPTION
// -----------------------------------------

const incidentOption =
    document.createElement(
        "option"
    );

incidentOption.value =
    area.area_name;

incidentOption.textContent =
    area.area_name;

incidentArea.appendChild(
    incidentOption
);
                // -----------------------------------------
                // DROPDOWN OPTION
                // -----------------------------------------

                const option =
                    document.createElement(
                        "option"
                    );


                option.value =
                    area.area_name;


                option.textContent =
                    area.area_name;


                areaSelect.appendChild(
                    option
                );


                // -----------------------------------------
                // INITIAL GRAY MAP MARKER
                // -----------------------------------------

                const marker =
                    L.circleMarker(
                        [
                            area.latitude,
                            area.longitude
                        ],
                        {

                            radius: 8,

                            color:
                                "#64748b",

                            fillColor:
                                "#94a3b8",

                            fillOpacity:
                                0.85,

                            weight: 2

                        }
                    ).addTo(map);


                marker.bindPopup(
                    `
                    <strong>
                        ${area.area_name}
                    </strong>

                    <br><br>

                    Loading risk estimate...
                    `
                );


                // -----------------------------------------
                // CLICK MAP MARKER
                // -----------------------------------------

                marker.on(
                    "click",
                    function () {

                        areaSelect.value =
                            area.area_name;

                        predictSelectedArea();

                    }
                );


                markers[
                    area.area_name
                ] = marker;

            }
        );


        // -------------------------------------------------
        // LOAD OVERALL PREDICTIONS
        // -------------------------------------------------

        await loadAllPredictions();

    }

    catch (error) {

        console.error(
            "Area loading error:",
            error
        );

        alert(
            "Unable to load area data."
        );

    }

}


// =========================================================
// LOAD ALL AREA PREDICTIONS
// =========================================================

async function loadAllPredictions() {

    try {

        const response =
            await fetch(
                "/api/all-predictions"
            );


        if (!response.ok) {

            throw new Error(
                "Unable to load overall predictions."
            );

        }


        const predictions =
            await response.json();


        let lowCount = 0;

        let mediumCount = 0;

        let highCount = 0;


        predictions.forEach(
            data => {


                // -----------------------------------------
                // COUNT AREA RISK
                // -----------------------------------------

                if (
                    data.risk_level
                    === "Low"
                ) {

                    lowCount++;

                }

                else if (
                    data.risk_level
                    === "Medium"
                ) {

                    mediumCount++;

                }

                else if (
                    data.risk_level
                    === "High"
                ) {

                    highCount++;

                }


                // -----------------------------------------
                // FIND MAP MARKER
                // -----------------------------------------

                const marker =
                    markers[
                        data.area
                    ];


                if (!marker) {

                    return;

                }


                // -----------------------------------------
                // COLOR MARKER
                // -----------------------------------------

                const color =
                    getRiskColor(
                        data.risk_level
                    );


                marker.setStyle(
                    {

                        color:
                            color,

                        fillColor:
                            color,

                        fillOpacity:
                            0.9

                    }
                );


                // -----------------------------------------
                // POPUP
                // -----------------------------------------

                marker.bindPopup(
                    `
                    <strong>
                        ${data.area}
                    </strong>

                    <br><br>

                    Risk Level:
                    <strong>
                        ${data.risk_level}
                    </strong>

                    <br>

                    Risk Score:
                    ${Number(
                        data.risk_score
                    ).toFixed(1)}
                    /100

                    <br>

                    Model Confidence:
                    ${Number(
                        data.confidence
                    ).toFixed(1)}
                    %
                    `
                );

            }
        );


        // -------------------------------------------------
        // UPDATE SUMMARY CARDS
        // -------------------------------------------------

        document.getElementById(
            "lowCount"
        ).textContent =
            lowCount;


        document.getElementById(
            "mediumCount"
        ).textContent =
            mediumCount;


        document.getElementById(
            "highCount"
        ).textContent =
            highCount;

    }

    catch (error) {

        console.error(
            "Overall prediction error:",
            error
        );

    }

}


// =========================================================
// PREDICT SELECTED AREA
// =========================================================

async function predictSelectedArea() {

    const area =
        document.getElementById(
            "areaSelect"
        ).value;


    const timePeriod =
        document.getElementById(
            "timePeriodSelect"
        ).value;


    if (!area) {

        alert(
            "Please select an area."
        );

        return;

    }


    const button =
        document.getElementById(
            "predictButton"
        );


    button.disabled =
        true;


    button.textContent =
        "Analyzing...";


    try {

        const response =
            await fetch(
                "/api/predict",
                {

                    method:
                        "POST",

                    headers:
                        {

                            "Content-Type":
                                "application/json"

                        },

                    body:
                        JSON.stringify(
                            {

                                area:
                                    area,

                                time_period:
                                    timePeriod

                            }
                        )

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error
                ||
                "Prediction failed."
            );

        }


        console.log(
            "Prediction:",
            data
        );


        showPrediction(
            data
        );

    }

    catch (error) {

        console.error(
            "Prediction error:",
            error
        );


        alert(
            error.message
        );

    }

    finally {

        button.disabled =
            false;


        button.textContent =
            "Predict Safety Risk";

    }

}


// =========================================================
// SHOW INDIVIDUAL PREDICTION
// =========================================================

function showPrediction(data) {

    const result =
        document.getElementById(
            "predictionResult"
        );


    result.classList.remove(
        "hidden"
    );


    // -----------------------------------------------------
    // AREA
    // -----------------------------------------------------

    document.getElementById(
        "resultArea"
    ).textContent =
        data.area;


    // -----------------------------------------------------
    // RISK SCORE
    // -----------------------------------------------------

    document.getElementById(
        "riskScore"
    ).textContent =
        Number(
            data.risk_score
        ).toFixed(1);


    // -----------------------------------------------------
    // CONFIDENCE
    // -----------------------------------------------------

    document.getElementById(
        "confidence"
    ).textContent =
        Number(
            data.confidence
        ).toFixed(1)
        + "%";


    // -----------------------------------------------------
    // TIME
    // -----------------------------------------------------

    document.getElementById(
        "timePeriod"
    ).textContent =
        data.time_period;


    // -----------------------------------------------------
    // OBSERVATIONS
    // -----------------------------------------------------

    document.getElementById(
        "observationCount"
    ).textContent =
        data.observation_count;


    // -----------------------------------------------------
    // INCIDENT VALUES
    // -----------------------------------------------------

    document.getElementById(
        "incidents"
    ).textContent =
        data.total_incidents;


    document.getElementById(
        "harassment"
    ).textContent =
        data.harassment_cases;


    document.getElementById(
        "stalking"
    ).textContent =
        data.stalking_cases;


    document.getElementById(
        "theft"
    ).textContent =
        data.theft_cases;


    document.getElementById(
        "otherCases"
    ).textContent =
        data.other_cases;


    // -----------------------------------------------------
    // ENVIRONMENT VALUES
    // -----------------------------------------------------

    document.getElementById(
        "lighting"
    ).textContent =
        data.street_lighting;


    document.getElementById(
        "crowd"
    ).textContent =
        data.crowd_level;


    document.getElementById(
        "transport"
    ).textContent =
        data.public_transport;


    document.getElementById(
        "policeDistance"
    ).textContent =
        Number(
            data.police_distance
        ).toFixed(1)
        + " km";


    document.getElementById(
        "unsafe"
    ).textContent =
        Number(
            data.survey_unsafe
        ).toFixed(1)
        + "%";


    // -----------------------------------------------------
    // PROBABILITIES
    // -----------------------------------------------------

    const probabilities =
        data.probabilities || {};


    const low =
        Number(
            probabilities.Low
            || 0
        );


    const medium =
        Number(
            probabilities.Medium
            || 0
        );


    const high =
        Number(
            probabilities.High
            || 0
        );


    document.getElementById(
        "lowProbability"
    ).textContent =
        low.toFixed(1)
        + "%";


    document.getElementById(
        "mediumProbability"
    ).textContent =
        medium.toFixed(1)
        + "%";


    document.getElementById(
        "highProbability"
    ).textContent =
        high.toFixed(1)
        + "%";


    document.getElementById(
        "lowProbabilityBar"
    ).style.width =
        low + "%";


    document.getElementById(
        "mediumProbabilityBar"
    ).style.width =
        medium + "%";


    document.getElementById(
        "highProbabilityBar"
    ).style.width =
        high + "%";


    // -----------------------------------------------------
    // RISK BADGE
    // -----------------------------------------------------

    updateRiskBadge(
        data.risk_level
    );


    // -----------------------------------------------------
    // MAP
    // -----------------------------------------------------

    updateMarker(
        data.area,
        data.risk_level,
        data.risk_score,
        data.time_period
    );


    // -----------------------------------------------------
    // SAFETY MESSAGE
    // -----------------------------------------------------

    showSafetyMessage(
        data.risk_level
    );


    // -----------------------------------------------------
    // SCROLL TO RESULT
    // -----------------------------------------------------

    result.scrollIntoView(
        {

            behavior:
                "smooth",

            block:
                "start"

        }
    );

}


// =========================================================
// UPDATE RISK BADGE
// =========================================================

function updateRiskBadge(
    risk
) {

    const badge =
        document.getElementById(
            "riskBadge"
        );


    badge.className =
        "risk-badge";


    if (risk === "Low") {

        badge.classList.add(
            "risk-low"
        );

        badge.textContent =
            "LOW RISK";

    }

    else if (
        risk === "Medium"
    ) {

        badge.classList.add(
            "risk-medium"
        );

        badge.textContent =
            "MEDIUM RISK";

    }

    else {

        badge.classList.add(
            "risk-high"
        );

        badge.textContent =
            "HIGH RISK";

    }

}


// =========================================================
// UPDATE SELECTED MARKER
// =========================================================

function updateMarker(
    area,
    risk,
    score,
    timePeriod
) {

    const marker =
        markers[area];


    if (!marker) {

        return;

    }


    const color =
        getRiskColor(
            risk
        );


    marker.setStyle(
        {

            color:
                color,

            fillColor:
                color,

            fillOpacity:
                1,

            weight:
                3

        }
    );


    marker.bindPopup(
        `
        <strong>
            ${area}
        </strong>

        <br><br>

        Selected Time:
        ${timePeriod}

        <br>

        Predicted Risk:
        <strong>
            ${risk}
        </strong>

        <br>

        Risk Score:
        ${Number(
            score
        ).toFixed(1)}
        /100
        `
    );


    marker.openPopup();


    map.setView(
        marker.getLatLng(),
        13
    );

}

function showSafetyMessage(
    risk
) {

    const message =
        document.getElementById(
            "safetyMessage"
        );


    if (risk === "High") {

        message.innerHTML =
            `
            <strong>
                Higher estimated-risk conditions detected.
            </strong>

            <br>

            Prefer well-lit and populated routes,
            remain aware of your surroundings,
            and consider alternative route options.
            `;

    }

    else if (
        risk === "Medium"
    ) {

        message.innerHTML =
            `
            <strong>
                Moderate estimated-risk conditions detected.
            </strong>

            <br>

            Remain alert and prefer
            well-lit, populated routes.
            `;

    }

    else {

        message.innerHTML =
            `
            <strong>
                Lower estimated-risk conditions detected.
            </strong>

            <br>

            The prototype model indicates
            comparatively lower estimated risk
            for these conditions.
            `;

    }

}

document.getElementById(
    "predictButton"
).addEventListener(
    "click",
    predictSelectedArea
);


loadAreas();
loadIncidents();
loadIncidentStats();