import { PLAYBOOK_NAME, PRODUCT_NAME, TAGLINE } from "../config/branding";

// Generate a downloadable PDF of the member's playbook WITHOUT a heavy library:
// open a print-optimized document and invoke the browser's native
// print-to-PDF. Works in every browser, adds zero dependencies, and the output
// is a clean, family-usable document.
//
// items: [{ id, title, action, domain, steps[], locked }]
// doneKeys: Set-like with .has(`${id}::${stepIndex}`)
export function downloadPlaybookPdf({ name, items, doneKeys }) {
  const title = name ? `${escapeHtml(name)}'s ${PLAYBOOK_NAME}` : PLAYBOOK_NAME;

  const sections = items
    .filter((it) => !it.locked) // only the unlocked (owned) items go in the PDF
    .map((it) => {
      const steps = it.steps || [];
      const rows = steps
        .map((s, i) => {
          const done = doneKeys.has(`${it.id}::${i}`);
          return `<li class="${done ? "done" : ""}">${escapeHtml(s)}</li>`;
        })
        .join("");
      return `
        <section class="item">
          <h2>${escapeHtml(it.title || it.action)}</h2>
          ${it.domain ? `<p class="domain">${escapeHtml(it.domain)}</p>` : ""}
          ${it.title && it.action ? `<p class="action">${escapeHtml(it.action)}</p>` : ""}
          ${rows ? `<ol class="steps">${rows}</ol>` : ""}
        </section>`;
    })
    .join("");

  const html = `<!doctype html><html><head><meta charset="utf-8"><title>${title}</title>
  <style>
    @page { margin: 22mm 18mm; }
    * { box-sizing: border-box; }
    body { font: 12pt/1.55 Georgia, "Times New Roman", serif; color: #08123A; margin: 0; }
    .cover { border-bottom: 3px solid #FF5D00; padding-bottom: 14px; margin-bottom: 22px; }
    .kicker { font: 600 10pt/1 -apple-system, Segoe UI, sans-serif; letter-spacing: .12em;
              text-transform: uppercase; color: #2E7F7B; margin: 0 0 6px; }
    h1 { font-size: 26pt; margin: 0 0 4px; letter-spacing: -0.01em; }
    .tag { font-style: italic; color: #45507A; margin: 0; }
    .item { break-inside: avoid; margin: 0 0 18px; padding: 0 0 4px; }
    .item h2 { font-size: 14pt; margin: 0 0 2px; }
    .domain { font: 600 8.5pt/1 -apple-system, Segoe UI, sans-serif; letter-spacing: .08em;
              text-transform: uppercase; color: #7C86A8; margin: 0 0 4px; }
    .action { margin: 0 0 8px; color: #45507A; }
    ol.steps { margin: 4px 0 0; padding-left: 20px; }
    ol.steps li { margin: 3px 0; }
    ol.steps li.done { color: #2E7F7B; text-decoration: line-through; }
    footer { margin-top: 26px; padding-top: 12px; border-top: 1px solid #D5D1C7;
             font: 9pt/1.4 -apple-system, Segoe UI, sans-serif; color: #9AA1B8; }
  </style></head>
  <body>
    <div class="cover">
      <p class="kicker">${escapeHtml(PRODUCT_NAME)}</p>
      <h1>${title}</h1>
      <p class="tag">${escapeHtml(TAGLINE)}</p>
    </div>
    ${sections}
    <footer>
      ${escapeHtml(PRODUCT_NAME)} · Educational only. Not legal, financial, or medical advice.<br>
      Keep this document with your important papers and tell your trusted person where it lives.
    </footer>
  </body></html>`;

  const w = window.open("", "_blank");
  if (!w) {
    alert("Please allow pop-ups to download your playbook.");
    return;
  }
  w.document.open();
  w.document.write(html);
  w.document.close();
  // Give the new document a tick to lay out, then open the print dialog
  // (where the user picks "Save as PDF").
  w.onload = () => {
    w.focus();
    w.print();
  };
}

function escapeHtml(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}
