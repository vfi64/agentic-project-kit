/* Progressive search only; the shared task contracts remain visible without JS. */
(() => {
  const search = document.getElementById("task-search");
  if (!search) return;
  const cards = Array.from(document.querySelectorAll(".task-card"));
  function apply() {
    const query = search.value.toLowerCase().trim();
    for (const card of cards) {
      card.hidden = !card.dataset.taskText.toLowerCase().includes(query);
    }
    for (const group of document.querySelectorAll("[data-task-phase]")) {
      group.hidden = !Array.from(group.querySelectorAll(".task-card")).some(card => !card.hidden);
    }
    document.getElementById("task-filter-status").textContent =
      cards.filter(card => !card.hidden).length + " matching tasks";
  }
  search.disabled = false;
  search.addEventListener("input", apply);
  apply();
})();
