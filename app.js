let statements = [];

let currentStatement = 0;
let maxStatements = 20;

let currentNum = 0;
let usedStatements = [];

let labels = JSON.parse(
    localStorage.getItem("fallacyLabels") || "[]"
);

let labelerId = "";

const supabaseUrl = "https://wpvypzxbkdflozuhwreo.supabase.co";
const supabaseAnonKey = "sb_publishable_TcwieLKitD8Zbi8tDB8GEA_64yKNW_u";
const supabase = window.supabase ? window.supabase.createClient(supabaseUrl, supabaseAnonKey) : null;

fetch("fallacy_dataset.json")
    .then(response => response.json())
    .then(data => {
        statements = data;
        showStatement();
    })
    .catch(() => {
        document.getElementById("statement").textContent =
            "Unable to load the dataset. Please make sure fallacy_dataset.json is available.";
    });

function showStatement() {
    if (!statements.length) {
        document.getElementById("statement").textContent =
            "No statements available.";
        document.getElementById("progress").textContent = "0 / 0";
        return;
    }

    if (currentStatement >= maxStatements) {
        document.getElementById("statement").textContent =
            "You finished all the statements!";
        document.getElementById("progress").textContent =
            `${maxStatements} / ${maxStatements}`;
        return;
    }

    currentNum = Math.floor(Math.random() * statements.length);
    while (usedStatements.includes(currentNum)) {
        currentNum = Math.floor(Math.random() * statements.length);
    }
    usedStatements.push(currentNum);

    document.getElementById("statement").textContent =
        statements[currentNum];

    document.getElementById("progress").textContent =
        `${currentStatement + 1} / ${maxStatements}`;
}

async function saveToSupabase({ mode, labeler, statement, fallacy }) {
    if (!supabase) return;

    try {
        const { error } = await supabase
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
        mode: "manual",
        labeler: labelerId,
        statement: statements[currentNum],
        fallacy
    };

    labels.push(response);
    localStorage.setItem(
        "fallacyLabels",
        JSON.stringify(labels)
    );

    await saveToSupabase(response);

    currentStatement++;
    showStatement();
}

document.querySelectorAll("[data-fallacy]").forEach(button => {
    button.addEventListener("click", () => {
        saveLabel(button.dataset.fallacy);
    });
});

document.getElementById("export").addEventListener("click", () => {
    const data = JSON.stringify(labels, null, 2);

    const blob = new Blob([data], {
        type: "application/json"
    });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "fallacy-labels.json";
    a.click();

    URL.revokeObjectURL(url);
});

const tutorialOverlay =
    document.getElementById("tutorialOverlay");

const tutorialButton =
    document.getElementById("tutorialButton");

const closeTutorial =
    document.getElementById("closeTutorial");

const startLabeling =
    document.getElementById("startLabeling");


tutorialButton.addEventListener("click", () => {
    tutorialOverlay.style.display = "flex";
});

closeTutorial.addEventListener("click", () => {
    tutorialOverlay.style.display = "none";
});

startLabeling.addEventListener("click", () => {
    tutorialOverlay.style.display = "none";
});

document.getElementById("startButton").addEventListener("click", () => {
    const input = document.getElementById("labelerId").value.trim();

    if (input === "") {
        alert("Please enter a labeler name.");
        return;
    }

    labelerId = input;

    document.getElementById("userSetup").style.display = "none";
    document.getElementById("labelingInterface").style.display = "block";

    tutorialOverlay.style.display = "flex";
    localStorage.setItem("fallacyTutorialSeen", "true");
});

showStatement();