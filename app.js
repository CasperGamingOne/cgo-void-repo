document.addEventListener("DOMContentLoaded", () => {
  // Setup copy buttons
  document.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const targetId = btn.getAttribute("data-target");
      const targetEl = document.getElementById(targetId);
      if (!targetEl) return;

      const text = targetEl.innerText.trim();
      try {
        await navigator.clipboard.writeText(text);
        const originalText = btn.innerText;
        btn.innerText = "Copied!";
        btn.classList.add("copied");
        setTimeout(() => {
          btn.innerText = originalText;
          btn.classList.remove("copied");
        }, 2000);
      } catch (err) {
        console.error("Clipboard copy failed: ", err);
      }
    });
  });

  // Package search filter
  const searchInput = document.getElementById("pkg-search");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      const query = e.target.value.toLowerCase().trim();
      const rows = document.querySelectorAll(".pkg-row");
      rows.forEach((row) => {
        const text = row.innerText.toLowerCase();
        row.style.display = text.includes(query) ? "" : "none";
      });
    });
  }
});
