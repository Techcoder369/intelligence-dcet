/**
 * Quiz Page JavaScript
 * Handles quiz generation, navigation, submission, and results
 */

let quizData = null;
let currentQuestion = 0;
let userAnswers = [];
let startTime = null;
let attemptId = null;

document.addEventListener("DOMContentLoaded", async function () {
  if (!requireAuth()) return;

  const config = JSON.parse(localStorage.getItem("quizConfig"));
  if (!config) {
    window.location.href = "/dashboard";
    return;
  }

  document.getElementById("quizTitle").textContent =
    `${config.subject_name} - Quiz`;

  await generateQuiz(config);
});

async function generateQuiz(config) {
  const loadingEl = document.getElementById("loadingState");
  const quizContentEl = document.getElementById("quizContent");

  loadingEl.classList.remove("hidden");
  quizContentEl.classList.add("hidden");

  const result = await QuizAPI.generate(
    config.subject_id,
    config.unit_id,
    config.difficulty,
    "quiz"
  );

  if (result.success && result.questions && result.questions.length > 0) {
    quizData = result;
    attemptId = result.attempt_id;
    userAnswers = new Array(result.questions.length).fill(-1);
    startTime = Date.now();

    loadingEl.classList.add("hidden");
    quizContentEl.classList.remove("hidden");

    renderQuestion();
    updateProgress();
  } else {
    loadingEl.innerHTML = `
      <div class="alert alert-error">
        ${result.message || "Failed to generate quiz. Please try again."}
      </div>
      <a href="/dashboard" class="btn btn-primary">Back to Dashboard</a>
    `;
  }
}

function renderQuestion() {
  const question = quizData.questions[currentQuestion];
  const questionCard = document.getElementById("questionCard");

  const letters = ["A", "B", "C", "D", "E", "F"];

  questionCard.innerHTML = `
    <div class="question-number">
      Question ${currentQuestion + 1} of ${quizData.questions.length}
    </div>
    <div class="question-text">${question.question}</div>
    <ul class="options-list">
      ${question.options
        .map(
          (option, index) => `
        <li class="option-item">
          <button type="button"
                  class="option-btn ${
                    userAnswers[currentQuestion] === index ? "selected" : ""
                  }"
                  data-index="${index}">
            <span class="option-label-badge">
              ${letters[index] || String.fromCharCode(65 + index)}
            </span>
            <span class="option-text">${option}</span>
          </button>
        </li>
      `
        )
        .join("")}
    </ul>
  `;

  // attach click handlers to buttons
  document.querySelectorAll(".option-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const index = parseInt(btn.dataset.index, 10);
      userAnswers[currentQuestion] = index;

      document
        .querySelectorAll(".option-btn")
        .forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");

      updateProgress();
    });
  });

  updateNavButtons();
}

function updateProgress() {
  const progressBar = document.getElementById("progressBar");
  const progressText = document.getElementById("progressText");
  const answered = userAnswers.filter((a) => a !== -1).length;
  const total = quizData.questions.length;
  const percentage = (answered / total) * 100;

  progressBar.style.width = `${percentage}%`;
  progressText.textContent = `${answered} of ${total} answered`;
}

function updateNavButtons() {
  const prevBtn = document.getElementById("prevBtn");
  const nextBtn = document.getElementById("nextBtn");
  const submitBtn = document.getElementById("submitBtn");

  prevBtn.disabled = currentQuestion === 0;

  if (currentQuestion === quizData.questions.length - 1) {
    nextBtn.classList.add("hidden");
    submitBtn.classList.remove("hidden");
  } else {
    nextBtn.classList.remove("hidden");
    submitBtn.classList.add("hidden");
  }
}

document.getElementById("prevBtn").addEventListener("click", function () {
  if (currentQuestion > 0) {
    currentQuestion--;
    renderQuestion();
  }
});

document.getElementById("nextBtn").addEventListener("click", function () {
  if (currentQuestion < quizData.questions.length - 1) {
    currentQuestion++;
    renderQuestion();
  }
});

document.getElementById("submitBtn").addEventListener("click", async function () {
  const unanswered = userAnswers.filter((a) => a === -1).length;

  if (unanswered > 0) {
    const confirmSubmit = confirm(
      `You have ${unanswered} unanswered questions. Are you sure you want to submit?`
    );
    if (!confirmSubmit) return;
  }

  this.disabled = true;
  this.innerHTML =
    '<span class="spinner" style="width:20px;height:20px;border-width:2px;"></span> Submitting...';

  const timeSpent = Math.round((Date.now() - startTime) / 1000);
  const result = await QuizAPI.submit(attemptId, userAnswers, timeSpent);

  if (result.success) {
    showResults(result);
  } else {
    alert("Failed to submit quiz. Please try again.");
    this.disabled = false;
    this.innerHTML = "Submit Quiz";
  }
});

function showResults(result) {
  const quizContent = document.getElementById("quizContent");
  const letters = ["A", "B", "C", "D", "E", "F"];

  quizContent.innerHTML = `
    <div class="results-card">
      <div class="score-circle">
        <div class="score-value">${result.percentage}%</div>
        <div class="score-label">${result.score}/${result.total} correct</div>
      </div>
      <h2>Quiz Completed!</h2>
      <p style="color: var(--muted); margin-bottom: 2rem;">
        Time spent: ${Math.floor(result.time_spent_seconds / 60)}m ${
    result.time_spent_seconds % 60
  }s
      </p>
      <div class="quiz-nav">
        <button class="btn btn-secondary" onclick="toggleExplanations()">
          View Explanations
        </button>
        <a href="/dashboard" class="btn btn-primary">Back to Dashboard</a>
      </div>
    </div>

    <div id="explanations" class="hidden" style="margin-top: 2rem;">
      ${result.results
        .map(
          (r, i) => `
        <div class="question-card">
          <div class="question-number">Question ${i + 1}</div>
          <div class="question-text">${r.question}</div>
          <ul class="options-list">
            ${r.options
              .map(
                (opt, j) => `
              <li class="option-item">
                <button type="button"
                        class="option-btn
                          ${j === r.correct_index ? "correct" : ""}
                          ${
                            j === r.user_answer && j !== r.correct_index
                              ? "incorrect"
                              : ""
                          }">
                  <span class="option-label-badge">
                    ${letters[j] || String.fromCharCode(65 + j)}
                  </span>
                  <span class="option-text">
                    ${opt}
                    ${
                      j === r.correct_index
                        ? " <strong>(Correct)</strong>"
                        : ""
                    }
                    ${
                      j === r.user_answer && j !== r.correct_index
                        ? " <strong>(Your answer)</strong>"
                        : ""
                    }
                  </span>
                </button>
              </li>
            `
              )
              .join("")}
          </ul>
          <div style="margin-top: 1rem; padding: 1rem; background: rgba(15,23,42,0.8); border-radius: 18px; border:1px solid rgba(148,163,184,0.5);">
            <strong>Explanation:</strong> ${r.explanation}
          </div>
        </div>
      `
        )
        .join("")}
    </div>
  `;
}

function toggleExplanations() {
  const explanations = document.getElementById("explanations");
  explanations.classList.toggle("hidden");
}
