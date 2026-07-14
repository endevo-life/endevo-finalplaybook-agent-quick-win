import { PLAYBOOK_NAME, PRODUCT_NAME, TAGLINE, SEAL_LABELS, BADGE_COPY } from "../config/branding";
import { sealedDomains, playbookComplete } from "./completion";
import endevoLogo from "../assets/logo/footer-logo-light.png";

// Fetch the ENDevo logo as a base64 data URI so it embeds INLINE in the print
// window (which can't reliably load bundled asset URLs). Cached after first use.
let _logoDataUri = null;
async function endevoLogoDataUri() {
  if (_logoDataUri) return _logoDataUri;
  try {
    const res = await fetch(endevoLogo);
    const blob = await res.blob();
    _logoDataUri = await new Promise((resolve) => {
      const r = new FileReader();
      r.onloadend = () => resolve(r.result);
      r.readAsDataURL(blob);
    });
  } catch {
    _logoDataUri = ""; // fall back to no image if it can't load
  }
  return _logoDataUri;
}

// Generate a downloadable PDF of the member's playbook WITHOUT a heavy library:
// open a print-optimized document and invoke the browser's native
// print-to-PDF. Works in every browser, adds zero dependencies, and the output
// is a clean, family-usable document, branded "My Final Playbook, Powered by
// ENDevo" with a tiled ENDevo watermark so it can't be cleanly repurposed.
//
// items: [{ id, title, action, domain, steps[], locked }]
// doneKeys: Set-like with .has(`${id}::${stepIndex}`)
export async function downloadPlaybookPdf({ name, items, doneKeys, fieldValues = {} }) {
  const title = name ? `${escapeHtml(name)}'s ${PLAYBOOK_NAME}` : PLAYBOOK_NAME;
  // Open the print window NOW, in the click handler, so the popup blocker allows
  // it (must happen before any await). Fill it once the logo has loaded.
  const w = window.open("", "_blank");
  if (!w) {
    alert("Please allow pop-ups to download your playbook.");
    return;
  }
  const logo = await endevoLogoDataUri();

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
      // The member's entered details (trusted person, phone, dates, ...) — the
      // actual usable content of the playbook.
      const details = (it.fields || [])
        .map((f) => ({ label: f.label, value: (fieldValues[`${it.id}::${f.key}`] || "").trim() }))
        .filter((f) => f.value)
        .map((f) => `<tr><th>${escapeHtml(f.label)}</th><td>${escapeHtml(prettyDate(f.value))}</td></tr>`)
        .join("");
      return `
        <section class="item">
          <h2>${escapeHtml(it.title || it.action)}</h2>
          ${it.domain ? `<p class="domain">${escapeHtml(it.domain)}</p>` : ""}
          ${it.title && it.action ? `<p class="action">${escapeHtml(it.action)}</p>` : ""}
          ${details ? `<table class="details">${details}</table>` : ""}
          ${rows ? `<ol class="steps">${rows}</ol>` : ""}
        </section>`;
    })
    .join("");

  // Earned seals + the complete badge print on the document, dated, so the
  // family can see the work was finished and when.
  const stampDate = new Date().toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
  const sealed = sealedDomains(items, doneKeys);
  const sealsHtml = sealed.length
    ? `<div class="seals">${sealed
        .map((d) => `<span class="seal"><span class="seal-tick">✓</span>${escapeHtml(SEAL_LABELS[d] || d)} · ${stampDate}</span>`)
        .join("")}</div>`
    : "";
  const badgeHtml = playbookComplete(items, doneKeys)
    ? `<div class="badge"><span class="badge-star">★</span>
         <span class="badge-title">${escapeHtml(BADGE_COPY.title)}</span>
         ${name ? `<span class="badge-name">${escapeHtml(name)}</span>` : ""}
         <span class="badge-when">${stampDate}</span>
         <span class="badge-sub">${escapeHtml(BADGE_COPY.sub)}</span></div>`
    : "";

  const html = `<!doctype html><html><head><meta charset="utf-8"><title>${title}</title>
  <style>
    @page { margin: 22mm 18mm; }
    * { box-sizing: border-box; }
    html { position: relative; }
    body { font: 12pt/1.55 Georgia, "Times New Roman", serif; color: #08123A; margin: 0;
           position: relative; z-index: 1; }
    /* Tiled ENDevo watermark behind everything, faint, so the PDF can't be
       cleanly repurposed. Fixed so it repeats on every printed page. */
    ${logo ? `
    body::before {
      content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
      background-image: url("${logo}");
      background-repeat: repeat; background-size: 150px auto; opacity: 0.05;
      -webkit-print-color-adjust: exact; print-color-adjust: exact;
    }
    ` : ""}
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
    table.details { border-collapse: collapse; margin: 4px 0 8px; }
    table.details th { text-align: left; font: 600 9.5pt/1.4 -apple-system, Segoe UI, sans-serif;
      color: #45507A; padding: 2px 14px 2px 0; vertical-align: top; white-space: nowrap; }
    table.details td { padding: 2px 0; font-weight: 600; }
    .seals { display: flex; flex-wrap: wrap; gap: 8px; margin: 0 0 20px; }
    .seal { display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px;
            border: 1px solid #B08D57; border-radius: 999px; background: #FBF5E9;
            color: #6E5327; font: 700 9.5pt/1.1 Georgia, serif;
            -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .seal-tick { display: inline-flex; align-items: center; justify-content: center;
                 width: 15px; height: 15px; border-radius: 50%; background: #B08D57;
                 color: #FFF9EC; font-size: 9pt; }
    .badge { break-inside: avoid; text-align: center; margin: 6px 0 20px; padding: 16px;
             border: 2px solid #B08D57; border-radius: 12px; background: #FCF7EC;
             -webkit-print-color-adjust: exact; print-color-adjust: exact; }
    .badge-star { display: block; font-size: 20pt; color: #B08D57; line-height: 1; }
    .badge-title { display: block; font: 700 14pt/1.3 Georgia, serif; color: #08123A; }
    .badge-name { display: block; font: 600 10.5pt/1.2 Georgia, serif; color: #6E5327; }
    .badge-when { display: block; font: 500 9pt/1.3 -apple-system, Segoe UI, sans-serif; color: #94793F; }
    .badge-sub { display: block; font: 400 9.5pt/1.35 -apple-system, Segoe UI, sans-serif; color: #7C86A8; }
    footer { margin-top: 26px; padding-top: 12px; border-top: 1px solid #D5D1C7;
             font: 9pt/1.4 -apple-system, Segoe UI, sans-serif; color: #9AA1B8; }
    .footer-brand { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
    .footer-brand img { height: 22px; width: auto; }
    .footer-brand span { font: 700 10pt/1 Georgia, serif; color: #08123A; }
    .footer-brand small { font: 600 8pt/1 -apple-system, Segoe UI, sans-serif;
      letter-spacing: .06em; text-transform: uppercase; color: #7C86A8; }
  </style></head>
  <body>
    <div class="cover">
      <p class="kicker">${escapeHtml(PRODUCT_NAME)}</p>
      <h1>${title}</h1>
      <p class="tag">${escapeHtml(TAGLINE)}</p>
    </div>
    ${badgeHtml}
    ${sealsHtml}
    ${sections}
    <footer>
      <div class="footer-brand">
        ${logo ? `<img src="${logo}" alt="ENDevo">` : ""}
        <span>${escapeHtml(PLAYBOOK_NAME)}</span>
        <small>Powered by ENDevo</small>
      </div>
      Educational only. Not legal, financial, or medical advice.<br>
      Keep this document with your important papers and tell your trusted person where it lives.<br>
      &copy; ENDevo · endevo.life · This document is personal to its owner and not for redistribution.
    </footer>
  </body></html>`;

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

function prettyDate(v) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec((v || "").trim());
  if (!m) return v;
  const d = new Date(+m[1], +m[2] - 1, +m[3]);
  if (isNaN(d)) return v;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function escapeHtml(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}
