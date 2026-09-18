let tweets = [];

let currentTweet = 0;
let maxTweets = 5;

let currentNum = 0;
let usedTweets = [];

let labels = JSON.parse(
    localStorage.getItem("tweetLabels") || "[]"
);

fetch("tweets.json")
    .then(response => response.json())
    .then(data => {
        tweets = data;
        showTweet();
    });

function showTweet() {
    if (currentTweet >= maxTweets) {
        document.getElementById("tweet").textContent =
            "You finished all the tweets!";
        document.getElementById("progress").textContent =
            `${maxTweets} / ${maxTweets}`;
        return;
    }

    currentNum = Math.floor(Math.random() * tweets.length);
    while (usedTweets.includes(currentNum)) {
        currentNum = Math.floor(Math.random() * tweets.length);
    }
    usedTweets.push(currentNum);

    document.getElementById("tweet").textContent =
        tweets[currentNum];

    document.getElementById("progress").textContent =
        `${currentTweet + 1} / ${maxTweets}`;
}

function saveLabel(emotion) {
    labels.push({
        labeler: labelerId,
        tweet: tweets[currentNum],
        emotion: emotion
    });

    localStorage.setItem(
        "tweetLabels",
        JSON.stringify(labels)
    );

    currentTweet++;
    showTweet();
}

document.querySelectorAll("[data-emotion]").forEach(button => {
    button.addEventListener("click", () => {
        saveLabel(button.dataset.emotion);
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
    a.download = "tweet-labels.json";
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

let labelerId = "";

document.getElementById("startButton").addEventListener("click", () => {
    const input = document.getElementById("labelerId").value.trim();

    if (input === "") {
        alert("Please enter a labeler ID.");
        return;
    }

    labelerId = input;

    document.getElementById("userSetup").style.display = "none";
    document.getElementById("labelingInterface").style.display = "block";

    tutorialOverlay.style.display = "flex";
    localStorage.setItem("tutorialSeen", "true");
});

showTweet();