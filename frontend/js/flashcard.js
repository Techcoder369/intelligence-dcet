/**
 * Flashcard Page JavaScript
 * Handles flashcard generation, flip animation, and adaptive repetition
 */

let flashcardData = null;
let cardsKnown = 0;
let cardsUnknown = 0;
let startTime = null;
let sessionId = null;
let cardQueue = [];
let isFlipped = false;

document.addEventListener("DOMContentLoaded", async function () {
  if (!requireAuth()) return;

  const config = JSON.parse(localStorage.getItem("quizConfig"));
  if (!config) {
    window.location.href = "/dashboard";
    return;
  }

  document.getElementById("flashcardTitle").textContent =
    `${config.subject_name} - Flashcards`;

  await generateFlashcards(config);
});

async function generateFlashcards(config) {
  const loadingEl = document.getElementById("loadingState");
  const flashcardContentEl = document.getElementById("flashcardContent");

  loadingEl.classList.remove("hidden");
  flashcardContentEl.classList.add("hidden");

  const result = await QuizAPI.generate(
    config.subject_id,
    config.unit_id,
    config.difficulty,
    "flashcard"
  );

  if (result.success && result.flashcards && result.flashcards.length > 0) {
    flashcardData = result;
    sessionId = result.session_id;
    startTime = Date.now();

    cardQueue = flashcardData.flashcards.map((_, i) => i);

    loadingEl.classList.add("hidden");
    flashcardContentEl.classList.remove("hidden");

    renderCard();
    updateProgress();
  } else {
    loadingEl.innerHTML = `
      <div class="alert alert-error">
        ${result.message || "Failed to generate flashcards. Please try again."}
      </div>
      <a href="/dashboard" class="btn btn-primary">Back to Dashboard</a>
    `;
  }
}

function renderCard() {
  if (cardQueue.length === 0) {
    showResults();
    return;
  }

  const cardIndex = cardQueue[0];
  const card = flashcardData.flashcards[cardIndex];

  const flashcard = document.getElementById("flashcard");
  flashcard.classList.remove("flipped");
  isFlipped = false;

  document.getElementById("frontContent").textContent = card.front;
  document.getElementById("backContent").textContent = card.back;
}

function updateProgress() {
  const progressText = document.getElementById("progressText");
  const remaining = cardQueue.length;
  const reviewed = cardsKnown + cardsUnknown;
  progressText.textContent = `${reviewed} reviewed | ${remaining} remaining`;
}

document.getElementById("flashcard").addEventListener("click", function () {
  this.classList.toggle("flipped");
  isFlipped = !isFlipped;
});

document.getElementById("knowBtn").addEventListener("click", function () {
  if (!isFlipped) {
    document.getElementById("flashcard").classList.add("flipped");
    isFlipped = true;
    return;
  }

  cardsKnown++;
  cardQueue.shift();

  updateProgress();
  renderCard();
});

document.getElementById("dontKnowBtn").addEventListener("click", function () {
  if (!isFlipped) {
    document.getElementById("flashcard").classList.add("flipped");
    isFlipped = true;
    return;
  }

  cardsUnknown++;

  const currentCardIndex = cardQueue.shift();
  const insertPosition = Math.min(3, cardQueue.length);
  cardQueue.splice(insertPosition, 0, currentCardIndex);

  updateProgress();
  renderCard();
});

async function showResults() {
  const timeSpent = Math.round((Date.now() - startTime) / 1000);
  await QuizAPI.completeFlashcard(sessionId, cardsKnown, cardsUnknown, timeSpent);

  const flashcardContent = document.getElementById("flashcardContent");
  const total = flashcardData.flashcards.length;
  const reviewed = cardsKnown + cardsUnknown || 1;
  const knownPercentage = Math.round((cardsKnown / reviewed) * 100);
  const timeLabel = `${Math.floor(timeSpent / 60)}m ${timeSpent % 60}s`;

  flashcardContent.innerHTML = `
    <div class="session-complete-card">
      <div class="session-main">
        <!-- ROUND PERCENTAGE CIRCLE -->
        <div class="score-circle">
          <div class="score-inner">
            <div class="score-value">${knownPercentage}%</div>
            <div class="score-label">Mastery</div>
          </div>
        </div>

        <!-- TEXT STATS -->
        <div class="session-text">
          <h2 class="session-title">Session Complete!</h2>
          <ul class="session-metrics">
            <li><span>${cardsKnown}</span> Cards Known</li>
            <li><span>${cardsUnknown}</span> Cards to Review</li>
            <li><span>${total}</span> Total Cards</li>
            <li><span>${timeLabel}</span> Time Spent</li>
          </ul>
        </div>
      </div>

      <div class="session-actions">
        <button class="btn btn-secondary" onclick="location.reload()">
          Practice Again
        </button>
        <a href="/dashboard" class="btn btn-primary">
          Back to Dashboard
        </a>
      </div>
    </div>
  `;
}

