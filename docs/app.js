document.addEventListener("DOMContentLoaded", () => {
  // Setup copy buttons for terminal install instructions
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

  // Architecture Channel Switcher
  const tabBtns = document.querySelectorAll(".arch-tab-btn");
  const channelViews = {
    v3: document.getElementById("view-channel-v3"),
    generic: document.getElementById("view-channel-generic"),
  };

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const channel = btn.getAttribute("data-channel");
      tabBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      Object.keys(channelViews).forEach((key) => {
        if (channelViews[key]) {
          channelViews[key].style.display = key === channel ? "block" : "none";
        }
      });
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

  // Package Request Form Handler
  const reqForm = document.getElementById("package-request-form");

  function getFormData() {
    const pkgname = document.getElementById("req-pkgname")?.value.trim() || "";
    const homepage = document.getElementById("req-homepage")?.value.trim() || "";
    const upstream = document.getElementById("req-upstream")?.value.trim() || "";
    const version = document.getElementById("req-version")?.value.trim() || "";
    const buildSystem = document.getElementById("req-buildsystem")?.value || "";
    const license = document.getElementById("req-license")?.value.trim() || "";
    const description = document.getElementById("req-description")?.value.trim() || "";
    const dependencies = document.getElementById("req-dependencies")?.value.trim() || "";
    const contact = document.getElementById("req-contact")?.value.trim() || "";
    const notes = document.getElementById("req-notes")?.value.trim() || "";

    return {
      pkgname,
      homepage,
      upstream,
      version,
      buildSystem,
      license,
      description,
      dependencies,
      contact,
      notes
    };
  }

  if (reqForm) {
    reqForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const data = getFormData();

      if (!data.pkgname || !data.homepage || !data.upstream || !data.description || !data.contact) {
        alert("Please complete all required fields: Package Name, Homepage, Source Repository, Description, and Discord Handle.");
        return;
      }

      // Construct GitHub prefilled issue URL
      const repoUrl = "https://github.com/CasperGamingOne/cgo-void-repo";
      const params = new URLSearchParams();
      params.append("template", "package_request.yml");
      params.append("title", `[Package Request]: ${data.pkgname}`);
      params.append("pkgname", data.pkgname);
      params.append("homepage", data.homepage);
      params.append("upstream_repo", data.upstream);
      params.append("version", data.version);
      params.append("build_system", data.buildSystem);
      params.append("license", data.license);
      params.append("description", data.description);
      if (data.dependencies) params.append("dependencies", data.dependencies);
      if (data.contact) params.append("contact", data.contact);
      if (data.notes) params.append("notes", data.notes);

      const targetUrl = `${repoUrl}/issues/new?${params.toString()}`;

      // Open GitHub issue page in new tab
      window.open(targetUrl, "_blank", "noopener,noreferrer");
    });
  }
});
