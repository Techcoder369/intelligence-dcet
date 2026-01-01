/**
 * Dashboard Page JavaScript
 * Displays subject cards for DCET preparation
 */

document.addEventListener("DOMContentLoaded", async () => {
  if (!requireAuth()) return;

  const user = getUser();
  const userNameEl = document.getElementById("userName");
  if (userNameEl) {
    userNameEl.textContent = user?.dcet_reg_number || "Student";
  }

  await loadSubjects();
});

async function loadSubjects() {
  const subjectGrid = document.getElementById("subjectGrid");
  if (!subjectGrid) return;

  // loading state
  subjectGrid.innerHTML = `
    <article class="subject-card loading-card">
      <div class="spinner"></div>
      <p>Loading subjects...</p>
    </article>
  `;

  const result = await SubjectAPI.getAll();

  if (!result.success) {
    subjectGrid.innerHTML =
      '<div class="alert alert-error">Failed to load subjects. Please refresh the page.</div>';
    return;
  }

  const iconMap = {
    calculate: "\u{1F4D0}",             // 📐
    assignment: "\u{1F4CB}",           // 📋
    electrical_services: "\u26A1",     // ⚡
    analytics: "\u{1F4CA}",            // 📊
    computer: "\u{1F4BB}",             // 💻
  };

  subjectGrid.innerHTML = result.subjects
    .map((subject) => {
      const icon = iconMap[subject.icon] || "\u{1F4DA}"; // 📚 fallback
      const desc = subject.description || "Core concepts for DCET preparation";
      return `
        <article class="subject-card" data-subject-id="${subject.id}">
          <div class="subject-icon">${icon}</div>
          <h2 class="subject-title">${subject.name}</h2>
          <p class="subject-tagline">${desc}</p>
          <button class="btn-gradient" type="button">Start Practice →</button>
        </article>
      `;
    })
    .join("");

  // make the whole card clickable
  document.querySelectorAll(".subject-card").forEach((card) => {
    const id = card.dataset.subjectId;
    if (!id) return;

    card.addEventListener("click", () => {
      const selected = result.subjects.find((s) => String(s.id) === String(id));
      if (selected) {
        localStorage.setItem("selectedSubject", JSON.stringify(selected));
      }
      window.location.href = `/pages/subject.html?id=${id}`;
    });
  });
}
