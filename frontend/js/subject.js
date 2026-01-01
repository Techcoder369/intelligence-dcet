/**
 * Subject Detail Page JavaScript
 * Handles unit, mode, and difficulty selection
 */

let selectedUnit = null;
let selectedMode = null;
let selectedDifficulty = null;
let subjectData = null;

document.addEventListener('DOMContentLoaded', async function () {
  if (!requireAuth()) return;

  const urlParams = new URLSearchParams(window.location.search);
  const subjectId = urlParams.get('id');

  if (!subjectId) {
    window.location.href = '/dashboard';
    return;
  }

  await loadSubjectDetails(subjectId);
  setupEventListeners();
});

async function loadSubjectDetails(subjectId) {
  const result = await SubjectAPI.getById(subjectId);

  if (result.success) {
    subjectData = result;
    document.getElementById('subjectName').textContent = result.subject.name;

    const unitGrid = document.getElementById('unitGrid');
    unitGrid.innerHTML = result.units
      .map(
        (unit) => `
        <button class="unit-card" data-unit-id="${unit.id}">
          ${unit.name}
        </button>
      `
      )
      .join('');
  } else {
    alert('Failed to load subject details');
    window.location.href = '/dashboard';
  }
}

function setupEventListeners() {
  // Units
  document.getElementById('unitGrid').addEventListener('click', function (e) {
    const target = e.target;
    if (target.classList.contains('unit-card')) {
      document
        .querySelectorAll('.unit-card')
        .forEach((btn) => btn.classList.remove('selected'));
      target.classList.add('selected');
      selectedUnit = parseInt(target.dataset.unitId, 10);
      checkCanStart();
    }
  });

  // Mode
  document.querySelectorAll('.mode-btn').forEach((btn) => {
    btn.addEventListener('click', function () {
      document
        .querySelectorAll('.mode-btn')
        .forEach((b) => b.classList.remove('selected'));
      this.classList.add('selected');
      selectedMode = this.dataset.mode;
      checkCanStart();
    });
  });

  // Difficulty
  document.querySelectorAll('.difficulty-btn').forEach((btn) => {
    btn.addEventListener('click', function () {
      document
        .querySelectorAll('.difficulty-btn')
        .forEach((b) => b.classList.remove('selected'));
      this.classList.add('selected');
      selectedDifficulty = this.dataset.difficulty;
      checkCanStart();
    });
  });

  // Start
  document.getElementById('startBtn').addEventListener('click', startSession);
}

function checkCanStart() {
  const startBtn = document.getElementById('startBtn');
  if (selectedUnit && selectedMode && selectedDifficulty) {
    startBtn.disabled = false;
  } else {
    startBtn.disabled = true;
  }
}

async function startSession() {
  const startBtn = document.getElementById('startBtn');
  startBtn.disabled = true;
  startBtn.innerHTML =
    '<span class="spinner" style="width:20px;height:20px;border-width:2px;"></span> Generating...';

  const urlParams = new URLSearchParams(window.location.search);
  const subjectId = urlParams.get('id');

  localStorage.setItem(
    'quizConfig',
    JSON.stringify({
      subject_id: parseInt(subjectId, 10),
      unit_id: selectedUnit,
      difficulty: selectedDifficulty,
      mode: selectedMode,
      subject_name: subjectData.subject.name,
    })
  );

  if (selectedMode === 'quiz') {
    window.location.href = '/pages/quiz.html';
  } else {
    window.location.href = '/pages/flashcard.html';
  }
}
