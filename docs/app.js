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

  // Package Request Form Logic
  const reqForm = document.getElementById("package-request-form");
  const copyMdBtn = document.getElementById("copy-request-md-btn");

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

    const voidSpecs = [];
    document.querySelectorAll(".req-void-spec:checked").forEach((chk) => {
      voidSpecs.push(chk.value);
    });

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
      notes,
      voidSpecs
    };
  }

  function generateMarkdown(data) {
    let md = `### 📦 Package Request: \`${data.pkgname || "package-name"}\`\n\n`;
    md += `- **Official Homepage:** ${data.homepage || "N/A"}\n`;
    md += `- **Source Repository:** ${data.upstream || "N/A"}\n`;
    md += `- **Latest Version / Release URL:** ${data.version || "N/A"}\n`;
    md += `- **Build System:** ${data.buildSystem || "N/A"}\n`;
    md += `- **License:** ${data.license || "N/A"}\n`;
    md += `- **Requester Contact:** ${data.contact || "GitHub User"}\n\n`;
    md += `#### Description & Purpose\n${data.description || "N/A"}\n\n`;

    if (data.dependencies) {
      md += `#### Known Dependencies\n\`\`\`\n${data.dependencies}\n\`\`\`\n\n`;
    }

    if (data.voidSpecs.length > 0) {
      md += `#### Void Linux Considerations\n`;
      data.voidSpecs.forEach((spec) => {
        md += `- [x] ${spec}\n`;
      });
      md += `\n`;
    }

    if (data.notes) {
      md += `#### Additional Context / Notes\n${data.notes}\n\n`;
    }

    md += `---\n*Submitted via [cgo-void-repo Web Request Form](https://caspergamingone.github.io/cgo-void-repo/#request)*`;
    return md;
  }

  if (reqForm) {
    reqForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const data = getFormData();

      if (!data.pkgname || !data.homepage || !data.upstream || !data.description || !data.contact) {
        alert("Please complete the required fields: Package Name, Homepage, Source Repository, Description, and Discord Handle.");
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

  if (copyMdBtn) {
    copyMdBtn.addEventListener("click", async () => {
      const data = getFormData();
      const md = generateMarkdown(data);
      try {
        await navigator.clipboard.writeText(md);
        const originalText = copyMdBtn.innerText;
        copyMdBtn.innerText = "✓ Markdown Copied!";
        copyMdBtn.classList.add("copied");
        setTimeout(() => {
          copyMdBtn.innerText = originalText;
          copyMdBtn.classList.remove("copied");
        }, 2500);
      } catch (err) {
        console.error("Failed to copy markdown: ", err);
      }
    });
  }
});
