let statements = [];
let currentStatement = 0;
let maxStatements = 20;
let currentNum = 0;
let usedStatements = [];
let labels = JSON.parse(localStorage.getItem("aiFallacyLabels") || "[]");
let labelerId = "";
let aiPrediction = null;
let surveyPrompted = false;
const SURVEY_URL = "https://forms.gle/RUZeN1aMqXJisXoa8";

const API_BASE = "https://emotion-labeling-ofk6.onrender.com";
const supabaseUrl = "https://wpvypzxbkdflozuhwreo.supabase.co";
const supabaseAnonKey = "sb_publishable_TcwieLKitD8Zbi8tDB8GEA_64yKNW_u";
const supabaseClient = window.supabase ? window.supabase.createClient(supabaseUrl, supabaseAnonKey) : null;

fetch("fallacy_dataset.json")
    .then(response => response.json())
    .then(data => {
        statements = data;
        showStatement();
    })
    .catch(() => {
        document.getElementById("statement").textContent =
            "Unable to load the statement dataset.";
    });

function showStatement() {
    if (!statements.length) {
        document.getElementById("statement").textContent = "No statements available.";
        document.getElementById("progress").textContent = "0 / 0";
        return;
    }

    if (currentStatement >= maxStatements) {
        document.getElementById("statement").textContent = "You finished all the statements.";
        document.getElementById("progress").textContent = `${maxStatements} / ${maxStatements}`;
        document.getElementById("prediction").textContent = "No prediction yet.";
        promptSurvey();
        return;
    }

    currentNum = Math.floor(Math.random() * statements.length);
    while (usedStatements.includes(currentNum)) {
        currentNum = Math.floor(Math.random() * statements.length);
    }
    usedStatements.push(currentNum);

    document.getElementById("statement").textContent = statements[currentNum];
    document.getElementById("progress").textContent = `${currentStatement + 1} / ${maxStatements}`;
    document.getElementById("prediction").textContent = "No prediction yet.";
    aiPrediction = null;
}

async function requestPrediction() {
    if (!statements.length) return;

    const text = statements[currentNum];
    const predictionField = document.getElementById("prediction");
    predictionField.textContent = "Generating model prediction (this may take a minute)...";

    try {
        const response = await fetch(`${API_BASE}/api/predict`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });

        if (!response.ok) {
            throw new Error("Prediction request failed");
        }

        const result = await response.json();
        aiPrediction = result.label;
        predictionField.textContent = `AI prediction: ${result.label} (${(result.score * 100).toFixed(1)}% confidence)`;
    } catch (error) {
        console.error(error);
        predictionField.textContent = "Prediction failed. Please make sure the Render backend is running.";
        aiPrediction = null;
    }
}

async function saveToSupabase({ mode, labeler, statement, fallacy }) {
    if (!supabaseClient) return;

    try {
        const { error } = await supabaseClient
            .from("task_responses")
            .insert([{ mode, labeler, statement, fallacy }]);

        if (error) {
            console.error("Supabase insert failed:", error);
        }
    } catch (error) {
        console.error("Supabase insert error:", error);
    }
}

async function saveLabel(fallacy) {
    const response = {
        mode: "ai_assisted",
        labeler: labelerId,
        statement: statements[currentNum],
        fallacy,
        ai_prediction: aiPrediction
    };

    labels.push(response);
    localStorage.setItem("aiFallacyLabels", JSON.stringify(labels));

    await saveToSupabase({
        mode: "ai_assisted",
        labeler: labelerId,
        statement: statements[currentNum],
        fallacy
    });

    currentStatement++;
    showStatement();
}

function promptSurvey() {
    if (surveyPrompted) return;
    surveyPrompted = true;

    const shouldOpen = window.confirm(
        "You have completed the labeling task. Would you like to complete the follow-up form now?"
    );

    if (shouldOpen) {
        window.open(SURVEY_URL, "_blank", "noopener,noreferrer");
    }
}

document.getElementById("startButton").addEventListener("click", () => {
    const input = document.getElementById("labelerId").value.trim();
    if (input === "") {
        alert("Please enter a uniqname.");
        return;
    }

    labelerId = input;
    document.getElementById("userSetup").style.display = "none";
    document.getElementById("labelingInterface").style.display = "block";
    const tutorialOverlay = document.getElementById("tutorialOverlay");
    if (tutorialOverlay) {
        tutorialOverlay.style.display = "flex";
    }
});

document.getElementById("requestPrediction").addEventListener("click", requestPrediction);

const tutorialOverlay = document.getElementById("tutorialOverlay");
const tutorialButton = document.getElementById("tutorialButton");
const closeTutorial = document.getElementById("closeTutorial");
const startLabeling = document.getElementById("startLabeling");

if (tutorialButton) {
    tutorialButton.addEventListener("click", () => {
        tutorialOverlay.style.display = "flex";
    });
}

if (closeTutorial) {
    closeTutorial.addEventListener("click", () => {
        tutorialOverlay.style.display = "none";
    });
}

if (startLabeling) {
    startLabeling.addEventListener("click", () => {
        tutorialOverlay.style.display = "none";
    });
}

document.querySelectorAll("[data-fallacy]").forEach(button => {
    button.addEventListener("click", () => saveLabel(button.dataset.fallacy));
});

document.getElementById("export").addEventListener("click", () => {
    const data = JSON.stringify(labels, null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ai-fallacy-labels.json";
    a.click();
    URL.revokeObjectURL(url);
});

showStatement();
